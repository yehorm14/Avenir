"""Tests for scripts/demo/pull_the_plug.py: no network, a fake client returns canned envelopes."""
import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import requests

from avenir_contracts import Career, Envelope, Meta, Metric, SourceStatus

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "demo" / "pull_the_plug.py"
spec = importlib.util.spec_from_file_location("pull_the_plug", SCRIPT)
ptp = importlib.util.module_from_spec(spec)
sys.modules["pull_the_plug"] = ptp
spec.loader.exec_module(ptp)

SOCS = {"2451": "Architect", "2135": "Software developer"}  # test-only values
BASE_STATUSES = [
    SourceStatus(name="ashe", status="snapshot", quality="final", as_of="2025-04"),
    SourceStatus(name="ml", status="snapshot", quality="preliminary", as_of="2026-10"),
]


def env(data: Any, sources: list[SourceStatus] | None = None, ok: bool = True) -> dict:
    meta = Meta(as_of="2026-10-17", request_id="abc123", sources=sources or [])
    return Envelope[Any](ok=ok, data=data, meta=meta).model_dump(mode="json")


def career(soc: str, ads: float | None) -> Career:
    if ads is not None:
        ad = Metric(value=ads, unit="count", source="adzuna", confidence="medium", as_of="2026-10-01")
    else:
        ad = Metric.missing("count", "adzuna")
    return Career(soc2020=soc, title=SOCS[soc], official_title=SOCS[soc] + " (official)", metrics={"ads_now": ad})


class FakeClient:
    """Mimics Nazar's API. ads_on / ads_off are the adzuna source states with the plug in / out."""

    def __init__(self, ads_on="live", ads_off="snapshot", mock=False, recs=True, toggle=True, bad_envelope=False,
                 fail_refetch: Exception | None = None, overrides: dict | None = None, missing_socs=(),
                 status_after_unplug: int | None = None):
        self.status_after_unplug = status_after_unplug  # career card HTTP status once the plug is pulled
        self.overrides = overrides or {}  # (method, path) -> (status, body)
        self.missing_socs = set(missing_socs)  # careers whose ads are missing whatever the plug does
        self.ads_on, self.ads_off, self.mock, self.recs, self.toggle = ads_on, ads_off, mock, recs, toggle
        self.bad_envelope, self.fail_refetch = bad_envelope, fail_refetch
        self.live = True
        self.calls: list[tuple[str, str, Any]] = []

    @property
    def state(self) -> str:
        return self.ads_on if self.live else self.ads_off

    def statuses(self) -> list[SourceStatus]:
        extra = [SourceStatus(name="catalogue", status="mock")] if self.mock else []
        return [*BASE_STATUSES, *extra]

    def get(self, path: str):
        self.calls.append(("GET", path, None))
        if ("GET", path) in self.overrides:
            return self.overrides[("GET", path)]
        if path == "/health":
            return 200, env({"status": "ok", "ml_mode": "real", "sources": []}, self.statuses())
        if path == "/api/v1/sources":
            return 200, env({"statuses": [s.model_dump(mode="json") for s in self.statuses()], "registry": []},
                            self.statuses())
        if path == "/api/v1/careers":
            return 200, env([career(s, None).model_dump(mode="json") for s in SOCS], self.statuses())
        if path.startswith("/api/v1/careers/"):
            if self.fail_refetch is not None and not self.live:
                raise self.fail_refetch
            if self.status_after_unplug is not None and not self.live:
                return self.status_after_unplug, err("INTERNAL", "boom")
            soc = path.rsplit("/", 1)[1]
            state = "missing" if soc in self.missing_socs else self.state
            value = {"live": 120.0, "snapshot": 100.0, "mock": 5.0, "missing": None}[state]
            body = env(career(soc, value).model_dump(mode="json"),
                       [*self.statuses(), SourceStatus(name="adzuna", status=state)])
            if self.bad_envelope:
                del body["meta"]["request_id"]
            return 200, body
        if path == "/api/v1/tags":
            tags = [{"id": i, "label": i, "keywords": []} for i in ("maths", "art_drawing", "design", "juggling")]
            return 200, env(tags, self.statuses())
        return 404, env(None, ok=False)

    def post(self, path: str, json: Any = None):
        self.calls.append(("POST", path, json))
        if ("POST", path) in self.overrides:
            return self.overrides[("POST", path)]
        if path == "/api/v1/recommendations":
            if not self.recs:
                return 404, env(None, ok=False)

            def pick(tier, soc):
                return {"tier": tier, "career": career(soc, 1).model_dump(mode="json")}

            data = {"picks": [pick("ambitious", "2451"), pick("safe", "2135"), pick("balanced", "2451")],
                    "hedge": {"career": career("2135", 1).model_dump(mode="json")},
                    "notices": ["n1", "n2"], "explanation": {"text": "t", "ai_written": False}}
            return 200, env(data, self.statuses())
        if path == "/api/v1/demo/live":
            if not self.toggle:
                return 404, env(None, ok=False)
            self.live = bool(json["enabled"])
            return 200, env({"live": self.live}, self.statuses())
        return 404, env(None, ok=False)

    def posts(self, path: str) -> list[Any]:
        return [c[2] for c in self.calls if c[0] == "POST" and c[1] == path]


