"""Machine-readable compatibility evidence, run in the temporary tree's environment."""

from __future__ import annotations

import json
from pathlib import Path


def exception_shape(exc):
    # Pydantic exception text includes input values; report only field locations/types.
    result = {"type": type(exc).__name__}
    if hasattr(exc, "errors"):
        result["fields"] = [{"location": list(e["loc"]), "type": e["type"]} for e in exc.errors(include_input=False)]
    return result


def probe():
    root = Path.cwd().resolve()
    result = {"sizes": {str(p.relative_to(root)).replace("\\", "/"): p.stat().st_size
                        for p in sorted((root / "snapshots/ml").glob("*.json"))}}
    try:
        import pathfinder_ml
        from pathfinder_ml import ML

        import avenir_contracts
        from avenir_contracts import load_data
        from avenir_contracts.data import join_career
        from avenir_contracts.vocab import ML_METRICS

        result["imports_from_temp_tree"] = all(Path(m.__file__).resolve().is_relative_to(root)
                                               for m in (avenir_contracts, pathfinder_ml))
        ml = ML()
        occupations = ml.occupations()
        result["ml_occupation_count"] = len(occupations)
        result["ml_demo_count"] = len(ml.occupations(demo_only=True))
        result["unknown_metric_keys"] = sorted({key for occ in occupations for key in occ.get("metrics", {})} - set(ML_METRICS))
        flag_loss = []
        checked = 0
        for occ in occupations:
            joined = join_career(occ, None)
            for key, metric in occ.get("metrics", {}).items():
                checked += 1
                if joined.metrics[key].flags != metric.get("flags", []):
                    flag_loss.append(f"{occ['soc2020']}:{key}")
        result["all_occupation_metrics_checked"] = checked
        result["join_metric_flag_losses"] = flag_loss
        data = load_data()
        result["load_data_demo_careers"] = len(data.careers)
        result["first_history_years"] = sorted({points[0].year for points in data.history.values() if points})
        lost = []
        checked = 0
        for occ in ml.occupations(demo_only=True):
            career = data.careers.get(occ["soc2020"])
            for key, metric in occ.get("metrics", {}).items():
                checked += 1
                if career is None or key not in career.metrics or career.metrics[key].flags != metric.get("flags", []):
                    lost.append(f"{occ['soc2020']}:{key}")
        result["loaded_demo_metrics_checked"] = checked
        result["load_data_metric_flag_losses"] = lost
        result["load_data_ok"] = True
    except Exception as exc:
        result["load_data_ok"] = False
        result["error"] = exception_shape(exc)
    return result


if __name__ == "__main__":
    print(json.dumps(probe()))
