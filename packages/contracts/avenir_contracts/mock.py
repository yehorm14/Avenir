"""Mock catalogue and routes for the 20 demo occupations, until Yehor's ETL lands.

    python -m avenir_contracts.mock     # writes snapshots/mock/catalogue.json and routes.json

ML artefacts have their own mocks in snapshots/ml/mock/ (Arsenii). Everything here has
status "mock", so the UI shows "sample data" and the freeze test fails if it is still served.
"""
from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path

from pathfinder_ml import ML

from .catalogue import CatalogueEntry, CatalogueFile, RoutesFile
from .data import SNAPSHOT_DIR
from .metric import MOCK_SOURCE, Metric
from .models import Route
from .vocab import CATALOGUE_METRICS

# soc2020 -> (aliases, entry subjects). Team to confirm; the ETL replaces this.
CATALOGUE_HINTS: dict[str, tuple[list[str], list[str]]] = {
    "2134": (["programmer", "software engineer", "coder"], ["maths", "computing"]),
    "3544": (["data scientist"], ["maths"]),
    "2133": (["systems analyst", "business analyst"], ["maths", "computing"]),
    "2135": (["cyber security", "ethical hacker"], ["computing", "maths"]),
    "2141": (["web developer", "ux designer"], ["art", "computing"]),
    "2142": (["graphic designer", "animator", "illustrator"], ["art", "graphic_communication"]),
    "2451": (["architecture"], ["maths", "art", "physics"]),
    "2452": (["town planner", "architectural technologist"], ["maths", "graphic_communication"]),
    "3120": (["cad technician", "draughtsperson"], ["maths", "graphic_communication"]),
    "2121": (["civil engineering"], ["maths", "physics"]),
    "2123": (["power engineer"], ["maths", "physics"]),
    "3113": ([], ["maths", "physics"]),
    "2453": (["qs"], ["maths"]),
    "2454": (["surveyor", "land surveyor"], ["maths", "geography"]),
    "2433": (["actuary", "economist", "statistician"], ["maths"]),
    "2422": (["investment analyst", "financial analyst"], ["maths", "business"]),
    "2421": (["accounting"], ["maths"]),
    "2254": (["radiographer"], ["biology", "physics"]),
    "5241": (["electrician"], ["maths", "physics"]),
    "2313": (["teacher", "maths teacher"], ["maths", "english"]),
}
RANGES = {"shortage": (0, 1), "wellbeing": (6.8, 7.8), "stress": (900, 2600), "ads_now": (40, 4000)}


def _metric(rng: random.Random, key: str) -> Metric:
    lo, hi = RANGES[key]
    v = float(rng.random() < 0.3) if key == "shortage" else round(rng.uniform(lo, hi), 1)
    return Metric(value=v, unit=CATALOGUE_METRICS[key], as_of="2025", source=MOCK_SOURCE,
                  granularity="major_group" if key in ("wellbeing", "stress") else "occupation",
                  confidence="low", flags=["mock"], status="mock", note="Sample data, not a real figure.")


def build(seed: int = 7, ml: ML | None = None) -> tuple[CatalogueFile, RoutesFile]:
    rng = random.Random(seed)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    occs = (ml or ML()).occupations(demo_only=True)
    entries, routes = [], []
    for o in occs:
        aliases, subjects = CATALOGUE_HINTS.get(o["soc2020"], ([], []))
        entries.append(CatalogueEntry(
            soc2020=o["soc2020"], title=o.get("short_title") or o["title"], aliases=aliases,
            description=f"MOCK description of {o.get('short_title') or o['title']}.",
            entry_subjects=subjects,  # type: ignore[arg-type]
            metrics={k: _metric(rng, k) for k in CATALOGUE_METRICS}))
        for kind in ("degree", "graduate_apprenticeship"):
            routes.append(Route(
                soc2020=o["soc2020"], nation="scotland", kind=kind,
                name=f"MOCK {kind.replace('_', ' ')} for {o.get('short_title') or o['title']}",
                provider="MOCK", entry_requirements="MOCK: e.g. 4 Highers including Maths",
                url="https://example.org/mock", source=MOCK_SOURCE, verified_by="MOCK"))
    return (CatalogueFile(generated_at=now, status="mock", entries=entries),
            RoutesFile(generated_at=now, status="mock", routes=routes))


def write(out: Path | None = None) -> Path:
    out = Path(out or SNAPSHOT_DIR / "mock")
    out.mkdir(parents=True, exist_ok=True)
    cat, routes = build()
    (out / "catalogue.json").write_text(cat.model_dump_json(indent=1), encoding="utf-8")
    (out / "routes.json").write_text(routes.model_dump_json(indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"wrote mock catalogue and routes to {write()}")
