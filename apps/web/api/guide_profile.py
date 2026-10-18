"""Preferences, links and the career path for the guide: pure assembly from the API's own data.

Nothing here is written by a model. Links come from the app's hash routes and the evidence pack's
sources; the path comes from the curated pathway plan and the ESCO skills in `career_texts`.
The grades note says what the app does not hold: entry requirements are never invented.
"""

from __future__ import annotations

import re
from typing import Any

PATH_PATTERN = re.compile(r"how do i become|what should i study|what to study|get into|\bpath|\bplan|\broute|\bsteps?\b")
SKILL_COUNT = 8
COMPARE_COUNT = 2
ROUTE_COUNT = 3
COURSE_COUNT = 4
ROLE_ROUTE = "#/guides/{soc}"
WEIGHT_NAMES = {"pay": "pay", "interest": "interest", "need": "UK need"}
GRADES_NOTE = (
    "Aventier holds no entry requirements for {title}, so it cannot say which grades a course asks for. "
    "Grades and subjects vary by course, provider and nation (Scotland, England, Wales and Northern Ireland "
    "use different qualifications); check each course page before planning around it."
)
NO_PATHWAY_STEP = (
    "No curated pathway example is loaded for this role. Read an official careers service profile "
    "for its routes and entry requirements, and compare the pay and employment evidence here."
)


def wants_path(message: str) -> bool:
    """True when the question asks for a path, plan, route or steps into the career."""
    return bool(PATH_PATTERN.search(message.lower()))


def weight_order(weights: dict) -> str:
    """Plain words for the weight order, e.g. "cares most about pay, then interest, then UK need"."""
    values = {key: float(weights.get(key) or 0) for key in WEIGHT_NAMES}
    if len(set(values.values())) == 1:
        return "weighs pay, interest and UK need equally"
    order = sorted(WEIGHT_NAMES, key=lambda key: -values[key])
    return "cares most about " + ", then ".join(WEIGHT_NAMES[key] for key in order)


def preference_words(profile: dict, titles: dict[str, str], tag_labels: dict[str, str]) -> dict:
    """The student's preferences in plain words, for the prompt and the prepared template."""
    interests = [tag_labels.get(tag, tag.replace("_", " ")) for tag in profile.get("tags", [])]
    selected = [f"{titles.get(soc, 'SOC ' + soc)} ({soc})" for soc in profile.get("selected", [])]
    words = {
        "interests": interests,
        "priorities": weight_order(profile.get("weights") or {}),
        "weights": {key: profile.get("weights", {}).get(key) for key in WEIGHT_NAMES},
        "selected_roles": selected,
    }
    free_text = (profile.get("free_text") or "").strip()
    if free_text:
        words["also_said"] = free_text
    return words


def _preference_parts(words: dict) -> list[str]:
    """The preferences addressed to the student ("you care most about ...")."""
    parts = []
    if words.get("interests"):
        parts.append("your quiz answers point to " + ", ".join(words["interests"][:4]))
    parts.append("you " + words["priorities"].replace("cares most", "care most", 1).replace("weighs ", "weigh ", 1))
    if words.get("selected_roles"):
        parts.append("you selected " + ", ".join(words["selected_roles"][:3]))
    return parts


def preference_sentence(words: dict) -> str:
    """One honest sentence tying a prepared reply to the quiz: the figures are history, not the student's outcome."""
    return (
        "Going by your preferences ("
        + "; ".join(_preference_parts(words))
        + "), weigh the figures above against what you enjoy: they describe what happened to employees in the past, "
        "not your outcome."
    )


def compact_pack(pack: dict) -> dict:
    """Metrics and hedges only, for a compared role."""
    return {"soc": pack.get("soc"), "title": pack.get("title"), "metrics": pack.get("metrics"), "hedges": pack.get("hedges")}


def _ok_url(url: Any) -> bool:
    return isinstance(url, str) and url.startswith(("https://", "http://"))


def role_links(pack: dict, compared: list[dict]) -> list[dict]:
    """The current role's page, each compared role's page, then every source URL in the pack."""
    links = [{"label": f"{pack['title']} in Aventier", "href": ROLE_ROUTE.format(soc=pack["soc"])}]
    links += [{"label": f"{other['title']} in Aventier", "href": ROLE_ROUTE.format(soc=other["soc"])} for other in compared]
    for source in pack.get("sources", []):
        if _ok_url(source.get("url")):
            links.append({"label": source.get("name") or source.get("id") or "Source", "href": source["url"]})
    seen: set[str] = set()
    return [link for link in links if not (link["href"] in seen or seen.add(link["href"]))]


def career_path(career: dict, plan: dict | None, skills: list[str]) -> dict:
    """The structured path from the API's own data: routes, courses, skills, the grades note and the first step."""
    title = career["title"]
    routes: list[dict] = []
    courses: list[dict] = []
    first_step = NO_PATHWAY_STEP
    if plan:
        routes = [{"label": r["label"], "summary": r["summary"]} for r in plan.get("routes", []) if r.get("available")]
        apprenticeship = plan.get("apprenticeship") or {}
        for route in apprenticeship.get("routes", [])[:ROUTE_COUNT]:
            level = str(route.get("level") or "")
            if level and not level.lower().startswith("level"):
                level = "level " + level
            summary = f"{level}, {route.get('nation', 'England')}" if level else route.get("nation", "England")
            routes.append({"label": f"{route['type']}: {route['name']}", "summary": summary})
        for degree in plan.get("degrees", [])[:COURSE_COUNT]:
            course = {"label": f"{degree['subject']} ({degree['qualification']})"}
            if _ok_url(degree.get("search")):
                course["href"] = degree["search"]
            courses.append(course)
        for finder in apprenticeship.get("finders", [])[:2]:
            if _ok_url(finder.get("url")):
                courses.append({"label": finder["name"], "href": finder["url"]})
        first_step = plan.get("first_step") or first_step
        if plan.get("demo_note"):
            first_step += " " + plan["demo_note"]
    plan_skills = [item["skill"] for item in (plan or {}).get("hard_skills", [])]
    merged = list(dict.fromkeys(skills + plan_skills + list(career.get("skills") or [])))[:SKILL_COUNT]
    return {
        "routes": routes,
        "courses": courses,
        "skills": merged,
        "grades_note": GRADES_NOTE.format(title=title.lower()),
        "first_step": first_step,
    }


def path_text(title: str, path: dict, words: dict | None, first_step: bool = True) -> str:
    """The prepared (no-model) walk through the path, naming the student's top tags and selected roles."""
    text = f"Your path into {title.lower()}, from Aventier's own data."
    if words:
        text += " Read it against your preferences: " + "; ".join(_preference_parts(words)) + "."
    if path["routes"]:
        text += " Routes: " + "; ".join(f"{r['label']} ({r['summary']})" for r in path["routes"]) + "."
    else:
        text += " No curated route is loaded for this role; an official careers service lists them."
    if path["courses"]:
        text += " Courses to compare: " + ", ".join(c["label"] for c in path["courses"]) + "."
    if path["skills"]:
        text += " Skills to build: " + ", ".join(path["skills"][:5]) + "."
    text += " About grades: " + path["grades_note"]
    if first_step:
        text += " First step this month: " + path["first_step"]
    return text
