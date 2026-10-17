"""Check that every raw input in data/manifest.yaml is present and record checksums.

    python scripts/fetch/check_manifest.py          # report, write data/manifest.lock.json
    python scripts/fetch/check_manifest.py --strict # exit 1 if anything is missing

Commit data/manifest.lock.json so every machine (laptop, cluster) can confirm it has the
same files. Never commit data/raw/ itself.
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml

from _common import REPO, sha256


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    manifest = yaml.safe_load((REPO / "data" / "manifest.yaml").read_text())
    lock, missing = {}, []
    for src in manifest["sources"]:
        base = REPO / src["path"]
        files = sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
        files = [p for p in files if not p.name.endswith(".part")]
        expected = src.get("expect", [])
        absent = [e for e in expected if not any(p.name == e for p in files)]
        licence = "ok" if src.get("licence_checked_by") else "licence not checked"
        if not files:
            missing.append(src["id"])
            print(f"MISSING  {src['id']:18s} -> {src['path']}  ({src['how']})")
        else:
            note = f"; expected but absent: {absent}" if absent else ""
            print(f"present  {src['id']:18s} {len(files)} files, {licence}{note}")
        lock[src["id"]] = {str(p.relative_to(REPO)).replace("\\", "/"): sha256(p) for p in files}

    (REPO / "data" / "manifest.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True))
    print(f"\n{len(manifest['sources']) - len(missing)}/{len(manifest['sources'])} sources present")
    if args.strict and missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
