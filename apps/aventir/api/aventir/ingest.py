"""Small, deterministic transformations of official source records."""

import math
from datetime import datetime

GROUPS = {
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and associate professionals",
    "4": "Clerical support",
    "5": "Service and sales",
    "6": "Agriculture, forestry and fishing",
    "7": "Craft and trades",
    "8": "Plant and machine operators",
    "9": "Elementary occupations",
    "0": "Armed forces",
}


def normalise_occupation(raw):
    uri = raw.get("uri", "")
    if not uri.startswith("http://data.europa.eu/esco/occupation/"):
        raise ValueError("An official ESCO occupation URI is required")
    links = raw.get("_links", {})

    def skills(relation):
        return [
            {
                "uri": s["uri"],
                "title": s.get("title", ""),
                "kind": "knowledge" if s.get("skillType", "").endswith("/knowledge") else "skill",
            }
            for s in links.get(relation, [])
            if s.get("uri")
        ]

    code = raw.get("code", "")
    description = raw.get("description", {}).get("en", {})
    aliases = raw.get("alternativeLabel", {}).get("en", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    return {
        "id": uri.rsplit("/", 1)[-1],
        "title": raw.get("title", ""),
        "code": code,
        "group": GROUPS.get(code[:1], "Other occupations"),
        "description": description.get("literal", "") if isinstance(description, dict) else description,
        "aliases": aliases,
        "essential": skills("hasEssentialSkill"),
        "optional": skills("hasOptionalSkill"),
        "skills_available": "hasEssentialSkill" in links,
        "salary": None,
        "sector_id": None,
        "featured": False,
        "source_url": uri,
    }


def normalise_series(raw):
    rows = {}
    for point in raw.get("months", []):
        try:
            value = float(point["value"]) * 1000
            time = datetime.strptime(point["date"].title(), "%Y %b").strftime("%Y-%m-01")
            if math.isfinite(value):
                rows[time] = {"time": time, "value": value}
        except (KeyError, ValueError, TypeError):
            continue
    return [rows[t] for t in sorted(rows)]
