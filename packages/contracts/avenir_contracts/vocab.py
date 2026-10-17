"""Fixed vocabularies shared by every slice. Change only through a contract PR.

Interest tags are NOT fixed here: they come from the ML artefact fit.json (`pathfinder_ml.ML.tags()`).
"""
from __future__ import annotations

from typing import Literal, get_args

Subject = Literal[
    "maths", "english", "physics", "chemistry", "biology", "computing", "art",
    "design_technology", "graphic_communication", "geography", "business", "music",
]
QualLevel = Literal["national5", "higher", "advanced_higher", "gcse", "a_level"]
Nation = Literal["scotland", "england", "wales", "northern_ireland"]
PickTier = Literal["ambitious", "safe", "balanced"]
Confidence = Literal["high", "medium", "low"]
MetricStatus = Literal["final", "preliminary", "mock", "pending"]  # packages/ml/CONTRACTS.md 2.2
SourceState = Literal["live", "snapshot", "mock", "missing"]
RouteKind = Literal["degree", "graduate_apprenticeship", "apprenticeship", "college"]

SUBJECTS: tuple[str, ...] = get_args(Subject)
CONFIDENCE_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2}

# Metric keys. ML ones are defined in packages/ml/CONTRACTS.md section 4.1 (Arsenii).
ML_METRICS: tuple[str, ...] = (
    "pay_median", "pay_p10", "pay_p90", "real_pay_change_10y", "jobs", "demand_trend",
    "demand_trend_2011_19", "exposure", "exposure_uk", "resilience_covid",
    "resilience_cost_of_living", "resilience_tech_slump", "resilience_2008",
)
# Catalogue ones come from Yehor's ETL; ads_now is overlaid live by the API.
CATALOGUE_METRICS: dict[str, str] = {
    "shortage": "flag",            # 1 = Occupations in Demand level elevated or critical (UK, some indicators GB)
    "wellbeing": "score 0-10",     # ONS APS by major group: never shown as occupation-level
    "stress": "rate per 100k",     # HSE by major group: never shown as occupation-level
    "ads_now": "count",            # Adzuna, live or snapshot
}
