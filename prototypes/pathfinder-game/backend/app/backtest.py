"""The self-grade. For each past year, rebuild the demand signal from data
published that year only, then check what happened to employment and pay
four years later.

No look-ahead: `inputs_for` copies only the fields that existed at the time
(skill-shortage density and the projection then in force) before any signal
is built; outcome fields are read only when grading.

The demand signal is graded on its own. Pay and AI-exposure series do not go
back far enough on SOC 2020 to be rebuilt as-of each year.
"""

from __future__ import annotations

import random

from .data import Store
from .models import (
    BacktestSummary, GameCandidate, GameReveal, GameRound, GameRow, GameSide, ReplayRow, Replay, TrackPoint, YearMetrics,
)

INPUT_FIELDS = ("ssv", "projection_10y_pct")
W_FUTURE, W_NOW = 0.20, 0.15  # the default weights of the two demand signals
CLEAN_BRIDGES = ("direct", "recoded")


def inputs_for(store: Store, year: int) -> dict[str, dict]:
    rows = store.backtest.get("years", {}).get(str(year), {})
    return {soc: {f: r.get(f) for f in INPUT_FIELDS} for soc, r in rows.items()}


def outcomes_for(store: Store, year: int) -> dict[str, dict]:
    rows = store.backtest.get("years", {}).get(str(year), {})
    return {soc: {"employment_change_pct": r.get("employment_change_pct"), "pay_change_pct": r.get("pay_change_pct")} for soc, r in rows.items()}


def _minmax(vals: dict[str, float | None]) -> dict[str, float | None]:
    present = [max(0.0, v) for v in vals.values() if v is not None]
    if not present:
        return {k: None for k in vals}
    lo, hi = min(present), max(present)
    return {k: None if v is None else (1.0 if hi == lo else (max(0.0, v) - lo) / (hi - lo)) for k, v in vals.items()}


def signal(inputs: dict[str, dict]) -> dict[str, float]:
    p = _minmax({s: r["projection_10y_pct"] for s, r in inputs.items()})
    n = _minmax({s: r["ssv"] for s, r in inputs.items()})
    out = {}
    for s in inputs:
        parts = [(W_FUTURE, p[s]), (W_NOW, n[s])]
        parts = [(w, v) for w, v in parts if v is not None]
        if parts:
            out[s] = sum(w * v for w, v in parts) / sum(w for w, _ in parts)
    return out


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3:
        return None
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return None if den == 0 else num / den


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _usable(store: Store, year: int, exclude_bridged: bool) -> list[tuple[str, float, dict]]:
    sig = signal(inputs_for(store, year))
    outs = outcomes_for(store, year)
    bridge = store.backtest.get("bridge", {})
    rows = []
    for soc, s in sig.items():
        o = outs.get(soc, {})
        if o.get("employment_change_pct") is None:
            continue
        if exclude_bridged and bridge.get(soc, {}).get("type") not in CLEAN_BRIDGES:
            continue
        rows.append((soc, s, o))
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


def year_metrics(store: Store, year: int, exclude_bridged: bool = False) -> YearMetrics:
    rows = _usable(store, year, exclude_bridged)
    horizon = int(store.backtest.get("horizon_years", 4))
    n = len(rows)
    if n < 6:
        return YearMetrics(year=year, outcome_year=year + horizon, n=n, spearman=None, hit_rate=None,
                           top_third_change=None, bottom_third_change=None, pay_spearman=None)
    sig = [r[1] for r in rows]
    emp = [r[2]["employment_change_pct"] for r in rows]
    pay_rows = [(r[1], r[2]["pay_change_pct"]) for r in rows if r[2]["pay_change_pct"] is not None]
    third = n // 3
    med = _median(emp)
    top, bottom = emp[:third], emp[-third:]
    return YearMetrics(
        year=year, outcome_year=year + horizon, n=n,
        spearman=round(spearman(sig, emp), 3),
        hit_rate=round(sum(1 for x in top if x > med) / third, 3),
        top_third_change=round(sum(top) / third, 1),
        bottom_third_change=round(sum(bottom) / third, 1),
        pay_spearman=round(spearman([a for a, _ in pay_rows], [b for _, b in pay_rows]), 3) if len(pay_rows) >= 3 else None,
    )


