"""LLM explanation adapter: number/notice/wording checks, fallback, env factory. No network."""
from __future__ import annotations

import logging
import threading
import time

import pytest
import requests
from pathfinder_ml import FLAG_TEXT

from avenir_adapters.llm import LlmExplanation, writer_from_env
from avenir_adapters.llm import writer as llm_writer
from avenir_adapters.llm.writer import allowed_numbers, numbers_in
from avenir_contracts.metric import Metric
from avenir_contracts.models import (
    Career,
    Components,
    ComponentScore,
    Explanation,
    Pick,
    RecommendationOut,
)
from avenir_contracts.ports import TemplateExplanation

NOTICE = FLAG_TEXT["covid_year"]
GOOD = (
    "Architects are worth exploring. Median pay is £56,914 a year. "
    f"{NOTICE}"
)


def _cs(score: float) -> ComponentScore:
    return ComponentScore(score=score, confidence="medium")


def _rec(notices: list[str] | None = None) -> RecommendationOut:
    pay = Metric(value=56914.3, unit="gbp_per_year", as_of="2025", source="ashe", confidence="high")
    career = Career(soc2020="2451", title="Architect", official_title="Architects",
                    metrics={"pay_median": pay})
    comps = Components(fit=_cs(80), expected_return=_cs(70), market_risk=_cs(30),
                       disruption_risk=_cs(20), risk=_cs(25))
    pick = Pick(tier="ambitious", career=career, components=comps, vs_first_idea={},
                reasons=["Median pay £56,914 a year (ASHE 2025)."])
    return RecommendationOut(
        first_idea=None, first_idea_components=None, picks=[pick], hedge=None, roadmap=None,
        notices=[NOTICE] if notices is None else notices,
        explanation=Explanation(text="template", ai_written=False))


class _Resp:
    def __init__(self, content: str | None, status: int = 200) -> None:
        self.status_code = status
        self._content = content

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def _writer(**kw) -> LlmExplanation:
    return LlmExplanation("http://llm.test/v1/", "k", "m", **kw)


def _patch_post(monkeypatch, content: str | None, calls: list | None = None, status: int = 200) -> None:
    def fake(url, headers=None, json=None, timeout=None):
        if calls is not None:
            calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _Resp(content, status)
    monkeypatch.setattr(requests, "post", fake)


def _is_template(exp: Explanation, rec: RecommendationOut) -> bool:
    return exp == TemplateExplanation().explain(rec) and exp.ai_written is False


# ---------- normalisation ----------

@pytest.mark.parametrize("text,expected", [
    ("£56,914", {"56914"}),
    ("56914.0", {"56914"}),
    ("0.350", {"0.35"}),
    ("+1.2%", {"1.2"}),
    ("-3.5%", {"-3.5"}),
    ("in 2025 about 12", {"2025", "12"}),
    ("2020-21", {"2020", "21"}),
    ("ends £56,914.", {"56914"}),
])
def test_numbers_in_normalises(text, expected):
    assert numbers_in(text) == expected


def test_allowed_numbers_formats_and_strings():
    allowed = allowed_numbers(_rec())
    assert {"56914", "56914.3", "2025"} <= allowed
    assert "57000" not in allowed
    assert {"70", "80"} <= allowed  # component scores


def test_allowed_numbers_percent_for_small_values():
    rec = _rec()
    rec.picks[0].career.metrics["x"] = Metric(value=0.012, unit="share", source="s", confidence="low")
    assert {"0.01", "0.012"} & allowed_numbers(rec)
    assert {"1", "1.2"} <= allowed_numbers(rec)


def test_allowed_numbers_ignores_bool():
    rec = _rec()
    rec.picks[0].career.metrics["x"] = Metric(value=1.0, unit="count", source="s", confidence="low",
                                              extra={"flag": True})
    assert "True" not in allowed_numbers(rec)
    assert "True" not in numbers_in("True")


# ---------- explain ----------

def test_good_text_is_accepted(monkeypatch):
    calls: list = []
    _patch_post(monkeypatch, GOOD + "  ", calls)
    exp = _writer().explain(_rec())
    assert exp.ai_written is True
    assert exp.text == GOOD
    assert "56914" in exp.cited_numbers
    call = calls[0]
    assert call["url"] == "http://llm.test/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer k"
    assert call["json"]["model"] == "m"
    assert call["json"]["temperature"] == 0.2
    assert call["json"]["max_tokens"] == 300


def test_invented_number_falls_back(monkeypatch):
    _patch_post(monkeypatch, GOOD.replace("£56,914", "£57,000"))
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


