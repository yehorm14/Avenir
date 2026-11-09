"""Build snapshots/catalogue.json from the curated CSV plus the data we can load.

    python -m avenir_etl.build [--curated PATH] [--routes PATH] [--oid PATH] [--out DIR]

Also writes snapshots/routes.json from the curated routes CSV. Both inputs are validated
before either file is written. Any metric input that is absent becomes `Metric.missing`
for that key.
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from pathfinder_ml import ML

from avenir_contracts.catalogue import CatalogueEntry, CatalogueFile
from avenir_contracts.data import REPO_ROOT, SNAPSHOT_DIR
from avenir_contracts.metric import Metric
from avenir_contracts.vocab import CATALOGUE_METRICS

from .curated import CuratedError, load_curated
from .routes import load_routes

DEFAULT_CURATED = REPO_ROOT / "data" / "curated" / "occupations.csv"
DEFAULT_ROUTES = REPO_ROOT / "data" / "curated" / "routes.csv"


def demo_socs() -> set[str]:
    return {o["soc2020"] for o in ML().occupations(demo_only=True)}


def _shortage_missing() -> Metric:
    return Metric.missing(CATALOGUE_METRICS["shortage"], "oid_2025", note="Occupations in Demand file not loaded.")


def build_catalogue(curated: list[CatalogueEntry], oid_csv: Path | None = None, *,
                    generated_at: str | None = None) -> CatalogueFile:
    shortage: dict[str, Metric] = {}
    if oid_csv is not None and Path(oid_csv).exists():
        from avenir_adapters.occupations_in_demand.parse import oid_shortage  # lazy: Task 5
        shortage = oid_shortage(Path(oid_csv))
    entries = []
    for e in curated:
        metrics = {
            "shortage": shortage.get(e.soc2020) or _shortage_missing(),
            "wellbeing": Metric.missing(CATALOGUE_METRICS["wellbeing"], "aps_occupation", granularity="major_group",
                                        note="Wellbeing by job group not loaded."),
            "stress": Metric.missing(CATALOGUE_METRICS["stress"], "hse_stress", granularity="major_group",
                                     note="Work stress by job group not loaded."),
            "ads_now": Metric.missing(CATALOGUE_METRICS["ads_now"], "adzuna",
                                      note="Live ad count added by the API (Jobs by Adzuna)."),
        }
        entries.append(e.model_copy(update={"metrics": metrics}))
    return CatalogueFile(generated_at=generated_at or datetime.now(UTC).isoformat(timespec="seconds"),
                         status="preliminary", entries=entries)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="avenir_etl.build", description="Build snapshots/catalogue.json and routes.json")
    p.add_argument("--curated", type=Path, default=DEFAULT_CURATED)
    p.add_argument("--routes", type=Path, default=DEFAULT_ROUTES)
    p.add_argument("--oid", type=Path, default=None, help="Occupations in Demand file (optional)")
    p.add_argument("--out", type=Path, default=SNAPSHOT_DIR)
    args = p.parse_args(argv)
    socs = demo_socs()
    curated, routes, failed = [], None, False
    try:
        curated = load_curated(args.curated, socs)
    except CuratedError as err:
        print(err)
        failed = True
    except FileNotFoundError:
        print(f"error: curated occupations file not found: {args.curated}")
        failed = True
    try:
        routes = load_routes(args.routes, socs)
    except CuratedError as err:
        print(err)
        failed = True
    except FileNotFoundError:
        print(f"error: routes file not found: {args.routes}")
        failed = True
    if failed or routes is None:
        return 1
    uncovered = sorted(socs - {e.soc2020 for e in curated})
    if uncovered:
        print(f"warning: curated CSV covers {len(curated)} of {len(socs)} demo SOCs; "
              f"missing: {', '.join(uncovered)}", file=sys.stderr)
    if args.oid is not None and not Path(args.oid).exists():
        print(f"warning: --oid file not found ({args.oid}); shortage will be missing", file=sys.stderr)
    if not routes.routes:
        print("routes.csv has no rows yet; roadmap will show routes as missing", file=sys.stderr)
    cat = build_catalogue(curated, args.oid)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "catalogue.json").write_text(cat.model_dump_json(indent=1), encoding="utf-8")
    (args.out / "routes.json").write_text(routes.model_dump_json(indent=1), encoding="utf-8")
    print(f"wrote {len(cat.entries)} catalogue entries to {args.out / 'catalogue.json'}")
    print(f"wrote {len(routes.routes)} routes to {args.out / 'routes.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
