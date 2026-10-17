"""One loader for everything the API serves: ML artefacts (via pathfinder_ml) + catalogue + routes.

The API calls `load_data()` once at start-up. This is the only file access outside adapters
(AGENTS.md rule 5). Each source reports live/snapshot/mock/missing for the badges.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from pathfinder_ml import ARTEFACTS, ML

from .catalogue import CatalogueEntry, CatalogueFile, RoutesFile
from .envelope import SourceStatus
from .metric import Metric
from .models import (
    BacktestWindow,
    Career,
    Crisis,
    HedgeCandidate,
    HistoryPoint,
    IscoShare,
    Route,
    SourceInfo,
    Tag,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = REPO_ROOT / "snapshots"


@dataclass
class AvenirData:
    careers: dict[str, Career] = field(default_factory=dict)          # demo set, keyed by soc2020
    tags: list[Tag] = field(default_factory=list)
    affinity: dict[str, dict[str, float]] = field(default_factory=dict)  # tag -> soc -> 0..1 (fit.json)
    hedges: dict[str, list[HedgeCandidate]] = field(default_factory=dict)
    routes: dict[str, list[Route]] = field(default_factory=dict)
    history: dict[str, list[HistoryPoint]] = field(default_factory=dict)
    backtest: dict[int, BacktestWindow] = field(default_factory=dict)
    backtest_caveats: list[str] = field(default_factory=list)
    backtest_status: str = "missing"
    crises: list[Crisis] = field(default_factory=list)
    sources: dict[str, SourceInfo] = field(default_factory=dict)
    statuses: list[SourceStatus] = field(default_factory=list)
    ml_mode: str = "missing"  # real | mock | mixed | missing


def _state(file_status: str) -> SourceStatus | dict:
    if file_status in ("final", "preliminary"):
        return {"status": "snapshot", "quality": file_status}
    if file_status == "mock":
        return {"status": "mock"}
    return {"status": "missing"}


def _read_own(name: str, model: type, base: Path) -> tuple[object | None, SourceStatus]:
    for path in (base / f"{name}.json", base / "mock" / f"{name}.json"):
        if path.is_file():
            obj = model.model_validate_json(path.read_text(encoding="utf-8"))
            return obj, SourceStatus(name=name, as_of=obj.generated_at, **_state(obj.status))
    return None, SourceStatus(name=name, status="missing")


def join_career(occ: dict, entry: CatalogueEntry | None) -> Career:
    metrics = {k: Metric.model_validate(v) for k, v in occ.get("metrics", {}).items()}
    if entry:
        metrics.update(entry.metrics)
    return Career(
        soc2020=occ["soc2020"],
        title=entry.title if entry else occ.get("short_title") or occ["title"],
        official_title=occ["title"],
        aliases=(entry.aliases if entry else []) + [a for a in (occ.get("short_title"),) if a],
        description=entry.description if entry else None,
        isco08=[IscoShare.model_validate(i) for i in occ.get("isco08", [])],
        entry_subjects=entry.entry_subjects if entry else [],
        metrics=metrics,
    )


def load_data(ml_dir: str | Path | None = None, snapshot_dir: str | Path | None = None) -> AvenirData:
    base = Path(snapshot_dir or os.environ.get("AVENIR_SNAPSHOT_DIR") or SNAPSHOT_DIR)
    ml = ML(data_dir=ml_dir) if ml_dir else ML()
    d = AvenirData()

    st = ml.status()
    d.ml_mode = st["mode"]
    for name in ARTEFACTS:
        d.statuses.append(SourceStatus(name=f"ml_{name}", **_state(st["artefacts"][name]["status"])))

    cat, cat_st = _read_own("catalogue", CatalogueFile, base)
    routes, routes_st = _read_own("routes", RoutesFile, base)
    d.statuses += [cat_st, routes_st]
    entries = {e.soc2020: e for e in cat.entries} if cat else {}

    try:
        occs = ml.occupations(demo_only=True)
    except FileNotFoundError:
        occs = []
    for occ in occs:
        c = join_career(occ, entries.get(occ["soc2020"]))
        d.careers[c.soc2020] = c
        d.hedges[c.soc2020] = [HedgeCandidate.model_validate(h) for h in ml.hedges(c.soc2020, k=5)]
        d.history[c.soc2020] = [HistoryPoint.model_validate(p) for p in ml.history(c.soc2020)]
    if routes:
        for r in routes.routes:
            d.routes.setdefault(r.soc2020, []).append(r)

    try:
        d.tags = [Tag.model_validate(t) for t in ml.tags()]
        d.affinity = ml._load("fit")["affinity"]  # TODO(arsenii): public accessor
    except FileNotFoundError:
        pass
    try:
        bt = ml._load("backtest")  # TODO(arsenii): public backtest_years(); backtest(y) gives one window
        d.backtest = {w["base_year"]: BacktestWindow.model_validate(w) for w in bt["windows"]}
        d.backtest_caveats = ml.backtest_caveats()
        d.backtest_status = bt.get("status", "unknown")
    except FileNotFoundError:
        pass
    for loader, target in ((ml.crises, "crises"), (ml.sources, "sources")):
        try:
            raw = loader()
        except FileNotFoundError:
            continue
        if target == "crises":
            d.crises = [Crisis.model_validate(c) for c in raw]
        else:
            d.sources = {k: SourceInfo.model_validate(v) for k, v in raw.items()}
    return d
