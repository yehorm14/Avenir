"""Return and risk components for each career.

Pure functions: no I/O, no network, no LLM. Each component is a weighted mean of the inputs
that are present (weights renormalised). Missing stays missing: it is skipped in the score
and lowers confidence. Pending metrics (source not loaded yet) are skipped in the score and
left out of confidence; exposure_uk is a cross-check only.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from avenir_contracts import Career, Components, ComponentScore, Metric, ProfileIn
from avenir_contracts.vocab import Confidence

from .confidence import component_confidence, downgrade, lowest
from .fit import fit_scores
from .normalise import rank_0_100

_RESILIENCE = ("resilience_covid", "resilience_cost_of_living", "resilience_tech_slump", "resilience_2008")
_WIDE_SPREAD = 0.2
_UK_DISAGREEMENT = 0.15


def _metric(career: Career, key: str) -> Metric | None:
    return career.metrics.get(key)


def _is_pending(m: Metric | None) -> bool:
    return m is not None and m.status == "pending"


def _value(m: Metric | None) -> float | None:
    return None if m is None or _is_pending(m) else m.value


def _inputs(career: Career, keys: Sequence[str]) -> list[Metric | None]:
    """Metrics for component_confidence: pending ones are left out; absent keys stay None."""
    return [m for m in (_metric(career, k) for k in keys) if not _is_pending(m)]


def _weighted(parts: Sequence[tuple[float, float | None]]) -> float | None:
    present = [(w, v) for w, v in parts if v is not None]
    if not present:
        return None
    total = sum(w for w, _ in present)
    return round(sum(w * v for w, v in present) / total, 1)


def _score(value: float | None, confidence: Confidence) -> ComponentScore:
    return ComponentScore(score=value, confidence="low" if value is None else confidence)


def _rank_metric(careers: Sequence[Career], key: str, higher_is_better: bool = True) -> dict[str, float | None]:
    return rank_0_100({c.soc2020: _value(_metric(c, key)) for c in careers}, higher_is_better)


def _disruption_confidence(career: Career) -> Confidence:
    exposure = _metric(career, "exposure")
    level = component_confidence([exposure])
    if exposure is None or exposure.value is None:
        return level
    if exposure.low is not None and exposure.high is not None and exposure.high - exposure.low > _WIDE_SPREAD:
        level = downgrade(level)
    uk = _value(_metric(career, "exposure_uk"))
    # DfE is a percentile, not an ILO task-exposure mean. Use the supplied
    # all-occupation percentile; ranking this subset would change the population.
    ilo_percentile = exposure.extra.get("ilo_percentile")
    if (
        uk is not None
        and 0 <= uk <= 1
        and isinstance(ilo_percentile, (int, float))
        and not isinstance(ilo_percentile, bool)
        and 0 <= ilo_percentile <= 1
        and abs(uk - ilo_percentile) > _UK_DISAGREEMENT
    ):
        level = downgrade(level)
    return level


def score_components(
    profile: ProfileIn,
    careers: Sequence[Career],
    affinity: Mapping[str, Mapping[str, float]],
) -> dict[str, Components]:
    """All five components per career soc2020. Ranks are across the careers passed in."""
    fit = fit_scores(profile, careers, affinity)
    pay = _rank_metric(careers, "pay_median")
    p90 = _rank_metric(careers, "pay_p90")
    growth = _rank_metric(careers, "real_pay_change_10y")
    demand = _rank_metric(careers, "demand_trend", higher_is_better=False)
    exposure = _rank_metric(careers, "exposure")

    resilience_means: dict[str, float | None] = {}
    for c in careers:
        vals = [v for v in (_value(_metric(c, k)) for k in _RESILIENCE) if v is not None]
        resilience_means[c.soc2020] = sum(vals) / len(vals) if vals else None
    resilience = rank_0_100(resilience_means, higher_is_better=False)

    w = 0.2 + 0.6 * profile.automation_worry
    out: dict[str, Components] = {}
    for c in careers:
        s = c.soc2020
        ret = _score(
            _weighted([(0.5, pay[s]), (0.2, p90[s]), (0.3, growth[s])]),
            component_confidence(_inputs(c, ("pay_median", "pay_p90", "real_pay_change_10y"))),
        )
        shortage = _value(_metric(c, "shortage"))
        market = _score(
            _weighted([
                (0.5, demand[s]),
                (0.35, resilience[s]),
                (0.15, None if shortage is None else (0.0 if shortage == 1 else 100.0)),
            ]),
            component_confidence(_inputs(c, ("demand_trend", *_RESILIENCE, "shortage"))),
        )
        disruption = _score(exposure[s], _disruption_confidence(c))

        if market.score is None and disruption.score is None:
            risk = ComponentScore(score=None, confidence="low")
        else:
            present = [x for x in (market, disruption) if x.score is not None]
            risk_value = _weighted([(1 - w, market.score), (w, disruption.score)])
            risk = ComponentScore(score=risk_value, confidence=lowest(*(x.confidence for x in present)))

        out[s] = Components(
            fit=fit[s], expected_return=ret, market_risk=market, disruption_risk=disruption, risk=risk
        )
    return out
