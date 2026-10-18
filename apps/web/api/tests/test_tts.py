"""Text to speech: Gemini replies are mocked; no test reaches the network or prints a key."""

import base64
import struct
import sys
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import tts  # noqa: E402

KEY_1 = "test-key-one"
KEY_2 = "test-key-two"
PCM = b"\x01\x00\x02\x00" * 100
WAV = tts.wav_from_pcm(b"\x00\x00" * 50)


class FakeResponse:
    def __init__(self, status: int, body: dict | None = None, text: str = ""):
        self.status_code = status
        self._body = body
        self.text = text or ("" if body is None else str(body))

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def audio_reply(data: bytes, mime: str) -> FakeResponse:
    inline = {"mimeType": mime, "data": base64.b64encode(data).decode()}
    return FakeResponse(200, {"candidates": [{"content": {"parts": [{"inlineData": inline}]}}]})


class Recorder:
    """Stands in for requests.post: replies in order and records (model, key) per call."""

    def __init__(self, *replies: FakeResponse):
        self.replies = list(replies)
        self.calls: list[tuple[str, str]] = []

    def __call__(self, url, headers=None, json=None, timeout=None):
        assert "key=" not in url, "the key must travel in a header, not the URL"
        model = url.rsplit("/", 1)[1].split(":")[0]
        self.calls.append((model, headers["x-goog-api-key"]))
        return self.replies.pop(0)


@pytest.fixture(autouse=True)
def clean_tts(monkeypatch, tmp_path):
    for name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "TTS_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "tts"))
    tts.reset_state()
    yield
    tts.reset_state()


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


def use(monkeypatch, *replies: FakeResponse) -> Recorder:
    recorder = Recorder(*replies)
    monkeypatch.setattr(requests, "post", recorder)
    return recorder


def speak(client, text="Software developers earned a median of £56,914.", **extra):
    return client.post("/api/tts", json={"text": text, **extra})


def decoded(response) -> bytes:
    body = response.json()
    assert body["mime_type"] == "audio/wav"
    return base64.b64decode(body["audio_base64"])


