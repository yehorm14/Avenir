from __future__ import annotations

import re

import pytest
from pathfinder_ml import FLAG_TEXT, MUST_MENTION

import avenir_decision.reasons as reasons_mod
from avenir_contracts import Career, Components, ComponentScore, Metric
from avenir_decision.reasons import SOURCE_LABELS, notices_for, pick_reasons


def _comps() -> Components:
    cs = ComponentScore(score=50.0, confidence="high")
    return Components(fit=cs, expected_return=cs, market_risk=cs, disruption_risk=cs, risk=cs)


def _m(value, unit="GBP", as_of="2025", source="ons_ashe_t14", confidence="high", flags=()):
    return Metric(value=value, unit=unit, as_of=as_of, source=source, confidence=confidence, flags=list(flags))


def _career(metrics, soc="1111"):
    return Career(soc2020=soc, title="T", official_title="O", metrics=metrics)


def _full():
    return _career({
        "pay_median": _m(48629.0),
        "demand_trend": _m(0.059, unit="ratio"),
        "exposure": _m(0.52, unit="score", source="ilo_wp140", as_of="2024", confidence="medium"),
    })


def test_tier_lines():
    c = _career({})
    assert pick_reasons("ambitious", c, _comps()) == ["Highest expected return among careers that fit you."]
    assert pick_reasons("safe", c, _comps()) == ["Lowest overall risk among careers that fit you."]
    assert pick_reasons("balanced", c, _comps()) == ["Best return for the risk among careers that fit you."]


def test_full_reasons_text_and_order():
    r = pick_reasons("ambitious", _full(), _comps())
    assert r == [
        "Highest expected return among careers that fit you.",
        "Median pay £48,629 a year for full-time employees (ONS ASHE, 2025).",
        "Jobs trend +5.9% a year (2025).",
        "GenAI exposure (research estimate): 0.52 on a 0 to 1 scale, medium confidence.",
    ]


def test_numbers_appear_in_metrics():
    c = _full()
    text = " ".join(pick_reasons("balanced", c, _comps())[1:])
    assert f"£{c.metrics['pay_median'].value:,.0f}" in text
    assert f"{c.metrics['demand_trend'].value * 100:+.1f}%" in text
    assert f"{c.metrics['exposure'].value:.2f}" in text
    # no stray numbers beyond years, the formatted values and the 0 to 1 scale
    nums = set(re.findall(r"[£+\-]?\d[\d,]*\.?\d*%?", text))
    assert nums <= {"£48,629", "2025", "+5.9%", "0.52", "0", "1"}


def test_mock_data_reasons_use_only_metric_numbers(careers):
    for c in careers:
        for line in pick_reasons("safe", c, _comps()):
            for m in re.finditer(r"£([\d,]+)", line):
                assert float(m.group(1).replace(",", "")) == round(c.metrics["pay_median"].value)


@pytest.mark.parametrize("key,needle", [("pay_median", "Median pay"), ("demand_trend", "Jobs trend"),
                                        ("exposure", "GenAI exposure")])
def test_missing_metric_skips_sentence(key, needle):
    c = _full()
    del c.metrics[key]
    assert not any(needle in s for s in pick_reasons("safe", c, _comps()))
    c = _full()
    c.metrics[key] = Metric.missing("GBP", "ons_ashe_t14")
    assert not any(needle in s for s in pick_reasons("safe", c, _comps()))
    assert len(pick_reasons("safe", c, _comps())) == 3


def test_unknown_source_uses_raw_id():
    c = _career({"pay_median": _m(30000.0, source="ons_ashe_t15")})
    assert pick_reasons("safe", c, _comps())[1].endswith("(ons_ashe_t15, 2025).")


def test_mock_source_label():
    assert SOURCE_LABELS["MOCK"] == "sample data"
    c = _career({"pay_median": _m(30000.0, source="MOCK")})
    assert pick_reasons("safe", c, _comps())[1].endswith("(sample data, 2025).")


@pytest.mark.parametrize("as_of", [None, ""])
def test_no_year_drops_year(as_of):
    c = _career({"pay_median": _m(48629.0, as_of=as_of), "demand_trend": _m(0.012, unit="ratio", as_of=as_of)})
    r = pick_reasons("safe", c, _comps())
    assert r[1] == "Median pay £48,629 a year for full-time employees (ONS ASHE)."
    assert r[2] == "Jobs trend +1.2% a year."


def test_negative_trend_sign():
    c = _career({"demand_trend": _m(-0.034, unit="ratio")})
    assert "Jobs trend -3.4% a year (2025)." in pick_reasons("safe", c, _comps())


def test_notices_from_flags_unique_first_seen():
    a = _career({"pay_median": _m(1.0, flags=["covid_year", "bridged_soc2010"])}, "1111")
    b = _career({"exposure": _m(0.5, flags=["bridged_soc2010", "employees_only"])}, "2222")
    assert notices_for([a, b]) == [FLAG_TEXT["covid_year"], FLAG_TEXT["bridged_soc2010"],
                                   FLAG_TEXT["employees_only"]]


def test_bridged_flag_notice():
    c = _career({"pay_median": _m(1.0, flags=["bridged_soc2010"])})
    assert FLAG_TEXT["bridged_soc2010"] in notices_for([c])


def test_non_must_mention_flags_ignored():
    other = next(f for f in FLAG_TEXT if f not in MUST_MENTION)
    assert notices_for([_career({"pay_median": _m(1.0, flags=[other])})]) == []


def test_mention_flag_without_text_is_skipped(monkeypatch):
    monkeypatch.setattr(reasons_mod, "FLAG_TEXT", {"covid_year": "C"})
    c = _career({"pay_median": _m(1.0, flags=["bridged_soc2010", "covid_year"])})
    assert notices_for([c]) == ["C"]


def test_notices_empty():
    assert notices_for([]) == []
