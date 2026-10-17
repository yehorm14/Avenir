"""Pay over time, in real terms.

£50,000 ten years ago and £50,000 now is not stability: prices rose, so the same
number buys less. Everything here is converted with CPI so years can be compared
in one year's money (the 'base year'). The spread (middle half of full-time
employees) is shown too, because a median hides how wide pay really is.
"""

from __future__ import annotations

from .data import Store
from .models import Band, CpiPoint, Inflation, PayCareer, PayPoint, PayResponse, PaySummary

KEPT_PACE = 3.0  # within +/- 3% real change counts as keeping pace
NOTE_CPI = (
    "Inflation uses approximate CPI annual averages (2015 = 100). Check them against ONS series D7BT before relying on them."
)


def cpi_index(store: Store) -> dict[int, float]:
    return {int(y): float(v) for y, v in store.cpi["index"].items()}


def real(value: float, year: int, base: int, cpi: dict[int, float]) -> float:
    """Put a pound amount from `year` into `base`-year prices."""
    return value * cpi[base] / cpi[year]


def _band(p25: float, med: float, p75: float, year: int, base: int, cpi: dict[int, float]) -> Band:
    return Band(
        p25=round(real(p25, year, base, cpi)), median=round(real(med, year, base, cpi)), p75=round(real(p75, year, base, cpi))
    )


def _sentence(title: str, s: PaySummary) -> str:
    direction = "up" if s.real_change_pct > 0 else "down"
    return (
        f"A median {title.lower()} earned £{s.median_then:,.0f} in {s.first_year}, "
        f"which is £{s.median_then_today:,.0f} in {s.last_year} money. "
        f"They earn £{s.median_now:,.0f} now: {s.nominal_change_pct:+.0f}% on paper, "
        f"but {direction} {abs(s.real_change_pct):.0f}% once prices are counted."
    )


def career_pay(store: Store, soc: str, base: int) -> PayCareer | None:
    occ = store.occupations.get(soc)
    if occ is None:
        return None
    cpi = cpi_index(store)
    row = store.pay_series.get("occupations", {}).get(soc)
    if not row:
        return PayCareer(soc=soc, title=occ.title, quality=(occ.pay or {}).get("quality"), series=[], summary=None)
    years = sorted(int(y) for y in row["years"])
    series = []
    for y in years:
        r = row["years"][str(y)]
        series.append(
            PayPoint(
                year=y,
                nominal=Band(p25=r["p25"], median=r["median"], p75=r["p75"]),
                real=_band(r["p25"], r["median"], r["p75"], y, base, cpi),
                cpi=cpi[y],
            )
        )
    first, last = series[0], series[-1]
    nominal = 100 * (last.nominal.median / first.nominal.median - 1)
    real_pct = 100 * (last.real.median / first.real.median - 1)
    spread_now = last.real.p75 - last.real.p25
    spread_then = first.real.p75 - first.real.p25
    verdict = "Beat inflation" if real_pct >= KEPT_PACE else "Fell behind" if real_pct <= -KEPT_PACE else "Kept pace"
    summary = PaySummary(
        first_year=first.year,
        last_year=last.year,
        median_then=first.nominal.median,
        median_then_today=round(real(first.nominal.median, first.year, last.year, cpi)),
        median_now=last.nominal.median,
        nominal_change_pct=round(nominal, 1),
        real_change_pct=round(real_pct, 1),
        verdict=verdict,
        spread_now=round(spread_now),
        spread_then=round(spread_then),
        spread_change_pct=round(100 * (spread_now / spread_then - 1), 1) if spread_then else 0.0,
        sentence="",
    )
    summary.sentence = _sentence(occ.title, summary)
    return PayCareer(soc=soc, title=occ.title, quality=row.get("quality"), series=series, summary=summary)


def pay(store: Store, socs: list[str], base: int | None = None) -> PayResponse:
    cpi = cpi_index(store)
    series_years = sorted({int(y) for r in store.pay_series.get("occupations", {}).values() for y in r["years"]})
    first, last = series_years[0], series_years[-1]
    base = base if base in cpi else last
    careers = [c for c in (career_pay(store, s, base) for s in dict.fromkeys(socs)) if c is not None]
    years = sorted(cpi)
    return PayResponse(
        base_year=base,
        first_year=first,
        last_year=last,
        cpi=[
            CpiPoint(year=y, index=cpi[y], change_pct=None if y - 1 not in cpi else round(100 * (cpi[y] / cpi[y - 1] - 1), 1))
            for y in years
        ],
        careers=careers,
        synthetic=bool(store.pay_series.get("synthetic")),
        note=(
            "SYNTHETIC DATA: The pay history is generated to show how the dashboard works, not real earnings. "
            if store.pay_series.get("synthetic")
            else ""
        )
        + NOTE_CPI,
    )


def inflation(store: Store, amount: float, from_year: int, to_year: int) -> Inflation | None:
    cpi = cpi_index(store)
    if from_year not in cpi or to_year not in cpi:
        return None
    eq = real(amount, from_year, to_year, cpi)
    ch = 100 * (cpi[to_year] / cpi[from_year] - 1)
    if from_year == to_year:
        sentence = f"£{amount:,.0f} in {from_year} is simply £{amount:,.0f}."
    else:
        sentence = (
            (
                f"£{amount:,.0f} in {from_year} buys what £{eq:,.0f} does in {to_year}. "
                f"If you still earn £{amount:,.0f}, it's worth {abs(100 * (1 - amount / eq)):.0f}% "
                f"{'less' if eq > amount else 'more'} than it was."
            )
            if eq != amount
            else f"£{amount:,.0f} in {from_year} is worth the same in {to_year}."
        )
    return Inflation(
        amount=amount,
        from_year=from_year,
        to_year=to_year,
        equivalent=round(eq),
        change_pct=round(ch, 1),
        cpi_from=cpi[from_year],
        cpi_to=cpi[to_year],
        sentence=sentence,
        note=NOTE_CPI,
    )
