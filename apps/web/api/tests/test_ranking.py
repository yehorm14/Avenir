"""Ranking tests use tiny transparent cases, then the actual committed artefacts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def career(soc, pay, demand):
    return {"soc": soc, "title": soc, "metrics": {"pay_median": {"value": pay}, "demand_trend": {"value": demand}}}


def test_pay_and_need_weights_change_the_order():
    from api.ranking import rank_careers

    careers = [career("0001", 100, 0.01), career("0002", 200, 0.02), career("0003", 300, -0.01)]
    affinity = {"design": {"0001": 0.9, "0002": 0.6, "0003": 0.1}}
    pay = rank_careers(careers, ["design"], {"pay": 1, "interest": 0, "need": 0}, affinity)
    need = rank_careers(careers, ["design"], {"pay": 0, "interest": 0, "need": 1}, affinity)
    fit = rank_careers(careers, ["design"], {"pay": 0, "interest": 1, "need": 0}, affinity)
    assert [c["soc"] for c in pay] == ["0003", "0002", "0001"]
    assert [c["soc"] for c in need] == ["0002", "0001", "0003"]
    assert [c["soc"] for c in fit] == ["0001", "0002", "0003"]


def test_missing_metrics_are_not_zero_and_weights_renormalise():
    from api.ranking import rank_careers

    ranked = rank_careers(
        [career("0001", None, None), career("0002", 200, 0.01)],
        ["design"],
        {"pay": 1, "interest": 1, "need": 1},
        {"design": {"0001": 0.8}},
    )
    missing = next(c for c in ranked if c["soc"] == "0001")
    assert missing["pay_score"] is None
    assert missing["need_score"] is None
    assert missing["score"] == 80
    assert missing["metrics"]["pay_median"]["value"] is None


def test_zero_weights_and_ties_have_stable_order():
    from api.ranking import rank_careers

    careers = [career("0002", 100, 0.1), career("0001", 100, 0.1)]
    zero = rank_careers(careers, [], {"pay": 0, "interest": 0, "need": 0}, {})
    equal = rank_careers(careers, [], {"pay": 1, "interest": 1, "need": 1}, {})
    assert zero == equal
    assert [c["soc"] for c in zero] == ["0001", "0002"]
    assert all(c["score"] == 50 for c in zero)


def test_unknown_tags_raise_instead_of_silently_changing_profile():
    import pytest
    from api.ranking import rank_careers

    with pytest.raises(ValueError, match="Unknown interest"):
        rank_careers([career("0001", 100, 0.1)], ["invented"], {"pay": 1}, {})
