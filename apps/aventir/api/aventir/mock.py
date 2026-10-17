"""Offline demo repository. Uses only bundled JSON; never opens SQLite or a provider."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "demo.json"


class MockRepository:
    def __init__(self):
        self._data = json.loads(FIXTURE.read_text())
        self._careers = {c["id"]: c for c in self._data["careers"]}
        self._industries = {s["id"]: s for s in self._data["industries"]}

    def metadata(self):
        result = deepcopy(self._data["metadata"])
        counts = Counter(c["group"] for c in self._careers.values())
        result["groups"] = [{"name": name, "count": counts[name]} for name in sorted(counts)]
        result["industries"] = deepcopy(self._data["industries"])
        return result

    def catalogue(self, query="", group="", offset=0, limit=30):
        query = query.casefold()
        matches = [
            c
            for c in self._careers.values()
            if (not group or c["group"] == group)
            and (not query or query in " ".join([c["title"]] + c.get("aliases", [])).casefold())
        ]
        matches.sort(key=lambda c: (not c.get("featured", False), c["title"].casefold()))
        return {
            "total": len(matches),
            "offset": offset,
            "limit": limit,
            "items": deepcopy(matches[offset : offset + limit]),
        }

    def career(self, career_id):
        source = self._careers.get(career_id)
        if source is None:
            return None
        career = deepcopy(source)
        career["industry"] = deepcopy(self._industries.get(career.get("sector_id")))
        return career

    def reflection(self, career, question):
        title = career["title"]
        route_question = any(
            word in question.casefold()
            for word in ("apprentice", "university", "college", "route", "course", "training")
        )
        summary = (
            f"Explore university, college and apprenticeship guidance for {title} before choosing a route. "
            if route_question
            else f"{title.capitalize()} is one career you can explore through its daily work and skills. "
        )
        summary += "This is a sample reflection for the demo, not a live AI response."
        essential = career.get("essential", [])
        activity = (
            "Try a small activity involving {} and note what you enjoy.".format(essential[0]["title"])
            if essential
            else "Try an introductory activity and ask someone in the role about their daily work."
        )
        return {
            "summary": summary,
            "considerations": [
                activity,
                "Read the official career profile and compare the daily work with your interests.",
                "Check university, college and apprenticeship options with official providers; "
                "requirements and openings vary.",
            ],
            "next_question": f"Which part of working as a {title} would you most like to try?",
            "is_mock": True,
            "model": "mock",
            "career_id": career["id"],
            "sources": [career["source_url"]]
            + ([career["salary"]["source_url"]] if career.get("salary") else []),
        }
