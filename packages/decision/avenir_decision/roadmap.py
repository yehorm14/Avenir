"""Three concrete next steps into a career, plus one thing to do this month.

Pure functions: no I/O, no network, no LLM. Only states what the route data states.
"""
from __future__ import annotations

from collections.abc import Sequence

from avenir_contracts import Career, ProfileIn, Roadmap, RoadmapStep, Route
from avenir_decision.fit import FULL_LEVELS

_KIND_PREFERENCE = ("graduate_apprenticeship", "degree", "apprenticeship", "college")


def _name(subject: str) -> str:
    return subject.replace("_", " ").title()


def _subjects_step(profile: ProfileIn, career: Career) -> str:
    """Wording by nation (Yehor, PR #8): Higher in Scotland, A-level in England, and
    "A-level or equivalent" in Wales and Northern Ireland."""
    if not career.entry_subjects:
        return "Check the subjects on the route's page."
    held = {q.subject for q in profile.qualifications if q.level in FULL_LEVELS}
    missing = [s for s in career.entry_subjects if s not in held]
    names = ", ".join(_name(s) for s in (missing or career.entry_subjects))
    if profile.nation == "scotland":
        return f"Take Higher {names}" if missing else f"Keep {names} to Higher or Advanced Higher"
    if profile.nation == "england":
        return f"Take A-level {names}" if missing else f"Keep {names} to A-level"
    return f"Take {names} at A-level or equivalent" if missing else f"Keep {names} to A-level or equivalent"


def _pick_route(profile: ProfileIn, routes: Sequence[Route]) -> Route | None:
    local = [r for r in routes if r.nation == profile.nation]
    for kind in _KIND_PREFERENCE:
        for r in local:
            if r.kind == kind:
                return r
    return None


def build_roadmap(profile: ProfileIn, career: Career, routes: Sequence[Route]) -> Roadmap:
    """Subjects, route in, first milestone, and this month's action for one career."""
    route = _pick_route(profile, routes)
    if route:
        route_detail = f"{route.name}: {route.entry_requirements}"
        milestone = "Check the application deadline and open days on the route's page."
        this_month = f"Read {route.name} at {route.url} and note its entry requirements."
    else:
        route_detail = "Routes for this nation are missing from our data."
        milestone = f"Ask your school's careers adviser about routes into {career.title}."
        this_month = f"Talk to your careers adviser about {career.title}."
    return Roadmap(
        soc2020=career.soc2020,
        steps=[
            RoadmapStep(order=1, title="Subjects", detail=_subjects_step(profile, career)),
            RoadmapStep(order=2, title="Route in", detail=route_detail, route=route),
            RoadmapStep(order=3, title="First milestone", detail=milestone),
        ],
        this_month=this_month,
    )
