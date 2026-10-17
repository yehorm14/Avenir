"""Avenir shared contract v2.1: built on packages/ml/CONTRACTS.md v1.1 (Arsenii).

Owner: Yehor. Change only through a PR with "needs a contract change" ticked.
"""
from .catalogue import CatalogueEntry, CatalogueFile, RoutesFile
from .data import AvenirData, join_career, load_data
from .envelope import HTTP_STATUS, Envelope, ErrorBody, ErrorCode, ErrorDetail, Meta, SourceStatus
from .metric import MOCK_SOURCE, Metric
from .models import (
    BacktestGroup,
    BacktestOccupation,
    BacktestOut,
    BacktestWindow,
    Career,
    CareerRef,
    Components,
    ComponentScore,
    Crisis,
    Explanation,
    Hedge,
    HedgeCandidate,
    HistoryPoint,
    IscoShare,
    Pick,
    ProfileIn,
    ProfileOut,
    Qualification,
    Range,
    RecommendationOut,
    RecommendationRequest,
    Roadmap,
    RoadmapStep,
    Route,
    SourceInfo,
    Tag,
    TagMatch,
)
from .ports import AdsSource, ExplanationWriter, KeywordSuggester, SnapshotAds, TagSuggester, TemplateExplanation
from .vocab import CATALOGUE_METRICS, ML_METRICS

__all__ = [n for n in dir() if not n.startswith("_")]