def err(code: str, message: str) -> dict:
    body = env(None, ok=False)
    body["error"] = {"code": code, "message": message, "details": []}
    return body


def lines_of(text: str) -> list[str]:
    return text.splitlines()


def has_row(text: str, *cells: str) -> bool:
    """A table row whose cells (in order) match, ignoring padding."""
    pattern = r"^\s*" + r"\s*\|\s*".join(re.escape(c) for c in cells) + r"(\s*\||\s*$)"
    return any(re.match(pattern, line) for line in lines_of(text))


def run(client, *argv: str) -> tuple[int, str]:
    lines: list[str] = []
    code = ptp.main(list(argv), client=client, out=lines.append)
    return code, "\n".join(lines)


def test_full_flow_shows_badges_picks_and_before_after():
    c = FakeClient()
    code, text = run(c)
    assert code == 0
    out = lines_of(text)
    assert "  HTTP 200   status: ok   ml_mode: real" in out
    assert has_row(text, "source", "status", "quality", "as_of")
    assert has_row(text, "ashe", "snapshot", "final", "2025-04")
    assert has_row(text, "ml", "snapshot", "preliminary", "2026-10")
    assert "  counts: snapshot 2" in out
    assert has_row(text, "soc", "title", "ads_now", "ads status", "ms")
    assert has_row(text, "2451", "Architect", "120", "live")
    assert has_row(text, "2135", "Software developer", "120", "live")
    for line in ("  ambitious: Architect", "  safe: Software developer", "  balanced: Architect",
                 "  hedge: Software developer", "  notices: 2", "  explanation.ai_written: False"):
        assert line in out
    assert has_row(text, "item", "before", "after")
    assert has_row(text, "adzuna (career card)", "live", "snapshot")
    assert has_row(text, "ads_now value, career 2451", "120", "100")
    assert "  adzuna (career card): live -> snapshot" in out
    assert "  PASS  ads after unplug: snapshot (not live)" in out
    # interests only include tag ids that exist; the Amira profile is exactly the contract profile
    profile = c.posts("/api/v1/recommendations")[0]
    assert profile["first_idea"] == "architect"
    assert profile["profile"] == {"interests": ["maths", "art_drawing", "design"], "nation": "scotland",
                                  "location": "Glasgow", "automation_worry": 0.5}
    assert c.posts("/api/v1/demo/live") == [{"enabled": False}, {"enabled": True}]
    assert c.live is True


def test_missing_endpoints_are_not_fatal():
    code, text = run(FakeClient(recs=False, toggle=False))
    assert code == 0
    out = lines_of(text)
    assert "  recommendations: not available yet (Nazar Task 13)" in out
    assert "  pull the plug: not available yet (Nazar Task 13)" in out
    assert not [x for x in out if x.lstrip().startswith("FAIL")]


def test_unreachable_server_exits_2_with_hint():
    class Down:
        def get(self, path):
            raise requests.ConnectionError("refused")

        post = get

    code, text = run(Down(), "--base-url", "http://localhost:9")
    assert code == 2
    assert "API not reachable at http://localhost:9; start it with: uvicorn avenir_api.app:app --port 8000" in text


def test_default_base_url_is_ipv4_loopback():
    assert ptp.parse([]).base_url == "http://127.0.0.1:8000"


def test_warm_only_stops_after_warming():
    c = FakeClient()
    code, text = run(c, "--warm-only")
    assert code == 0 and "Architect" in text
    assert c.posts("/api/v1/recommendations") == [] and c.posts("/api/v1/demo/live") == []


def test_no_toggle_never_posts_demo_live():
    c = FakeClient()
    code, _ = run(c, "--no-toggle")
    assert code == 0 and c.posts("/api/v1/demo/live") == []
    assert len(c.posts("/api/v1/recommendations")) == 1


def test_freeze_with_mock_status_fails():
    code, text = run(FakeClient(mock=True), "--freeze")
    assert code == 1
    assert "  FAIL  mock status on: catalogue (--freeze)" in lines_of(text)
    code, text = run(FakeClient(mock=True))
    assert code == 0 and "  WARN  mock status on: catalogue" in lines_of(text)


def test_no_keys_ads_missing_is_an_honest_warning_not_a_failure():
    c = FakeClient(ads_on="missing", ads_off="missing")
    code, text = run(c)
    assert code == 0
    assert ("  WARN  no Adzuna snapshot: ads show 'missing' (run scripts/fetch/adzuna_snapshot.py with keys)"
            in lines_of(text))
    assert has_row(text, "2451", "Architect", "missing", "missing")
    assert "120" not in text  # nothing invented


def test_partial_missing_ads_lists_the_socs_not_the_blanket_message():
    code, text = run(FakeClient(missing_socs=["2135"]))
    out = lines_of(text)
    assert code == 0
    assert "  WARN  ads missing for 1 of 2 careers: 2135" in out
    assert not [x for x in out if "no Adzuna snapshot" in x]


