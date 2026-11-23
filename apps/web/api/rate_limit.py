"""Per-IP sliding-window rate limit for the public `POST /api/guide` and `POST /api/tts` routes.

Both routes spend a shared quota (the language model budget, Gemini's TTS free tier), so one visitor or bot
must not be able to use up a day's allowance. Over the limit the route answers 429 with a `Retry-After`
header and code `RATE_LIMITED`; the web app turns that into a friendly message.

Settings (read on every request, so tests and deploys can change them without a reload):
- `GUIDE_RATE_LIMIT`: guide requests per window per IP (default 20; 0 turns the limit off)
- `TTS_RATE_LIMIT`: TTS requests that reach the speech model per window per IP (default 5; 0 turns it off)
- `RATE_LIMIT_WINDOW_S`: window length in seconds (default 60)
- `TRUST_PROXY_HEADERS`: 1/true to take the client IP from the last `X-Forwarded-For` entry (set it behind
  Render's proxy; leave it off otherwise, because the header is client-controlled when there is no proxy)

State is in memory, per process: a restart or a second worker starts a fresh count.
"""

from __future__ import annotations

import math
import os
import threading
import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request

DEFAULTS = {"guide": 20, "tts": 5}
ENV_LIMIT = {"guide": "GUIDE_RATE_LIMIT", "tts": "TTS_RATE_LIMIT"}
DEFAULT_WINDOW_S = 60.0
MAX_TRACKED_IPS = 10_000

_hits: dict[tuple[str, str], deque[float]] = {}
_lock = threading.Lock()
_clock: Callable[[], float] = time.monotonic


def set_clock(clock: Callable[[], float] | None) -> None:
    """Replace the time source (tests); None restores the real one."""
    global _clock
    _clock = clock or time.monotonic


def reset() -> None:
    """Forget every count (tests)."""
    with _lock:
        _hits.clear()


def _number(name: str, default: float) -> float:
    try:
        return float((os.environ.get(name) or "").strip())
    except ValueError:
        return default


def limit_for(scope: str) -> int:
    return max(0, int(_number(ENV_LIMIT[scope], DEFAULTS[scope])))


def window_s() -> float:
    value = _number("RATE_LIMIT_WINDOW_S", DEFAULT_WINDOW_S)
    return value if value > 0 else DEFAULT_WINDOW_S


def client_ip(request: Request) -> str:
    if (os.environ.get("TRUST_PROXY_HEADERS") or "").strip().lower() in {"1", "true", "yes", "on"}:
        forwarded = request.headers.get("x-forwarded-for", "")
        # The last entry is the one the trusted proxy appended; earlier ones can be forged by the client.
        last = forwarded.split(",")[-1].strip()
        if last:
            return last
    return request.client.host if request.client else "unknown"


def check(scope: str, request: Request) -> None:
    """Count one request for this IP and scope; raise 429 when the window is already full."""
    limit = limit_for(scope)
    if limit <= 0:
        return
    window = window_s()
    now = _clock()
    key = (scope, client_ip(request))
    with _lock:
        hits = _hits.setdefault(key, deque())
        while hits and hits[0] <= now - window:
            hits.popleft()
        if len(hits) >= limit:
            retry = max(1, math.ceil(hits[0] + window - now))
            raise HTTPException(
                429,
                {"code": "RATE_LIMITED", "message": f"Too many requests. Try again in {retry} seconds.", "retry_after": retry},
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)
        if len(_hits) > MAX_TRACKED_IPS:
            for stale in [k for k, v in _hits.items() if not v or v[-1] <= now - window]:
                del _hits[stale]
