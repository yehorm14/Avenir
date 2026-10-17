"""Deterministic, transparent matching. No AI is involved in ranking.

score = 100 * sum(weight_i * signal_i) over the signals that have data, with
weights renormalised over those signals. Missing data is never filled in.

Each pick then gets the analysis an investor would expect before committing:
a stress test (does it still rank if things go wrong?), a hedge career
(similar strengths, different risks) and a confidence level (how much the
evidence behind it can be trusted).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .data import RIASEC, Occupation, Store
from .path import degree_role_label
from .models import (
    CareerSummary, Component, Confidence, Hedge, KeyFigures, MatchRequest, MatchResponse,
    Scenario, StressTest, Weights,
)

FIT_THRESHOLD = 0.5
KEEP_WITHIN = 5  # a pick "holds" a stress test if it stays in your top 5

LABELS = {
    "interest": "Fits your interests",
    "demand_future": "UK need by 2035",
    "demand_now": "UK need now",
    "pay": "Pay",
    "ai_resilience": "AI resilience",
    "head_start": "Your head start",
}
SOURCE_FOR = {
    "interest": "onet",
    "demand_future": "skills_england",
    "demand_now": "ess",
    "pay": "ashe",
    "ai_resilience": "ai_exposure",
    "head_start": "curated",
}
MISSING_TEXT = {
    "demand_future": "projected growth to 2035",
    "demand_now": "current skill shortages",
    "pay": "pay",
    "ai_resilience": "AI exposure",
}
PHRASES = {
    "interest": ("a strong match for your interests", "only a partial match for your interests"),
    "demand_future": ("the UK will need many more people by 2035", "growth to 2035 is modest"),
    "demand_now": ("employers struggle to fill these jobs today", "current shortages are small"),
    "pay": ("pay is strong", "pay is lower than most options"),
    "ai_resilience": ("AI touches few of its tasks", "AI could change a large share of its tasks"),
    "head_start": ("you already have a head start", "you would be starting mostly from scratch"),
}


# ------------------------------------------------------------- basics ----

def profile_from_answers(answers: dict[str, int], items: list[dict]) -> dict[str, float]:
    """Mean answer per RIASEC type, scaled from 1..5 to 0..1."""
    sums = {k: 0.0 for k in RIASEC}
    counts = {k: 0 for k in RIASEC}
    for item in items:
        a = answers.get(item["id"])
        if a is None:
            continue
        a = min(5, max(1, int(a)))
        sums[item["type"]] += (a - 1) / 4
        counts[item["type"]] += 1
    return {k: round(sums[k] / counts[k], 4) if counts[k] else 0.0 for k in RIASEC}


def top_code(profile: dict[str, float], n: int = 3) -> str:
    order = sorted(RIASEC, key=lambda k: (-profile[k], RIASEC.index(k)))
    return "".join(order[:n])


def pearson(a: list[float], b: list[float]) -> float | None:
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    da = [x - ma for x in a]
    db = [y - mb for y in b]
    den = math.sqrt(sum(x * x for x in da) * sum(y * y for y in db))
    if den == 0:
        return None
    return sum(x * y for x, y in zip(da, db)) / den


def interest_fit(profile: dict[str, float], riasec: list[float]) -> float | None:
    """Correlation of shape between the user's and the job's interest profile,
    clipped at 0. Scale-free, so 1..5 answers and O*NET 1..7 compare fairly."""
    r = pearson([profile[k] for k in RIASEC], riasec)
    return None if r is None else max(0.0, r)


def head_start(occ: Occupation, subjects: list[str], skills: list[str]) -> tuple[float, list[str], list[str]]:
    ms = [s for s in occ.subjects if s in subjects]
    mk = [s for s in occ.skills_have if s in skills]
    subj_part = min(1.0, len(ms) / min(2, len(occ.subjects))) if occ.subjects else 0.0
    skill_part = min(1.0, len(mk) / min(2, len(occ.skills_have))) if occ.skills_have else 0.0
    return 0.6 * subj_part + 0.4 * skill_part, ms, mk


def normalise_weights(w: Weights) -> Weights:
    d = w.model_dump()
    total = sum(d.values())
    if total == 0:
        return Weights()
    return Weights(**{k: v / total for k, v in d.items()})


# --------------------------------------------------- market inputs ----

@dataclass(frozen=True)
class Raw:
    """Market inputs for one occupation, after the regional lens, before scaling."""
    growth: float | None
    ssv: float | None
    pay: float | None
    exposure: float | None


def region_multiplier(store: Store, region: str, occ: Occupation) -> float:
    r = store.regions.get(region) or store.regions.get("UK-wide") or {}
    return float(r.get("multipliers", {}).get(occ.sector or "", 1.0))


def market_raw(store: Store, region: str) -> dict[str, Raw]:
    latest = store.latest_ess
    out = {}
    for soc, occ in store.occupations.items():
        m = region_multiplier(store, region, occ)
        g = occ.growth_2035_pct
        s = occ.ssv.get(latest)
        out[soc] = Raw(
            growth=None if g is None else max(0.0, g) * m,
            ssv=None if s is None else min(100.0, s * m),
            pay=occ.pay_median,
            exposure=occ.ai_exposure,
        )
    return out


Bounds = dict[str, tuple[float, float]]


def bounds_of(raw: dict[str, Raw]) -> Bounds:
    def span(vals: list[float | None]) -> tuple[float, float]:
        present = [v for v in vals if v is not None]
        return (min(present), max(present)) if present else (0.0, 1.0)

    return {
        "growth": span([r.growth for r in raw.values()]),
        "ssv": span([r.ssv for r in raw.values()]),
        "pay": span([r.pay for r in raw.values()]),
        "resilience": span([None if r.exposure is None else 1 - r.exposure for r in raw.values()]),
    }


def scale(v: float | None, b: tuple[float, float]) -> float | None:
    """Min-max against fixed baseline bounds, clipped, so stressed values stay comparable."""
    if v is None:
        return None
    lo, hi = b
    if hi == lo:
        return 1.0
    return min(1.0, max(0.0, (v - lo) / (hi - lo)))


# ------------------------------------------------------------ context ----

@dataclass
class Context:
    store: Store
    region: str
    profile: dict[str, float]
    code: str
    weights: Weights
    fits: dict[str, float]  # only occupations we can check against the safeguard
    head: dict[str, tuple[float, list[str], list[str]]]
    raw: dict[str, Raw]
    bounds: Bounds


def build_context(req: MatchRequest, store: Store) -> Context:
    if req.profile:
        profile = {k: float(req.profile.get(k, 0.0)) for k in RIASEC}
    else:
        profile = profile_from_answers(req.answers, store.quiz["items"])
    region = req.region if req.region in store.regions else "UK-wide"
    fits = {}
    for soc, occ in store.occupations.items():
        if occ.riasec is None:
            continue  # cannot check the interest safeguard, so never show it
        f = interest_fit(profile, occ.riasec)
        if f is not None:
            fits[soc] = f
    raw = market_raw(store, region)
    return Context(
        store=store, region=region, profile=profile, code=top_code(profile),
        weights=normalise_weights(req.weights), fits=fits,
        head={soc: head_start(o, req.subjects, req.skills) for soc, o in store.occupations.items()},
        raw=raw, bounds=bounds_of(raw),
    )


def signal_values(ctx: Context, soc: str, raw: Raw, fit: float) -> dict[str, float | None]:
    b = ctx.bounds
    return {
        "interest": fit,
        "demand_future": scale(raw.growth, b["growth"]),
        "demand_now": scale(raw.ssv, b["ssv"]),
        "pay": scale(raw.pay, b["pay"]),
        "ai_resilience": scale(None if raw.exposure is None else 1 - raw.exposure, b["resilience"]),
        "head_start": ctx.head[soc][0],
    }


def total_score(ctx: Context, values: dict[str, float | None]) -> tuple[float, dict[str, float]]:
    w = ctx.weights.model_dump()
    available = sum(w[k] for k, v in values.items() if v is not None)
    eff = {k: (w[k] / available if (v is not None and available > 0) else 0.0) for k, v in values.items()}
    return sum(100 * eff[k] * (v or 0.0) for k, v in values.items()), eff


def ranking(ctx: Context, raw: dict[str, Raw], fits: dict[str, float]) -> list[tuple[str, float]]:
    """Eligible careers (fit >= threshold), best first. Deterministic tie-breaks."""
    rows = []
    for soc, fit in fits.items():
        if fit < FIT_THRESHOLD:
            continue
        s, _ = total_score(ctx, signal_values(ctx, soc, raw[soc], fit))
        rows.append((soc, s, fit, ctx.store.occupations[soc].title))
    rows.sort(key=lambda r: (-r[1], -r[2], r[3]))
    return [(r[0], r[1]) for r in rows]


# ---------------------------------------------------------- summaries ----

def _money(v: float) -> str:
    return f"£{v:,.0f}"


def _trade_off(components: list[Component], missing: list[str]) -> str:
    used = [c for c in components if c.value is not None and c.weight > 0]
    text = ""
    if used:
        best = max(used, key=lambda c: (c.value, c.weight))
        worst = min(used, key=lambda c: (c.value, -c.weight))
        hi = PHRASES[best.key][0]
        if best.value - worst.value < 0.25:
            level = "strong" if best.value >= 0.6 else "moderate" if best.value >= 0.35 else "modest"
            text = f"An even profile: every signal is {level}."
        elif worst.value >= 0.5:
            text = f"{hi[0].upper()}{hi[1:]}, and the other signals are solid too."
        else:
            text = f"{hi[0].upper()}{hi[1:]}, but {PHRASES[worst.key][1]}."
    if missing:
        names = " or ".join(MISSING_TEXT[m] for m in missing)
        text += f" No data on {names}, so the score uses the other signals."
    return text.strip()


def summarise(ctx: Context, soc: str, rank: int) -> CareerSummary:
    store = ctx.store
    occ = store.occupations[soc]
    raw = ctx.raw[soc]
    fit = ctx.fits[soc]
    values = signal_values(ctx, soc, raw, fit)
    total, eff = total_score(ctx, values)
    m = region_multiplier(store, ctx.region, occ)
    lens = f" · {ctx.region} ×{m:g}" if m != 1 else ""
    hs, ms, mk = ctx.head[soc]
    pay = occ.pay or {}
    tasks = sorted(occ.ai_tasks, key=lambda t: -t["score"])

    detail = {
        "interest": f"Your interests ({ctx.code}) vs this job ({top_code(dict(zip(RIASEC, occ.riasec)))}): match {fit:.2f}",
        "demand_future": "No published projection" if occ.growth_2035_pct is None
        else f"{occ.growth_2035_pct:+g}% projected employment change, 2025 to 2035" + (" · priority occupation" if occ.priority else "") + lens,
        "demand_now": "No reliable figure published" if raw.ssv is None
        else f"{occ.ssv.get(store.latest_ess):g}% of vacancies hard to fill for skills reasons (ESS {store.latest_ess}){lens}",
        "pay": "Not published for this occupation (sample too small)" if raw.pay is None
        else f"Median {_money(raw.pay)} a year, middle half {_money(pay['p25'])} to {_money(pay['p75'])} ({store.pay_edition})",
        "ai_resilience": "No exposure estimate" if raw.exposure is None
        else f"AI exposure {raw.exposure:.2f} on a 0 to 1 scale; most exposed task: {tasks[0]['task'].lower()}",
        "head_start": ("You have: " + ", ".join(ms + mk)) if (ms or mk) else "None of your subjects or skills listed for this job yet",
    }
    w = ctx.weights.model_dump()
    components = [
        Component(
            key=k, label=LABELS[k], value=None if v is None else round(v, 3), weight=round(w[k], 3),
            effective_weight=round(eff[k], 3), contribution=round(100 * eff[k] * (v or 0.0), 1),
            detail=detail[k], source_id=SOURCE_FOR[k],
        )
        for k, v in values.items()
    ]
    missing = [k for k, v in values.items() if v is None]
    return CareerSummary(
        soc=soc, title=occ.title, soc_title=occ.soc_title, summary=occ.summary,
        score=round(total, 1), rank=rank, interest_fit=round(fit, 3), components=components,
        figures=KeyFigures(
            pay_median=raw.pay, pay_p25=pay.get("p25"), pay_p75=pay.get("p75"),
            growth_2035_pct=occ.growth_2035_pct, ssv_latest=occ.ssv.get(store.latest_ess),
            ai_exposure=raw.exposure, region_multiplier=m,
        ),
        trade_off=_trade_off(components, missing), missing=missing,
        sector=occ.sector, priority=occ.priority,
        family=store.family_of.get(soc, ""), degree_role=degree_role_label(store, soc),
        degrees=[c["subject"] for c in occ.courses][:4],
    )


# -------------------------------------------------------- stress test ----

SCENARIOS = [
    ("ai_faster", "AI moves faster", "AI exposure is 50% higher for every job than today's estimate."),
    ("sector_slows", "Your sector slows", "Growth to 2035 is 8 points lower and shortages 15 points lower across this career's sector."),
    ("pay_lags", "Pay falls behind", "Pay in this career's sector is 10% lower than today."),
    ("interests_shift", "Your interests shift", "Your interest match with this career is 0.15 lower, as tastes often change at 16 to 20."),
]


def stress_test(ctx: Context, soc: str, baseline: float, hedge: str | None = None) -> StressTest:
    occ = ctx.store.occupations[soc]
    sector = occ.sector
    out = []
    for sid, label, desc in SCENARIOS:
        raw, fits = dict(ctx.raw), dict(ctx.fits)
        if sid == "ai_faster":
            raw = {k: replace(r, exposure=None if r.exposure is None else min(1.0, r.exposure * 1.5)) for k, r in raw.items()}
        elif sid == "sector_slows":
            for k, r in raw.items():
                if ctx.store.occupations[k].sector == sector:
                    raw[k] = replace(
                        r,
                        growth=None if r.growth is None else max(0.0, r.growth - 8),
                        ssv=None if r.ssv is None else max(0.0, r.ssv - 15),
                    )
        elif sid == "pay_lags":
            for k, r in raw.items():
                if ctx.store.occupations[k].sector == sector and r.pay is not None:
                    raw[k] = replace(r, pay=r.pay * 0.9)
        elif sid == "interests_shift":
            fits[soc] = max(0.0, fits[soc] - 0.15)
        order = ranking(ctx, raw, fits)
        rank = next((i + 1 for i, (s, _) in enumerate(order) if s == soc), None)
        score, _ = total_score(ctx, signal_values(ctx, soc, raw[soc], fits[soc]))
        hedge_score = None
        if hedge is not None:
            hedge_score = round(total_score(ctx, signal_values(ctx, hedge, raw[hedge], fits[hedge]))[0], 1)
        out.append(Scenario(
            id=sid, label=label, description=desc, score=round(score, 1), delta=round(score - baseline, 1),
            rank=rank, holds=rank is not None and rank <= KEEP_WITHIN, hedge_score=hedge_score,
        ))
    hedge_baseline = None
    if hedge is not None:
        hedge_baseline = round(total_score(ctx, signal_values(ctx, hedge, ctx.raw[hedge], ctx.fits[hedge]))[0], 1)
    return StressTest(
        baseline=round(baseline, 1), worst=min(s.score for s in out), holds=sum(s.holds for s in out),
        total=len(out), keep_within=KEEP_WITHIN, scenarios=out, hedge_baseline=hedge_baseline,
    )


# --------------------------------------------------------------- hedge ----

def features(occ: Occupation) -> set[str]:
    return set(occ.subjects) | set(occ.skills_have)


def similarity(a: Occupation, b: Occupation) -> float:
    """0.5 x interest-profile correlation (floored at 0) + 0.5 x Jaccard overlap of
    the subjects and experience each job draws on. Both parts are published, so
    the hedge can be checked by hand."""
    r = pearson(a.riasec, b.riasec) or 0.0
    fa, fb = features(a), features(b)
    jac = len(fa & fb) / len(fa | fb) if (fa | fb) else 0.0
    return 0.5 * max(0.0, r) + 0.5 * jac


def find_hedge(ctx: Context, soc: str, exclude: set[str], scores: dict[str, float]) -> Hedge | None:
    occs = ctx.store.occupations
    p = occs[soc]
    best = None
    for c_soc, fit in ctx.fits.items():
        if c_soc in exclude or c_soc == soc or fit < FIT_THRESHOLD:
            continue
        c = occs[c_soc]
        reasons = []
        other_sector = bool(c.sector and p.sector and c.sector != p.sector)
        if other_sector:
            reasons.append(f"Different sector: {c.sector} rather than {p.sector}")
        if c.ai_exposure is not None and p.ai_exposure is not None and p.ai_exposure - c.ai_exposure >= 0.08:
            reasons.append(f"Less exposed to AI: {c.ai_exposure:.2f} against {p.ai_exposure:.2f}")
        if not reasons:
            continue
        sim = similarity(p, c)
        # A different sector spreads the biggest risk (a sector downturn), so it wins first.
        key = (other_sector, sim, scores.get(c_soc, 0.0))
        if best is None or key > best[0]:
            best = (key, c_soc, reasons, sim)
    if best is None:
        return None
    _, c_soc, reasons, sim = best
    c = occs[c_soc]
    shared = sorted(features(p) & features(c))
    letters = [l for l in top_code(dict(zip(RIASEC, p.riasec)), 2) if l in top_code(dict(zip(RIASEC, c.riasec)), 3)]
    names = {"R": "hands-on", "I": "investigative", "A": "creative", "S": "helping", "E": "leading", "C": "organising"}
    if letters:
        shared = [f"{' and '.join(names[l] for l in letters).capitalize()} interests"] + shared
    return Hedge(
        soc=c_soc, title=c.title, sector=c.sector, similarity=round(sim, 2),
        interest_fit=round(ctx.fits[c_soc], 3), score=round(scores.get(c_soc, 0.0), 1),
        shared=shared[:5], diversifies=reasons,
    )


# ---------------------------------------------------------- confidence ----

def data_confidence(store: Store, occ: Occupation) -> tuple[float, list[str]]:
    score, reasons = 1.0, []
    raw_missing = [
        name for name, v in (
            ("projected growth", occ.growth_2035_pct),
            ("current shortages", occ.ssv.get(store.latest_ess)),
            ("pay", occ.pay_median),
            ("AI exposure", occ.ai_exposure),
        ) if v is None
    ]
    for name in raw_missing:
        score -= 0.15
        reasons.append(f"No data on {name}")
    if not raw_missing:
        reasons.append("Every signal has data")
    if occ.pay and occ.pay.get("quality") == "use with caution":
        score -= 0.1
        reasons.append("ONS flags the pay estimate 'use with caution'")
    bridge = store.backtest.get("bridge", {}).get(occ.soc, {}).get("type")
    if bridge == "split":
        score -= 0.1
        reasons.append("Its job code was split in the 2020 recoding, so past data is approximate")
    elif bridge == "new":
        score -= 0.2
        reasons.append("Its job code is new in 2020, so there is little history")
    return score, reasons


def level(score: float) -> str:
    return "High" if score >= 0.75 else "Medium" if score >= 0.5 else "Low"


def confidence(ctx: Context, soc: str, stress: StressTest) -> Confidence:
    score, reasons = data_confidence(ctx.store, ctx.store.occupations[soc])
    if ctx.fits[soc] < FIT_THRESHOLD + 0.1:
        score -= 0.1
        reasons.append("Your interest match is close to our cut-off")
    if stress.holds == stress.total:
        reasons.append(f"Stays in your top {stress.keep_within} in all {stress.total} stress tests")
    elif stress.holds <= stress.total // 2:
        score -= 0.15
        reasons.append(f"Drops out of your top {stress.keep_within} in {stress.total - stress.holds} of {stress.total} stress tests")
    else:
        reasons.append(f"Stays in your top {stress.keep_within} in {stress.holds} of {stress.total} stress tests")
    score = max(0.0, round(score, 2))
    return Confidence(level=level(score), score=score, reasons=reasons)


# --------------------------------------------------------------- match ----

def score_all(req: MatchRequest, store: Store) -> tuple[Context, list[CareerSummary]]:
    """Every occupation we can check, best first (including ones below the cut-off)."""
    ctx = build_context(req, store)
    rows = []
    for soc, fit in ctx.fits.items():
        s, _ = total_score(ctx, signal_values(ctx, soc, ctx.raw[soc], fit))
        rows.append((soc, s, fit))
    rows.sort(key=lambda r: (-r[1], -r[2], store.occupations[r[0]].title))
    return ctx, [summarise(ctx, soc, i + 1) for i, (soc, _, _) in enumerate(rows)]


def match(req: MatchRequest, store: Store) -> MatchResponse:
    ctx = build_context(req, store)
    flat = pearson([ctx.profile[k] for k in RIASEC], [1, 2, 3, 4, 5, 6]) is None
    order = ranking(ctx, ctx.raw, ctx.fits)
    scores = dict(order)
    hidden = len(ctx.fits) - len(order)
    notes = []
    picks: list[CareerSummary] = []
    more: list[CareerSummary] = []
    if flat:
        notes.append("Your answers were the same for every type of activity, so we cannot tell your interests apart. Try the quiz again and use the full scale.")
        hidden = len(store.occupations)
    else:
        if len(order) < 3:
            n = len(order)
            what = "career in our list fits" if n == 1 else "careers in our list fit"
            notes.append(f"Only {n} {what} your interests well enough (match of {FIT_THRESHOLD} or more). We would rather show fewer than show poor fits.")
        pick_socs = [s for s, _ in order[: req.limit]]
        for i, soc in enumerate(pick_socs):
            c = summarise(ctx, soc, i + 1)
            c.hedge = find_hedge(ctx, soc, set(pick_socs), scores)
            c.stress = stress_test(ctx, soc, scores[soc], c.hedge.soc if c.hedge else None)
            c.confidence = confidence(ctx, soc, c.stress)
            picks.append(c)
        more = [summarise(ctx, soc, req.limit + i + 1) for i, (soc, _) in enumerate(order[req.limit: req.limit + 2])]
    return MatchResponse(
        profile=ctx.profile, code=ctx.code, flat_profile=flat, region=ctx.region,
        results=picks, more=more, considered=len(store.occupations), hidden_low_fit=hidden,
        fit_threshold=FIT_THRESHOLD, weights=ctx.weights, notes=notes,
    )


def analyse(req: MatchRequest, store: Store, soc: str) -> CareerSummary | None:
    """Full analysis (stress test, hedge, confidence) for any one career, pick or not."""
    ctx = build_context(req, store)
    if soc not in ctx.fits:
        return None
    order = ranking(ctx, ctx.raw, ctx.fits)
    scores = dict(order)
    rank = next((i + 1 for i, (s, _) in enumerate(order) if s == soc), 0)  # 0 = below the interest cut-off
    c = summarise(ctx, soc, rank)
    c.hedge = find_hedge(ctx, soc, {s for s, _ in order[: req.limit]}, scores)
    c.stress = stress_test(ctx, soc, c.score, c.hedge.soc if c.hedge else None)
    c.confidence = confidence(ctx, soc, c.stress)
    return c
