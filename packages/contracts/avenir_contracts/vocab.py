"""Fixed vocabularies shared by every slice. Change only through a contract PR."""
from __future__ import annotations

from typing import Literal, get_args

InterestTag = Literal[
    "maths", "art", "design", "building", "computers", "science", "people",
    "fixing_things", "outdoors", "writing", "business", "health",
]
Subject = Literal[
    "maths", "english", "physics", "chemistry", "biology", "computing", "art",
    "design_technology", "graphic_communication", "geography", "business", "music",
]
QualLevel = Literal["national5", "higher", "advanced_higher", "gcse", "a_level"]
Nation = Literal["scotland", "england", "wales", "northern_ireland"]
PickTier = Literal["ambitious", "safe", "balanced"]
BacktestTier = Literal["top", "middle", "bottom"]
Confidence = Literal["high", "medium", "low"]
Granularity = Literal["occupation", "group", "estimate"]
SourceState = Literal["live", "snapshot", "mock", "missing"]
RouteKind = Literal["degree", "graduate_apprenticeship", "apprenticeship", "college"]

INTEREST_TAGS: tuple[str, ...] = get_args(InterestTag)
SUBJECTS: tuple[str, ...] = get_args(Subject)
CONFIDENCE_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
