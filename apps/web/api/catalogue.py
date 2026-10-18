"""Lightweight browsing and exact evidence for the complete supplied SOC catalogue.

Curated context is limited to the existing demo careers. Other profiles do not
borrow study routes, skills or descriptions from a different occupation.
"""

from __future__ import annotations

from pathfinder_ml import ML

from .evidence_metadata import evidence_metadata

SOC_SECTORS = {
    "1": "Managers, directors and senior officials",
    "2": "Professional occupations",
    "3": "Associate professional occupations",
    "4": "Administrative and secretarial occupations",
    "5": "Skilled trades occupations",
    "6": "Caring, leisure and other service occupations",
    "7": "Sales and customer service occupations",
    "8": "Process, plant and machine operatives",
    "9": "Elementary occupations",
}


def jobs_observation(evidence: ML, occupation: dict) -> dict:
    """Use an older observed count only when the current estimate is missing.

    This display metric never changes the canonical occupation metrics. Retain
    source coverage/confidence, replace year-specific flags with the old point's
    flags, and label the fallback explicitly rather than implying current jobs.
    """
    current = occupation["metrics"]["jobs"]
    if current["value"] is not None and "suppressed" not in current["flags"] and current["status"] != "pending":
        return current
    available = [point for point in evidence.history(occupation["soc2020"]) if point["jobs_k"] is not None]
    if not available:
        return current
    point = max(available, key=lambda item: item["year"])
    flags = set(point["flags"]) | {flag for flag in current["flags"] if flag == "employees_only"}
    flags.add("historical_observation")
    return {
        **current,
        "value": point["jobs_k"],
        "as_of": str(point["year"]),
        "low": None,
        "high": None,
        "flags": sorted(flags),
        "note": (
            f"Latest available historical observation ({point['year']}); the {current['as_of']} estimate is unavailable. "
            + current["note"]
        ),
        "extra": {**current["extra"], "current_observation_as_of": current["as_of"]},
    }


def summaries(evidence: ML, curated: list[dict]) -> list[dict]:
    context = {career["soc"]: career for career in curated}
    return [
        {
            "soc": occupation["soc2020"],
            "title": context.get(occupation["soc2020"], {}).get("title", occupation["title"]),
            "sector": context.get(occupation["soc2020"], {}).get(
                "sector", SOC_SECTORS[occupation["soc2020"][0]]
            ),
            "pay": occupation["metrics"]["pay_median"],
            "jobs": jobs_observation(evidence, occupation),
            "match_supported": occupation["in_demo_set"],
        }
        for occupation in evidence.occupations()
    ]


def detail(evidence: ML, soc: str, curated: list[dict]) -> dict | None:
    occupation = evidence.occupation(soc)
    if occupation is None:
        return None
    context = next((career for career in curated if career["soc"] == soc), None)
    supported = occupation["in_demo_set"]
    if context is None:
        context = {
            "soc": soc,
            "title": occupation["title"],
            "summary": (
                f"Official UK occupation group: {occupation['title']} (SOC 2020 {soc}). "
                "Detailed skills and study routes for this profile have not been added yet. "
                "Explore the supplied pay and employment evidence below."
            ),
            "sector": SOC_SECTORS[soc[0]],
            "family": "explore",
            "skills": [],
        }
    registry = evidence.sources()
    source_ids = {measure["source"] for measure in occupation["metrics"].values()} | {"ons_cpih"}
    return {
        **context,
        "evidence_metadata": evidence_metadata(evidence),
        "sources": [registry[key] for key in sorted(source_ids) if key in registry],
        "metrics": occupation["metrics"],
        "jobs_observation": jobs_observation(evidence, occupation),
        "history": evidence.history(soc),
        "hedges": evidence.hedges(soc, k=5),
        "match_supported": supported,
        "pathway_available": supported,
    }
