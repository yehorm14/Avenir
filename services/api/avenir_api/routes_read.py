"""Read-only endpoints. Every response is an envelope; unknown ids are 404."""
from __future__ import annotations

from fastapi import APIRouter, Request

from avenir_contracts import AdsSource, BacktestOut, Career, ErrorCode, SourceStatus
from avenir_contracts.vocab import Nation

from .envelope import fail, ok

router = APIRouter(prefix="/api/v1")


def _not_found(what: str):
    return fail(ErrorCode.NOT_FOUND, f"{what} not found")


def with_ads_now(ads: AdsSource, career: Career) -> tuple[Career, SourceStatus]:
    """Copy of `career` with its ads_now metric from the ads source (never mutates the original)."""
    metric, status = ads.ads_now(career, "UK")
    return career.model_copy(update={"metrics": {**career.metrics, "ads_now": metric}}), status


@router.get("/tags")
def tags(request: Request):
    d = request.app.state.data
    return ok(d.tags, d.statuses)


@router.get("/sources")
def sources(request: Request):
    d = request.app.state.data
    return ok({"statuses": d.statuses, "registry": d.sources}, d.statuses)


@router.get("/careers")
def careers(request: Request):
    d = request.app.state.data
    return ok(list(d.careers.values()), d.statuses)


@router.get("/careers/{soc}")
def career(soc: str, request: Request):
    d = request.app.state.data
    c = d.careers.get(soc)
    if c is None:
        return _not_found("Career")
    c, status = with_ads_now(request.app.state.ads, c)
    return ok(c, [*d.statuses, status])


@router.get("/careers/{soc}/history")
def career_history(soc: str, request: Request):
    d = request.app.state.data
    if soc not in d.careers:
        return _not_found("Career")
    return ok(d.history.get(soc, []), d.statuses)


@router.get("/crises")
def crises(request: Request):
    d = request.app.state.data
    return ok(d.crises, d.statuses)


@router.get("/backtest/years")
def backtest_years(request: Request):
    d = request.app.state.data
    return ok(sorted(d.backtest), d.statuses)


@router.get("/backtest")
def backtest(request: Request, year: int | None = None):
    d = request.app.state.data
    if not d.backtest:
        return fail(ErrorCode.UPSTREAM_UNAVAILABLE, "Backtest data is not available")
    window = d.backtest.get(year if year is not None else max(d.backtest))
    if window is None:
        return _not_found("Backtest year")
    out = BacktestOut(window=window, caveats=d.backtest_caveats, status=d.backtest_status)
    return ok(out, d.statuses)


@router.get("/routes/{soc}")
def routes(soc: str, request: Request, nation: Nation = "scotland"):
    d = request.app.state.data
    if soc not in d.careers:
        return _not_found("Career")
    return ok([r for r in d.routes.get(soc, []) if r.nation == nation], d.statuses)
