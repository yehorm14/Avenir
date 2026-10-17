"""Resolve the student's free-text first career idea to a career. Pure, deterministic.

Steps on text.strip().casefold(), over title, official_title and aliases: exact SOC code, exact
name, name contains text or text contains name (shortest name wins), then fuzzy matching
(SequenceMatcher ratio >= 0.75, best wins). A step that finds two or more distinct careers
equally good is ambiguous: nothing is guessed, resolve_first_idea returns None and
first_idea_candidates returns the tied careers sorted by SOC.
"""
from __future__ import annotations

from collections.abc import Sequence
from difflib import SequenceMatcher

from avenir_contracts import Career

_CUTOFF = 0.75


def _names(career: Career) -> set[str]:
    return {n.strip().casefold() for n in (career.title, career.official_title, *career.aliases) if n.strip()}


def _best(careers: Sequence[Career], score) -> list[Career]:
    """Careers sharing the best (lowest) score; each career scored by its best name. Sorted by SOC."""
    per_career: dict[str, tuple[float, Career]] = {}
    for c in careers:
        scores = [s for n in _names(c) if (s := score(n)) is not None]
        if scores:
            per_career[c.soc2020] = (min(scores), c)
    if not per_career:
        return []
    top = min(s for s, _ in per_career.values())
    return sorted((c for s, c in per_career.values() if s == top), key=lambda c: c.soc2020)


def _match(text: str, careers: Sequence[Career]) -> list[Career]:
    """Winners of the first step that matches anything: one career if unique, else the tie."""
    q = text.strip().casefold()
    if not q:
        return []
    by_soc = [c for c in careers if c.soc2020 == q]
    if by_soc:
        return by_soc[:1]
    steps = (
        lambda n: 0.0 if n == q else None,
        lambda n: float(len(n)) if q in n or n in q else None,
        # negated so that the best ratio is the lowest score
        lambda n: -r if (r := SequenceMatcher(None, q, n).ratio()) >= _CUTOFF else None,
    )
    for step in steps:
        found = _best(careers, step)
        if found:
            return found
    return []


def resolve_first_idea(text: str, careers: Sequence[Career]) -> Career | None:
    found = _match(text, careers)
    return found[0] if len(found) == 1 else None


def first_idea_candidates(text: str, careers: Sequence[Career]) -> list[Career]:
    """Tied careers when the text is ambiguous; [] when it resolves uniquely or matches nothing."""
    found = _match(text, careers)
    return found if len(found) > 1 else []
