"""Domain and API models. The API serves exactly these; the frontend client is generated from them."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .metric import Metric
from .vocab import (
    BacktestTier,
    Confidence,
    InterestTag,
    Nation,
    PickTier,
    QualLevel,
    RouteKind,
    Subject,
)

STRICT = ConfigDict(extra="forbid")

# Units each career metric must use. ETL and mocks are checked against this.
METRIC_UNITS: dict[str, str] = {
    "pay_now": "GBP_per_year",          # ASHE median gross annual pay, all employees
    "pay_early": "GBP_per_year",        # ASHE median, age band 22-29 (verify band in Table 14)
    "pay_ceiling": "GBP_per_year",      # ASHE 75th percentile
    "pay_growth_10y": "pct",            # real growth of the median over ten years, CPIH-deflated
    "pay_spread": "ratio",              # p90 / p10
    "demand_trend": "pct_per_year",     # Theil-Sen slope of APS employment over five years
    "shortage": "flag",                 # 1.0 = Occupations in Demand level elevated or critical
    "ads_now": "count",                 # live Adzuna ad count
    "exposure_ilo": "index_0_1",        # ILO WP140 mean exposure score
    "exposure_inhouse": "index_0_1",    # M2 research estimate
    "wellbeing": "score_0_10",          # ONS APS, job group level only
    "stress": "rate_per_100k",          # HSE, job group level only
}


class CareerMetrics(BaseModel):
    model_config = STRICT
    pay_now: Metric
    pay_early: Metric
    pay_ceiling: Metric
    pay_growth_10y: Metric
    pay_spread: Metric
    demand_trend: Metric
    shortage: Metric
    ads_now: Metric
    exposure_ilo: Metric
    exposure_inhouse: Metric
    wellbeing: Metric
    stress: Metric


class Career(BaseModel):
    model_config = STRICT
    soc2020: str = Field(pattern=r"^\d{4}$")
    title: str
    aliases: list[str] = Field(default_factory=list, description="other names used to match a typed first idea")
    isco08: list[str] = Field(default_factory=list)
    esco_id: str | None = None
    interest_tags: list[InterestTag] = Field(default_factory=list)
    entry_subjects: list[Subject] = Field(default_factory=list, description="school subjects usually asked for")
    metrics: CareerMetrics


# ---------- profile ----------

class Qualification(BaseModel):
    model_config = STRICT
    subject: Subject
    level: QualLevel
    grade: str | None = Field(default=None, max_length=3)


class ProfileIn(BaseModel):
    model_config = STRICT
    interests: list[InterestTag] = Field(default_factory=list, max_length=12)
    free_text: str = Field(default="", max_length=300)
    qualifications: list[Qualification] = Field(default_factory=list, max_length=20)
    nation: Nation = "scotland"
    location: str = Field(default="Glasgow", max_length=60)
    automation_worry: float = Field(default=0.5, ge=0.0, le=1.0)


class ProfileOut(BaseModel):
    model_config = STRICT
    suggested_tags: list[InterestTag]
    tag_source: str = Field(description="matcher | keyword | none")
    interests: list[InterestTag] = Field(description="checklist interests merged with suggestions, user confirms")


# ---------- recommendations ----------

class ComponentScore(BaseModel):
    model_config = STRICT
    score: float | None = Field(ge=0, le=100, description="0-100 rank within the occupation set; None = missing")
    confidence: Confidence


class Components(BaseModel):
    model_config = STRICT
    fit: ComponentScore
    expected_return: ComponentScore
    market_risk: ComponentScore
    disruption_risk: ComponentScore
    risk: ComponentScore


class Pick(BaseModel):
    model_config = STRICT
    tier: PickTier
    career: Career
    components: Components
    vs_first_idea: dict[str, float | None] = Field(
        description="component name -> pick score minus first-idea score; None if either is missing")
    reasons: list[str] = Field(description="template sentences built only from numbers in this response")


class HedgeCandidate(BaseModel):
    """One related role from ML artefact hedge.json (M3)."""
    model_config = STRICT
    soc2020: str = Field(pattern=r"^\d{4}$")
    shared_skills: list[str]
    skill_overlap: float = Field(ge=0, le=1)


class Hedge(BaseModel):
    model_config = STRICT
    for_soc: str
    career: Career
    shared_skills: list[str]
    skill_overlap: float = Field(ge=0, le=1)
    risk_delta: float | None = Field(description="hedge risk minus top-pick risk; negative = safer")


class Explanation(BaseModel):
    model_config = STRICT
    text: str
    ai_written: bool
    cited_numbers: list[str] = Field(default_factory=list)


class Route(BaseModel):
    model_config = STRICT
    soc2020: str = Field(pattern=r"^\d{4}$")
    nation: Nation
    kind: RouteKind
    name: str
    provider: str | None = None
    entry_requirements: str
    url: str
    source: str
    verified_by: str = Field(min_length=1)


class RoadmapStep(BaseModel):
    model_config = STRICT
    order: int = Field(ge=1, le=3)
    title: str
    detail: str
    route: Route | None = None


class Roadmap(BaseModel):
    model_config = STRICT
    soc2020: str
    steps: list[RoadmapStep] = Field(max_length=3)
    this_month: str


class RecommendationRequest(BaseModel):
    model_config = STRICT
    profile: ProfileIn
    first_idea: str = Field(min_length=1, max_length=80, description="SOC 2020 code or free text, e.g. 'architect'")


class RecommendationOut(BaseModel):
    model_config = STRICT
    first_idea: Career | None
    first_idea_components: Components | None
    picks: list[Pick] = Field(max_length=3, description="0-3; fewer if not enough careers pass the fit gate")
    hedge: Hedge | None
    roadmap: Roadmap | None
    explanation: Explanation


# ---------- backtest ----------

class BacktestOccupation(BaseModel):
    model_config = STRICT
    soc: str
    title: str
    rating: float = Field(ge=0, le=100)
    pay_growth_5y: float | None
    employment_growth_5y: float | None
    confidence: Confidence


class BacktestTierResult(BaseModel):
    model_config = STRICT
    tier: BacktestTier
    occupations: list[BacktestOccupation]
    median_pay_growth_5y: float | None
    share_employment_decline: float | None = Field(ge=0, le=1)
    worst_case: BacktestOccupation | None


class BacktestYear(BaseModel):
    model_config = STRICT
    year: int = Field(ge=2010, le=2020)
    horizon_years: int = 5
    tiers: list[BacktestTierResult]
    caveats: list[str]
    source: str
