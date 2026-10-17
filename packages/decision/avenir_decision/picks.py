"""Ambitious, safe and balanced picks.

Pure functions: no I/O, no network, no LLM. Eligible careers are not excluded (the first idea),
have a return and a risk score, and clear the fit gate: max(FIT_FLOOR, FIT_RELATIVE * best_fit),
where best_fit is the highest fit among non-excluded careers. Picks are distinct, in order:
ambitious = max return; safe = min risk of the rest; balanced = max (return - 50) / max(risk, 10)
of the rest. Ties: higher fit, then lower SOC string.
"""
from __future__ import annotations

from collections.abc import Callable, Collection, Mapping

from avenir_contracts import Components
from avenir_contracts.vocab import PickTier

FIT_RELATIVE = 0.5
FIT_FLOOR = 5.0
_RISK_FLOOR = 10.0


def eligible(components: Mapping[str, Components], exclude: Collection[str] = ()) -> list[str]:
    """SOCs that can be picked, sorted by SOC."""
    pool = {s: c for s, c in components.items() if s not in exclude}
    fits = [c.fit.score for c in pool.values() if c.fit.score is not None]
    if not fits:
        return []
    gate = max(FIT_FLOOR, FIT_RELATIVE * max(fits))
    return sorted(
        s
        for s, c in pool.items()
        if c.expected_return.score is not None
        and c.risk.score is not None
        and c.fit.score is not None
        and c.fit.score >= gate
    )


def choose_picks(
    components: Mapping[str, Components], exclude: Collection[str] = ()
) -> list[tuple[PickTier, str]]:
    remaining = eligible(components, exclude)

    def best(metric: Callable[[Components], float]) -> str:
        # maximise metric; ties: higher fit, then lower SOC
        return min(remaining, key=lambda s: (-metric(components[s]), -(components[s].fit.score or 0.0), s))

    rules: list[tuple[PickTier, Callable[[Components], float]]] = [
        ("ambitious", lambda c: c.expected_return.score or 0.0),
        ("safe", lambda c: -(c.risk.score or 0.0)),
        ("balanced", lambda c: ((c.expected_return.score or 0.0) - 50) / max(c.risk.score or 0.0, _RISK_FLOOR)),
    ]
    picks: list[tuple[PickTier, str]] = []
    for tier, metric in rules:
        if not remaining:
            break
        soc = best(metric)
        picks.append((tier, soc))
        remaining.remove(soc)
    return picks
