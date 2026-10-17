"""Read-only endpoints. Every response is an envelope; unknown ids are 404."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from avenir_contracts import (
    AdsSource,
    BacktestOut,
    Career,
    Crisis,
    Envelope,
    ErrorCode,
    HistoryPoint,
    Route,
    SourceInfo,
    SourceStatus,
    Tag,
)
from avenir_contracts.vocab import Nation

from .envelope import fail, ok

ERROR_RESPONSES: dict[int | str, dict] = {
    422: {"model": Envelope[None]},
    404: {"model": Envelope[None]},
    503: {"model": Envelope[None]},
    500: {"model": Envelope[None]},
}
router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)


class SourcesOut(BaseModel):
    statuses: list[SourceStatus]
    registry: dict[str, SourceInfo]


def _not_found(what: str):
    return fail(ErrorCode.NOT_FOUND, f"{what} not found")


def with_ads_now(ads: AdsSource, career: Career) -> tuple[Career, SourceStatus]:
    """Copy of `career` with its ads_now metric from the ads source (never mutates the original)."""
    metric, status = ads.ads_now(career, "UK")
    return career.model_copy(update={"metrics": {**career.metrics, "ads_now": metric}}), status


@router.get("/tags", response_model=Envelope[list[Tag]])
def tags(request: Request):
    d = request.app.state.data
    return ok(d.tags, d.statuses)


@router.get("/sources", response_model=Envelope[SourcesOut])
def sources(request: Request):
    d = request.app.state.data
    return ok({"statuses": d.statuses, "registry": d.sources}, d.statuses)


@router.get("/careers", response_model=Envelope[list[Career]])
def careers(request: Request):
    d = request.app.state.data
    return ok(list(d.careers.values()), d.statuses)


@router.get("/careers/{soc}", response_model=Envelope[Career])
def career(soc: str, request: Request):
    d = request.app.state.data
    c = d.careers.get(soc)
    if c is None:
        return _not_found("Career")
    c, status = with_ads_now(request.app.state.ads, c)
    return ok(c, [*d.statuses, status])


@router.get("/careers/{soc}/history", response_model=Envelope[list[HistoryPoint]])
def career_history(soc: str, request: Request):
    d = request.app.state.data
    if soc not in d.careers:
        return _not_found("Career")
    return ok(d.history.get(soc, []), d.statuses)


@router.get("/crises", response_model=Envelope[list[Crisis]])
def crises(request: Request):
    d = request.app.state.data
    return ok(d.crises, d.statuses)


@router.get("/backtest/years", response_model=Envelope[list[int]])
def backtest_years(request: Request):
    d = request.app.state.data
    return ok(sorted(d.backtest), d.statuses)


@router.get("/backtest", response_model=Envelope[BacktestOut])
def backtest(request: Request, year: int | None = None):
    d = request.app.state.data
    if not d.backtest:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Backtest data is not available")
    window = d.backtest.get(year if year is not None else max(d.backtest))
    if window is None:
        return _not_found("Backtest year")
    out = BacktestOut(window=window, caveats=d.backtest_caveats, status=d.backtest_status)
    return ok(out, d.statuses)


@router.get("/routes/{soc}", response_model=Envelope[list[Route]])
def routes(soc: str, request: Request, nation: Nation = "scotland"):
    d = request.app.state.data
    if soc not in d.careers:
        return _not_found("Career")
    return ok([r for r in d.routes.get(soc, []) if r.nation == nation], d.statuses)
