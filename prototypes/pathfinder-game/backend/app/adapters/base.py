"""One adapter per data source. Each tries a live fetch (when enabled) and
falls back to the checked-in snapshot, so the app always works offline."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots"


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    publisher: str
    url: str | None
    licence: str
    gives: str
    coverage: str
    scored: bool = True


class SourceAdapter:
    info: SourceInfo
    snapshot_file: str | None = None

    def __init__(self) -> None:
        self.mode = "snapshot"
        self.edition: str | None = None

    def fetch_live(self) -> dict:
        """Override per source. Not implemented means: use the snapshot."""
        raise NotImplementedError

    def load(self) -> dict:
        if os.getenv("CAREERS_LIVE") == "1":
            try:
                data = self.fetch_live()
                self.mode = "live"
                self.edition = data.get("edition")
                return data
            except NotImplementedError:
                pass
            except Exception:  # live source down or changed: never break the app
                log.exception("Live fetch failed for %s, using snapshot", self.info.id)
        if self.snapshot_file is None:
            return {}
        with open(SNAPSHOT_DIR / self.snapshot_file, encoding="utf-8") as f:
            data = json.load(f)
        self.mode = "snapshot"
        self.edition = data.get("edition")
        return data