def test_missing_notice_falls_back(monkeypatch):
    _patch_post(monkeypatch, "Architects are worth exploring. Median pay is £56,914 a year.")
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


@pytest.mark.parametrize("phrase", ["You should", "you should", "Don't", "don't", "Don’t"])
def test_banned_wording_falls_back(monkeypatch, phrase):
    _patch_post(monkeypatch, GOOD + f" {phrase} wait.")
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


@pytest.mark.parametrize("content,status", [("", 200), (None, 200), ("   ", 200), (GOOD, 500)])
def test_empty_or_bad_status_falls_back(monkeypatch, content, status):
    _patch_post(monkeypatch, content, status=status)
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


def test_bad_json_falls_back(monkeypatch):
    class Bad:
        status_code = 200

        def json(self):
            raise ValueError("no json")
    monkeypatch.setattr(requests, "post", lambda *a, **k: Bad())
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


def test_timeout_falls_back_within_budget(monkeypatch):
    timeouts: list[float] = []

    def fake(url, headers=None, json=None, timeout=None):
        timeouts.append(timeout)
        raise requests.Timeout("slow")
    monkeypatch.setattr(requests, "post", fake)
    rec = _rec()
    assert _is_template(_writer(timeout=3.0).explain(rec), rec)
    assert 1 <= len(timeouts) <= 2
    assert all(0 < t <= 3.0 for pair in timeouts for t in pair)  # (connect, read) within the budget


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_no_retry_when_budget_spent(monkeypatch):
    clock = _Clock()
    calls: list = []

    def fake(url, headers=None, json=None, timeout=None):
        calls.append(timeout)
        clock.now += 2.9
        raise requests.ConnectionError("down")
    monkeypatch.setattr(requests, "post", fake)
    rec = _rec()
    assert _is_template(_writer(timeout=3.0, clock=clock).explain(rec), rec)
    assert len(calls) == 1


def test_retry_after_transient_error(monkeypatch):
    seq = [requests.ConnectionError("blip"), _Resp(GOOD)]

    def fake(url, headers=None, json=None, timeout=None):
        r = seq.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(requests, "post", fake)
    assert _writer().explain(_rec()).ai_written is True


# ---------- env factory ----------

def _never_called(*a, **k):
    raise AssertionError("network must not be called")


def test_env_disabled_returns_template_without_network(monkeypatch):
    monkeypatch.setattr(requests, "post", _never_called)
    env = {"LLM_ENABLED": "false", "LLM_BASE_URL": "http://x", "LLM_API_KEY": "k", "LLM_MODEL": "m"}
    w = writer_from_env(env)
    assert isinstance(w, TemplateExplanation)
    rec = _rec()
    assert _is_template(w.explain(rec), rec)


def test_env_missing_model_returns_template():
    env = {"LLM_ENABLED": "true", "LLM_BASE_URL": "http://x", "LLM_API_KEY": "k", "LLM_MODEL": ""}
    assert isinstance(writer_from_env(env), TemplateExplanation)


@pytest.mark.parametrize("flag", ["1", "true", "YES", "True"])
def test_env_enabled_returns_llm(flag):
    env = {"LLM_ENABLED": flag, "LLM_BASE_URL": "http://x", "LLM_API_KEY": "k", "LLM_MODEL": "m"}
    assert isinstance(writer_from_env(env), LlmExplanation)


