"""Confidence rules for scores built from metrics.

Pure functions: no I/O, no network, no LLM. A missing metric (None, or value None) is never
filled in; it only lowers the confidence of the component that depends on it.
"""
from __future__ import annotations

from collections.abc import Sequence

from avenir_contracts import Metric
from avenir_contracts.vocab import CONFIDENCE_ORDER, Confidence

_LEVELS: tuple[Confidence, ...] = tuple(sorted(CONFIDENCE_ORDER, key=CONFIDENCE_ORDER.__getitem__))


def lowest(*levels: Confidence) -> Confidence:
    """The weakest of the given confidence levels."""
    return min(levels, key=CONFIDENCE_ORDER.__getitem__)


def downgrade(level: Confidence) -> Confidence:
    """One step down: high to medium, medium to low, low stays low."""
    index = CONFIDENCE_ORDER[level]
    return _LEVELS[max(index - 1, 0)]


def component_confidence(metrics: Sequence[Metric | None]) -> Confidence:
    """Confidence of a component built from these metrics.

    Takes the lowest confidence among the present metrics, then downgrades it once if any
    input is missing. If nothing is present, the result is "low".
    """
    present = [m for m in metrics if m is not None and m.value is not None]
    if not present:
        return "low"
    level = lowest(*(m.confidence for m in present))
    if len(present) < len(metrics):
        level = downgrade(level)
    return level
