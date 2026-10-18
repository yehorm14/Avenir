"""Evidence pack per role and the grounded guide, without network or credentials."""

import json
import sys
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

GOOD_REPLY = (
    "Software developer is worth exploring. The published median pay is £56,914 a year for full-time employees "
    "(2025); the middle half earn £42,289–£75,794. The 2025 figure is an ONS provisional estimate and may be "
    "revised. Employment grew +2.62% a year relative to the typical occupation over 2022-2025; this is history, "
    "not a forecast. Automation exposure is 0.5444 on a 0–1 scale. Based on: ONS ASHE, ILO WP140."
)


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


class _Response:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _openai_env(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_BASE_URL", "http://model.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")


def _fake_post(monkeypatch, reply: str | Exception, provider: str = "openai", status: int = 200) -> list[dict]:
    calls: list[dict] = []

    def post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "payload": json, "timeout": timeout})
        if isinstance(reply, Exception):
            raise reply
        if provider == "anthropic":
            return _Response(status, {"content": [{"type": "text", "text": reply}]})
        return _Response(status, {"choices": [{"message": {"content": reply}}]})

    monkeypatch.setattr(requests, "post", post)
    return calls


def test_evidence_pack_has_every_section_for_a_cs_role(client):
    response = client.get("/api/careers/2134/evidence-pack")
    assert response.status_code == 200
    pack = response.json()
    assert pack["title"] == "Software developer"
    assert set(pack["metrics"]) == {"pay", "jobs", "trend", "exposure"}
    pay = pack["metrics"]["pay"]
    assert pay["value"] == 56914
    assert "£56,914" in pay["display"] and "£42,289–£75,794" in pay["display"]
    assert "The 2025 figure is an ONS provisional estimate and may be revised." in pay["caveats"]
    assert "Covers employees only; self-employed and freelance workers are not included." in pay["caveats"]
    assert "56914" in pack["allowed_numbers"] and "42289" in pack["allowed_numbers"]
    assert [point["year"] for point in pack["history"]["points"]] == [2011, 2015, 2019, 2022, 2025]
    assert pack["history"]["price_base"] == "2024/25 prices, tax-year CPIH"
    assert any("2021" in caveat for caveat in pack["history"]["caveats"])
    assert len(pack["hedges"]) == 3
    assert all(hedge["title"] and hedge["pay"]["value"] and hedge["evidence"] for hedge in pack["hedges"])
    assert pack["backtest"]["windows"] and pack["backtest"]["caveats"]
    assert pack["backtest"]["windows"][0]["rule_group_then"] == "ambitious"
    crises = {crisis["key"]: crisis for crisis in pack["crises"]}
    assert crises["covid"]["placebo_passed"] is True and crises["covid"]["excluded_from_recommendations"] is False
    assert crises["gfc_2008"]["excluded_from_recommendations"] is True
    assert crises["covid"]["result"]["value"] == 0.0096
    assert pack["fit_tags"][0]["tag"] == "computers_coding"
    assert pack["demand"] is None and pack["starting_pay"] is None
    assert {source["id"] for source in pack["sources"]} >= {"ons_ashe_t14", "ons_cpih", "ilo_wp140"}
    assert pack["based_on"][0] == "Median pay £56,914 (ONS ASHE 2025, provisional)"
    assert len(json.dumps(pack, separators=(",", ":")).encode("utf-8")) < 13_000


def test_evidence_pack_unknown_soc_is_404_and_non_demo_role_has_no_fit_tags(client):
    assert client.get("/api/careers/9999/evidence-pack").status_code == 404
    pack = client.get("/api/careers/1111/evidence-pack").json()
    assert pack["fit_tags"] is None
    assert pack["backtest"] is None or pack["backtest"]["windows"]


def test_guide_without_configuration_is_the_unchanged_prepared_reply(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the salary?"}).json()
    assert answer["mode"] == "prepared_demo" and answer["ai_written"] is False and answer["model"] is None
    assert "56,914" in answer["text"]
    assert answer["checks"] == "fallback: no model configured"
    assert answer["based_on"]
    assert client.get("/api/health").json()["guide_mode"] == "prepared_demo"


def test_guide_uses_the_configured_model_and_grounded_reply_passes_checks(client, monkeypatch):
    _openai_env(monkeypatch)
    calls = _fake_post(monkeypatch, GOOD_REPLY)
    answer = client.post(
        "/api/guide",
        json={"soc": "2134", "message": "What is the pay?", "history": [{"role": "assistant", "content": "Hello"}]},
    ).json()
    assert answer["mode"] == "llm_grounded" and answer["ai_written"] is True
    assert answer["model"] == "test-model" and answer["checks"] == "passed"
    assert answer["text"] == GOOD_REPLY.split(" Based on:")[0]
    assert {source["id"] for source in answer["sources"]} >= {"ons_ashe_t14", "ilo_wp140"}
    assert answer["based_on"][0].startswith("Median pay £56,914")
    assert client.get("/api/health").json()["guide_mode"] == "llm_grounded"
    call = calls[0]
    assert call["url"] == "http://model.invalid/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    system = call["payload"]["messages"][0]["content"]
    assert "allowed_numbers" not in system and '"pay"' in system and "56914" in system
    assert call["payload"]["messages"][1:] == [{"role": "user", "content": "What is the pay?"}]


def test_guide_calls_anthropic_directly_when_only_its_key_is_set(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    calls = _fake_post(monkeypatch, GOOD_REPLY, provider="anthropic")
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "llm_grounded" and answer["model"] == "claude-sonnet-5-5"
    call = calls[0]
    assert call["url"] == "https://api.anthropic.com/v1/messages"
    assert call["headers"] == {"x-api-key": "test-anthropic-key", "anthropic-version": "2023-06-01"}
    assert call["payload"]["max_tokens"] == 600 and "Evidence pack" in call["payload"]["system"]
    assert call["payload"]["messages"][-1] == {"role": "user", "content": "Tell me about pay"}


@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        ("The median pay is £99,999 a year. Based on: ONS ASHE.", "number not in the evidence pack"),
        ("You should become a developer. Based on: ONS ASHE.", "banned phrase"),
        ("   ", "empty reply"),
    ],
)
def test_guide_falls_back_when_a_check_fails(client, monkeypatch, reply, reason):
    _openai_env(monkeypatch)
    _fake_post(monkeypatch, reply)
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the pay?"}).json()
    assert answer["mode"] == "prepared_demo" and answer["ai_written"] is False and answer["model"] is None
    assert answer["checks"].startswith("fallback: " + reason)
    assert "56,914" in answer["text"]
    assert "not used" in answer["note"]


def test_guide_falls_back_on_transport_error_and_http_error(client, monkeypatch):
    _openai_env(monkeypatch)
    _fake_post(monkeypatch, requests.ConnectionError("refused"))
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the pay?"}).json()
    assert answer["mode"] == "prepared_demo" and answer["checks"] == "fallback: ConnectionError"
    _fake_post(monkeypatch, "irrelevant", status=503)
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the pay?"}).json()
    assert answer["checks"] == "fallback: HTTP 503"


def test_failed_check_names_each_rule():
    from api.guide_llm import failed_check

    allowed = {"56914", "2025"}
    assert failed_check("Median pay £56,914 in 2025.", allowed) is None
    assert failed_check("Pay was £56,914 in 2024.", allowed).startswith("number not in the evidence pack: 2024")
    assert failed_check("There is a 90% probability of growth.", allowed | {"90"}) == "banned phrase: probability"
    assert failed_check("x" * 1201, allowed) == "reply over 1,200 characters"
