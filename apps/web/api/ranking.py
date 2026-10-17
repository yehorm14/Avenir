"""Deterministic comparison of committed evidence; no I/O or language model."""

from __future__ import annotations

from math import isfinite


def _value(career: dict, key: str) -> float | None:
    metric = career.get("metrics", {}).get(key, {})
    value = metric.get("value")
    if metric.get("status") == "pending" or "suppressed" in metric.get("flags", []):
        return None
    return float(value) if isinstance(value, (int, float)) and isfinite(value) else None


def _percentiles(values: dict[str, float | None]) -> dict[str, float | None]:
    present = sorted(v for v in values.values() if v is not None)
    if len(present) <= 1:
        return {soc: 50.0 if value is not None else None for soc, value in values.items()}
    return {
        soc: None
        if value is None
        else round(100 * (present.index(value) + (present.count(value) - 1) / 2) / (len(present) - 1), 2)
        for soc, value in values.items()
    }


def rank_careers(
    careers: list[dict], tags: list[str], weights: dict[str, float], affinity: dict[str, dict[str, float]]
) -> list[dict]:
    """Return all careers with 0–100 component scores and a weighted score.

    Pay and need are percentile ranks across available career values. Need uses
    historical 2021–2025 demand, not a forecast. Missing inputs stay null and are
    omitted from the weighted mean. The mean affinity is the original mock fit
    method; no interests means a neutral 50. Zero weights use equal importance.
    """
    selected = sorted(set(tags))
    unknown = [tag for tag in selected if tag not in affinity]
    if unknown:
        raise ValueError("Unknown interest tag(s): " + ", ".join(unknown))
    w = {key: float(weights.get(key, 0)) for key in ("pay", "interest", "need")}
    if any(not isfinite(value) or value < 0 for value in w.values()):
        raise ValueError("Weights must be finite and non-negative")
    if not any(w.values()):
        w = dict.fromkeys(w, 1.0)
    pay = _percentiles({c["soc"]: _value(c, "pay_median") for c in careers})
    need = _percentiles({c["soc"]: _value(c, "demand_trend") for c in careers})
    results = []
    for career in careers:
        soc = career["soc"]
        fit = round(100 * sum(affinity[t].get(soc, 0.0) for t in selected) / len(selected), 2) if selected else 50.0
        components = {"pay": pay[soc], "interest": fit, "need": need[soc]}
        present = [(w[key], value) for key, value in components.items() if value is not None and w[key] > 0]
        score = (
            round(sum(weight * value for weight, value in present) / sum(weight for weight, _ in present), 2) if present else None
        )
        matched = [tag.replace("_", " ") for tag in selected if affinity[tag].get(soc, 0) >= 0.5]
        reasons = (
            ["Connected to your interest in " + ", ".join(matched[:3]) + "."]
            if matched
            else ["Compare the work itself with your interests; this is an exploratory suggestion."]
        )
        if pay[soc] is not None:
            reasons.append("Pay compares the published median with other careers in this collection.")
        if need[soc] is not None:
            reasons.append("Need reflects the observed 2021–2025 employment trend; it is not a prediction.")
        results.append(
            {
                **career,
                "score": score,
                "fit": fit,
                "pay_score": pay[soc],
                "need_score": need[soc],
                "reasons": reasons,
                "fit_status": "mock",
            }
        )
    return sorted(results, key=lambda c: (c["score"] is None, -(c["score"] or 0), c["soc"]))
