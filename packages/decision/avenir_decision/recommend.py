"""The decision engine's single entry point. Pure: no I/O, no network, no LLM in ranking."""
from __future__ import annotations

from collections.abc import Sequence

from avenir_contracts import (
    AvenirData,
    Career,
    Explanation,
    Pick,
    RecommendationOut,
    RecommendationRequest,
)
from avenir_contracts.ports import ExplanationWriter, TemplateExplanation

from .compare import vs_first_idea
from .components import score_components
from .first_idea import first_idea_candidates, resolve_first_idea
from .hedge import choose_hedge
from .picks import choose_picks
from .reasons import notices_for, pick_reasons
from .roadmap import build_roadmap


def _candidate_refs(text: str, careers: Sequence[Career]) -> list[tuple[str, str]]:
    """(soc2020, title) of the tied careers when the first idea is ambiguous; [] otherwise."""
    return [(c.soc2020, c.title) for c in first_idea_candidates(text, careers)]


def recommend(
    req: RecommendationRequest, data: AvenirData, writer: ExplanationWriter | None = None
) -> RecommendationOut:
    if not data.careers:
        raise ValueError("no careers loaded")
    careers = list(data.careers.values())
    profile = req.profile

    comps = score_components(profile, careers, data.affinity)
    first = resolve_first_idea(req.first_idea, careers)
    first_comps = None if first is None else comps.get(first.soc2020)

    picks = [
        Pick(
            tier=tier,
            career=data.careers[soc],
            components=comps[soc],
            vs_first_idea=vs_first_idea(comps[soc], first_comps),
            reasons=pick_reasons(tier, data.careers[soc], comps[soc]),
        )
        for tier, soc in choose_picks(comps, exclude={first.soc2020} if first else ())
    ]

    hedge = None
    roadmap = None
    if picks:
        top = picks[0].career
        hedge = choose_hedge(top, data.hedges.get(top.soc2020, []), comps, data.careers)
        roadmap = build_roadmap(profile, top, data.routes.get(top.soc2020, []))

    noticed = [p.career for p in picks]
    if first is not None:
        noticed.append(first)
    if hedge is not None:
        noticed.append(hedge.career)

    extra: dict[str, object] = {}
    if "first_idea_candidates" in RecommendationOut.model_fields:  # contract v2.1
        from avenir_contracts import CareerRef

        extra["first_idea_candidates"] = [
            CareerRef(soc2020=s, title=t) for s, t in _candidate_refs(req.first_idea, careers)
        ]

    template = TemplateExplanation()
    out = RecommendationOut(
        first_idea=first,
        first_idea_components=first_comps,
        picks=picks,
        hedge=hedge,
        roadmap=roadmap,
        notices=notices_for(noticed),
        explanation=Explanation(text="", ai_written=False),  # replaced below, needs the draft
        **extra,
    )
    out = out.model_copy(update={"explanation": template.explain(out)})
    if writer is not None:
        try:
            out = out.model_copy(update={"explanation": Explanation.model_validate(writer.explain(out))})
        except Exception:
            pass  # the template explanation stays
    return out

