import pytest

from avenir_decision.normalise import rank_0_100


def test_rank_spreads_0_to_100():
    assert rank_0_100({"a": 1, "b": 2, "c": 3}) == {"a": 0.0, "b": 50.0, "c": 100.0}


def test_rank_lower_is_better():
    assert rank_0_100({"a": 1, "b": 3}, higher_is_better=False) == {"a": 100.0, "b": 0.0}


def test_ties_share_average_rank():
    assert rank_0_100({"a": 1, "b": 1, "c": 2}) == {"a": 25.0, "b": 25.0, "c": 100.0}


def test_none_stays_none_and_single_value_is_50():
    assert rank_0_100({"a": None, "b": 5}) == {"a": None, "b": 50.0}


def test_all_missing():
    assert rank_0_100({"a": None, "b": None}) == {"a": None, "b": None}


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_is_missing(bad):
    # a NaN from a broken data file must not be ranked, nor shift the others
    assert rank_0_100({"a": 1.0, "b": bad, "c": 3.0}) == {"a": 0.0, "b": None, "c": 100.0}
