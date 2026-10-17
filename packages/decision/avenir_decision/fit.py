"""Fit of a profile to each career, and the head start from qualifications held.

Pure functions: no I/O, no network, no LLM.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from avenir_contracts import Career, ComponentScore, ProfileIn

_FULL = {"higher", "advanced_higher", "a_level"}
FULL_LEVELS = _FULL  # shared with roadmap: levels that count as held at Higher or above
_HALF = {"national5", "gcse"}


def head_start(profile: ProfileIn, career: Career) -> float:
    """Share (0..1) of the career's entry subjects held, using the best level per subject.

    Higher, advanced higher and A level count 1.0; National 5 and GCSE count 0.5.
    No entry subjects gives 1.0.
    """
    if not career.entry_subjects:
        return 1.0
    best: dict[str, float] = {}
    for q in profile.qualifications:
        credit = 1.0 if q.level in _FULL else 0.5
        best[q.subject] = max(best.get(q.subject, 0.0), credit)
    return sum(best.get(s, 0.0) for s in career.entry_subjects) / len(career.entry_subjects)


def fit_scores(
    profile: ProfileIn,
    careers: Sequence[Career],
    affinity: Mapping[str, Mapping[str, float]],
) -> dict[str, ComponentScore]:
    """Fit (0-100) per career soc2020: mean interest affinity, scaled by head start.

    No interests gives a neutral 50.0 with low confidence. An unknown tag raises ValueError.
    """
    if not profile.interests:
        return {c.soc2020: ComponentScore(score=50.0, confidence="low") for c in careers}
    unknown = [t for t in profile.interests if t not in affinity]
    if unknown:
        raise ValueError(f"unknown interest tag(s): {', '.join(unknown)}")
    confidence = "high" if len(profile.interests) >= 3 else "medium"
    out: dict[str, ComponentScore] = {}
    for c in careers:
        base = sum(affinity[t].get(c.soc2020, 0.0) for t in profile.interests) / len(profile.interests)
        score = round(100 * base * (0.8 + 0.2 * head_start(profile, c)), 1)
        out[c.soc2020] = ComponentScore(score=score, confidence=confidence)
    return out
