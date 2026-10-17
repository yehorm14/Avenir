"""Build snapshots/catalogue.json from the curated CSV plus the data we can load.

    python -m avenir_etl.build [--curated PATH] [--oid PATH] [--out DIR]

Any input that is absent becomes `Metric.missing` for that key (AGENTS.md rule 3).
Routes come from a separate step.
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

DEFAULT_CURATED = REPO_ROOT / "data" / "curated" / "occupations.csv"


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
    p = argparse.ArgumentParser(prog="avenir_etl.build", description="Build snapshots/catalogue.json")
    p.add_argument("--curated", type=Path, default=DEFAULT_CURATED)
    p.add_argument("--oid", type=Path, default=None, help="Occupations in Demand file (optional)")
    p.add_argument("--out", type=Path, default=SNAPSHOT_DIR)
    args = p.parse_args(argv)
    try:
        curated = load_curated(args.curated, demo_socs())
    except CuratedError as err:
        print(err)
        return 1
    cat = build_catalogue(curated, args.oid)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "catalogue.json").write_text(cat.model_dump_json(indent=1), encoding="utf-8")
    print(f"wrote {len(cat.entries)} catalogue entries to {args.out / 'catalogue.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
