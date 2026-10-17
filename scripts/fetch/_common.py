"""Shared helpers for fetch scripts: one HTTP session, streamed downloads, checksums.

Only scripts in scripts/fetch/ and adapters in packages/adapters/ may touch the network.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
USER_AGENT = "Pathfinder-GUTS-Hackathon/0.1 (student project; data fetch)"


def session(timeout_retries: int = 3) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    retry = Retry(total=timeout_retries, backoff_factor=1.0,
                  status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def download(s: requests.Session, url: str, dest: Path, overwrite: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"  skip (exists) {dest.relative_to(REPO)}")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    with s.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    tmp.replace(dest)
    print(f"  saved {dest.relative_to(REPO)} ({dest.stat().st_size:,} bytes)")
    return dest


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)
