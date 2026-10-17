from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import backtest
from .data import RIASEC, SKILLS, SUBJECTS, get_store
from .discover import discover, evaluate
from .explain import explain
from .models import (
    AnalyseRequest,
    BacktestSummary,
    CareerDetail,
    CareerSummary,
    ChangeItem,
    ChangesResponse,
    Course,
    DiscoverEval,
    DiscoverRequest,
    DiscoverResponse,
    ExplainRequest,
    ExplainResponse,
    Figures,
    GameRequest,
    GameReveal,
    GameRound,
    Inflation,
    Market,
    MarketRow,
    MatchRequest,
    MatchResponse,
    PathPlan,
    PayResponse,
    Quiz,
    Radar,
    Replay,
    Route,
    SourceOut,
    Task,
    Trend,
    TrustReport,
)
from .path import build_plan
from .pay import inflation as build_inflation
from .pay import pay as build_pay
from .radar import radar as build_radar
from .radar import trends as build_trends
from .scoring import analyse, data_confidence, level, match, region_multiplier, top_code
from .trust import run_eval

PAY_SOC_QUERY = Query(default=[], max_length=6)
RADAR_FIELDS_QUERY = Query(default=[])
CHANGES_SOC_QUERY = Query(default=[], max_length=5)

app = FastAPI(
    title="Pathfinder API",
    version="2.0.0",
    description=(
        "The analysis an investor would expect before committing years to a career: fit, pay, demand, "
        "AI exposure, confidence, a hedge career and a next step. Publishes its own track record."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CURATED = SourceOut(
    id="curated",
    name="Our occupation list and subject mapping",
    publisher="Pathfinder team",
    url=None,
    licence="Open",
    gives=(
        "SOC 2020 list, school subjects and experience, first steps, example universities, "
        "societies, competitions and skills advice (demo: verify before use)"
    ),
    coverage="UK",
    scored=True,
    mode="snapshot",
    edition="2026-10",
)


def _sources() -> list[SourceOut]:
    out = [SourceOut(**a.info.__dict__, mode=a.mode, edition=a.edition) for a in get_store().adapters.values()]
    return out + [CURATED]


@app.get("/api/quiz", response_model=Quiz)
def get_quiz() -> Quiz:
    store = get_store()
    q = store.quiz
    return Quiz(
        scale=q["scale"], items=q["items"], subjects=SUBJECTS, skills=SKILLS, regions=list(store.regions), note=q["_note"]
    )


@app.post("/api/match", response_model=MatchResponse)
def post_match(req: MatchRequest) -> MatchResponse:
    return match(req, get_store())


@app.get("/api/path/{soc}", response_model=PathPlan)
def get_path(soc: str, nation: str = "England") -> PathPlan:
    """Degrees, universities, skills, societies, competitions, alumni kit and a year-by-year plan."""
    plan = build_plan(get_store(), soc, nation)
    if plan is None:
        raise HTTPException(404, "Unknown SOC code")
    return plan


@app.get("/api/pay", response_model=PayResponse)
def get_pay(soc: list[str] = PAY_SOC_QUERY, base: int | None = None) -> PayResponse:
    """Pay each year with its spread, nominal and in real terms (CPI-adjusted to the base year)."""
    return build_pay(get_store(), soc, base)


@app.get("/api/inflation", response_model=Inflation)
def get_inflation(amount: float = Query(50000, ge=0, le=10_000_000), from_year: int = 2015, to_year: int = 2025) -> Inflation:
    """What an amount from one year is worth in another year's money."""
    r = build_inflation(get_store(), amount, from_year, to_year)
    if r is None:
        raise HTTPException(422, "Years must be between 2010 and 2025")
    return r


@app.get("/api/radar", response_model=Radar)
def get_radar(
    fields: list[str] = RADAR_FIELDS_QUERY,
    stage: str = "school",
    nation: str = "England",
    today: date | None = None,
) -> Radar:
    """Opportunities in your fields, with a digest. `today` is for testing; it defaults to the server date."""
    return build_radar(get_store(), fields, stage, nation, today)


@app.get("/api/trends", response_model=list[Trend])
def get_trends() -> list[Trend]:
    """Hot specialisms, and the broader degrees that lead to them while keeping other doors open."""
    return build_trends(get_store())


@app.post("/api/analyse", response_model=CareerSummary)
def post_analyse(req: AnalyseRequest) -> CareerSummary:
    """Stress test, hedge and confidence for one career, given your answers."""
    res = analyse(req, get_store(), req.soc)
    if res is None:
        raise HTTPException(404, "Unknown SOC code, or no interest profile to check it against")
    return res


@app.get("/api/careers/{soc}", response_model=CareerDetail)
def get_career(soc: str) -> CareerDetail:
    store = get_store()
    occ = store.occupations.get(soc)
    if occ is None:
        raise HTTPException(404, "Unknown SOC code")
    routes = []
    if occ.courses:
        routes.append(
            Route(
                type="University",
                name=occ.courses[0]["subject"],
                level=occ.courses[0]["qualification"],
                detail="Any UK nation; see example courses below",
                nation="UK",
                source_id="discover_uni",
            )
        )
    for r in occ.routes:
        routes.append(
            Route(type=r["type"], name=r["name"], level=r.get("level"), nation="England", source_id="occupational_maps")
        )
    for nation, rs in occ.nation_routes.items():
        for r in rs:
            routes.append(Route(type=r["type"], name=r["name"], level=r.get("level"), nation=nation, source_id="nations"))
    notes = []
    if not occ.courses:
        notes.append(
            "Most people start this career through an apprenticeship or college, so there are no university earnings figures."
        )
    pay = occ.pay or {}
    bridge = store.backtest.get("bridge", {}).get(soc, {})
    return CareerDetail(
        soc=occ.soc,
        title=occ.title,
        soc_title=occ.soc_title,
        summary=occ.summary,
        study_level=occ.study_level,
        routes=routes,
        courses=[Course(**c, source_id="discover_uni") for c in occ.courses],
        skills=occ.skills_build,
        first_step=occ.first_step,
        onet_code=occ.onet_code,
        onet_title=occ.onet_title,
        onet_url=f"https://www.onetonline.org/link/summary/{occ.onet_code}" if occ.onet_code else None,
        riasec=dict(zip("RIASEC", occ.riasec or [0] * 6, strict=False)),
        figures=Figures(
            growth_2035_pct=occ.growth_2035_pct,
            priority=occ.priority,
            sector=occ.sector,
            ssv_latest=occ.ssv.get(store.latest_ess),
            ssv_previous=occ.ssv.get(store.previous_ess),
            latest_edition=f"ESS {store.latest_ess}",
            previous_edition=f"ESS {store.previous_ess}",
            pay_median=pay.get("median"),
            pay_p25=pay.get("p25"),
            pay_p75=pay.get("p75"),
            pay_quality=pay.get("quality"),
            pay_edition=store.pay_edition,
            ai_exposure=occ.ai_exposure,
            ai_tasks=[Task(**t) for t in sorted(occ.ai_tasks, key=lambda t: -t["score"])],
        ),
        soc2010=bridge.get("soc2010"),
        bridge=bridge.get("type"),
        track=backtest.track(store, soc),
        track_synthetic=bool(store.backtest.get("synthetic")),
        sources=_sources(),
        notes=notes,
    )


@app.get("/api/changes", response_model=ChangesResponse)
def get_changes(soc: list[str] = CHANGES_SOC_QUERY) -> ChangesResponse:
    store = get_store()
    items = []
    for s in soc:
        occ = store.occupations.get(s)
        if occ is None:
            continue
        prev, latest = occ.ssv.get(store.previous_ess), occ.ssv.get(store.latest_ess)
        if prev is None or latest is None:
            delta, direction = None, "no data"
            msg = "No reliable shortage figure in one or both surveys."
        else:
            delta = latest - prev
            direction = "up" if delta > 0 else "down" if delta < 0 else "same"
            msg = {
                "up": f"Harder to fill: up {delta:g} points since the {store.previous_ess} survey.",
                "down": f"Easier to fill: down {-delta:g} points since the {store.previous_ess} survey.",
                "same": f"No change since the {store.previous_ess} survey.",
            }[direction]
        pay = occ.pay or {}
        pp, pl = pay.get("median_prev"), pay.get("median")
        if pp and pl:
            ch = 100 * (pl - pp) / pp
            pay_msg = f"Median pay {'up' if ch >= 0 else 'down'} {abs(ch):.1f}% (£{pp:,.0f} to £{pl:,.0f})."
        else:
            pay_msg = "No published pay figure."
        items.append(
            ChangeItem(
                soc=s,
                title=occ.title,
                previous=prev,
                latest=latest,
                delta=delta,
                direction=direction,
                message=msg,
                pay_previous=pp,
                pay_latest=pl,
                pay_message=pay_msg,
                growth_2035_pct=occ.growth_2035_pct,
                priority=occ.priority,
            )
        )
    return ChangesResponse(
        latest_edition=f"ESS {store.latest_ess}",
        previous_edition=f"ESS {store.previous_ess}",
        pay_edition=store.pay_edition,
        items=items,
    )


@app.post("/api/explain", response_model=ExplainResponse)
def post_explain(req: ExplainRequest) -> ExplainResponse:
    res = explain(req, get_store())
    if res is None:
        raise HTTPException(404, "This career is not in your results")
    return res


@app.get("/api/backtest", response_model=BacktestSummary)
def get_backtest(exclude_bridged: bool = False) -> BacktestSummary:
    return backtest.summary(get_store(), exclude_bridged)


@app.get("/api/backtest/{year}", response_model=Replay)
def get_replay(year: int, exclude_bridged: bool = False) -> Replay:
    r = backtest.replay(get_store(), year, exclude_bridged)
    if r is None:
        raise HTTPException(404, "No backtest for that year")
    return r


@app.get("/api/game/round", response_model=GameRound)
def get_game_round(year: int, seed: int = 0) -> GameRound:
    """Ten careers as they looked in a past year, without the outcomes. Same year and seed, same ten."""
    r = backtest.game_round(get_store(), year, seed)
    if r is None:
        raise HTTPException(404, "No game for that year")
    return r


@app.post("/api/game/reveal", response_model=GameReveal)
def post_game_reveal(req: GameRequest) -> GameReveal:
    r = backtest.game_reveal(get_store(), req.year, req.seed, req.picks)
    if r is None:
        raise HTTPException(422, "Pick three different careers from the round")
    return r


@app.post("/api/discover", response_model=DiscoverResponse)
def post_discover(req: DiscoverRequest) -> DiscoverResponse:
    return discover(get_store(), req.text)


@app.get("/api/discover/eval", response_model=DiscoverEval)
def get_discover_eval() -> DiscoverEval:
    return evaluate(get_store())


@app.get("/api/trust", response_model=TrustReport)
def get_trust() -> TrustReport:
    return run_eval()


@app.get("/api/market", response_model=Market)
def get_market(region: str = "UK-wide") -> Market:
    """The adviser view: every career at a glance, for one nation or region."""
    store = get_store()
    region = region if region in store.regions else "UK-wide"
    rows = []
    for soc, occ in store.occupations.items():
        conf, _ = data_confidence(store, occ)
        rows.append(
            MarketRow(
                soc=soc,
                title=occ.title,
                sector=occ.sector,
                priority=occ.priority,
                growth_2035_pct=occ.growth_2035_pct,
                ssv_latest=occ.ssv.get(store.latest_ess),
                pay_median=occ.pay_median,
                ai_exposure=occ.ai_exposure,
                region_multiplier=region_multiplier(store, region, occ),
                data_confidence=level(conf),
                riasec_code=top_code(dict(zip(RIASEC, occ.riasec, strict=False))) if occ.riasec else "",
            )
        )
    rows.sort(key=lambda r: r.title)
    return Market(region=region, regions=list(store.regions), rows=rows)


@app.get("/api/sources", response_model=list[SourceOut])
def get_sources() -> list[SourceOut]:
    return _sources()


# Serve the built frontend, if present, so one process runs the whole app.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
