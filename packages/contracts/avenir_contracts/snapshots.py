"""Snapshot file formats and the one loader the API uses at start-up.

Files live in snapshots/ (real, written by ETL and ML) with a fallback to snapshots/mock/
(written by `python -m avenir_contracts.mock`). Each file reports its state:
real -> "snapshot", mock fallback -> "mock", neither -> "missing".
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .envelope import SourceStatus
from .metric import Metric
from .models import BacktestYear, Career, HedgeCandidate, Route

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIR = REPO_ROOT / "snapshots"


class CareersFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    careers: list[Career]


class HedgeFile(BaseModel):
    """M3 output: up to three related roles per occupation, best first."""
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    source: str
    related: dict[str, list[HedgeCandidate]]


class BacktestFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    years: list[BacktestYear]


class RoutesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    routes: list[Route]


class MetricFile(BaseModel):
    """One metric for many occupations. Format for ML artefacts demand.json (M4 -> demand_trend)
    and exposure.json (M2 -> exposure_inhouse); ETL merges them into careers.json."""
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    source: str
    metric: str
    values: dict[str, Metric]  # SOC 2020 code -> Metric


FILES: dict[str, type[BaseModel]] = {
    "careers": CareersFile,
    "hedge": HedgeFile,
    "backtest": BacktestFile,
    "routes": RoutesFile,
}


@dataclass
class Snapshots:
    careers: dict[str, Career] = field(default_factory=dict)
    hedges: dict[str, list[HedgeCandidate]] = field(default_factory=dict)
    backtest: dict[int, BacktestYear] = field(default_factory=dict)
    routes: dict[str, list[Route]] = field(default_factory=dict)
    statuses: list[SourceStatus] = field(default_factory=list)


def _read(name: str, base: Path) -> tuple[BaseModel | None, SourceStatus]:
    model = FILES[name]
    for path, state in ((base / f"{name}.json", "snapshot"), (base / "mock" / f"{name}.json", "mock")):
        if path.exists():
            obj = model.model_validate_json(path.read_text(encoding="utf-8"))
            return obj, SourceStatus(name=name, status=state, as_of=getattr(obj, "generated_at", None))
    return None, SourceStatus(name=name, status="missing")


def load_snapshots(base: Path | None = None) -> Snapshots:
    base = Path(base or os.environ.get("AVENIR_SNAPSHOT_DIR") or DEFAULT_DIR)
    snap = Snapshots()
    careers, st = _read("careers", base)
    snap.statuses.append(st)
    if careers:
        snap.careers = {c.soc2020: c for c in careers.careers}
    hedge, st = _read("hedge", base)
    snap.statuses.append(st)
    if hedge:
        snap.hedges = dict(hedge.related)
    bt, st = _read("backtest", base)
    snap.statuses.append(st)
    if bt:
        snap.backtest = {y.year: y for y in bt.years}
    routes, st = _read("routes", base)
    snap.statuses.append(st)
    if routes:
        for r in routes.routes:
            snap.routes.setdefault(r.soc2020, []).append(r)
    return snap
