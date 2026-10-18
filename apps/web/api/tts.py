"""Read a guide answer aloud with Gemini's native text-to-speech model.

`POST /api/tts` takes `{text, voice?}` and returns `{mime_type: "audio/wav", audio_base64, voice, model, cached}`.
The audio travels as base64 JSON because the assembled app (`api.application`) wraps every experience
route in the `{ok, data, error, meta}` envelope, so raw bytes would not survive it.

Keys: `GEMINI_API_KEY`, then `GEMINI_API_KEY_2`, then `LLM_API_KEY` when `LLM_BASE_URL` points at
generativelanguage.googleapis.com. The key is sent in the `x-goog-api-key` header (never in the URL) and is
never logged or returned; logs name only the environment variable. A key that hits a quota (429) or is
rejected (401/403) is skipped for the rest of the process (a per-minute limit for 60 s), and the next key is
tried. Model: `TTS_MODEL` (default `gemini-3.8-flash-tts`), falling back once to `gemini-2.5-flash-preview-tts`
on 404, 5xx or when every key is out of quota for the first model. 20 s total deadline.

Audio is cached in memory (LRU, 64 entries) and on disk (`TTS_CACHE_DIR`, default `data/cache/tts/`, which
writes its own `.gitignore`), keyed by sha256 of (model, voice, cleaned text), so rehearsed answers replay with
no quota across restarts. When no key is configured, or every key is exhausted, the route answers 503 with code
`TTS_UNAVAILABLE` and a short reason; the frontend then uses the browser's own speechSynthesis.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import struct
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Literal

import requests
from fastapi import HTTPException
from pydantic import BaseModel, Field

from avenir_adapters._deadline import DeadlineExceeded, call_with_deadline

log = logging.getLogger(__name__)

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.8-flash-tts"
FALLBACK_MODEL = "gemini-2.5-flash-preview-tts"
VOICES = ("Kore", "Puck", "Charon", "Aoede")
MAX_TEXT = 1500
DEADLINE_S = 20.0
MEMORY_ENTRIES = 64
MINUTE_COOLDOWN_S = 60.0
PCM_RATE = 24000
KEY_VARS = ("GEMINI_API_KEY", "GEMINI_API_KEY_2")
QUOTA_NOTE = "Gemini TTS free tier: 10 requests/day per key; cached replays are free"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache" / "tts"

_memory: OrderedDict[str, bytes] = OrderedDict()
_blocked: dict[tuple[str, str], float] = {}  # (key env name, model or "*") -> monotonic time it is usable again
_lock = threading.Lock()


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT)
    voice: Literal["Kore", "Puck", "Charon", "Aoede"] = "Kore"


class Unavailable(Exception):
    """No audio could be made; `reason` is a short code safe to show (never a key or URL)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


# ---- configuration -----------------------------------------------------------------------------------


def _keys() -> list[tuple[str, str]]:
    """(env var name, key) pairs in try order, de-duplicated."""
    found: list[tuple[str, str]] = []
    for name in KEY_VARS:
        key = (os.environ.get(name) or "").strip()
        if key:
            found.append((name, key))
    if "generativelanguage.googleapis.com" in (os.environ.get("LLM_BASE_URL") or ""):
        key = (os.environ.get("LLM_API_KEY") or "").strip()
        if key:
            found.append(("LLM_API_KEY", key))
    unique: list[tuple[str, str]] = []
    for name, key in found:
        if key not in {k for _, k in unique}:
            unique.append((name, key))
    return unique


def _models() -> list[str]:
    primary = (os.environ.get("TTS_MODEL") or "").strip() or DEFAULT_MODEL
    return [primary] if primary == FALLBACK_MODEL else [primary, FALLBACK_MODEL]


def _cache_dir() -> Path:
    configured = (os.environ.get("TTS_CACHE_DIR") or "").strip()
    return Path(configured) if configured else DEFAULT_CACHE_DIR


def tts_available() -> bool:
    return bool(_keys())


def tts_status() -> dict:
    """Fields for the health and bootstrap payloads."""
    return {"tts": tts_available(), "tts_quota_note": QUOTA_NOTE}


def reset_state() -> None:
    """Forget the memory cache and blocked keys (tests)."""
    with _lock:
        _memory.clear()
        _blocked.clear()


# ---- text and audio ----------------------------------------------------------------------------------

_MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_LINE_MARK = re.compile(r"^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+•]\s+|\d+[.)]\s+)", re.MULTILINE)
_EMPHASIS = re.compile(r"(\*\*|__|\*|_|~~|`+)")


def clean_text(text: str) -> str:
    """Spoken form: markdown links read as their label, URLs, headings, bullets and emphasis dropped."""
    text = _MD_LINK.sub(r"\1", text)
    text = _URL.sub("", text)
    text = re.sub(r"^\s*([-*_])\s*(?:\1\s*){2,}$", "", text, flags=re.MULTILINE)  # horizontal rules
    text = _LINE_MARK.sub("", text)
    text = _EMPHASIS.sub("", text)
    text = re.sub(r"\(\s*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def wav_from_pcm(pcm: bytes, rate: int = PCM_RATE, channels: int = 1, sample_bits: int = 16) -> bytes:
    """A RIFF/WAVE header around raw little-endian PCM."""
    block = channels * sample_bits // 8
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(pcm),
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        rate,
        rate * block,
        block,
        sample_bits,
        b"data",
        len(pcm),
    )
    return header + pcm


