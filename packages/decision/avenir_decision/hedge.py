"""Hedge career: a related, safer role for the top pick. Pure function, no I/O."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from avenir_contracts import Career, Components, Hedge, HedgeCandidate


def choose_hedge(
    top: Career,
    candidates: Sequence[HedgeCandidate],
    components: Mapping[str, Components],
    careers: Mapping[str, Career],
) -> Hedge | None:
    """Most similar candidate that is demonstrably safer than the top pick.

    Qualifies: in `careers`, scored, and risk.score strictly below the top pick's (a missing
    risk cannot be shown to be safer, so it does not qualify). Order: highest similarity,
    then lower risk, then higher fit, then lower SOC. None if nothing qualifies.
    """
    top_comp = components.get(top.soc2020)
    top_risk = None if top_comp is None else top_comp.risk.score
    if top_risk is None:
        return None

    best: tuple[tuple[float, float, float, str], HedgeCandidate, float] | None = None
    for cand in candidates:
        comp = components.get(cand.soc2020)
        if cand.soc2020 not in careers or comp is None:
            continue
        risk = comp.risk.score
        if risk is None or risk >= top_risk:
            continue
        fit = comp.fit.score
        key = (-cand.similarity, risk, -(fit if fit is not None else float("-inf")), cand.soc2020)
        if best is None or key < best[0]:
            best = (key, cand, risk)
    if best is None:
        return None
    _, cand, risk = best
    return Hedge(
        for_soc=top.soc2020,
        career=careers[cand.soc2020],
        similarity=cand.similarity,
        shared_skills=list(cand.shared_skills),
        why=cand.why,
        risk_delta=round(risk - top_risk, 1),
        status=str(cand.status),
    )
