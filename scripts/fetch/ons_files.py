"""Download fixed-URL files listed under `files:` in data/manifest.yaml (ONS crosswalks).

    python scripts/fetch/ons_files.py                 # all sources that have `files`
    python scripts/fetch/ons_files.py soc2010_isco08  # one source
    python scripts/fetch/ons_files.py --dry-run
"""
from __future__ import annotations

import argparse
from urllib.parse import parse_qs, urlparse

import yaml

from _common import REPO, die, download, session


def filename(url: str) -> str:
    uri = parse_qs(urlparse(url).query).get("uri", [urlparse(url).path])[0]
    return uri.rstrip("/").split("/")[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="manifest source ids (default: all with files)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    manifest = yaml.safe_load((REPO / "data" / "manifest.yaml").read_text())
    sources = [x for x in manifest["sources"] if x.get("files")]
    if args.ids:
        sources = [x for x in sources if x["id"] in args.ids]
        if not sources:
            die(f"no source with files matches {args.ids}")

    s = session()
    for src in sources:
        print(f"{src['id']}: {src['name']}")
        for url in src["files"]:
            dest = REPO / src["path"] / filename(url)
            if args.dry_run:
                print(f"  would fetch {url}\n    -> {dest.relative_to(REPO)}")
            else:
                download(s, url, dest, args.overwrite)


if __name__ == "__main__":
    main()