def _to_wav(mime: str, data: bytes) -> bytes:
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return data
    lowered = mime.lower().replace(" ", "")
    if lowered.startswith(("audio/l16", "audio/pcm")):
        match = re.search(r"rate=(\d+)", lowered)
        return wav_from_pcm(data, int(match.group(1)) if match else PCM_RATE)
    raise Unavailable("unexpected_audio_format")


def _audio_from(body: dict) -> bytes:
    try:
        parts = body["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as error:
        raise Unavailable("no_audio_in_reply") from error
    for part in parts:
        inline = part.get("inlineData") if isinstance(part, dict) else None
        if inline and inline.get("data"):
            try:
                raw = base64.b64decode(inline["data"])
            except (ValueError, TypeError) as error:
                raise Unavailable("bad_audio_data") from error
            return _to_wav(inline.get("mimeType", ""), raw)
    raise Unavailable("no_audio_in_reply")


# ---- cache -------------------------------------------------------------------------------------------


def _cache_key(model: str, voice: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{voice}\n{text}".encode()).hexdigest()


def _cache_get(digest: str) -> bytes | None:
    with _lock:
        if digest in _memory:
            _memory.move_to_end(digest)
            return _memory[digest]
    path = _cache_dir() / f"{digest}.wav"
    try:
        audio = path.read_bytes()
    except OSError:
        return None
    _memory_put(digest, audio)
    return audio


def _memory_put(digest: str, audio: bytes) -> None:
    with _lock:
        _memory[digest] = audio
        _memory.move_to_end(digest)
        while len(_memory) > MEMORY_ENTRIES:
            _memory.popitem(last=False)


def _cache_put(digest: str, audio: bytes) -> None:
    _memory_put(digest, audio)
    folder = _cache_dir()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        ignore = folder / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n", encoding="utf-8")
        tmp = folder / f"{digest}.wav.tmp"
        tmp.write_bytes(audio)
        tmp.replace(folder / f"{digest}.wav")
    except OSError:
        log.warning("tts: disk cache write failed")


# ---- calling Gemini ----------------------------------------------------------------------------------


def _post(url: str, key: str, payload: dict, timeout: float) -> tuple[int, dict | None, str]:
    resp = requests.post(url, headers={"x-goog-api-key": key}, json=payload, timeout=(min(timeout, 5.0), timeout))
    try:
        body = resp.json()
    except ValueError:
        body = None
    return resp.status_code, body if isinstance(body, dict) else None, (resp.text or "")[:2000]


def _is_blocked(name: str, model: str, now: float) -> bool:
    with _lock:
        return any(_blocked.get((name, scope), 0.0) > now for scope in (model, "*"))


def _block(name: str, scope: str, seconds: float) -> None:
    with _lock:
        _blocked[(name, scope)] = time.monotonic() + seconds


def synthesise(text: str, voice: str = "Kore") -> tuple[bytes, str, bool]:
    """(wav bytes, model, cached). Raises Unavailable with a short reason."""
    spoken = clean_text(text)
    if not spoken:
        raise HTTPException(422, "Nothing to read aloud after removing links and formatting")
    models = _models()
    for model in models:
        audio = _cache_get(_cache_key(model, voice, spoken))
        if audio is not None:
            return audio, model, True
    keys = _keys()
    if not keys:
        raise Unavailable("no_key_configured")
    payload = {
        "contents": [{"parts": [{"text": spoken}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    deadline = time.monotonic() + DEADLINE_S
    reason = "all_keys_rate_limited"
    for model in models:
        url = f"{API_ROOT}/{model}:generateContent"
        for name, key in keys:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Unavailable("timeout")
            if _is_blocked(name, model, time.monotonic()):
                continue
            try:
                status, body, text_body = call_with_deadline(_post, remaining, url, key, payload, remaining)
            except (DeadlineExceeded, requests.Timeout):
                log.warning("tts: %s timed out with %s", model, name)
                raise Unavailable("timeout") from None
            except requests.RequestException:
                log.warning("tts: network error calling %s with %s", model, name)
                reason = "network_error"
                break
            if status == 200 and body is not None:
                try:
                    audio = _audio_from(body)
                except Unavailable as error:
                    log.warning("tts: %s returned no usable audio (%s)", model, error.reason)
                    reason = error.reason
                    break
                _cache_put(_cache_key(model, voice, spoken), audio)
                return audio, model, False
            if status == 429:
                daily = "perday" in text_body.lower().replace(" ", "").replace("_", "")
                _block(name, model, float("inf") if daily else MINUTE_COOLDOWN_S)
                log.warning("tts: %s rate limited for %s (%s)", name, model, "daily quota" if daily else "per minute")
                reason = "daily_quota_used" if daily else "rate_limited"
                continue
            if status in (401, 403):
                _block(name, "*", float("inf"))
                log.warning("tts: %s rejected (HTTP %s)", name, status)
                reason = "key_rejected"
                continue
            log.warning("tts: %s answered HTTP %s", model, status)
            reason = f"model_http_{status}"
            break  # 404, 5xx and anything else: try the fallback model
    raise Unavailable(reason)


def text_to_speech(request: TtsRequest) -> dict:
    """`POST /api/tts` (registered in main.py): base64 WAV for one guide answer; 503 means use speechSynthesis."""
    try:
        audio, model, cached = synthesise(request.text, request.voice)
    except Unavailable as error:
        raise HTTPException(503, {"code": "TTS_UNAVAILABLE", "message": error.reason}) from None
    return {
        "mime_type": "audio/wav",
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "voice": request.voice,
        "model": model,
        "cached": cached,
    }
