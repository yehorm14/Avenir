"""Per-IP sliding-window rate limit for the public `POST /api/guide` and `POST /api/tts` routes.

Both routes spend a shared quota (the language model budget, Gemini's TTS free tier), so one visitor or bot
must not be able to use up a day's allowance. Over the limit the route answers 429 with a `Retry-After`
header and code `RATE_LIMITED`; the web app turns that into a friendly message.

Settings (read on every request, so tests and deploys can change them without a reload):
- `GUIDE_RATE_LIMIT`: guide requests per window per IP (default 20; 0 turns the limit off)
- `TTS_RATE_LIMIT`: TTS requests that reach the speech model per window per IP (default 5; 0 turns it off)
- `RATE_LIMIT_WINDOW_S`: window length in seconds (default 60)
- `TRUSTED_PROXY_HOPS`: number of trusted proxies in front of the app (default 0: ignore `X-Forwarded-For` and
  use the socket peer). With N > 0 the client is the Nth entry from the right of `X-Forwarded-For` (N=1 is the
  last entry); a header with fewer entries falls back to the peer. `CF-Connecting-IP` and `True-Client-IP` are
  never trusted.

State is in memory, per process: a restart or a second worker starts a fresh count. The store holds at most
`MAX_TRACKED_IPS` keys: expired keys are pruned at most once per window, then the least recently seen are
evicted down to the cap.
"""

from __future__ import annotations

import math
import os
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request

DEFAULTS = {"guide": 20, "tts": 5}
ENV_LIMIT = {"guide": "GUIDE_RATE_LIMIT", "tts": "TTS_RATE_LIMIT"}
DEFAULT_WINDOW_S = 60.0
MAX_TRACKED_IPS = 10_000

_hits: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()
_last_prune = float("-inf")
_lock = threading.Lock()
_clock: Callable[[], float] = time.monotonic


def set_clock(clock: Callable[[], float] | None) -> None:
    """Replace the time source (tests); None restores the real one."""
    global _clock
    _clock = clock or time.monotonic


def reset() -> None:
    """Forget every count (tests)."""
    global _last_prune
    with _lock:
        _hits.clear()
        _last_prune = float("-inf")


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
    peer = request.client.host if request.client else "unknown"
    hops = int(_number("TRUSTED_PROXY_HOPS", 0))
    if hops <= 0:
        return peer
    entries = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
    return entries[-hops] if len(entries) >= hops else peer


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
        _hits.move_to_end(key)
        _prune(now, window)


def _prune(now: float, window: float) -> None:
    """Called with the lock held: drop expired keys once per window, then cap the store by recency."""
    global _last_prune
    if now - _last_prune >= window:
        _last_prune = now
        for stale in [k for k, v in _hits.items() if not v or v[-1] <= now - window]:
            del _hits[stale]
    while len(_hits) > MAX_TRACKED_IPS:
        _hits.popitem(last=False)
