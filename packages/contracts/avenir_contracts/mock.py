"""Generate clearly fake snapshots so every slice can build before real data lands.

    python -m avenir_contracts.mock            # writes snapshots/mock/*.json

Every number has source "MOCK" and every SOC code is 00NN (SOC 2020 has no major group 0),
so mock data can never be mistaken for real data. tests/test_freeze.py fails at freeze
if the API would still serve any of it.
"""
from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from .metric import MOCK_SOURCE, Metric
from .models import (
    METRIC_UNITS,
    BacktestOccupation,
    BacktestTierResult,
    BacktestYear,
    Career,
    CareerMetrics,
    HedgeCandidate,
    Route,
)
from .snapshots import DEFAULT_DIR, BacktestFile, CareersFile, HedgeFile, RoutesFile

# title, aliases, interest tags, entry subjects (team to confirm real ones in data/curated)
OCCUPATIONS: list[tuple[str, list[str], list[str], list[str]]] = [
    ("Software developer", ["programmer", "software engineer", "coder"], ["computers", "maths"], ["maths", "computing"]),
    ("Data analyst", ["data scientist"], ["maths", "computers", "business"], ["maths"]),
    ("UX designer", ["ui designer", "user experience designer"], ["design", "computers", "people"], ["art"]),
    ("Architect", ["architecture"], ["art", "design", "building", "maths"], ["maths", "art", "physics"]),
    ("Architectural technologist", [], ["design", "building", "computers"], ["maths", "graphic_communication"]),
    ("Civil engineer", [], ["building", "maths", "outdoors"], ["maths", "physics"]),
    ("Structural engineer", [], ["building", "maths", "science"], ["maths", "physics"]),
    ("Electrical power networks engineer", ["power engineer"], ["fixing_things", "science", "maths"], ["maths", "physics"]),
    ("Building controls (BEMS) engineer", ["bems engineer"], ["fixing_things", "computers", "building"], ["maths", "physics"]),
    ("Quantity surveyor", [], ["building", "maths", "business"], ["maths"]),
    ("Geospatial surveyor", ["land surveyor"], ["outdoors", "maths", "computers"], ["maths", "geography"]),
    ("Actuary", [], ["maths", "business"], ["maths"]),
    ("Accountant", [], ["maths", "business"], ["maths"]),
    ("Graphic designer", [], ["art", "design"], ["art", "graphic_communication"]),
    ("Animator / VFX artist", ["animator", "vfx artist"], ["art", "computers", "design"], ["art"]),
    ("Product designer", ["industrial designer"], ["design", "art", "fixing_things"], ["art", "design_technology"]),
    ("Maths teacher", ["teacher"], ["maths", "people"], ["maths"]),
    ("Radiographer", [], ["health", "science", "people"], ["biology", "physics"]),
    ("Electrician", [], ["fixing_things", "building"], ["maths"]),
    ("Marketing analyst", [], ["business", "maths", "writing"], ["maths", "english"]),
]

RANGES: dict[str, tuple[float, float]] = {
    "pay_now": (24000, 62000), "pay_early": (20000, 40000), "pay_ceiling": (30000, 85000),
    "pay_growth_10y": (-8, 18), "pay_spread": (1.6, 3.4), "demand_trend": (-3, 5),
    "shortage": (0, 1), "ads_now": (40, 4000), "exposure_ilo": (0.1, 0.65),
    "exposure_inhouse": (0.1, 0.7), "wellbeing": (6.8, 7.8), "stress": (900, 2600),
}
GROUP_LEVEL = {"wellbeing", "stress"}


def mock_soc(i: int) -> str:
    return f"{i + 1:04d}"  # 0001..0020


