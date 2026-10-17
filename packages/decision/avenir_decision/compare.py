"""Comparison of a pick against the student's first idea. Pure function, no I/O."""
from __future__ import annotations

from avenir_contracts import Components

COMPONENT_NAMES = ("fit", "expected_return", "market_risk", "disruption_risk", "risk")


def vs_first_idea(pick: Components, first: Components | None) -> dict[str, float | None]:
    """pick minus first idea per component, 1 decimal; None where either side is None."""
    out: dict[str, float | None] = {}
    for name in COMPONENT_NAMES:
        a = getattr(pick, name).score
        b = None if first is None else getattr(first, name).score
        out[name] = None if a is None or b is None else round(a - b, 1)
    return out
