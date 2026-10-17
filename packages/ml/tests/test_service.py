"""Tests for the optional matcher service. The HTTP tests use a fake embedding model so they
run in a second without downloads; set PATHFINDER_SLOW_TESTS=1 to also exercise the real model.
Requests go through httpx's ASGI transport (works with any httpx/starlette combination)."""
import asyncio
import os
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from pathfinder_ml import service  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TEXTS = ROOT / "snapshots" / "ml" / "career_texts.json"


def call(method: str, path: str, json=None):
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=service.app), base_url="http://test") as c:
            return await c.request(method, path, json=json)
    return asyncio.run(go())


class FakeModel:
    """Deterministic stand-in: a bag-of-characters vector, normalised. Enough to test the plumbing."""

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False):
        out = []
        for t in texts:
            v = np.zeros(64)
            for ch in t.lower():
                v[ord(ch) % 64] += 1
            n = np.linalg.norm(v)
            out.append(v / n if n else v)
        return np.asarray(out)


@pytest.fixture
def fake_matcher(monkeypatch):
    if not TEXTS.is_file():
        pytest.skip("career_texts.json not built yet")
    m = service.Matcher(TEXTS, "fake")
    m.model, m.device = FakeModel(), "cpu"
    for soc, e in m.texts.items():
        chunks = [c["text"] for c in e["chunks"]] or [e["title"]]
        m.vecs[soc] = m.model.encode(chunks)
    monkeypatch.setattr(service, "_matcher", m)
    return m


def test_health_reports_loaded(fake_matcher):
    r = call("GET", "/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["data"]["loaded"] and body["data"]["n_careers"] == 20


def test_match_returns_top_k_in_order(fake_matcher):
    r = call("POST", "/match", json={"text": "I like drawing and fixing bikes", "top_k": 4})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["matches"]) == 4
    scores = [m["score"] for m in data["matches"]]
    assert scores == sorted(scores, reverse=True)
    assert {"soc2020", "short_title", "score", "evidence"} <= set(data["matches"][0])
    assert any(t["tag"] == "art_drawing" for t in data["tags"])


def test_match_validates_input(fake_matcher):
    assert call("POST", "/match", json={"text": "", "top_k": 3}).status_code == 422
    assert call("POST", "/match", json={"text": "x", "top_k": 0}).status_code == 422


def test_unloaded_model_gives_503_with_envelope(monkeypatch):
    if not TEXTS.is_file():
        pytest.skip("career_texts.json not built yet")
    monkeypatch.setattr(service, "_matcher", service.Matcher(TEXTS, "fake"))
    r = call("POST", "/match", json={"text": "maths and art"})
    assert r.status_code == 503
    assert r.json()["ok"] is False and r.json()["error"]["code"] == "matcher_unavailable"


@pytest.mark.skipif(not os.environ.get("PATHFINDER_SLOW_TESTS"), reason="set PATHFINDER_SLOW_TESTS=1 to load the real model")
def test_real_model_smoke():
    m = service.Matcher(TEXTS, os.environ.get("MATCHER_MODEL", service.DEFAULT_MODEL))
    m.load()
    top = m.match("I love drawing buildings and I'm good at maths", 3)
    assert "2451" in {t["soc2020"] for t in top}
