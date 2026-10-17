from __future__ import annotations

import pytest

from avenir_contracts import Career
from avenir_decision.first_idea import first_idea_candidates, resolve_first_idea


def _soc(text, careers):
    c = resolve_first_idea(text, careers)
    return c.soc2020 if c else None


@pytest.mark.parametrize(
    ("text", "soc"),
    [
        ("Architect ", "2451"),
        ("ARCHITECTS", "2451"),
        ("architecture", "2451"),
        ("programmer", "2134"),
        ("2254", "2254"),
        ("astronaut", None),
        ("surveyor", "2454"),
        ("analyst", "3544"),
        ("designer", "2141"),
        ("arkitect", "2451"),
    ],
)
def test_resolves(careers, text, soc):
    assert _soc(text, careers) == soc
    assert first_idea_candidates(text, careers) == []


def test_contains_tie_is_ambiguous(careers):
    # "civil engineer" (2121) and "power engineer" (alias of 2123) are both 14 characters
    assert resolve_first_idea("engineer", careers) is None
    assert [c.soc2020 for c in first_idea_candidates("engineer", careers)] == ["2121", "2123"]


def _career(soc: str, title: str, aliases: list[str] | None = None) -> Career:
    return Career(soc2020=soc, title=title, official_title=title, aliases=aliases or [], metrics={})


def test_exact_name_tie_is_ambiguous():
    cs = [_career("2222", "Zed"), _career("1111", "Other", ["zed"])]
    assert resolve_first_idea("ZED", cs) is None
    assert [c.soc2020 for c in first_idea_candidates("zed", cs)] == ["1111", "2222"]


def test_one_career_matching_via_several_names_counts_once():
    cs = [_career("1111", "Rock climber", ["climber guide"]), _career("2222", "Baker")]
    assert _soc("climb", cs) == "1111"
    assert first_idea_candidates("climb", cs) == []


def test_fuzzy_tie_is_ambiguous():
    cs = [_career("2222", "Plumbers"), _career("1111", "Plumbert")]
    assert resolve_first_idea("plumber", cs) is None
    assert [c.soc2020 for c in first_idea_candidates("plumber", cs)] == ["1111", "2222"]