def years(store: Store) -> list[int]:
    return sorted(int(y) for y in store.backtest.get("years", {}))


def summary(store: Store, exclude_bridged: bool = False) -> BacktestSummary:
    ms = [year_metrics(store, y, exclude_bridged) for y in years(store)]
    graded = [m for m in ms if m.spearman is not None]
    pooled_n = sum(m.n for m in graded)
    mean_rho = round(sum(m.spearman for m in graded) / len(graded), 3) if graded else None
    tops = sum(m.n // 3 for m in graded)
    hits = sum(round(m.hit_rate * (m.n // 3)) for m in graded)
    pooled_hit = round(hits / tops, 3) if tops else None
    synthetic = bool(store.backtest.get("synthetic"))

    if mean_rho is None:
        verdict = "Not enough data to grade the signal."
    else:
        beat = sum(1 for m in graded if m.hit_rate is not None and m.hit_rate > 0.5)
        strength = "weak" if abs(mean_rho) < 0.2 else "moderate" if abs(mean_rho) < 0.4 else "strong"
        verdict = (
            f"Careers our signal ranked in the top third beat the median in {pooled_hit:.0%} of cases (chance is 50%), "
            f"and did better than chance in {beat} of {len(graded)} years. The average rank correlation is {mean_rho:.2f}, "
            f"which is {strength}."
        )
    if synthetic:
        verdict = "SYNTHETIC DATA: this shows how the grade is worked out, not how good the signal is. " + verdict
    caveats = [
        "Job codes changed from SOC 2010 to SOC 2020 in 2021. Older years are bridged; switch on 'Exclude bridged codes' to see the result without split or new codes.",
        f"Only {pooled_n} occupation-years, and they are confounded (the 2019 window includes COVID). Treat the track record as indicative, not proof.",
        "It grades the demand signal only. Pay and AI-exposure data do not go back far enough on SOC 2020.",
        "It checks whether jobs grew, not whether any one person was happy or well paid in them.",
    ]
    if synthetic:
        caveats.insert(0, "These numbers are generated by scripts/build_demo_snapshots.py. Load ESS 2011–2019, Working Futures, LFS and ASHE to get a real track record.")
    return BacktestSummary(
        synthetic=synthetic, note=store.backtest.get("_note", ""), horizon_years=int(store.backtest.get("horizon_years", 4)),
        exclude_bridged=exclude_bridged, years=ms, pooled_n=pooled_n, mean_spearman=mean_rho,
        pooled_hit_rate=pooled_hit, verdict=verdict, caveats=caveats,
    )


def replay(store: Store, year: int, exclude_bridged: bool = False) -> Replay | None:
    if year not in years(store):
        return None
    rows = _usable(store, year, exclude_bridged)
    inputs = inputs_for(store, year)
    bridge = store.backtest.get("bridge", {})
    med = _median([r[2]["employment_change_pct"] for r in rows])

    def row(soc: str, s: float, o: dict) -> ReplayRow:
        occ = store.occupations[soc]
        e = o["employment_change_pct"]
        return ReplayRow(
            soc=soc, title=occ.title, sector=occ.sector, signal=round(s, 3),
            ssv=inputs[soc]["ssv"], projection_10y_pct=inputs[soc]["projection_10y_pct"],
            employment_change_pct=e, pay_change_pct=o["pay_change_pct"],
            beat_median=None if (e is None or med is None) else e > med,
            bridge=bridge.get(soc, {}).get("type", "unknown"),
        )

    return Replay(
        year=year, outcome_year=year + int(store.backtest.get("horizon_years", 4)),
        synthetic=bool(store.backtest.get("synthetic")),
        metrics=year_metrics(store, year, exclude_bridged),
        median_change=None if med is None else round(med, 1),
        top=[row(*r) for r in rows[:5]], bottom=[row(*r) for r in rows[-5:]][::-1],
    )


def track(store: Store, soc: str) -> list[TrackPoint]:
    """Where our signal placed this career each year, and where it ended up."""
    out = []
    for y in years(store):
        sig = signal(inputs_for(store, y))
        if soc not in sig:
            continue
        outs = outcomes_for(store, y)
        vals = sorted(sig.values())
        sp = 100 * sum(1 for v in vals if v <= sig[soc]) / len(vals)
        emp = {k: o["employment_change_pct"] for k, o in outs.items() if o["employment_change_pct"] is not None}
        e = emp.get(soc)
        op = None if e is None else 100 * sum(1 for v in emp.values() if v <= e) / len(emp)
        out.append(TrackPoint(year=y, signal_pct=round(sp), outcome_pct=None if op is None else round(op), employment_change_pct=e))
    return out


# ------------------------------------------------------------ arcade game ----

GAME_N = 10
GAME_PICKS = 3


def _game_sample(store: Store, year: int, seed: int) -> list[tuple[str, float, dict]]:
    """A deterministic set of careers for one round. Same year and seed, same ten."""
    rows = _usable(store, year, False)
    rng = random.Random(f"{year}:{seed}")
    return rng.sample(rows, min(GAME_N, len(rows)))


def game_round(store: Store, year: int, seed: int) -> GameRound | None:
    if year not in years(store):
        return None
    sample = _game_sample(store, year, seed)
    inputs, bridge = inputs_for(store, year), store.backtest.get("bridge", {})
    cands = [
        GameCandidate(
            soc=soc, title=store.occupations[soc].title, sector=store.occupations[soc].sector,
            ssv=inputs[soc]["ssv"], projection_10y_pct=inputs[soc]["projection_10y_pct"],
            bridge=bridge.get(soc, {}).get("type", "unknown"),
        )
        for soc, _, _ in sample
    ]
    cands.sort(key=lambda c: c.title)  # no hint from order
    return GameRound(
        year=year, outcome_year=year + int(store.backtest.get("horizon_years", 4)), seed=seed,
        synthetic=bool(store.backtest.get("synthetic")), picks_needed=GAME_PICKS, candidates=cands,
    )


def game_reveal(store: Store, year: int, seed: int, picks: list[str]) -> GameReveal | None:
    if year not in years(store):
        return None
    sample = _game_sample(store, year, seed)
    socs = {s for s, _, _ in sample}
    if len(set(picks)) != GAME_PICKS or not set(picks) <= socs:
        return None
    change = {s: o["employment_change_pct"] for s, _, o in sample}
    signal_of = {s: sg for s, sg, _ in sample}
    med = _median(list(change.values()))
    algo = [s for s, _ in sorted(((s, sg) for s, sg, _ in sample), key=lambda r: (-r[1], r[0]))[:GAME_PICKS]]
    best = [s for s, _ in sorted(change.items(), key=lambda r: (-r[1], r[0]))[:GAME_PICKS]]

    def side(group: list[str]) -> GameSide:
        return GameSide(avg_change=round(sum(change[s] for s in group) / len(group), 1), beat_median=sum(1 for s in group if change[s] > med))

    you, ai, top = side(picks), side(algo), side(best)
    result = "win" if you.avg_change > ai.avg_change else "tie" if you.avg_change == ai.avg_change else "lose"
    verdict = {
        "win": f"You beat the algorithm: your picks averaged {you.avg_change:+g}% against its {ai.avg_change:+g}%.",
        "tie": f"A tie: your picks and the algorithm's both averaged {you.avg_change:+g}%.",
        "lose": f"The algorithm edged it: its picks averaged {ai.avg_change:+g}% against your {you.avg_change:+g}%.",
    }[result]
    rows = [
        GameRow(
            soc=s, title=store.occupations[s].title, sector=store.occupations[s].sector, signal=round(signal_of[s], 3),
            employment_change_pct=change[s], beat_median=change[s] > med, picked_by_you=s in picks,
            picked_by_algorithm=s in algo, best=s in best,
        )
        for s in sorted(change, key=lambda s: -change[s])
    ]
    synthetic = bool(store.backtest.get("synthetic"))
    note = (
        "Ten careers is a small sample, and the future is noisy, so even a good signal loses some rounds. "
        "That is the point: forecasts are evidence, not certainty."
    )
    if synthetic:
        note = "SYNTHETIC DATA: The outcomes in this round are generated demo data. " + note
    return GameReveal(
        year=year, outcome_year=year + int(store.backtest.get("horizon_years", 4)), synthetic=synthetic, rows=rows,
        median_change=round(med, 1), you=you, algorithm=ai, best=top, result=result, verdict=verdict, note=note,
    )
