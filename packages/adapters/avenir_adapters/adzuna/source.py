"""Adzuna live job-ad counts with an instant snapshot fallback (the "pull the plug" demo).

`AdzunaAds.ads_now` never raises and returns within `DEADLINE_S` seconds in total: one live
attempt, one retry only if at least `MIN_RETRY_S` of the budget is left, then the latest
`<snapshot_dir>/adzuna/<YYYY-MM-DD>.json` entry for the SOC, then the catalogue `ads_now`
metric, then a missing metric. Show "Jobs by Adzuna" wherever the number appears.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

from avenir_contracts import Career, Metric, SourceStatus
from avenir_contracts.ports import SnapshotAds

API_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
DEADLINE_S = 3.0
MIN_RETRY_S = 0.5
CACHE_TTL_S = 600.0
NOTE = "Jobs by Adzuna: live ads matching the job title."
_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def _metric(count: float, as_of: str) -> Metric:
    return Metric(value=count, unit="count", as_of=as_of, source="adzuna", granularity="estimate",
                  confidence="medium", status="final", note=NOTE)


def _is_count(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and v >= 0


class AdzunaAds:
    """Implements `avenir_contracts.AdsSource`. `snapshot_dir` is the `snapshots/` root."""

    def __init__(self, app_id: str | None, app_key: str | None, snapshot_dir: Path,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._app_id = app_id
        self._app_key = app_key
        self._dir = Path(snapshot_dir) / "adzuna"
        self._clock = clock
        self._cache: dict[str, tuple[float, Metric, str]] = {}  # soc -> (expires_at, metric, as_of)
        self._catalogue = SnapshotAds()
        self.live = bool(app_id and app_key)

    def set_live(self, enabled: bool) -> None:
        self.live = enabled

    def ads_now(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        try:
            if self.live and self._app_id and self._app_key:
                hit = self._live(career)
                if hit is not None:
                    return hit
            return self._fallback(career, region)
        except Exception:  # the demo must never fail on this adapter
            return self._missing("Could not read ads data.")

    # ---- live -------------------------------------------------------------------------

    def _live(self, career: Career) -> tuple[Metric, SourceStatus] | None:
        cached = self._cache.get(career.soc2020)
        if cached and self._clock() < cached[0]:
            return cached[1], SourceStatus(name="adzuna", status="live", as_of=cached[2], region="UK")
        count = self._fetch_count(career.title)
        if count is None:
            return None
        as_of = dt.date.today().isoformat()
        metric = _metric(count, as_of)
        self._cache[career.soc2020] = (self._clock() + CACHE_TTL_S, metric, as_of)
        return metric, SourceStatus(name="adzuna", status="live", as_of=as_of, region="UK")

    def _fetch_count(self, what: str) -> float | None:
        deadline = self._clock() + DEADLINE_S
        params = {"app_id": self._app_id, "app_key": self._app_key, "what": what,
                  "results_per_page": 1, "content-type": "application/json"}
        for attempt in range(2):
            remaining = deadline - self._clock()
            if remaining <= 0 or (attempt == 1 and remaining < MIN_RETRY_S):
                return None
            try:
                resp = requests.get(API_URL, params=params, timeout=remaining)
                resp.raise_for_status()
                body = resp.json()
                count = body.get("count") if isinstance(body, dict) else None
                if _is_count(count):
                    return count
            except Exception:  # timeout, connection, non-2xx (incl. quota), bad JSON: all mean fall back
                pass
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
        """(count, retrieved date) from the latest snapshot file; None if absent or unreadable."""
        try:
            files = sorted(p for p in self._dir.glob("*.json") if _FILE_RE.match(p.name))
            if not files:
                return None
            latest = files[-1]
            data = json.loads(latest.read_text(encoding="utf-8"))
            search = data["occupations"][soc]["search"]
            count = search["count"]
            if not _is_count(count):
                return None
            retrieved = data.get("retrieved")
            return count, retrieved if isinstance(retrieved, str) else latest.stem
        except Exception:
            return None

    @staticmethod
    def _missing(note: str) -> tuple[Metric, SourceStatus]:
        return (Metric.missing("count", "adzuna", note=note),
                SourceStatus(name="adzuna", status="missing", region="UK"))
