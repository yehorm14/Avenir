"""Production data boundary: missing reviewed catalogue inputs stay missing.

The canonical loader can fall back to the team's sample catalogue and routes.
The launched product uses genuine ML evidence while withholding those synthetic
catalogue metrics and unreviewed route examples from the decision engine.
"""

from pathfinder_ml import ML

from avenir_contracts import SourceStatus, load_data


def product_data():
    data = load_data()
    evidence = ML()
    for soc, career in data.careers.items():
        occupation = evidence.occupation(soc)
        # No reviewed catalogue observation exists for sample-only fields. An
        # absent input participates in the engine's confidence penalty; marking
        # it pending would incorrectly opt it out of that calculation.
        metrics = {key: metric for key, metric in career.metrics.items() if not metric.is_mock}
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
