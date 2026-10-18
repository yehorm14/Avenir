"""Disk cache of accepted model replies, so a rehearsed demo replays without spending model quota.

Keyed by sha256 of the SOC, the message, the quiz profile and the model name. Only replies that passed
the hard checks are stored (text, model, tools used, checks); links and the path are rebuilt by the API
on every request. The directory is git-ignored (`apps/web/api/.cache/`); set `GUIDE_CACHE_DIR` to move it
or `GUIDE_CACHE=0` to turn it off. Read or write failures are ignored: the cache never breaks the guide.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path(__file__).resolve().parent / ".cache" / "guide"
FIELDS = ("text", "model", "tools_used", "checks")


def _dir() -> Path | None:
    if (os.environ.get("GUIDE_CACHE") or "").strip().lower() in ("0", "false", "no", "off"):
        return None
    configured = (os.environ.get("GUIDE_CACHE_DIR") or "").strip()
    return Path(configured) if configured else DEFAULT_DIR


def cache_key(soc: str, message: str, profile: dict | None, model: str) -> str:
    raw = json.dumps({"soc": soc, "message": message, "profile": profile, "model": model}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load(key: str) -> dict[str, Any] | None:
    folder = _dir()
    if folder is None:
        return None
    try:
        entry = json.loads((folder / f"{key}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(entry, dict) or not isinstance(entry.get("text"), str) or not entry["text"]:
        return None
    return {field: entry.get(field) for field in FIELDS}


def save(key: str, entry: dict[str, Any]) -> None:
    folder = _dir()
    if folder is None:
        return
    try:
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / f"{key}.tmp"
        tmp.write_text(json.dumps({field: entry.get(field) for field in FIELDS}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(folder / f"{key}.json")
    except OSError:
        return