def _metric(rng: random.Random, name: str) -> Metric:
    lo, hi = RANGES[name]
    if rng.random() < 0.06 and name not in {"pay_now"}:  # a few gaps on purpose: UI must show "missing"
        return Metric.missing(METRIC_UNITS[name], MOCK_SOURCE)
    v = float(rng.random() < 0.3) if name == "shortage" else round(rng.uniform(lo, hi), 2)
    spread = (hi - lo) * 0.08
    return Metric(
        value=v, low=None if name == "shortage" else round(v - spread, 2),
        high=None if name == "shortage" else round(v + spread, 2),
        unit=METRIC_UNITS[name], source=MOCK_SOURCE, year="2025", region="UK",
        granularity="group" if name in GROUP_LEVEL else "occupation",
        n=rng.randint(15, 900), confidence=rng.choice(["high", "medium", "low"]),
    )


def build(seed: int = 7) -> dict[str, object]:
    rng = random.Random(seed)
    today = date.today().isoformat()
    careers = [
        Career(
            soc2020=mock_soc(i), title=t, aliases=a, isco08=[], esco_id=None,
            interest_tags=tags, entry_subjects=subj,  # type: ignore[arg-type]
            metrics=CareerMetrics(**{k: _metric(rng, k) for k in METRIC_UNITS}),
        )
        for i, (t, a, tags, subj) in enumerate(OCCUPATIONS)
    ]
    socs = [c.soc2020 for c in careers]
    related = {
        s: [HedgeCandidate(soc2020=o, shared_skills=[f"mock skill {k}" for k in range(3)],
                           skill_overlap=round(rng.uniform(0.2, 0.8), 2))
            for o in rng.sample([x for x in socs if x != s], 3)]
        for s in socs
    }
    years = []
    for y in range(2010, 2020):
        order = rng.sample(careers, len(careers))
        tiers = []
        for name, chunk in zip(("top", "middle", "bottom"), (order[:7], order[7:14], order[14:]), strict=True):
            occ = [BacktestOccupation(soc=c.soc2020, title=c.title, rating=round(rng.uniform(0, 100), 1),
                                      pay_growth_5y=round(rng.uniform(-5, 20), 1),
                                      employment_growth_5y=round(rng.uniform(-15, 25), 1),
                                      confidence=rng.choice(["high", "medium", "low"])) for c in chunk]
            pays = sorted(o.pay_growth_5y for o in occ if o.pay_growth_5y is not None)
            tiers.append(BacktestTierResult(
                tier=name, occupations=occ, median_pay_growth_5y=pays[len(pays) // 2],
                share_employment_decline=round(sum((o.employment_growth_5y or 0) < 0 for o in occ) / len(occ), 2),
                worst_case=min(occ, key=lambda o: o.pay_growth_5y or 0)))
        years.append(BacktestYear(year=y, tiers=tiers, caveats=["MOCK DATA: not a real backtest."],
                                  source=MOCK_SOURCE))
    routes = [
        Route(soc2020=c.soc2020, nation="scotland", kind=k, name=f"MOCK {k.replace('_', ' ')} for {c.title}",
              provider="MOCK", entry_requirements="MOCK: e.g. 4 Highers including Maths",
              url="https://example.org/mock", source=MOCK_SOURCE, verified_by="MOCK")
        for c in careers for k in ("degree", "graduate_apprenticeship")
    ]
    return {
        "careers": CareersFile(generated_at=today, careers=careers),
        "hedge": HedgeFile(generated_at=today, source=MOCK_SOURCE, related=related),
        "backtest": BacktestFile(generated_at=today, years=years),
        "routes": RoutesFile(generated_at=today, routes=routes),
    }


def write(out: Path | None = None) -> Path:
    out = Path(out or DEFAULT_DIR / "mock")
    out.mkdir(parents=True, exist_ok=True)
    for name, obj in build().items():
        (out / f"{name}.json").write_text(obj.model_dump_json(indent=1), encoding="utf-8")  # type: ignore[attr-defined]
    return out


if __name__ == "__main__":
    print(f"wrote mock snapshots to {write()}")
