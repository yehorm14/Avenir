"""Disk cache of accepted model replies, so a rehearsed demo replays without spending model quota.

Keyed by sha256 of every input the model sees: the SOC, the message, the follow-up history, the quiz
profile, the model name, a digest of the evidence handed to the model (role pack, compared packs, career
path, link labels, preference wording) and CACHE_VERSION. A follow-up with different history, a changed
profile, changed evidence data or another model therefore never replays a stale reply; an identical
repeat request does. Only replies that passed the hard checks are stored (text, model, tools used,
checks, typed claims); links and the path are rebuilt by the API on every request. The directory is git-ignored
(`apps/web/api/.cache/`); set `GUIDE_CACHE_DIR` to move it or `GUIDE_CACHE=0` to turn it off. Writes go to
a uniquely named temporary file and are swapped in atomically, so concurrent saves never interleave.
Read or write failures (including a missing or unwritable directory) are ignored: the cache never breaks
the guide, and the key-free prepared fallback never touches the cache.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path(__file__).resolve().parent / ".cache" / "guide"
FIELDS = ("text", "model", "tools_used", "checks", "claims")
CACHE_VERSION = 3  # bump when the prompt, checks or reply shape change


def _dir() -> Path | None:
    if (os.environ.get("GUIDE_CACHE") or "").strip().lower() in ("0", "false", "no", "off"):
        return None
    configured = (os.environ.get("GUIDE_CACHE_DIR") or "").strip()
    return Path(configured) if configured else DEFAULT_DIR


def evidence_digest(*parts: Any) -> str:
    """Short stable digest of the evidence/config the model is given alongside the conversation."""
    raw = json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cache_key(
    soc: str,
    message: str,
    profile: dict | None,
    model: str,
    history: list[dict] | None = None,
    evidence: str = "",
) -> str:
    raw = json.dumps(
        {
            "v": CACHE_VERSION,
            "soc": soc,
            "message": message,
            "history": history or [],
            "profile": profile,
            "model": model,
            "evidence": evidence,
        },
        sort_keys=True,
    )
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
    tmp_name = None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({field: entry.get(field) for field in FIELDS}, ensure_ascii=False)
        fd, tmp_name = tempfile.mkstemp(dir=folder, prefix=f"{key}.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_name, folder / f"{key}.json")
        tmp_name = None
    except OSError:
        pass
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
