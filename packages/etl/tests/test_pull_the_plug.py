"""Tests for scripts/demo/pull_the_plug.py: no network, a fake client returns canned envelopes."""
import importlib.util
import sys
from pathlib import Path
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
                 fail_refetch: Exception | None = None):
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
            soc = path.rsplit("/", 1)[1]
            value = {"live": 120.0, "snapshot": 100.0, "mock": 5.0, "missing": None}[self.state]
            body = env(career(soc, value).model_dump(mode="json"),
                       [*self.statuses(), SourceStatus(name="adzuna", status=self.state)])
            if self.bad_envelope:
                del body["meta"]["request_id"]
            return 200, body
        if path == "/api/v1/tags":
            tags = [{"id": i, "label": i, "keywords": []} for i in ("maths", "art_drawing", "design", "juggling")]
            return 200, env(tags, self.statuses())
        return 404, env(None, ok=False)

    def post(self, path: str, json: Any = None):
        self.calls.append(("POST", path, json))
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


def run(client, *argv: str) -> tuple[int, str]:
    lines: list[str] = []
    code = ptp.main(list(argv), client=client, out=lines.append)
    return code, "\n".join(lines)


def test_full_flow_shows_badges_picks_and_before_after():
    c = FakeClient()
    code, text = run(c)
    assert code == 0
    assert "ml_mode" in text and "real" in text
    assert "source" in text and "status" in text and "quality" in text and "as_of" in text
    assert "ashe" in text and "preliminary" in text
    assert "soc" in text and "Architect" in text and "Software developer" in text
    assert "ambitious" in text and "safe" in text and "balanced" in text
    assert "hedge" in text.lower() and "notices: 2" in text and "ai_written: False" in text
    assert "adzuna" in text and "live -> snapshot" in text
    assert "PASS" in text
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
    assert "recommendations: not available yet (Nazar Task 13)" in text
    assert "pull the plug: not available yet (Nazar Task 13)" in text


def test_unreachable_server_exits_2_with_hint():
    class Down:
        def get(self, path):
            raise requests.ConnectionError("refused")

        post = get

    code, text = run(Down(), "--base-url", "http://localhost:9")
    assert code == 2
    assert "API not reachable at http://localhost:9; start it with: uvicorn avenir_api.app:app --port 8000" in text


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
    assert code == 1 and "FAIL" in text and "mock" in text
    code, text = run(FakeClient(mock=True))
    assert code == 0 and "WARN" in text and "mock" in text


def test_no_keys_ads_missing_is_an_honest_warning_not_a_failure():
    c = FakeClient(ads_on="missing", ads_off="missing")
    code, text = run(c)
    assert code == 0
    assert "no Adzuna snapshot: ads show 'missing' (run scripts/fetch/adzuna_snapshot.py with keys)" in text
    assert "missing" in text and "120" not in text  # nothing invented


def test_ads_still_live_after_unplug_fails():
    code, text = run(FakeClient(ads_off="live"))
    assert code == 1 and "FAIL" in text


def test_invalid_envelope_fails():
    code, text = run(FakeClient(bad_envelope=True))
    assert code == 1 and "request_id" in text


@pytest.mark.parametrize("boom", [requests.Timeout("slow"), RuntimeError("bug")])
def test_restore_always_posted_even_if_refetch_raises(boom):
    c = FakeClient(fail_refetch=boom)
    if isinstance(boom, requests.RequestException):
        code, text = run(c)
        assert code == 1 and "FAIL" in text
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
