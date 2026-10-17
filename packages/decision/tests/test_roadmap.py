from __future__ import annotations

from avenir_contracts import Career, ProfileIn, Qualification
from avenir_decision.roadmap import build_roadmap


def _career(subjects=("art", "computing")):
    return Career(
        soc2020="2141",
        title="Web designer",
        official_title="Web design",
        entry_subjects=list(subjects),
        metrics={},
    )


def _profile(nation="scotland", quals=(("maths", "higher"), ("art", "higher"))):
    return ProfileIn(
        interests=["design"],
        qualifications=[Qualification(subject=s, level=lv) for s, lv in quals],
        nation=nation,
        automation_worry=0.5,
    )


def test_amira_gets_scottish_graduate_apprenticeship(data, amira):
    routes = data.routes["2141"]
    rm = build_roadmap(amira, data.careers["2141"], routes)
    assert rm.soc2020 == "2141"
    assert [s.order for s in rm.steps] == [1, 2, 3]
    assert rm.steps[0].title == "Subjects"
    assert rm.steps[0].detail == "Take Higher Computing"
    assert rm.steps[1].title == "Route in"
    assert rm.steps[1].route is not None
    assert rm.steps[1].route.nation == "scotland"
    assert rm.steps[1].route.kind == "graduate_apprenticeship"
    r = rm.steps[1].route
    assert rm.steps[1].detail == f"{r.name}: {r.entry_requirements}"
    assert rm.steps[2].title == "First milestone"
    assert rm.steps[2].detail == "Check the application deadline and open days on the route's page."
    assert rm.this_month == f"Read {r.name} at {r.url} and note its entry requirements."


def test_english_profile_with_only_scottish_routes(data):
    rm = build_roadmap(_profile("england"), data.careers["2141"], data.routes["2141"])
    assert rm.steps[1].route is None
    assert rm.steps[1].detail == "Routes for this nation are missing from our data."
    assert rm.steps[2].detail == "Ask your school's careers adviser about routes into Web designer."
    assert rm.this_month == "Talk to your careers adviser about Web designer."


def test_subject_held_at_higher_is_not_listed(data):
    rm = build_roadmap(_profile(), _career(("maths", "computing")), data.routes["2141"])
    assert rm.steps[0].detail == "Take Higher Computing"


def test_a_level_counts_but_national5_does_not():
    quals = (("computing", "a_level"), ("art", "national5"))
    rm = build_roadmap(_profile(quals=quals), _career(), [])
    assert rm.steps[0].detail == "Take Higher Art"


def test_all_subjects_held_keeps_them():
    rm = build_roadmap(_profile(quals=(("art", "higher"), ("computing", "advanced_higher"))), _career(), [])
    assert rm.steps[0].detail == "Keep Art, Computing to Higher or Advanced Higher"


def test_underscore_subjects_title_cased():
    rm = build_roadmap(_profile(quals=()), _career(("design_technology", "art")), [])
    assert rm.steps[0].detail == "Take Higher Design Technology, Art"


def test_no_entry_subjects():
    rm = build_roadmap(_profile(), _career(()), [])
    assert rm.steps[0].detail == "Check the subjects on the route's page."
