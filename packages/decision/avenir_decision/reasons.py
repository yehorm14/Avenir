"""Reasons and notices: template sentences built only from numbers in the data. Pure, no I/O."""
from __future__ import annotations

from collections.abc import Sequence

from pathfinder_ml import FLAG_TEXT, MUST_MENTION

from avenir_contracts import Career, Components, Metric
from avenir_contracts.vocab import PickTier

SOURCE_LABELS = {"ons_ashe_t14": "ONS ASHE", "ilo_wp140": "ILO", "MOCK": "sample data"}

_TIER_LINE = {
    "ambitious": "Highest expected return among careers that fit you.",
    "safe": "Lowest overall risk among careers that fit you.",
    "balanced": "Best return for the risk among careers that fit you.",
}


def _usable(career: Career, key: str) -> Metric | None:
    m = career.metrics.get(key)
    return m if m is not None and m.value is not None else None


def _year(m: Metric) -> str | None:
    return m.as_of or None


def pick_reasons(tier: PickTier, career: Career, comps: Components) -> list[str]:
    """Tier line, then pay, jobs trend, exposure; a sentence is skipped if its metric is missing."""
    out = [_TIER_LINE[tier]]

    pay = _usable(career, "pay_median")
    if pay is not None:
        label = SOURCE_LABELS.get(pay.source, pay.source)
        year = _year(pay)
        src = f"{label}, {year}" if year else label
        out.append(f"Median pay £{pay.value:,.0f} a year for full-time employees ({src}).")

    trend = _usable(career, "demand_trend")
    if trend is not None:
        year = _year(trend)
        tail = f" ({year})" if year else ""
        out.append(f"Jobs trend {trend.value * 100:+.1f}% a year{tail}.")

    exp = _usable(career, "exposure")
    if exp is not None:
        out.append(
            f"GenAI exposure (research estimate): {exp.value:.2f} on a 0 to 1 scale, {exp.confidence} confidence."
        )
    return out


def notices_for(careers: Sequence[Career]) -> list[str]:
    """FLAG_TEXT for every MUST_MENTION flag on any metric, unique, first-seen order."""
    seen: list[str] = []
    for career in careers:
        for metric in career.metrics.values():
            for flag in metric.flags:
                if flag in MUST_MENTION and flag in FLAG_TEXT and FLAG_TEXT[flag] not in seen:
                    seen.append(FLAG_TEXT[flag])
    return seen
