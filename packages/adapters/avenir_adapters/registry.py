"""The live adapters the API uses: Adzuna ads, LLM explanation writer, tag suggester.

Each function is a process-wide singleton, built on its first call. Importing this module does no I/O,
reads no environment variables and makes no network call. On the first call, a `.env` file at the repo root
fills in keys that are not already set (real environment variables win; values are never logged).
With no keys, every function returns a default that never touches the network, so the demo runs as-is.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path

from avenir_contracts.data import REPO_ROOT, SNAPSHOT_DIR
from avenir_contracts.ports import AdsSource, ExplanationWriter, KeywordSuggester, TagSuggester

from .adzuna.source import AdzunaAds
from .llm.writer import writer_from_env

ENV_FILE = REPO_ROOT / ".env"
_dotenv_loaded = False


def _load_dotenv(path: Path) -> None:
    """Sets each KEY=VALUE from `path` that is not already in the environment. Missing file: nothing."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():  # utf-8-sig drops a Notepad/PowerShell BOM
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            try:
                os.environ.setdefault(key, value)
            except ValueError:  # NUL in key or value: skip this line, keep the rest
                continue


def _ensure_dotenv() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True  # set first: a broken .env is not retried on every call
    try:
        _load_dotenv(ENV_FILE)
    except (OSError, ValueError):  # ValueError covers UnicodeDecodeError; a broken .env must never stop start-up
        pass


def _env(name: str) -> str | None:
    """The variable's value, or None when it is unset or empty."""
    return (os.environ.get(name) or "").strip() or None


@functools.lru_cache(maxsize=1)
def tag_suggester() -> TagSuggester:
    """ML's deterministic keyword matcher. Swap here when Arsenii's matcher ships."""
    _ensure_dotenv()
    return KeywordSuggester()


@functools.lru_cache(maxsize=1)
def ads_source() -> AdsSource:
    """Adzuna live ad counts; without keys or when live fails, the snapshot / catalogue value."""
    _ensure_dotenv()
    snapshot_dir = os.environ.get("AVENIR_SNAPSHOT_DIR") or SNAPSHOT_DIR
    return AdzunaAds(_env("ADZUNA_APP_ID"), _env("ADZUNA_APP_KEY"), snapshot_dir=Path(snapshot_dir))


@functools.lru_cache(maxsize=1)
def explanation_writer() -> ExplanationWriter:
    """LLM explanation only when LLM_ENABLED and its base URL, key and model are set; else the template."""
    _ensure_dotenv()
    return writer_from_env()


def reset() -> None:
    """Forget the singletons and the .env load, so the next call rebuilds from the current environment."""
    global _dotenv_loaded
    tag_suggester.cache_clear()
    ads_source.cache_clear()
    explanation_writer.cache_clear()
    _dotenv_loaded = False
