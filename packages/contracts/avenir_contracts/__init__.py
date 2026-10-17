"""Avenir shared contract: models, envelope, snapshot formats, adapter interfaces.

Owner: Yehor. Change only through a PR with "needs a contract change" ticked.
"""
from .envelope import HTTP_STATUS, Envelope, ErrorBody, ErrorCode, ErrorDetail, Meta, SourceStatus
from .metric import MOCK_SOURCE, Metric
from .models import (
    METRIC_UNITS,
    BacktestOccupation,
    BacktestTierResult,
    BacktestYear,
    Career,
    CareerMetrics,
    Components,
    ComponentScore,
    Explanation,
    Hedge,
    HedgeCandidate,
    Pick,
    ProfileIn,
    ProfileOut,
    Qualification,
    RecommendationOut,
    RecommendationRequest,
    Roadmap,
    RoadmapStep,
    Route,
)
from .ports import AdsSource, ExplanationWriter, NoTagSuggester, SnapshotAds, TagSuggester, TemplateExplanation
from .snapshots import BacktestFile, CareersFile, HedgeFile, MetricFile, RoutesFile, Snapshots, load_snapshots

__all__ = [n for n in dir() if not n.startswith("_")]
