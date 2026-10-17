import os

import pytest
from fastapi.testclient import TestClient
from test_provenance import AMIRA, _metrics

from avenir_api.app import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("AVENIR_FREEZE") != "1",
    reason="code-freeze check; set AVENIR_FREEZE=1 to run",
)

WATCHED = {"catalogue", "routes", "ml_occupations", "ml_backtest"}


def _is_mock(m):
    return m.get("status") == "mock" or m.get("source") == "MOCK" or "mock" in (m.get("flags") or [])


def test_no_mock_at_freeze():
    client = TestClient(create_app())
    health = client.get("/health")
    assert health.status_code == 200, health.text
    sources = health.json()["data"]["sources"]
    mocked = [s["name"] for s in sources if s["name"] in WATCHED and s["status"] == "mock"]
    assert not mocked, f"mock sources at freeze: {mocked}"
    r = client.post("/api/v1/recommendations", json={"profile": AMIRA, "first_idea": "architect"})
    assert r.status_code == 200, r.text
    bad = [p for p, m in _metrics(r.json()) if _is_mock(m)]
    assert not bad, f"mock metrics at freeze: {bad[:10]}"
