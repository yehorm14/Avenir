"""Fetch APS employment by occupation from the Nomis API (no key needed for basic use).

Datasets (checked 17 Oct 2026 on nomisweb.co.uk):
  NM_218_1  APS218, SOC 2020, 1 to 4-digit, latest Apr 2025-Mar 2026   -> 2021 onwards
  NM_168_1  APS168, SOC 2010, 1 to 4-digit, to Jan-Dec 2021             -> 2011 to 2021

Step 1, see the dimensions and their codes (saved to data/raw/aps/<id>_def/):
    python scripts/fetch/nomis_aps.py NM_218_1 --describe

Step 2, fetch, passing Nomis query parameters as key=value (names come from step 1):
    python scripts/fetch/nomis_aps.py NM_218_1 --param date=latest --param measures=20100
    python scripts/fetch/nomis_aps.py NM_218_1 --param date=2022-12,2023-12,2024-12 --dry-run

Defaults: geography=K02000001 (UK, verify that Nomis accepts the GSS code; otherwise use the
Nomis id from the geography codelist). Results are paged 25,000 rows at a time and written to
data/raw/aps/<id>.csv. 4-digit APS counts are small samples: keep the confidence columns.
"""
from __future__ import annotations

import argparse
import csv
import io
import json

from _common import RAW, die, session

API = "https://www.nomisweb.co.uk/api/v01/dataset"
PAGE = 25_000


def describe(s, ds: str) -> None:
    out = RAW / "aps" / f"{ds}_def"
    out.mkdir(parents=True, exist_ok=True)
    r = s.get(f"{API}/{ds}.def.sdmx.json", timeout=30)
    r.raise_for_status()
    (out / "dataset.json").write_text(r.text)
    data = r.json()
    try:
        kf = data["structure"]["keyfamilies"]["keyfamily"][0]
        dims = [d["conceptref"].lower() for d in kf["components"]["dimension"]]
        print(f"{ds}: {kf.get('name', {}).get('value', '')}")
    except (KeyError, IndexError, TypeError):
        die(f"unexpected definition format; see {out / 'dataset.json'}")
    for dim in dims:
        if dim == "geography":
            print("  geography (codelist too large; see Nomis docs)")
            continue
        rr = s.get(f"{API}/{ds}/{dim}.def.sdmx.json", timeout=30)
        if not rr.ok:
            print(f"  {dim}: could not list codes ({rr.status_code})")
            continue
        (out / f"{dim}.json").write_text(rr.text)
        try:
            codes = rr.json()["structure"]["codelists"]["codelist"][0]["code"]
        except (KeyError, IndexError, TypeError):
            codes = []
        sample = ", ".join(f"{c['value']}={c['description']['value']}" for c in codes[:6])
        print(f"  {dim} ({len(codes)} codes): {sample}{' ...' if len(codes) > 6 else ''}")


def fetch(s, ds: str, params: dict[str, str], dry_run: bool) -> None:
    url = f"{API}/{ds}.data.csv"
    if dry_run:
        q = "&".join(f"{k}={v}" for k, v in params.items())
        print(f"would fetch {url}?{q}&recordoffset=0&recordlimit={PAGE} (paged)")
        return
    out = RAW / "aps" / f"{ds}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    offset, total, writer, fh = 0, 0, None, open(out, "w", newline="", encoding="utf-8")
    try:
        while True:
            r = s.get(url, params={**params, "recordoffset": offset, "recordlimit": PAGE}, timeout=120)
            r.raise_for_status()
            rows = list(csv.reader(io.StringIO(r.text)))
            if not rows:
                break
            header, body = rows[0], rows[1:]
            if writer is None:
                writer = csv.writer(fh)
                writer.writerow(header)
            writer.writerows(body)
            total += len(body)
            print(f"  rows {offset:,} to {offset + len(body):,}")
            if len(body) < PAGE:
                break
            offset += PAGE
    finally:
        fh.close()
    meta = {"dataset": ds, "params": params, "rows": total, "source": url}
    (out.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"saved data/raw/aps/{ds}.csv ({total:,} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", help="e.g. NM_218_1 or NM_168_1")
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = session()
    if args.describe:
        describe(s, args.dataset)
        return
    params = {"geography": "K02000001"}
    for p in args.param:
        if "=" not in p:
            die(f"--param needs KEY=VALUE, got {p!r}")
        k, v = p.split("=", 1)
        params[k] = v
    fetch(s, args.dataset, params, args.dry_run)


if __name__ == "__main__":
    main()
