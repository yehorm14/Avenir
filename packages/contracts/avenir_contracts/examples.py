"""Generate the frontend handoff pack: JSON Schemas and real example payloads.

    python -m avenir_contracts.examples [--out DIR]     (default: <repo>/docs/frontend)

Everything comes from the models in this package and from `load_data()`; nothing is hand-written.
The output is deterministic (sorted keys, no clock), so committed files only change when code or data does.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pathfinder_ml import FLAG_TEXT, MUST_MENTION
from pydantic import BaseModel

from . import envelope, models
from .data import REPO_ROOT, AvenirData, load_data
from .envelope import Envelope, ErrorBody, ErrorCode, Meta
from .metric import Metric

SCHEMA_MODELS: tuple[str, ...] = (
    "Metric", "Career", "CareerRef", "Tag", "TagMatch", "ProfileIn", "ProfileOut", "RecommendationRequest",
    "RecommendationOut", "Pick", "Components", "Hedge", "HedgeCandidate", "Route", "Roadmap",
    "HistoryPoint", "Crisis", "BacktestOut", "SourceStatus", "Meta", "ErrorBody", "Explanation",
)
DEFAULT_OUT = REPO_ROOT / "docs" / "frontend"
EXAMPLE_SOC = "2451"
MANIFEST = "manifest.json"  # lists the files this module generated, so a rerun can remove stale ones


def _model(name: str) -> type[BaseModel]:
    if name == "Metric":
        return Metric
    return getattr(models, name, None) or getattr(envelope, name)


def _plain(obj: Any) -> Any:
    """Models to JSON-mode dicts, recursively through lists and dicts."""
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_plain(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def _dump(obj: Any) -> str:
    return json.dumps(_plain(obj), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _as_of(data: AvenirData) -> str:
    """Deterministic envelope timestamp taken from the data: the catalogue's, else any source's."""
    by_name = {s.name: s.as_of for s in data.statuses}
    for name in ("catalogue", "routes"):
        if by_name.get(name):
            return by_name[name]
    return next((s.as_of for s in data.statuses if s.as_of), "unknown")


def build(data: AvenirData | None = None) -> dict[str, str]:
    """Return {relative path: file text} for the whole pack."""
    data = data or load_data()
    files: dict[str, str] = {}

    for name in SCHEMA_MODELS:
        files[f"schemas/{name}.json"] = _dump(_model(name).model_json_schema())

    ex: dict[str, Any] = {}
    soc = EXAMPLE_SOC if EXAMPLE_SOC in data.careers else next(iter(sorted(data.careers)), None)
    ex["careers"] = [{"soc2020": c.soc2020, "title": c.title} for _, c in sorted(data.careers.items())]
    ex["tags"] = data.tags
    ex["crises"] = data.crises
    ex["backtest_years"] = sorted(data.backtest)
    ex["sources"] = {"statuses": data.statuses, "registry": data.sources}
    ex["flags"] = {k: {"text": FLAG_TEXT[k], "must_mention": k in MUST_MENTION} for k in sorted(FLAG_TEXT)}
    ex["error_404"] = Envelope[None](
        ok=False, data=None,
        error=ErrorBody(code=ErrorCode.NOT_FOUND, message="Unknown SOC code 9999"),
        meta=Meta(as_of=_as_of(data), request_id="example", sources=data.statuses))
    if soc:
        career = data.careers[soc]
        ex[f"career_{soc}"] = career
        ex[f"history_{soc}"] = data.history.get(soc, [])
        ex[f"hedge_candidates_{soc}"] = data.hedges.get(soc, [])
        ex[f"routes_{soc}"] = data.routes.get(soc, [])
        ex[f"envelope_career_{soc}"] = Envelope[type(career)](
            ok=True, data=career, error=None,
            meta=Meta(as_of=_as_of(data), request_id="example", sources=data.statuses))
    if data.backtest:
        year = min(data.backtest)
        ex[f"backtest_{year}"] = models.BacktestOut(
            window=data.backtest[year], caveats=data.backtest_caveats, status=data.backtest_status)

    for name, obj in ex.items():
        files[f"examples/{name}.json"] = _dump(obj)
    files[MANIFEST] = _dump({"files": sorted(files)})
    return files


def write(out: str | Path = DEFAULT_OUT, data: AvenirData | None = None) -> list[Path]:
    """Write the pack under `out`. Files a previous run listed in the manifest but this run does not make are
    deleted; nothing else in `out` is touched."""
    out = Path(out)
    files = build(data)
    old_manifest = out / MANIFEST
    if old_manifest.is_file():
        for rel in json.loads(old_manifest.read_text(encoding="utf-8")).get("files", []):
            if rel not in files and (out / rel).is_file():
                (out / rel).unlink()
    paths = []
    for rel, text in sorted(files.items()):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        paths.append(p)
    return paths


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory (default: docs/frontend)")
    args = ap.parse_args(argv)
    paths = write(args.out)
    print(f"wrote {len(paths)} files under {args.out}")


if __name__ == "__main__":
    main()
