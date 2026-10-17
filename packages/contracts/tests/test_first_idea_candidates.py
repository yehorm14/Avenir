import pytest
from pydantic import ValidationError

from avenir_contracts import CareerRef, Explanation, RecommendationOut


def _rec(**kw):
    base = dict(first_idea=None, first_idea_components=None, picks=[], hedge=None, roadmap=None,
                explanation=Explanation(text="t", ai_written=False))
    return RecommendationOut(**base, **kw)


def test_candidates_default_empty():
    assert _rec().first_idea_candidates == []


def test_candidates_validate_with_two_refs():
    r = _rec(first_idea_candidates=[{"soc2020": "2121", "title": "Civil engineer"},
                                    CareerRef(soc2020="2123", title="Electrical engineer")])
    assert [c.soc2020 for c in r.first_idea_candidates] == ["2121", "2123"]
    assert r.first_idea is None


@pytest.mark.parametrize("bad", [
    {"soc2020": "2121", "title": "x", "extra": 1}, {"soc2020": "212", "title": "x"},
    {"soc2020": "21211", "title": "x"}, {"soc2020": "abcd", "title": "x"},
])
def test_career_ref_rejects_bad(bad):
    with pytest.raises(ValidationError):
        CareerRef(**bad)
