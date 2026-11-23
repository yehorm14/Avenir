"""Per-IP rate limit on /api/guide and /api/tts; the clock is injected, no test sleeps or reaches a model."""

import base64
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import rate_limit, tts  # noqa: E402
from api.tests.test_tts import WAV, audio_reply, use  # noqa: E402

GUIDE = {"soc": "2134", "message": "What does a software developer do?", "history": []}


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    fake = Clock()
    rate_limit.set_clock(fake)
    return fake


@pytest.fixture
def client(monkeypatch, tmp_path):
    from api.main import app

    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "tts"))
    tts.reset_state()
    return TestClient(app)


def guide(client, **headers):
    return client.post("/api/guide", json=GUIDE, headers=headers)


def test_guide_is_limited_per_ip_then_recovers(client, clock, monkeypatch):
    monkeypatch.setenv("GUIDE_RATE_LIMIT", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_S", "60")
    assert guide(client).status_code == 200
    assert guide(client).status_code == 200
    blocked = guide(client)
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "RATE_LIMITED"
    assert blocked.headers["retry-after"] == "60"
    clock.now += 30
    assert guide(client).status_code == 429
    assert guide(client).headers["retry-after"] == "30"
    clock.now += 31
    assert guide(client).status_code == 200


def test_limit_zero_turns_it_off(client, monkeypatch):
    monkeypatch.setenv("GUIDE_RATE_LIMIT", "0")
    assert all(guide(client).status_code == 200 for _ in range(30))


def test_defaults_apply_without_env(client, clock):
    statuses = [guide(client).status_code for _ in range(rate_limit.DEFAULTS["guide"] + 1)]
    assert statuses[:-1] == [200] * rate_limit.DEFAULTS["guide"] and statuses[-1] == 429


def test_forwarded_header_is_ignored_unless_trusted(client, clock, monkeypatch):
    monkeypatch.setenv("GUIDE_RATE_LIMIT", "1")
    assert guide(client, **{"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert guide(client, **{"X-Forwarded-For": "2.2.2.2"}).status_code == 429


def test_trusted_proxy_separates_clients_by_the_last_forwarded_entry(client, clock, monkeypatch):
    monkeypatch.setenv("GUIDE_RATE_LIMIT", "1")
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert guide(client, **{"X-Forwarded-For": "9.9.9.9, 1.1.1.1"}).status_code == 200
    assert guide(client, **{"X-Forwarded-For": "8.8.8.8, 1.1.1.1"}).status_code == 429
    assert guide(client, **{"X-Forwarded-For": "9.9.9.9, 2.2.2.2"}).status_code == 200


def test_tts_limit_counts_only_real_synthesis_and_cached_replays_pass(client, clock, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-one")
    monkeypatch.setenv("TTS_RATE_LIMIT", "1")
    use(monkeypatch, audio_reply(WAV, "audio/wav"))
    first = client.post("/api/tts", json={"text": "Hello there"})
    assert first.status_code == 200 and first.json()["cached"] is False
    for _ in range(3):
        replay = client.post("/api/tts", json={"text": "Hello there"})
        assert replay.status_code == 200 and replay.json()["cached"] is True
        assert base64.b64decode(replay.json()["audio_base64"]) == WAV
    fresh = client.post("/api/tts", json={"text": "Something not cached"})
    assert fresh.status_code == 429
    assert fresh.json()["detail"]["code"] == "RATE_LIMITED"


def test_tts_without_a_key_is_not_counted(client, clock, monkeypatch):
    monkeypatch.setenv("TTS_RATE_LIMIT", "1")
    for text in ("one", "two", "three"):
        assert client.post("/api/tts", json={"text": text}).status_code == 503


def test_assembled_app_keeps_the_429_status(monkeypatch, clock, tmp_path):
    from api.application import app

    monkeypatch.setenv("GUIDE_RATE_LIMIT", "1")
    product = TestClient(app)
    assert product.post("/api/guide", json=GUIDE).status_code == 200
    blocked = product.post("/api/guide", json=GUIDE)
    assert blocked.status_code == 429 and blocked.json()["ok"] is False
    assert blocked.headers["retry-after"]


