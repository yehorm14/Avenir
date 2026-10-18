#!/usr/bin/env python3
"""Package a committed source tree and its built web UI without local extras."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from check_secrets import scan_repository


class DeliveryError(Exception):
    """A reviewable source or build checkpoint is missing."""


class AssetReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value and (key == "src" or (tag == "link" and key == "href")):
                self.references.append(value)


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def make_archive(root: Path) -> bytes:
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise DeliveryError("Commit tracked changes before packaging a delivery.")
    if scan_repository(root):
        raise DeliveryError("Secret check failed; inspect scripts/check_secrets.py output before packaging.")
    files: dict[str, bytes] = {}
    names = git(root, "ls-files", "-z").decode().split("\0")
    for name in filter(None, names):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise DeliveryError(f"Source symlink is not supported in the delivery: {name}")
        if name == "data/raw/.gitkeep":
            continue
        if "node_modules" in path.parts or name.startswith("data/raw/"):
            raise DeliveryError("Tracked dependencies or raw data must be removed before packaging.")
        files[name] = path.read_bytes()

    dist = root / "apps/web/dist"
    index = dist / "index.html"
    if not index.is_file() or dist.is_symlink():
        raise DeliveryError("Build the web app before packaging (apps/web/dist/index.html is missing).")
    for path in sorted(dist.rglob("*")):
        if path.is_symlink():
            raise DeliveryError("Build contains a symlink; rebuild using ordinary files.")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    parser = AssetReferences()
    parser.feed(index.read_text())
    for reference in parser.references:
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        asset = (dist / unquote(parsed.path).lstrip("/")).resolve()
        if not asset.is_relative_to(dist.resolve()) or not asset.is_file():
            raise DeliveryError("Build is incomplete: an asset referenced by index.html is missing.")
    manifest = {
        "revision": git(root, "rev-parse", "HEAD").decode().strip(),
        "contents": "Committed source and prebuilt web UI. Local settings, raw data and dependencies excluded.",
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    }
    files["SUBMISSION.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise DeliveryError("Output already exists; choose a new delivery filename.")
        payload = make_archive(args.root.resolve())
        with args.output.open("xb") as output:
            output.write(payload)
    except (DeliveryError, OSError, subprocess.CalledProcessError) as error:
        print(f"Delivery not created: {error}", file=sys.stderr)
        return 1
    print(f"Created {args.output.name} ({len(payload):,} bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
