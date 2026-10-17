from __future__ import annotations

from avenir_contracts import Components, ComponentScore
from avenir_decision.components import score_components
from avenir_decision.picks import FIT_FLOOR, FIT_RELATIVE, choose_picks, eligible


def cs(score: float | None) -> ComponentScore:
    return ComponentScore(score=score, confidence="low" if score is None else "high")


def comp(fit: float | None, ret: float | None, risk: float | None) -> Components:
    return Components(
        fit=cs(fit), expected_return=cs(ret), market_risk=cs(risk), disruption_risk=cs(risk), risk=cs(risk)
    )


def test_constants() -> None:
    assert FIT_RELATIVE == 0.5
    assert FIT_FLOOR == 5.0


def test_three_distinct_picks_in_order() -> None:
    c = {
        "A": comp(50, 90, 60),  # max return
        "B": comp(50, 40, 10),  # min risk
        "C": comp(50, 80, 20),  # balanced: (80-50)/20 = 1.5
        "D": comp(50, 60, 50),
    }
    assert choose_picks(c) == [("ambitious", "A"), ("safe", "B"), ("balanced", "C")]


def test_picks_are_distinct_when_one_career_leads_everything() -> None:
    c = {
        "A": comp(50, 90, 5),
        "B": comp(50, 70, 30),
        "C": comp(50, 60, 20),
    }
    # A is ambitious; safe among rest is C (risk 20); balanced among B, then: B (20/30) over none left
    assert choose_picks(c) == [("ambitious", "A"), ("safe", "C"), ("balanced", "B")]


def test_balanced_uses_risk_floor_of_10() -> None:
    c = {
        "A": comp(50, 99, 90),
        "B": comp(50, 10, 1),  # safe
        "C": comp(50, 70, 2),  # 20/10 = 2.0 (risk floored)
        "D": comp(50, 75, 12),  # 25/12 = 2.08
    }
    assert choose_picks(c) == [("ambitious", "A"), ("safe", "B"), ("balanced", "D")]


def test_ties_prefer_higher_fit_then_lower_soc() -> None:
    c = {
        "B": comp(40, 80, 50),
        "A": comp(40, 80, 50),
        "C": comp(60, 80, 50),
    }
    assert choose_picks(c)[0] == ("ambitious", "C")
    c2 = {"B": comp(40, 80, 50), "A": comp(40, 80, 50)}
    assert choose_picks(c2)[0] == ("ambitious", "A")


def test_first_idea_excluded() -> None:
    c = {"A": comp(50, 90, 10), "B": comp(50, 60, 30), "C": comp(50, 50, 40)}
    picks = choose_picks(c, exclude={"A"})
    assert "A" not in [s for _, s in picks]
    assert picks[0] == ("ambitious", "B")


def test_excluded_career_does_not_set_best_fit() -> None:
    c = {"A": comp(100, 90, 10), "B": comp(20, 60, 30), "C": comp(11, 50, 40)}
    assert eligible(c, exclude={"A"}) == ["B", "C"]


def test_relative_gate() -> None:
    c = {"A": comp(60, 50, 50), "OUT": comp(29, 50, 50), "IN": comp(30, 50, 50)}
    assert sorted(eligible(c)) == ["A", "IN"]


def test_floor_gate() -> None:
    c = {"A": comp(8, 50, 50), "B": comp(4.9, 50, 50), "C": comp(5, 50, 50)}
    assert sorted(eligible(c)) == ["A", "C"]


def test_missing_return_or_risk_not_eligible() -> None:
    c = {"A": comp(50, None, 10), "B": comp(50, 60, None), "C": comp(50, 60, 10)}
    assert eligible(c) == ["C"]


def test_one_eligible_one_pick() -> None:
    assert choose_picks({"A": comp(50, 60, 10), "B": comp(50, None, 10)}) == [("ambitious", "A")]


def test_none_eligible() -> None:
    assert choose_picks({}) == []
    assert choose_picks({"A": comp(50, 60, 10)}, exclude={"A"}) == []


def test_amira_real_fixtures(amira, careers, data) -> None:  # type: ignore[no-untyped-def]
    comps = score_components(amira, careers, data.affinity)
    el = eligible(comps, exclude={"2451"})
    # Arsenii's cb9e169 embedding affinities replace the earlier hand-made fit table.
    assert len(el) == 11
    picks = choose_picks(comps, exclude={"2451"})
    assert len(picks) == 3
    assert len({s for _, s in picks}) == 3
    assert "2451" not in [s for _, s in picks]