def test_ads_still_live_after_unplug_fails():
    code, text = run(FakeClient(ads_off="live"))
    assert code == 1 and "  FAIL  ads still live after the plug was pulled" in lines_of(text)


def test_invalid_envelope_fails():
    code, text = run(FakeClient(bad_envelope=True))
    assert code == 1
    assert any(x.startswith("  FAIL  invalid envelope:") and "GET /api/v1/careers/2135: missing meta.request_id" in x
               for x in lines_of(text))


@pytest.mark.parametrize("status", [500, 404])
def test_career_card_error_is_a_fail_naming_soc_and_status(status):
    bad = {("GET", "/api/v1/careers/2135"): (status, err("INTERNAL", "boom"))}
    code, text = run(FakeClient(overrides=bad), "--warm-only")
    assert code == 1
    assert f"  FAIL  career card 2135: HTTP {status}" in lines_of(text)
    assert has_row(text, "2135", "Software developer", "-", f"error HTTP {status}")


def test_post_unplug_card_error_is_a_fail_not_a_pass_and_plug_is_restored():
    c = FakeClient(status_after_unplug=500)
    code, text = run(c)
    out = lines_of(text)
    assert code == 1
    assert "  FAIL  career card 2451 after unplug: HTTP 500" in out
    assert not [x for x in out if x.startswith("  PASS  ads after unplug")]
    assert c.posts("/api/v1/demo/live") == [{"enabled": False}, {"enabled": True}]
    assert c.live is True


def test_recommendations_error_body_that_is_not_a_dict_is_tolerated():
    bad = {("POST", "/api/v1/recommendations"): (422, {"ok": False, "error": "oops",
                                                       "meta": {"as_of": "x", "request_id": "r", "sources": []}})}
    code, text = run(FakeClient(overrides=bad))
    assert code == 0
    assert "  WARN  recommendations: HTTP 422" in lines_of(text)


def test_recommendations_5xx_is_a_fail():
    bad = {("POST", "/api/v1/recommendations"): (500, err("INTERNAL", "Something went wrong"))}
    code, text = run(FakeClient(overrides=bad))
    assert code == 1
    assert "  FAIL  recommendations: HTTP 500: Something went wrong" in lines_of(text)


def test_recommendations_4xx_is_a_warn_with_the_error_message():
    bad = {("POST", "/api/v1/recommendations"): (422, err("VALIDATION_ERROR", "Invalid request"))}
    code, text = run(FakeClient(overrides=bad))
    assert code == 0
    assert "  WARN  recommendations: HTTP 422: Invalid request" in lines_of(text)


@pytest.mark.parametrize("override", [
    {("GET", "/api/v1/careers"): (200, env([]))},
    {("GET", "/api/v1/careers"): (500, err("INTERNAL", "boom"))},
])
def test_no_careers_is_a_fail(override):
    code, text = run(FakeClient(overrides=override), "--warm-only")
    assert code == 1
    assert any(x.startswith("  FAIL  careers: ") for x in lines_of(text))


def test_sources_error_is_a_fail():
    bad = {("GET", "/api/v1/sources"): (500, err("INTERNAL", "boom"))}
    code, text = run(FakeClient(overrides=bad), "--warm-only")
    assert code == 1
    assert "  FAIL  sources: HTTP 500" in lines_of(text)


def test_total_request_time_includes_the_health_call(monkeypatch):
    ticks = iter(range(0, 10_000))  # every timed call takes exactly 1 s
    monkeypatch.setattr(ptp, "time", SimpleNamespace(perf_counter=lambda: float(next(ticks))))
    code, text = run(FakeClient(), "--warm-only")
    assert code == 0
    # health + sources + careers list + 2 cards
    assert "  total request time: 5000 ms" in lines_of(text)


@pytest.mark.parametrize("boom", [requests.Timeout("slow"), RuntimeError("bug")])
def test_restore_always_posted_even_if_refetch_raises(boom):
    c = FakeClient(fail_refetch=boom)
    if isinstance(boom, requests.RequestException):
        code, text = run(c)
        assert code == 1
        assert "  FAIL  GET /api/v1/careers/2451 failed: Timeout" in lines_of(text)
    else:
        with pytest.raises(RuntimeError):
            run(c)
    assert c.posts("/api/v1/demo/live") == [{"enabled": False}, {"enabled": True}]
    assert c.live is True


def test_in_process_against_real_api(monkeypatch):
    pytest.importorskip("avenir_api.app")
    from fastapi.testclient import TestClient

    from avenir_api.app import create_app

    def boom(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(requests, "post", boom)
    tc = TestClient(create_app())

    class Wrap:
        def get(self, path):
            r = tc.get(path)
            return r.status_code, r.json()

        def post(self, path, json=None):
            r = tc.post(path, json=json)
            return r.status_code, r.json()

    lines: list[str] = []
    assert ptp.main([], client=Wrap(), out=lines.append) in (0, 1)  # 1 only if the real API has a real FAIL
    assert any("Health" in line for line in lines)
