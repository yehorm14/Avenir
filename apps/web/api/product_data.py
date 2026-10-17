"""Production data boundary: missing reviewed catalogue inputs stay missing.

The canonical loader can fall back to the team's sample catalogue and routes.
The launched product uses genuine ML evidence while withholding those synthetic
catalogue metrics and unreviewed route examples from the decision engine.
"""

from pathfinder_ml import ML

from avenir_contracts import Metric, SourceStatus, load_data


def product_data():
    data = load_data()
    evidence = ML()
    input_sources = {"shortage": "oid_2025", "wellbeing": "aps_occupation", "stress": "hse_stress", "ads_now": "adzuna"}
    for soc, career in data.careers.items():
        occupation = evidence.occupation(soc)
        metrics = {
            key: Metric.missing(
                metric.unit,
                input_sources.get(key, metric.source),
                granularity=metric.granularity,
                note="Reviewed evidence for this input is not available; sample values are excluded.",
            )
            if metric.status == "mock"
            else metric
            for key, metric in career.metrics.items()
        }
        data.careers[soc] = career.model_copy(
            update={
                "title": (occupation.get("short_title") or occupation["title"]) if occupation else career.official_title,
                "description": None if (career.description or "").startswith("MOCK") else career.description,
                "aliases": [] if (career.description or "").startswith("MOCK") else career.aliases,
                "entry_subjects": [] if (career.description or "").startswith("MOCK") else career.entry_subjects,
                "metrics": metrics,
            }
        )
    for soc, routes in data.routes.items():
        data.routes[soc] = [route for route in routes if route.source != "mock" and route.verified_by != "MOCK"]
    data.statuses = [
        SourceStatus(name=status.name, status="missing", region=status.region)
        if status.name in {"catalogue", "routes"} and status.status == "mock"
        else status
        for status in data.statuses
    ]
    return data
