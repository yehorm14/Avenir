"""Write endpoints: profile, recommendations, hedge, and the demo 'pull the plug' switch."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from avenir_contracts import (
    ErrorCode,
    ErrorDetail,
    ProfileIn,
    ProfileOut,
    RecommendationRequest,
    SourceStatus,
)
from avenir_decision import choose_hedge, recommend, score_components

from .envelope import fail, ok
from .routes_read import with_ads_now

log = logging.getLogger("avenir_api")
router = APIRouter(prefix="/api/v1")


class LiveSwitch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


def _unknown_tags(request: Request, interests: list[str], field: str):
    known = {t.id for t in request.app.state.data.tags}
    bad = [ErrorDetail(field=field, issue=f"unknown tag: {i}") for i in interests if i not in known]
    return fail(ErrorCode.VALIDATION_ERROR, "Unknown interest", bad) if bad else None


@router.post("/profile")
def profile(body: ProfileIn, request: Request):
    d = request.app.state.data
    if (err := _unknown_tags(request, body.interests, "interests")) is not None:
        return err
    suggester = request.app.state.suggester
    suggested, source = [], suggester.name
    if body.free_text.strip():
        try:
            suggested = list(suggester.suggest(body.free_text))
        except Exception:
            log.warning("tag suggester failed; continuing without suggestions", exc_info=True)
            suggested, source = [], "none"
    interests = list(body.interests)
    for m in suggested:
        if m.tag not in interests:
            interests.append(m.tag)
    return ok(ProfileOut(suggested=suggested, tag_source=source, interests=interests), d.statuses)


@router.post("/recommendations")
def recommendations(body: RecommendationRequest, request: Request):
    d = request.app.state.data
    if (err := _unknown_tags(request, body.profile.interests, "profile.interests")) is not None:
        return err
    if not d.careers:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Career data is not available")
    out = recommend(body, d, request.app.state.writer)
    ads = request.app.state.ads
    status: SourceStatus | None = None

    picks = []
    for p in out.picks:
        career, status = with_ads_now(ads, p.career)
        picks.append(p.model_copy(update={"career": career}))
    update: dict[str, object] = {"picks": picks}
    if out.first_idea is not None:
        update["first_idea"], status = with_ads_now(ads, out.first_idea)
    if out.hedge is not None:
        career, status = with_ads_now(ads, out.hedge.career)
        update["hedge"] = out.hedge.model_copy(update={"career": career})
    out = out.model_copy(update=update)
    return ok(out, [*d.statuses, *([status] if status else [])])


@router.get("/careers/{soc}/hedge")
def hedge(soc: str, request: Request):
    d = request.app.state.data
    if not d.careers:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Career data is not available")
    career = d.careers.get(soc)
    if career is None:
        return fail(ErrorCode.NOT_FOUND, "Career not found")
    comps = score_components(ProfileIn(), list(d.careers.values()), d.affinity)
    return ok(choose_hedge(career, d.hedges.get(soc, []), comps, d.careers), d.statuses)


@router.post("/demo/live")
def demo_live(body: LiveSwitch, request: Request):
    request.app.state.ads.set_live(body.enabled)
    return ok({"live": body.enabled}, request.app.state.data.statuses)
