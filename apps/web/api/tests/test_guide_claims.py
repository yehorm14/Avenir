"""Typed numeric claims: a figure must match its occupation, measure, unit and period, not just appear somewhere."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import guide_llm  # noqa: E402
from api.evidence_pack import allowed_numbers  # noqa: E402
from api.guide_claims import FactBook, format_value, render_claim  # noqa: E402


def _pack(soc, title, pay, trend, exposure, jobs=343.0, start=None):
    return {
        "soc": soc,
        "title": title,
        "metrics": {
            "pay": {
                "label": "Median pay",
                "value": pay,
                "display": f"£{pay:,.0f} a year, median for full-time employees (2025)",
                "as_of": "2025",
            },
            "jobs": {
                "label": "Employee jobs",
                "value": jobs,
                "display": f"{jobs:,.0f} thousand full-time employee jobs (2025)",
                "as_of": "2025",
            },
            "trend": {
                "label": "Trend",
                "value": trend,
                "display": f"{100 * trend:+.2f}% a year over 2022-2025",
                "as_of": "2022-2025",
            },
            "exposure": {"label": "Exposure", "value": exposure, "display": f"{exposure:.4f} on a 0–1 scale", "as_of": "2025"},
        },
        "history": {"points": [{"year": 2022, "pay_median_nominal": pay - 4000.0, "jobs_k": jobs - 20}]},
        "starting_pay": start,
    }


DEV = _pack("2134", "Software developer", 56914.0, 0.0262, 0.5444)
NURSE = _pack("3211", "Nurse", 41000.0, 0.0150, 0.1200, jobs=612.0)


@pytest.fixture
def book():
    return FactBook("2134").add(DEV).add([NURSE])


def _allowed():
    return allowed_numbers(DEV) | allowed_numbers(NURSE)


def _fails(book, text):
    return guide_llm.failed_check(text, _allowed(), book)


def test_the_old_check_accepts_the_counterexample_the_typed_check_rejects(book):
    text = "The unemployment rate is 50000%."
    allowed = _allowed() | {"50000"}  # a salary-like number sits in the global whitelist
    assert guide_llm.failed_check(text, allowed) is None  # plain check: the bug
    assert "unemployment" in guide_llm.failed_check(text, allowed, book)
    assert guide_llm.failed_check("Pay is 56914%.", _allowed(), book) is not None  # salary written as a percentage


@pytest.mark.parametrize(
    "text",
    [
        "Software developer median pay is £56,914 a year (2025).",
        "Employment grew +2.62% a year over 2022-2025; exposure is 0.5444 on a 0–1 scale.",
        "Nurses earn £41,000, while software developers earn £56,914.",
        "There are 343 thousand jobs for software developers (2025).",
        "Pay was £52,914 in 2022.",
    ],
)
def test_matching_figures_pass(book, text):
    assert _fails(book, text) is None


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ("Nurses earn £56,914 a year.", "occupation swap"),
        ("Software developers earn £41,000 a year.", "occupation swap"),
        ("Nurse jobs grew 2.62% a year.", "occupation swap on a percentage"),
        ("Starting pay for software developers is £56,914.", "median offered as starting pay"),
        ("Graduates earn £56,914 a year.", "median offered as starting pay"),
        ("Median pay is 56914%.", "salary as a percentage"),
        ("Exposure is £0.5444.", "index as money"),
        ("Pay was £56,914 in 2024.", "wrong period"),
        ("Employment grew 2.62% a year in 2019.", "wrong period"),
        ("Software developers earn £343 a year.", "jobs count as pay"),
        ("Automation exposure is 56914.", "pay as exposure"),
    ],
)
def test_adversarial_swaps_are_rejected(book, text, why):
    failure = _fails(book, text)
    assert failure is not None, why
    assert failure.startswith("claim not supported by the evidence") or failure.startswith("number not in")


def test_median_is_not_starting_pay_but_can_be_said_not_to_be(book):
    assert _fails(book, "The median is £56,914 for all staff, not starting pay.") is None


def test_starting_pay_is_accepted_only_when_the_evidence_holds_one():
    pack = _pack(
        "2134",
        "Software developer",
        56914.0,
        0.0262,
        0.5444,
        start={"value": 31000.0, "display": "£31,000 (2025)", "as_of": "2025"},
    )
    facts = FactBook("2134").add(pack)
    allowed = allowed_numbers(pack)
    assert guide_llm.failed_check("Starting pay is £31,000 (2025).", allowed, facts) is None
    assert guide_llm.failed_check("Starting pay is £56,914.", allowed, facts) is not None
    assert guide_llm.failed_check("Median pay is £31,000.", allowed, facts) is not None


def test_claims_are_typed_and_rendered_deterministically(book):
    claims = book.claims("Nurses earn £41,000 (2025) and software developers see 2.62% growth over 2022-2025.")
    assert [(c.occupation, c.metric, c.unit, c.value, c.period) for c in claims] == [
        ("Nurse", "pay", "gbp", "41000", "2025"),
        ("Software developer", "trend", "pct", "2.62", "2022-2025"),
    ]
    assert render_claim(claims[0]) == "Nurse, median pay: £41,000 (2025)"
    assert render_claim(claims[1]) == "Software developer, employment trend (a year): 2.62% (2022-2025)"
    assert format_value("-0.04", "num") == "-0.04" and format_value("1234.5", "gbp") == "£1,234.5"


def test_tool_results_extend_the_facts_for_their_own_occupation():
    facts = FactBook("2134").add(DEV)
    allowed = allowed_numbers(DEV)
    result = {"results": [{"soc": "2461", "title": "Welfare professional", "median_pay": "£38,100", "pay_as_of": "2025"}]}
    allowed |= allowed_numbers(result)
    assert guide_llm.failed_check("Welfare professionals earn £38,100.", allowed, facts) is not None  # unknown yet
    facts.add(result)
    assert guide_llm.failed_check("Welfare professionals earn £38,100.", allowed, facts) is None
    assert guide_llm.failed_check("Software developers earn £38,100.", allowed, facts) is not None


@pytest.mark.parametrize("period", ["2022–2025", "2022 – 2025", "2022 to 2025", "2024"])
def test_single_year_pay_cannot_support_a_different_period(book, period):
    assert book.check(f"Median pay was £56,914 in {period}.")[0] is not None


def test_tool_metrics_keep_separate_periods_and_require_evidence_for_dated_claims():
    facts = FactBook("2134").add({
        "soc": "2134",
        "title": "Software developer",
        "median_pay": "£38,100",
        "pay_as_of": "2025",
        "trend": "+3% a year",
        "trend_as_of": "2022–2025",
        "starting_pay": "£30,000",
    })
    assert facts.check("Median pay was £38,100 in 2025.")[0] is None
    assert facts.check("Jobs grew 3% over 2022–2025.")[0] is None
    assert facts.check("Median pay was £38,100 over 2022–2025.")[0] is not None
    assert facts.check("Jobs grew 3% in 2025.")[0] is not None
    assert facts.check("Starting pay was £30,000 in 2025.")[0] is not None


@pytest.mark.parametrize("jobs", [73, 343])
def test_jobs_counts_keep_thousands_and_are_checked_even_when_small(jobs):
    facts = FactBook("2134").add(_pack("2134", "Software developer", 56914, 0.0262, 0.5444, jobs=jobs))
    failure, claims = facts.check(f"There were {jobs} thousand employee jobs in 2025.")
    assert failure is None
    assert claims[0].unit == "thousand"
    assert render_claim(claims[0]) == f"Software developer, employee jobs: {jobs} thousand (2025)"
    assert facts.check(f"There were {jobs} jobs in 2025.")[0] is not None


def test_absolute_and_relative_trends_match_different_measures(book):
    pack = _pack("2134", "Software developer", 56914, 0.0262, 0.5444)
    pack["metrics"]["trend"]["display"] = "2.62% a year relative to the typical occupation over 2022–2025"
    relative = "Employment grew 2.62% relative to the typical occupation over 2022–2025."
    facts = FactBook("2134").add(pack)
    failure, claims = facts.check(relative)
    assert failure is None and claims[0].metric == "relative_trend"
    assert "relative to the typical occupation" in render_claim(claims[0])
    assert facts.check("Employment grew 2.62% over 2022–2025.")[0] is not None
    assert book.check(relative)[0] is not None


def test_employer_pay_ranges_do_not_validate_occupational_medians_or_other_levels(book):
    book.add({
        "employer": "BlackRock",
        "career_ladder_uk": {"levels": [
            {"level": "Analyst", "low": 43000, "high": 66000},
            {"level": "Associate", "low": 62000, "high": 96000},
        ]},
    })
    failure, claims = book.check("At BlackRock, base pay for an Analyst ranges from £43,000 to £66,000.")
    assert failure is None and len(claims) == 2
    assert claims[0].occupation == "BlackRock Analyst"
    assert book.check("At BlackRock, base pay for an Associate is £43,000.")[0] is not None
    assert book.check("Software developer median pay is £43,000.")[0] is not None
    assert book.check("At BlackRock, median pay for an Analyst is £43,000.")[0] is not None


def test_temporal_comma_tails_stay_with_the_claim(book):
    assert book.check("Median pay was £56,914, in 2025.")[0] is None
    assert book.check("Median pay was £56,914, in 2022.")[0] is not None
    assert book.check("Median pay was £56,914, as of 2022.")[0] is not None


def test_year_shaped_counts_still_need_matching_units_and_values(book):
    assert book.check("In 2025 employee jobs totalled 343 thousand.")[0] is None
    assert book.check("There were 2025 thousand employee jobs.")[0] is not None
    assert book.check("There were 2025 employee jobs.")[0] is not None
    facts = FactBook("2134").add(_pack("2134", "Software developer", 56914, 0.0262, 0.5444, jobs=2025))
    failure, claims = facts.check("There were 2025 thousand employee jobs in 2025.")
    assert failure is None and claims[0].period == "2025" and claims[0].unit == "thousand"


@pytest.mark.parametrize("figure", ["−2.62%", "negative 2.62%"])
def test_opposite_signed_trend_is_rejected(book, figure):
    assert book.check(f"Employment growth was {figure} over 2022–2025.")[0] is not None


def test_catalogue_names_without_loaded_facts_cannot_use_primary_role_pay():
    facts = FactBook("2134").add(DEV)
    facts.add_occupation_names([{"soc": "3211", "title": "Nurse"}])
    assert facts.check("Nurses earn £56,914 in 2025.")[0] is not None
    assert facts.check("Software developers earn £56,914 in 2025.")[0] is None


def test_small_unitless_counts_are_left_to_the_plain_check(book):
    assert book.check("It is a 3 step plan for 16-18 year olds.")[0] is None


def test_guide_api_rejects_a_swapped_figure_and_returns_typed_claims(monkeypatch, tmp_path):
    from api.main import app
    from fastapi.testclient import TestClient
    from test_guide_grounded import GOOD_REPLY, _fake_post, _openai_env

    monkeypatch.setenv("GUIDE_CACHE_DIR", str(tmp_path))
    client = TestClient(app)
    body = {"soc": "2134", "message": "What is the pay?"}
    _openai_env(monkeypatch)

    _fake_post(monkeypatch, GOOD_REPLY.replace("Median pay", "Starting pay").replace("The published median pay", "Starting pay"))
    swapped = client.post("/api/guide", json=body).json()
    assert swapped["mode"] == "prepared_demo" and swapped["claims"] == []
    assert swapped["checks"].startswith("fallback: claim not supported by the evidence")

    _fake_post(monkeypatch, GOOD_REPLY)
    good = client.post("/api/guide", json=body).json()
    assert good["mode"] == "llm_grounded" and good["checks"] == "passed"
    assert "Software developer, median pay: £56,914 (2025)" in [c["text"] for c in good["claims"]]
    assert "wording around the figures is not verified" in good["note"]
