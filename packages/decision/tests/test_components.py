from __future__ import annotations

import pytest

from avenir_contracts import Career, Metric, ProfileIn
from avenir_decision.components import score_components


def test_slider_moves_risk_toward_disruption(careers, data):
    lo = score_components(ProfileIn(automation_worry=0.0), careers, data.affinity)
    hi = score_components(ProfileIn(automation_worry=1.0), careers, data.affinity)
    c = hi["2134"]
    assert c.risk.score == pytest.approx(0.2 * c.market_risk.score + 0.8 * c.disruption_risk.score, abs=0.1)
    assert any(lo[s].risk.score != hi[s].risk.score for s in hi)


def test_pending_resilience_is_skipped(careers, data):
    out = score_components(ProfileIn(), careers, data.affinity)  # tech_slump and 2008 are null in mocks
    assert all(v.market_risk.score is not None for v in out.values())


def test_scores_bounded(amira, careers, data):
    for comps in score_components(amira, careers, data.affinity).values():
        for cs in comps.model_dump().values():
            assert cs["score"] is None or 0 <= cs["score"] <= 100


def _m(value, confidence="high", status="final", **kw):
    return Metric(value=value, unit="x", source="MOCK", confidence=confidence, status=status, **kw)


def _career(soc, **metrics):
    return Career(soc2020=soc, title=soc, official_title=soc, metrics=metrics)


def _full(soc, **over):
    base = {
        "pay_median": _m(30000.0), "pay_p90": _m(50000.0), "real_pay_change_10y": _m(0.1),
        "demand_trend": _m(0.1), "resilience_covid": _m(0.5), "resilience_cost_of_living": _m(0.5),
        "resilience_tech_slump": _m(None, "low", "pending"), "resilience_2008": _m(None, "low", "pending"),
        "shortage": _m(0.0), "exposure": _m(0.5, low=0.4, high=0.6),
    }
    base.update(over)
    return _career(soc, **base)


def test_pending_metrics_do_not_lower_market_confidence():
    cs = [
        _full("1111", resilience_tech_slump=_m(None, "low", "pending")),
        _full("2222", resilience_2008=_m(None, "low", "pending"), demand_trend=_m(0.3)),
    ]
    out = score_components(ProfileIn(), cs, {})
    assert out["1111"].market_risk.confidence == "high"
    assert out["2222"].market_risk.confidence == "high"


def test_missing_non_pending_lowers_confidence_and_absent_key_is_missing():
    cs = [
        _full("1111", pay_p90=_m(None, "low", "preliminary", flags=["suppressed"])),
        _full("2222"),
        _full("3333"),
    ]
    del cs[2].metrics["demand_trend"]
    out = score_components(ProfileIn(), cs, {})
    assert out["1111"].expected_return.confidence == "medium"
    assert out["2222"].expected_return.confidence == "high"
    assert out["3333"].market_risk.confidence == "medium"
    assert out["3333"].market_risk.score is not None


def test_exposure_uk_pending_does_not_lower_disruption_confidence():
    cs = [_full("1111", exposure_uk=_m(None, "low", "pending")), _full("2222")]
    out = score_components(ProfileIn(), cs, {})
    assert out["1111"].disruption_risk.confidence == "high"


def test_exposure_uk_disagreement_and_wide_spread_downgrade():
    cs = [
        _full("1111", exposure_uk=_m(0.8)),
        _full("2222", exposure_uk=_m(0.55)),
        _full("3333", exposure=_m(0.5, low=0.3, high=0.6)),
        _full("4444", exposure=_m(0.5, low=0.3, high=0.6), exposure_uk=_m(0.9)),
    ]
    out = score_components(ProfileIn(), cs, {})
    assert out["1111"].disruption_risk.confidence == "medium"
    assert out["2222"].disruption_risk.confidence == "high"
    assert out["3333"].disruption_risk.confidence == "medium"
    assert out["4444"].disruption_risk.confidence == "low"


def test_all_missing_gives_none_low_and_risk_uses_other_side():
    cs = [_career("1111"), _full("2222"), _full("3333", exposure=_m(0.9, low=0.8, high=0.9))]
    out = score_components(ProfileIn(), cs, {})
    c = out["1111"]
    assert c.expected_return.score is None and c.expected_return.confidence == "low"
    assert c.market_risk.score is None and c.disruption_risk.score is None
    assert c.risk.score is None and c.risk.confidence == "low"
    only = score_components(ProfileIn(), [_full("2222"), _career("5555", exposure=_m(0.5))], {})
    assert only["5555"].risk.score == only["5555"].disruption_risk.score
    assert only["5555"].risk.confidence == only["5555"].disruption_risk.confidence


def test_shortage_flag_scores_zero_when_in_shortage():
    cs = [_full("1111", shortage=_m(1.0)), _full("2222", shortage=_m(0.0))]
    out = score_components(ProfileIn(), cs, {})
    assert out["1111"].market_risk.score < out["2222"].market_risk.score
