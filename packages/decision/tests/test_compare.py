from __future__ import annotations

from avenir_contracts import Components, ComponentScore
from avenir_decision.compare import COMPONENT_NAMES, vs_first_idea


def _cs(score):
    return ComponentScore(score=score, confidence="high")


def _comp(fit, ret, mr, dr, risk):
    return Components(
        fit=_cs(fit), expected_return=_cs(ret), market_risk=_cs(mr), disruption_risk=_cs(dr), risk=_cs(risk)
    )


def test_names():
    assert COMPONENT_NAMES == ("fit", "expected_return", "market_risk", "disruption_risk", "risk")


def test_none_first_gives_all_none():
    out = vs_first_idea(_comp(50, 60, 40, 30, 35), None)
    assert out == dict.fromkeys(COMPONENT_NAMES)


def test_difference_rounded_and_none_aware():
    out = vs_first_idea(_comp(50.26, 60, 40, None, 35), _comp(40.0, 70.04, 40, 10, None))
    assert out == {
        "fit": 10.3,
        "expected_return": -10.0,
        "market_risk": 0.0,
        "disruption_risk": None,
        "risk": None,
    }
