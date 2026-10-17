"""Hard wall-clock limit for a blocking call, shared by every live adapter.

`requests` applies its timeout per connect and per read (and not to DNS), so a slow-drip server can hold a
request far past it. Running the call in a pooled worker thread and waiting with `future.result(timeout=...)`
bounds the caller's wait exactly. An abandoned call keeps its thread until its own (connect, read) timeout
ends it, so callers must still pass one to `requests`.
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as DeadlineExceeded
from typing import Any

_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="avenir-live")  # threads are reused

__all__ = ["DeadlineExceeded", "call_with_deadline"]


def call_with_deadline[T](fn: Callable[..., T], remaining: float, *args: Any, **kwargs: Any) -> T:
    """Run `fn(*args, **kwargs)` in the pool; return its result or raise what it raised.

    Raises `DeadlineExceeded` (concurrent.futures.TimeoutError) if it is not done within `remaining` seconds;
    the future is then abandoned (cancelled if it had not started).
    """
    future = _POOL.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=max(remaining, 0.0))
    except DeadlineExceeded:
        future.cancel()
        raise
