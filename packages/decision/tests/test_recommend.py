from __future__ import annotations

import dataclasses

import pytest

from avenir_contracts import AvenirData, Explanation, ProfileIn, RecommendationRequest
from avenir_decision import recommend
from avenir_decision.compare import COMPONENT_NAMES
from avenir_decision.recommend import _candidate_refs


def _req(profile, text="architect"):
    return RecommendationRequest(profile=profile, first_idea=text)


def test_amira_architect(data, amira):
    out = recommend(_req(amira), data)
    assert out.first_idea is not None and out.first_idea.soc2020 == "2451"
    assert out.first_idea_components is not None
    assert [p.tier for p in out.picks] == ["ambitious", "safe", "balanced"]
    assert [p.career.soc2020 for p in out.picks] == ["2141", "2452", "2453"]
    for p in out.picks:
        assert set(p.vs_first_idea) == set(COMPONENT_NAMES)
        assert p.reasons
    assert out.hedge is not None and out.hedge.for_soc == "2141" and out.hedge.career.soc2020 == "2123"
    assert out.roadmap is not None and out.roadmap.steps[0].detail.startswith("Take Higher Computing")
    assert out.notices
    assert out.explanation.ai_written is False


def test_deterministic(data, amira):
    assert recommend(_req(amira), data) == recommend(_req(amira), data)


class _Boom:
    def explain(self, rec):
        raise RuntimeError("llm down")


class _Fancy:
    def explain(self, rec):
        return Explanation(text="hello", ai_written=True)


def test_writer_raises_keeps_template(data, amira):
    out = recommend(_req(amira), data, _Boom())
    assert out.explanation.ai_written is False
    assert out.explanation.text


class _Junk:
    def explain(self, rec):
        return "oops"


def test_writer_junk_keeps_template(data, amira):
    out = recommend(_req(amira), data, _Junk())
    assert out.explanation.ai_written is False
    assert out.explanation.text != "oops"


def test_writer_used(data, amira):
    assert recommend(_req(amira), data, _Fancy()).explanation.text == "hello"


def test_empty_data_raises(amira):
    with pytest.raises(ValueError, match="no careers loaded"):
        recommend(_req(amira), AvenirData())


def test_empty_profile(data):
    out = recommend(_req(ProfileIn()), data)
    assert out.picks
    assert all(p.components.fit.score == 50 for p in out.picks)


@pytest.mark.parametrize("text", ["astronaut", "engineer"])
def test_unresolved_first_idea(data, amira, text):
    out = recommend(_req(amira, text), data)
    assert out.first_idea is None and out.first_idea_components is None
    assert out.picks
    for p in out.picks:
        assert set(p.vs_first_idea) == set(COMPONENT_NAMES)
        assert all(v is None for v in p.vs_first_idea.values())


def test_narrow_data_fewer_picks(data, amira):
    keep = list(data.careers)[:2]
    small = dataclasses.replace(data, careers={k: data.careers[k] for k in keep})
    out = recommend(_req(amira, "astronaut"), small)
    assert len(out.picks) <= 2


def test_single_career(data, amira):
    k = next(iter(data.careers))
    one = dataclasses.replace(data, careers={k: data.careers[k]})
    out = recommend(_req(amira, "astronaut"), one)
    assert len(out.picks) <= 1


def test_candidate_refs(careers):
    assert _candidate_refs("astronaut", careers) == []
    assert _candidate_refs("architect", careers) == []
    refs = _candidate_refs("engineer", careers)
    assert {s for s, _ in refs} >= {"2121", "2123"}
