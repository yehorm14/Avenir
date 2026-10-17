"""The path planner: from a career to degrees, universities, skills, societies,
competitions, alumni outreach and a year-by-year plan.

Skills come first. The degree is shown as one vehicle for building them, and
where a career can be reached another way (apprenticeship, college), that route
sits beside it. All content is curated in data/pathways/ and labelled demo.
"""

from __future__ import annotations

from .data import Store
from .models import (
    AlumniKit, ApprenticeshipRoute, Competition, DegreeOption, DegreeRole, Link, PathPlan, Route, RouteChoice,
    SafeChoice, SafePath, SkillItem, Society, TimelineStage, University,
)

NATIONS = ("England", "Scotland", "Wales", "Northern Ireland")
DEMO_NOTE = (
    "Examples to get you started, not a ranking. Courses, entry requirements, societies and competitions change "
    "every year, so check each university, students' union and organiser before you plan around them."
)
FIRST_PERSON = {"required": "preferred", "preferred": "preferred"}


def _lc(text: str) -> str:
    """Lower-case the first letter for use mid-sentence, unless it starts an acronym (SQL, CAD)."""
    return text if text[:2].isupper() or not text else text[0].lower() + text[1:]


def doors_for(store: Store, subject: str) -> list[str]:
    """Careers in our list that a degree subject leads to. A guide to flexibility, not a prediction."""
    return sorted(o.title for o in store.occupations.values() if any(c["subject"] == subject for c in o.courses))


def _uni(u: dict, nation: str) -> University:
    return University(name=u["name"], nation=u["nation"], kind=u.get("kind", "university"), home=u["nation"] == nation)


def _degrees(store: Store, soc: str, nation: str) -> list[DegreeOption]:
    out = []
    subjects = store.pathways["subjects"]
    for c in store.occupations[soc].courses:
        s = subjects.get(c["subject"])
        if s is None:
            continue
        unis = sorted((_uni(u, nation) for u in s["universities"]), key=lambda u: (not u.home, u.kind == "college", u.name))
        out.append(DegreeOption(
            subject=c["subject"], qualification=c["qualification"], median_earnings_15m=c["median_earnings_15m"],
            doors=doors_for(store, c["subject"]), about=s["about"], builds=s["builds"], best_if=s["best_if"], search=s["search"], universities=unis,
        ))
    return out


def _safe_path(title: str, fam: dict, degrees: list[DegreeOption]) -> SafePath | None:
    """The degree that keeps the most careers open, when it differs from the most direct one."""
    if len(degrees) < 2:
        return None
    direct = degrees[0]
    widest = max(degrees, key=lambda d: (len(d.doors), -degrees.index(d)))
    if len(widest.doors) <= len(direct.doors):
        return None
    others = [t for t in widest.doors if t != title][:4]
    return SafePath(
        headline=f"{direct.subject} is the most direct route, but {widest.subject} keeps more doors open.",
        most_direct=SafeChoice(subject=direct.subject, doors=direct.doors),
        most_doors=SafeChoice(subject=widest.subject, doors=widest.doors),
        how_to_specialise=[
            f"Study {widest.subject}, which also opens: {', '.join(t.lower() for t in others)}." if others else f"Study {widest.subject}.",
            f"Join {fam['societies'][0]['name'].lower()} in your first term, and enter {fam['competitions'][0]['name']}.",
            f"Choose optional modules, a project or a dissertation in {fam['field']}.",
            "Add a specialist Masters later only if you're still sure. You can choose it then, with more evidence.",
        ],
        note="Doors are the careers in our list that each degree leads to. They are a guide to flexibility, not a prediction. Check each course on UCAS.",
    )


def _routes(store: Store, soc: str) -> list[Route]:
    occ = store.occupations[soc]
    out = [
        Route(type=r["type"], name=r["name"], level=r.get("level"), nation="England", source_id="occupational_maps")
        for r in occ.routes
    ]
    for nation, rs in occ.nation_routes.items():
        out += [Route(type=r["type"], name=r["name"], level=r.get("level"), nation=nation, source_id="nations") for r in rs]
    return [r for r in out if "pprenticeship" in r.type or r.type in ("T Level", "Direct entry")]


def _skill_items(items: list[dict]) -> list[SkillItem]:
    return [SkillItem(skill=i["skill"], how=i["how"], proof=i["proof"]) for i in items]


def _timeline_university(fam: dict, school_subjects: list[str], first_step: str, has_degree: bool) -> list[TimelineStage]:
    soc1 = fam["societies"][0]["name"]
    comp1 = fam["competitions"][0]["name"]
    h = fam["hard"]
    now = [first_step]
    if school_subjects:
        now.append(f"Keep these subjects strong: {', '.join(school_subjects[:4])}.")
    if has_degree:
        now.append("Shortlist 3 to 5 courses, and check each course's entry requirements on UCAS and Discover Uni.")
    return [
        TimelineStage(stage="Now", title="Before you apply", items=now),
        TimelineStage(stage="Year 1", title="Join, learn, explore", items=[
            f"Join {soc1}, and one society that has nothing to do with your career.",
            f"Start building: {_lc(h[0]['skill'])}.",
            "Visit the careers service in your first term and ask about " + fam["experience"] + ".",
        ]),
        TimelineStage(stage="Year 2", title="Compete and reach out", items=[
            f"Enter {comp1}, or a similar competition.",
            "Take a committee role, and practise leading something small.",
            f"Message three alumni for 15-minute chats, using the kit below.",
            f"Start applying: {fam['experience']}.",
        ]),
        TimelineStage(stage="Year 3", title="Get real experience", items=[
            f"Do real work: {fam['experience']}.",
            f"Deepen: {_lc(h[1]['skill'])}" + (f" and {_lc(h[2]['skill'])}." if len(h) > 2 else "."),
            "Put your evidence in one place: a portfolio, a CV and a short LinkedIn profile.",
        ]),
        TimelineStage(stage="Final year", title="Convert it into a job", items=[
            f"Apply: {fam['final']}.",
            "Ask alumni for introductions and for feedback on your application.",
            "Keep adding to your evidence while you wait for decisions.",
        ]),
    ]


