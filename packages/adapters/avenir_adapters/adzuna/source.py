"""Adzuna live job-ad counts with an instant snapshot fallback (the "pull the plug" demo).

`AdzunaAds.ads_now` never raises and returns within `deadline_s` (3 s) in total. The HTTP call runs in a
pooled worker thread and we wait for it with a hard timeout, so a slow DNS, connect or read cannot stretch the
budget; the abandoned thread ends on its own through the (connect, read) timeout given to `requests`.
Order: cached live value, live call (one retry only on timeout, connection error or 5xx, only if at least
`MIN_RETRY_S` is left), then the newest snapshot file with a usable entry for the SOC in
`<snapshot_dir>/adzuna/<YYYY-MM-DD>.json`, then the catalogue `ads_now` metric, then a missing metric.
A circuit breaker skips live calls for `BREAKER_S` after a timeout, connection error or HTTP 401/403/429,
so an outage costs the stage one slow request, not one per click. Show "Jobs by Adzuna" next to the number.
Logs carry only exception types and HTTP status codes, never keys or URLs.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

from avenir_adapters._deadline import DeadlineExceeded, call_with_deadline
from avenir_contracts import Career, Metric, SourceStatus
from avenir_contracts.ports import SnapshotAds

log = logging.getLogger(__name__)

API_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
DEADLINE_S = 3.0
MIN_RETRY_S = 0.5
CACHE_TTL_S = 600.0
BREAKER_S = 60.0
NOTE = "Jobs by Adzuna: live ads matching the job title."
_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def _metric(count: float, as_of: str) -> Metric:
    return Metric(value=count, unit="count", as_of=as_of, source="adzuna", granularity="estimate",
                  confidence="medium", status="final", note=NOTE)


def _is_count(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and v >= 0


def _get(params: dict[str, Any], timeout: tuple[float, float]) -> tuple[int, Any]:
    """Runs in a worker thread: (status code, parsed body, or None for a non-2xx)."""
    resp = requests.get(API_URL, params=params, timeout=timeout)
    status = resp.status_code
    return status, (resp.json() if 200 <= status < 300 else None)


class AdzunaAds:
    """Implements `avenir_contracts.AdsSource`. `snapshot_dir` is the `snapshots/` root."""

    def __init__(self, app_id: str | None, app_key: str | None, snapshot_dir: Path,
                 clock: Callable[[], float] = time.monotonic, deadline_s: float = DEADLINE_S) -> None:
        self._app_id = app_id
        self._app_key = app_key
        self._dir = Path(snapshot_dir) / "adzuna"
        self._clock = clock
        self._deadline_s = deadline_s
        self._cache: dict[str, tuple[float, Metric, str]] = {}  # soc -> (expires_at, metric, as_of)
        self._snap_cache: dict[str, tuple[int, Any]] = {}  # file name -> (mtime_ns, parsed JSON or None)
        self._breaker_until = 0.0
        self._catalogue = SnapshotAds()
        self.live = bool(app_id and app_key)

    def set_live(self, enabled: bool) -> None:
        self.live = enabled
        if enabled:
            self._breaker_until = 0.0  # an explicit switch-on is a fresh start

    def ads_now(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        try:
            if self.live and self._app_id and self._app_key:
                hit = self._live(career)
                if hit is not None:
                    return hit
            return self._fallback(career, region)
        except Exception as e:  # the demo must never fail on this adapter
            log.warning("Adzuna adapter error: %s", type(e).__name__)
            return self._missing("Could not read ads data.")

    # ---- live -------------------------------------------------------------------------

    def _live(self, career: Career) -> tuple[Metric, SourceStatus] | None:
        cached = self._cache.get(career.soc2020)
        if cached and self._clock() < cached[0]:
            return cached[1], SourceStatus(name="adzuna", status="live", as_of=cached[2], region="UK")
        if self._clock() < self._breaker_until:
            return None
        count = self._fetch_count(career.title)
        if count is None or not self.live:  # plug pulled while the call was in flight: snapshot now
            return None
        as_of = dt.date.today().isoformat()
        metric = _metric(count, as_of)
        self._cache[career.soc2020] = (self._clock() + CACHE_TTL_S, metric, as_of)
        return metric, SourceStatus(name="adzuna", status="live", as_of=as_of, region="UK")

    def _fetch_count(self, what: str) -> float | None:
        deadline = self._clock() + self._deadline_s
        params = {"app_id": self._app_id, "app_key": self._app_key, "what": what,
                  "results_per_page": 1, "content-type": "application/json"}
        trip = False
        for attempt in range(2):
            remaining = deadline - self._clock()
            if remaining <= 0 or (attempt == 1 and remaining < MIN_RETRY_S):
                break
            retry = False  # `trip` is sticky: a timeout followed by a 5xx still opens the breaker
            try:
                status, body = call_with_deadline(_get, remaining, params, (remaining, remaining))
            except (DeadlineExceeded, requests.Timeout, requests.ConnectionError) as e:
                log.warning("Adzuna live call failed: %s", type(e).__name__)
                retry = trip = True
            except Exception as e:  # bad JSON, unexpected error: fall back, no retry
                log.warning("Adzuna live call failed: %s", type(e).__name__)
            else:
                if 200 <= status < 300:
                    count = body.get("count") if isinstance(body, dict) else None
                    if _is_count(count):
                        return count
                    log.warning("Adzuna live call failed: response without a usable count")
                else:
                    log.warning("Adzuna live call failed: HTTP %s", status)
                    retry = status >= 500
                    trip = trip or status in (401, 403, 429)
            if not retry:
                break
        if trip:
            self._breaker_until = self._clock() + BREAKER_S
            log.warning("Adzuna live calls paused for %.0f s", BREAKER_S)
        return None

    # ---- fallback ---------------------------------------------------------------------

    def _fallback(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        snap = self._snapshot_count(career.soc2020)
        if snap is not None:
            count, retrieved = snap
            return _metric(count, retrieved), SourceStatus(name="adzuna", status="snapshot",
                                                           as_of=retrieved, region="UK")
        if "ads_now" in career.metrics:
            return self._catalogue.ads_now(career, region)
        return self._missing("No Adzuna ads count available for this job.")

    def _snapshot_count(self, soc: str) -> tuple[float, str] | None:
        """(count, retrieved date) from the newest snapshot file with a usable entry for `soc`."""
        try:
            files = sorted((p for p in self._dir.glob("*.json") if _FILE_RE.match(p.name)), reverse=True)
        except OSError:
            return None
        for path in files:
            data = self._read_snapshot(path)
            try:
                count = data["occupations"][soc]["search"]["count"]
                retrieved = data.get("retrieved")
            except (KeyError, TypeError, AttributeError):
                continue
            if _is_count(count):
                return count, retrieved if isinstance(retrieved, str) else path.stem
        return None

    def _read_snapshot(self, path: Path) -> Any:
        """Parsed JSON, or None if unreadable. Cached by (name, mtime) so outages don't re-parse."""
        try:
            mtime = path.stat().st_mtime_ns
            cached = self._snap_cache.get(path.name)
            if cached and cached[0] == mtime:
                return cached[1]
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            self._snap_cache[path.name] = (mtime, data)
            return data
        except OSError:
            return None

    @staticmethod
    def _missing(note: str) -> tuple[Metric, SourceStatus]:
        return (Metric.missing("count", "adzuna", note=note),
                SourceStatus(name="adzuna", status="missing", region="UK"))
