import pytest

from avenir_contracts import ProfileIn, Qualification
from avenir_decision.fit import fit_scores, head_start


def test_amira_fits_architect_best(amira, careers, data):
    s = fit_scores(amira, careers, data.affinity)
    assert max(s, key=lambda k: s[k].score) == "2451"  # Architects
    assert s["2451"].score > s["2254"].score  # vs Medical radiographers


def test_empty_profile_is_neutral(careers, data):
    s = fit_scores(ProfileIn(), careers, data.affinity)
    assert {v.score for v in s.values()} == {50.0} and {v.confidence for v in s.values()} == {"low"}


def test_unknown_tag_raises(careers, data):
    with pytest.raises(ValueError, match="juggling"):
        fit_scores(ProfileIn(interests=["juggling"]), careers, data.affinity)


def test_head_start_counts_national5_as_half(data):
    arch = data.careers["2451"]  # mock entry subjects: maths, art, physics
    p = ProfileIn(qualifications=[Qualification(subject="maths", level="national5")])
    assert head_start(p, arch) == pytest.approx(0.5 / 3)
