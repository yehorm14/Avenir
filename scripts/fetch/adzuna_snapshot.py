"""Take a dated Adzuna snapshot for every occupation in data/curated/occupations.csv.

Run from a laptop (keys in .env: ADZUNA_APP_ID, ADZUNA_APP_KEY). Not needed on the cluster.
Writes snapshots/adzuna/<YYYY-MM-DD>.json: ad count, salary histogram and monthly history
per occupation query. The API adapter serves this file when the live call fails
(pull-the-plug demo). Show "Jobs by Adzuna" wherever these numbers appear.

    python scripts/fetch/adzuna_snapshot.py
    python scripts/fetch/adzuna_snapshot.py --dry-run
    python scripts/fetch/adzuna_snapshot.py --where Glasgow
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import time

from _common import REPO, die, session

BASE = "https://api.adzuna.com/v1/api/jobs/gb"


def load_env() -> None:
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--where", default="", help="optional location filter, e.g. Glasgow")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    occ_file = REPO / "data" / "curated" / "occupations.csv"
    occs = list(csv.DictReader(occ_file.open(encoding="utf-8")))
    if args.dry_run:
        for o in occs:
            print(f"would query what={o['adzuna_query']!r} where={args.where!r}")
        return

    load_env()
    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        die("set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env")
    auth = {"app_id": app_id, "app_key": app_key}
    where = {"where": args.where} if args.where else {}

    s = session()
    today = dt.date.today().isoformat()
    out = {"retrieved": today, "where": args.where or "UK", "attribution": "Jobs by Adzuna",
           "occupations": {}}
    for o in occs:
        q = {**auth, **where, "what": o["adzuna_query"]}
        rec: dict = {"title": o["title"], "soc2020": o.get("soc2020", ""), "query": o["adzuna_query"]}
        for name, path, extra in [
            ("search", "search/1", {"results_per_page": 1, "content-type": "application/json"}),
            ("histogram", "histogram", {}),
            ("history", "history", {"months": 12}),
        ]:
            try:
                r = s.get(f"{BASE}/{path}", params={**q, **extra}, timeout=10)
                r.raise_for_status()
                body = r.json()
                if name == "search":
                    body = {"count": body.get("count"), "mean": body.get("mean")}
                rec[name] = body
            except Exception as e:  # keep going; record the gap, never fill it
                rec[name] = None
                rec.setdefault("errors", []).append(f"{name}: {type(e).__name__}")
            time.sleep(0.3)  # stay well under rate limits
        out["occupations"][o["title"]] = rec
        print(f"  {o['title']}: {rec.get('search')}")

    dest = REPO / "snapshots" / "adzuna" / f"{today}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(f"saved {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