def test_env_reads_os_environ(monkeypatch):
    for k in ("LLM_ENABLED", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    assert isinstance(writer_from_env(), TemplateExplanation)
    monkeypatch.setenv("LLM_ENABLED", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://x")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("LLM_MODEL", "m")
    assert isinstance(writer_from_env(), LlmExplanation)


# ---------- hard deadline, breaker, logging ----------

def test_slow_server_is_cut_off_at_the_deadline_in_real_time(monkeypatch):
    release = threading.Event()

    def blocking(*a, **k):  # a server that drips forever and ignores the requests timeout
        release.wait(5)
        return _Resp(GOOD)
    monkeypatch.setattr(requests, "post", blocking)
    rec = _rec()
    try:
        start = time.monotonic()
        exp = _writer(timeout=0.3).explain(rec)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    assert elapsed < 0.3 + 0.5
    assert _is_template(exp, rec)


@pytest.mark.parametrize(("failure", "attempts"), [
    (requests.Timeout("slow"), 2),
    (requests.ConnectionError("down"), 2),
    (_Resp(GOOD, 401), 1),
    (_Resp(GOOD, 403), 1),
    (_Resp(GOOD, 429), 1),
])
def test_breaker_skips_network_for_60s_then_retries(monkeypatch, failure, attempts):
    clock = _Clock()
    seq = [failure] * attempts + [_Resp(GOOD)]
    calls: list = []

    def fake(url, headers=None, json=None, timeout=None):
        calls.append(timeout)
        r = seq[min(len(calls) - 1, len(seq) - 1)]
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(requests, "post", fake)
    w = _writer(clock=clock)
    rec = _rec()
    assert _is_template(w.explain(rec), rec)
    assert len(calls) == attempts
    clock.now += 59
    assert _is_template(w.explain(rec), rec)
    assert len(calls) == attempts  # breaker open: template with no network call
    clock.now += 2
    assert w.explain(rec).ai_written is True
    assert len(calls) == attempts + 1


def test_timeout_then_5xx_still_opens_breaker(monkeypatch):
    clock = _Clock()
    seq = [requests.Timeout("slow"), _Resp(GOOD, 503)]
    calls: list = []

    def fake(url, headers=None, json=None, timeout=None):
        calls.append(timeout)
        r = seq[len(calls) - 1] if len(calls) <= len(seq) else _Resp(GOOD)
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(requests, "post", fake)
    w = _writer(clock=clock)
    w.explain(_rec())
    assert len(calls) == 2
    w.explain(_rec())
    assert len(calls) == 2


def test_5xx_alone_retries_but_does_not_open_breaker(monkeypatch):
    clock = _Clock()
    calls: list = []

    def fake(url, headers=None, json=None, timeout=None):
        calls.append(timeout)
        return _Resp(GOOD, 503)
    monkeypatch.setattr(requests, "post", fake)
    w = _writer(clock=clock)
    w.explain(_rec())
    assert len(calls) == 2
    w.explain(_rec())
    assert len(calls) == 4


def test_no_retry_on_401(monkeypatch):
    calls: list = []

    def fake(url, headers=None, json=None, timeout=None):
        calls.append(timeout)
        return _Resp(GOOD, 401)
    monkeypatch.setattr(requests, "post", fake)
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)
    assert len(calls) == 1


def test_logs_never_contain_secrets_or_text(monkeypatch, caplog):
    secret = "sk-SECRET-123"
    err = requests.ConnectionError(f"HTTPSConnectionPool(host='llm.test'): Authorization: Bearer {secret}")
    monkeypatch.setattr(requests, "post", lambda *a, **k: (_ for _ in ()).throw(err))
    w = LlmExplanation("http://llm.test/v1", secret, "m")
    with caplog.at_level(logging.INFO, logger=llm_writer.log.name):
        w.explain(_rec())
    assert "ConnectionError" in caplog.text
    assert "paused" in caplog.text
    for forbidden in (secret, "llm.test", "Architect", "56,914", "56914"):
        assert forbidden not in caplog.text


@pytest.mark.parametrize(("content", "reason"), [
    (GOOD.replace("£56,914", "£57,000"), "number check"),
    ("Architects are worth exploring. Median pay is £56,914 a year.", "notice check"),
    (GOOD + " You should wait.", "wording check"),
])
def test_check_failures_are_logged_by_reason_only(monkeypatch, caplog, content, reason):
    _patch_post(monkeypatch, content)
    with caplog.at_level(logging.INFO, logger=llm_writer.log.name):
        _writer().explain(_rec())
    assert reason in caplog.text
    assert "57,000" not in caplog.text and "Architects are worth" not in caplog.text


# ---------- numbers written as words ----------

@pytest.mark.parametrize("phrase", [
    "about fifty-seven thousand pounds a year",
    "pay could double by twenty thirty",
    "Pay could Double soon",
    "roughly half of roles",
    "a hundred openings",
    "twice the average",
    "three openings",
    "about a dozen employers",
    "Nineteen employers",
])
def test_numbers_in_words_fall_back(monkeypatch, phrase):
    _patch_post(monkeypatch, GOOD + f" {phrase}.")
    rec = _rec()
    assert _is_template(_writer().explain(rec), rec)


def test_plain_one_is_not_a_number_word(monkeypatch):
    _patch_post(monkeypatch, GOOD + " It is one path worth exploring.")
    assert _writer().explain(_rec()).ai_written is True


@pytest.mark.parametrize("key", sorted(FLAG_TEXT))
def test_every_flag_text_notice_passes_the_checks(monkeypatch, key):
    notice = FLAG_TEXT[key]
    text = f"Architects are worth exploring. {notice}"
    _patch_post(monkeypatch, text)
    rec = _rec(notices=[notice])
    exp = _writer().explain(rec)
    assert exp.ai_written is True and notice in exp.text
