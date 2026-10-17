"""Write endpoints: profile, recommendations, hedge, and the demo 'pull the plug' switch."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from avenir_contracts import (
    Envelope,
    ErrorCode,
    ErrorDetail,
    Hedge,
    ProfileIn,
    ProfileOut,
    RecommendationOut,
    RecommendationRequest,
    SourceStatus,
)
from avenir_decision import choose_hedge, recommend, score_components

from .envelope import fail, ok
from .routes_read import ERROR_RESPONSES, with_ads_now

log = logging.getLogger("avenir_api")
router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)


class LiveSwitch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


_STATE_RANK = {"live": 0, "snapshot": 1, "mock": 2, "missing": 3}  # higher = less live


class LiveState(BaseModel):
    live: bool


def _unknown_tags(request: Request, interests: list[str], field: str):
    known = {t.id for t in request.app.state.data.tags}
    bad = [ErrorDetail(field=field, issue=f"unknown tag: {i}") for i in interests if i not in known]
    return fail(ErrorCode.VALIDATION_ERROR, "Unknown interest", bad) if bad else None


@router.post("/profile", response_model=Envelope[ProfileOut])
def profile(body: ProfileIn, request: Request):
    d = request.app.state.data
    if not d.careers:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Career data is not available")
    if (err := _unknown_tags(request, body.interests, "body.interests")) is not None:
        return err
    suggester = request.app.state.suggester
    known = {t.id for t in d.tags}
    suggested, source = [], suggester.name
    if body.free_text.strip():
        try:
            suggested = [m for m in suggester.suggest(body.free_text) if m.tag in known]
        except Exception:
            log.warning("tag suggester failed; continuing without suggestions", exc_info=True)
            suggested, source = [], "none"
    interests = list(body.interests)
    for m in suggested:
        if m.tag not in interests:
            interests.append(m.tag)
    return ok(ProfileOut(suggested=suggested, tag_source=source, interests=interests), d.statuses)


@router.post("/recommendations", response_model=Envelope[RecommendationOut])
def recommendations(body: RecommendationRequest, request: Request):
    d = request.app.state.data
    if not d.careers:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Career data is not available")
    if (err := _unknown_tags(request, body.profile.interests, "body.profile.interests")) is not None:
        return err
    out = recommend(body, d, request.app.state.writer)
    ads = request.app.state.ads
    statuses: list[SourceStatus] = []

    picks = []
    for p in out.picks:
        career, st = with_ads_now(ads, p.career)
        statuses.append(st)
        picks.append(p.model_copy(update={"career": career}))
    update: dict[str, object] = {"picks": picks}
    if out.first_idea is not None:
        update["first_idea"], st = with_ads_now(ads, out.first_idea)
        statuses.append(st)
    if out.hedge is not None:
        career, st = with_ads_now(ads, out.hedge.career)
        statuses.append(st)
        update["hedge"] = out.hedge.model_copy(update={"career": career})
    out = out.model_copy(update=update)
    worst = max(statuses, key=lambda s: _STATE_RANK[s.status], default=None)
    return ok(out, [*d.statuses, *([worst] if worst else [])])


@router.get("/careers/{soc}/hedge", response_model=Envelope[Hedge | None])
def hedge(soc: str, request: Request):
    d = request.app.state.data
    if not d.careers:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Career data is not available")
    career = d.careers.get(soc)
    if career is None:
        return fail(ErrorCode.NOT_FOUND, "Career not found")
    comps = score_components(ProfileIn(), list(d.careers.values()), d.affinity)
    found = choose_hedge(career, d.hedges.get(soc, []), comps, d.careers)
    if found is None:
        return ok(None, d.statuses)
    shown, status = with_ads_now(request.app.state.ads, found.career)
    return ok(found.model_copy(update={"career": shown}), [*d.statuses, status])


@router.post("/demo/live", response_model=Envelope[LiveState])
def demo_live(body: LiveSwitch, request: Request):
    request.app.state.ads.set_live(body.enabled)
    return ok({"live": body.enabled}, request.app.state.data.statuses)