def _timeline_apprenticeship(fam: dict, first_step: str) -> list[TimelineStage]:
    h = fam["hard"]
    comps = fam["competitions"]
    return [
        TimelineStage(stage="Now", title="Before you apply", items=[
            first_step,
            "Look at vacancies on your nation's apprenticeship site, and note application windows. Good employers fill early.",
            "Shadow someone for a day or a week if you can, and ask what they look for.",
        ]),
        TimelineStage(stage="Application", title="Apply widely", items=[
            "Apply to several employers, and tailor each one.",
            f"Show evidence of interest: {_lc(h[0]['proof']).rstrip('.')}.",
            "Ask your school or college careers adviser to check your application.",
        ]),
        TimelineStage(stage="Year 1", title="Learn on the job", items=[
            f"Build the basics: {_lc(h[0]['skill'])}.",
            "Find a mentor at work, and ask for feedback every month.",
            "Keep a log of what you learn: it becomes your portfolio.",
        ]),
        TimelineStage(stage="Year 2+", title="Stand out", items=[
            f"Enter {comps[0]['name']}, or an in-house competition.",
            f"Deepen: {_lc(h[1]['skill'])}.",
            "Talk to people two to five years ahead of you, using the kit below.",
        ]),
        TimelineStage(stage="Qualified", title="Choose your next step", items=[
            "Move up, specialise, or study for a degree part-time. Many employers help pay for it.",
            "Consider running your own business if your trade allows it.",
        ]),
    ]


def build_plan(store: Store, soc: str, nation: str = "England") -> PathPlan | None:
    occ = store.occupations.get(soc)
    fid = store.family_of.get(soc)
    if occ is None or fid is None:
        return None
    nation = nation if nation in NATIONS else "England"
    pw = store.pathways
    fam, common = pw["families"][fid], pw["common"]

    role_info = common["degree_roles"][fam["degree_role"]]
    degrees = _degrees(store, soc, nation)
    routes = _routes(store, soc)
    has_degree = bool(degrees)
    has_apprentice = any("pprenticeship" in r.type for r in routes)

    choices = [
        RouteChoice(
            id="university", label="University", available=has_degree,
            summary="Study a degree, and use it to build skills, contacts and evidence." if has_degree
            else "There is no typical degree route for this career.",
        ),
        RouteChoice(
            id="apprenticeship", label="Apprenticeship and college", available=has_apprentice,
            summary=fam["apprentice"]["summary"] if has_apprentice else "There is no apprenticeship route for this career.",
        ),
    ]
    if has_degree and has_apprentice:
        default = "apprenticeship" if fam["degree_role"] == "optional" else "university"
    else:
        default = "university" if has_degree else "apprenticeship"

    finders = [Link(name=v["name"], url=v["url"], nation=k) for k, v in common["finders"].items()]
    finders.sort(key=lambda f: f.nation != nation)

    soft = [
        SkillItem(skill=common["soft_skills"][k]["label"], how=common["soft_skills"][k]["how"], proof=common["soft_skills"][k]["proof"])
        for k in fam["soft"]
    ]
    alumni = common["alumni"]
    kit = AlumniKit(
        why=alumni["why"], find=alumni["find"], who=fam["who"], tips=alumni["tips"],
        questions=alumni["questions"][:2] + fam["questions"] + alumni["questions"][2:],
        template=alumni["template"], template_apprenticeship=alumni["template_apprenticeship"],
    )
    school_subjects = occ.subjects
    timelines = {
        "university": _timeline_university(fam, school_subjects, occ.first_step, has_degree),
        "apprenticeship": _timeline_apprenticeship(fam, occ.first_step),
    }
    funding = common["funding"][nation]
    return PathPlan(
        soc=soc, title=occ.title, summary=occ.summary, study_level=occ.study_level, first_step=occ.first_step, nation=nation, field=fam["field"],
        degree_role=DegreeRole(level=fam["degree_role"], label=role_info["label"], tone=role_info["tone"], note=fam["degree_note"]),
        routes=choices, default_route=default, degrees=degrees, safe_path=_safe_path(occ.title, fam, degrees),
        apprenticeship=ApprenticeshipRoute(
            summary=fam["apprentice"]["summary"], employers=fam["apprentice"]["employers"],
            routes=sorted(routes, key=lambda r: (r.nation != nation, r.nation)), finders=finders,
        ) if has_apprentice else None,
        school_subjects=school_subjects, hard_skills=_skill_items(fam["hard"]), soft_skills=soft,
        societies=[Society(**s) for s in fam["societies"]], competitions=[Competition(**c) for c in fam["competitions"]],
        alumni=kit, experience=fam["experience"], experience_detail=fam["experience_detail"], timelines=timelines,
        funding=Link(name=funding["name"], url=funding["url"], nation=nation),
        tools=[Link(name=t["name"], url=t["url"]) for t in common["tools"].values()], demo_note=DEMO_NOTE,
    )


def degree_role_label(store: Store, soc: str) -> str:
    fid = store.family_of.get(soc)
    if fid is None:
        return ""
    return store.pathways["common"]["degree_roles"][store.pathways["families"][fid]["degree_role"]]["label"]