def test_wav_reply_is_passed_through(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    recorder = use(monkeypatch, audio_reply(WAV, "audio/wav"))
    response = speak(client)
    assert response.status_code == 200
    assert decoded(response) == WAV
    assert response.json()["model"] == tts.DEFAULT_MODEL
    assert response.json()["cached"] is False
    assert recorder.calls == [(tts.DEFAULT_MODEL, KEY_1)]
    assert KEY_1 not in response.text


def test_l16_pcm_is_wrapped_in_a_24khz_riff_header(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    use(monkeypatch, audio_reply(PCM, "audio/L16;codec=pcm;rate=24000"))
    audio = decoded(speak(client))
    riff, size, wave, fmt, fmt_len, pcm_format, channels, rate, byte_rate, block, bits, data, data_len = struct.unpack(
        "<4sI4s4sIHHIIHH4sI", audio[:44]
    )
    assert (riff, wave, fmt, data) == (b"RIFF", b"WAVE", b"fmt ", b"data")
    assert size == len(audio) - 8 and data_len == len(PCM) and audio[44:] == PCM
    assert (fmt_len, pcm_format, channels, rate, byte_rate, block, bits) == (16, 1, 1, 24000, 48000, 2, 16)


def test_fallback_model_on_404(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    recorder = use(monkeypatch, FakeResponse(404, {"error": {"code": 404}}), audio_reply(WAV, "audio/wav"))
    response = speak(client)
    assert response.status_code == 200
    assert response.json()["model"] == tts.FALLBACK_MODEL
    assert recorder.calls == [(tts.DEFAULT_MODEL, KEY_1), (tts.FALLBACK_MODEL, KEY_1)]


def test_second_key_after_a_daily_quota_429_and_the_spent_key_is_remembered(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    monkeypatch.setenv("GEMINI_API_KEY_2", KEY_2)
    daily = FakeResponse(429, text='{"error": {"status": "RESOURCE_EXHAUSTED", "quotaId": "RequestsPerDayPerModel"}}')
    recorder = use(monkeypatch, daily, audio_reply(WAV, "audio/wav"), audio_reply(WAV, "audio/wav"))
    assert speak(client).status_code == 200
    assert speak(client, text="A different answer.").status_code == 200
    assert recorder.calls == [(tts.DEFAULT_MODEL, KEY_1), (tts.DEFAULT_MODEL, KEY_2), (tts.DEFAULT_MODEL, KEY_2)]


def test_both_keys_exhausted_gives_503_tts_unavailable(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    monkeypatch.setenv("GEMINI_API_KEY_2", KEY_2)
    use(monkeypatch, *[FakeResponse(429, text="RequestsPerDay") for _ in range(4)])
    response = speak(client)
    assert response.status_code == 503
    assert response.json()["detail"] == {"code": "TTS_UNAVAILABLE", "message": "daily_quota_used"}
    assert KEY_1 not in response.text and KEY_2 not in response.text
    recorder = use(monkeypatch)  # every key is now remembered as spent: no further calls
    assert speak(client).status_code == 503
    assert recorder.calls == []


def test_cache_hit_avoids_a_second_call(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    recorder = use(monkeypatch, audio_reply(WAV, "audio/wav"))
    first = speak(client, text="**Worth exploring:** see [the course page](https://example.org/x).")
    second = speak(client, text="**Worth exploring:** see [the course page](https://example.org/x).")
    assert first.status_code == second.status_code == 200
    assert second.json()["cached"] is True and decoded(second) == WAV
    assert len(recorder.calls) == 1


def test_disk_cache_survives_a_restart_without_quota_or_key(client, monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    use(monkeypatch, audio_reply(WAV, "audio/wav"))
    assert speak(client).status_code == 200
    cache = tmp_path / "tts"
    assert len(list(cache.glob("*.wav"))) == 1 and (cache / ".gitignore").read_text() == "*\n"
    tts.reset_state()  # a new process: memory cache and key state gone
    monkeypatch.delenv("GEMINI_API_KEY")
    recorder = use(monkeypatch)
    response = speak(client)
    assert response.status_code == 200 and response.json()["cached"] is True and decoded(response) == WAV
    assert recorder.calls == []


def test_markdown_and_urls_are_stripped_before_speaking():
    text = "## Pay\n- **Median** pay is £56,914 ([ONS ASHE](https://www.ons.gov.uk/x)); see www.example.org now."
    assert tts.clean_text(text) == "Pay Median pay is £56,914 (ONS ASHE); see now."


def test_503_without_key(client, monkeypatch):
    recorder = use(monkeypatch)
    response = speak(client)
    assert response.status_code == 503
    assert response.json()["detail"] == {"code": "TTS_UNAVAILABLE", "message": "no_key_configured"}
    assert recorder.calls == []


@pytest.mark.parametrize(
    "body",
    [{}, {"text": ""}, {"text": "x" * 1501}, {"text": "Hello", "voice": "Nobody"}, {"text": 5}, {"text": "https://example.org"}],
)
def test_bad_input_is_422(client, monkeypatch, body):
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    recorder = use(monkeypatch)
    assert client.post("/api/tts", json=body).status_code == 422
    assert recorder.calls == []


def test_health_and_bootstrap_report_tts(client, monkeypatch):
    assert client.get("/api/health").json()["tts"] is False
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    health = client.get("/api/health").json()
    assert health["tts"] is True and health["tts_quota_note"] == tts.QUOTA_NOTE
    assert client.get("/api/bootstrap").json()["data_status"]["tts"] is True


def test_assembled_app_returns_the_audio_in_the_envelope(monkeypatch):
    from api.application import app

    product = TestClient(app)
    monkeypatch.setenv("GEMINI_API_KEY", KEY_1)
    use(monkeypatch, audio_reply(WAV, "audio/wav"))
    response = product.post("/api/tts", json={"text": "Hello", "voice": "Puck"})
    assert response.status_code == 200 and response.json()["ok"] is True
    assert base64.b64decode(response.json()["data"]["audio_base64"]) == WAV
    monkeypatch.delenv("GEMINI_API_KEY")
    tts.reset_state()
    unavailable = product.post("/api/tts", json={"text": "Not cached yet"})
    assert unavailable.status_code == 503 and unavailable.json()["ok"] is False
    assert product.post("/api/tts", json={"text": ""}).status_code == 422
