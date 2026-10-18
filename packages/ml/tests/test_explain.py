"""Tests for the explanation templates and the no-invented-numbers validator."""
from pathlib import Path

import pytest

from pathfinder_ml import ML
from pathfinder_ml.explain import allowed_numbers, template_explanation, validate_explanation

ROOT = Path(__file__).resolve().parents[3]
MOCK = ROOT / "snapshots" / "ml" / "mock"


@pytest.fixture(scope="module")
def ml(tmp_path_factory):
    return ML(data_dir=tmp_path_factory.mktemp("empty"), mock_dir=MOCK)


def test_template_is_valid_for_every_demo_occupation(ml):
    for occ in ml.occupations(demo_only=True):
        out = template_explanation(occ)
        assert out["text"], occ["soc2020"]
        assert validate_explanation(out["text"], occ) == [], (occ["soc2020"], validate_explanation(out["text"], occ))


def test_invented_number_is_caught(ml):
    occ = ml.occupation("2134")
    good = template_explanation(occ)["text"]
    assert validate_explanation(good + " Graduates typically start on £31,250.", occ) == ["number not in the record: 31,250"]


def test_missing_flag_is_caught(ml):
    occ = ml.occupation("2134")
    pay = occ["metrics"]["pay_median"]
    text = f"Software developers earn a median of £{pay['value']:,.0f} a year."
    problems = validate_explanation(text, occ)
    assert any(p.startswith("flag not mentioned: employees_only") for p in problems)


def test_rounded_citations_are_accepted(ml):
    occ = ml.occupation("2134")
    v = occ["metrics"]["real_pay_change_10y"]["value"]
    text = f"Real pay changed by {v * 100:.0f}% over ten years. Covers employees only; before 2021 the figures are estimated from the older occupation codes."
    assert [p for p in validate_explanation(text, occ) if p.startswith("number")] == []


def test_allowed_numbers_include_percent_forms(ml):
    occ = ml.occupation("5241")
    v = occ["metrics"]["demand_trend"]["value"]
    nums = allowed_numbers(occ)
    assert any(abs(n - v * 100) < 1e-9 for n in nums)
