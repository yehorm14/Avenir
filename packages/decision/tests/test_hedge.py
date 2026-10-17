from __future__ import annotations

from avenir_contracts import Career, Components, ComponentScore, HedgeCandidate
from avenir_decision.components import score_components
from avenir_decision.hedge import choose_hedge


def _cs(score):
    return ComponentScore(score=score, confidence="high")


def _comp(risk, fit=50.0):
    return Components(
        fit=_cs(fit), expected_return=_cs(50.0), market_risk=_cs(50.0), disruption_risk=_cs(50.0), risk=_cs(risk)
    )


def _career(soc):
    return Career(soc2020=soc, title=f"Career {soc}", official_title=f"Official {soc}", metrics={})


def _cand(soc, sim):
    return HedgeCandidate(soc2020=soc, title=f"Cand {soc}", similarity=sim, shared_skills=["a"], why="w", status="mock")


def _world(specs):
    """specs: {soc: (risk, fit)}"""
    careers = {s: _career(s) for s in specs}
    comps = {s: _comp(r, f) for s, (r, f) in specs.items()}
    return careers, comps


def test_safer_lower_similarity_beats_riskier_higher():
    careers, comps = _world({"1111": (50.0, 50), "2222": (60.0, 50), "3333": (40.0, 50)})
    h = choose_hedge(careers["1111"], [_cand("2222", 0.95), _cand("3333", 0.6)], comps, careers)
    assert h is not None
    assert h.career.soc2020 == "3333"
    assert h.for_soc == "1111"
    assert h.similarity == 0.6
    assert h.risk_delta == -10.0
    assert h.shared_skills == ["a"]
    assert h.why == "w"
    assert h.status == "mock"


def test_unknown_soc_skipped():
    careers, comps = _world({"1111": (50.0, 50), "3333": (40.0, 50)})
    h = choose_hedge(careers["1111"], [_cand("9999", 0.99), _cand("3333", 0.5)], comps, careers)
    assert h is not None and h.career.soc2020 == "3333"


def test_none_safer_returns_none():
    careers, comps = _world({"1111": (50.0, 50), "2222": (50.0, 50), "3333": (70.0, 50)})
    assert choose_hedge(careers["1111"], [_cand("2222", 0.9), _cand("3333", 0.9)], comps, careers) is None


def test_similarity_tie_lower_risk_wins():
    careers, comps = _world({"1111": (50.0, 50), "2222": (45.0, 90), "3333": (40.0, 10)})
    h = choose_hedge(careers["1111"], [_cand("2222", 0.8), _cand("3333", 0.8)], comps, careers)
    assert h is not None and h.career.soc2020 == "3333"


def test_risk_tie_higher_fit_wins():
    careers, comps = _world({"1111": (50.0, 50), "2222": (40.0, 30), "3333": (40.0, 70)})
    h = choose_hedge(careers["1111"], [_cand("2222", 0.8), _cand("3333", 0.8)], comps, careers)
    assert h is not None and h.career.soc2020 == "3333"


def test_risk_and_fit_tie_lower_soc_wins():
    careers, comps = _world({"1111": (50.0, 50), "2222": (40.0, 70), "3333": (40.0, 70)})
    h = choose_hedge(careers["1111"], [_cand("3333", 0.8), _cand("2222", 0.8)], comps, careers)
    assert h is not None and h.career.soc2020 == "2222"


def test_candidate_with_none_risk_skipped():
    careers, comps = _world({"1111": (50.0, 50), "2222": (40.0, 50), "3333": (30.0, 50)})
    comps["2222"] = _comp(None)
    h = choose_hedge(careers["1111"], [_cand("2222", 0.9), _cand("3333", 0.5)], comps, careers)
    assert h is not None and h.career.soc2020 == "3333"


def test_top_risk_none_returns_none():
    careers, comps = _world({"1111": (50.0, 50), "2222": (40.0, 50)})
    comps["1111"] = _comp(None)
    assert choose_hedge(careers["1111"], [_cand("2222", 0.9)], comps, careers) is None


def test_risk_delta_rounded():
    careers, comps = _world({"1111": (50.26, 50), "2222": (40.0, 50)})
    h = choose_hedge(careers["1111"], [_cand("2222", 0.9)], comps, careers)
    assert h is not None and h.risk_delta == -10.3


def test_amira_mock_hedge(data, careers, amira):
    comps = score_components(amira, careers, data.affinity)
    top = data.careers["2141"]
    cands = data.hedges["2141"]
    h = choose_hedge(top, cands, comps, data.careers)
    assert h is not None and h.career.soc2020 == "2123"
