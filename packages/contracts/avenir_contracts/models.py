"""API models. ML pass-through shapes mirror packages/ml/CONTRACTS.md v1.1 (Arsenii); the rest is ours.

STRICT models are request/response models we own. LOOSE models mirror ML artefacts and ignore
unknown keys, because ML minor versions may add fields (CONTRACTS.md section 7).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .metric import Metric
from .vocab import Confidence, MetricStatus, Nation, PickTier, QualLevel, RouteKind, Subject

STRICT = ConfigDict(extra="forbid")
LOOSE = ConfigDict(extra="ignore")
SOC = Field(pattern=r"^\d{4}$")


# ---------- careers (ML occupation + catalogue + live ads, joined on soc2020) ----------

class IscoShare(BaseModel):
    model_config = LOOSE
    code: str
    share: float


class Career(BaseModel):
    model_config = STRICT
    soc2020: str = SOC
    title: str = Field(description="friendly title: catalogue title, else ML short_title")
    official_title: str = Field(description="ONS SOC 2020 unit group title")
    aliases: list[str] = Field(default_factory=list, description="other names, for matching a typed first idea")
    description: str | None = None
    isco08: list[IscoShare] = Field(default_factory=list)
    entry_subjects: list[Subject] = Field(default_factory=list)
    metrics: dict[str, Metric] = Field(
        description="keys: vocab.ML_METRICS + vocab.CATALOGUE_METRICS; an absent key means missing")


class Tag(BaseModel):
    """One checklist interest, from ML fit.json."""
    model_config = LOOSE
    id: str
    label: str
    keywords: list[str] = Field(default_factory=list)


class TagMatch(BaseModel):
    model_config = LOOSE
    tag: str
    score: float = Field(ge=0, le=1)
    matched: list[str] = Field(default_factory=list)


class HistoryPoint(BaseModel):
    model_config = LOOSE
    year: int
    pay_median: float | None = None
    pay_median_real: float | None = None
    jobs_k: float | None = None
    flags: list[str] = Field(default_factory=list)


class Crisis(BaseModel):
    model_config = LOOSE
    key: str
    label: str
    window: str
    measure: str
    baseline_median: float | None = None
    baseline_real_pay_median: float | None = None
    status: MetricStatus | str = "preliminary"
    flags: list[str] = Field(default_factory=list)


class SourceInfo(BaseModel):
    model_config = LOOSE
    name: str
    publisher: str | None = None
    url: str | None = None
    licence: str | None = None
    coverage: str | None = None
    years: str | None = None
    status: str | None = None
    notes: str | None = None


# ---------- profile ----------

class Qualification(BaseModel):
    model_config = STRICT
    subject: Subject
    level: QualLevel
    grade: str | None = Field(default=None, max_length=3)


class ProfileIn(BaseModel):
    model_config = STRICT
    interests: list[str] = Field(default_factory=list, max_length=16, description="tag ids from GET /api/v1/tags")
    free_text: str = Field(default="", max_length=300)
    qualifications: list[Qualification] = Field(default_factory=list, max_length=20)
    nation: Nation = "scotland"
    location: str = Field(default="Glasgow", max_length=60)
    automation_worry: float = Field(default=0.5, ge=0.0, le=1.0)


class ProfileOut(BaseModel):
    model_config = STRICT
    suggested: list[TagMatch]
    tag_source: str = Field(description="keyword | matcher | llm | none")
    interests: list[str] = Field(description="checklist interests plus suggestions; the user confirms them")


# ---------- recommendations ----------

class ComponentScore(BaseModel):
    model_config = STRICT
    score: float | None = Field(ge=0, le=100, description="0-100 rank within the demo set; None = missing")
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
        description="component -> pick score minus first-idea score; None if either is missing")
    reasons: list[str] = Field(description="template sentences built only from numbers in this response")


class HedgeCandidate(BaseModel):
    """One related role from ML hedges.json (CONTRACTS.md 4.3)."""
    model_config = LOOSE
    soc2020: str = SOC
    title: str
    similarity: float = Field(ge=0, le=1)
    shared_skills: list[str] = Field(default_factory=list)
    why: str | None = None
    evidence: str | None = Field(default=None, description="title | estimate (ML v1.1)")
    status: MetricStatus | str = "mock"


class Hedge(BaseModel):
    model_config = STRICT
    for_soc: str
    career: Career
    similarity: float = Field(ge=0, le=1)
    shared_skills: list[str]
    why: str | None
    evidence: str | None = Field(default=None, description="title | estimate; show 'estimate' as a badge")
    risk_delta: float | None = Field(description="hedge risk minus top-pick risk; negative = safer")
    status: str


class Explanation(BaseModel):
    model_config = STRICT
    text: str
    ai_written: bool
    cited_numbers: list[str] = Field(default_factory=list)


class Route(BaseModel):
    model_config = STRICT
    soc2020: str = SOC
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
    notices: list[str] = Field(
        default_factory=list,
        description="FLAG_TEXT for every MUST_MENTION flag on a metric in this response; shown and cited by the LLM")
    explanation: Explanation


# ---------- track record (mirrors CONTRACTS.md 4.5) ----------

class Range(BaseModel):
    model_config = LOOSE
    median: float | None = None
    low: float | None = None
    high: float | None = None


class BacktestGroup(BaseModel):
    model_config = LOOSE
    key: str  # ambitious | safe | balanced | all
    label: str
    n: int | None = None
    real_pay_growth: Range | None = None
    jobs_growth: Range | None = None
    share_jobs_fell: float | None = None


class BacktestOccupation(BaseModel):
    model_config = LOOSE
    soc2020: str
    group_then: str | None = None
    real_pay_growth: float | None = None
    jobs_growth: float | None = None
    flags: list[str] = Field(default_factory=list)


class BacktestWindow(BaseModel):
    model_config = LOOSE
    base_year: int
    outcome_year: int
    horizon: int
    coding: str
    flags: list[str] = Field(default_factory=list)
    jobs_comparable: bool
    groups: list[BacktestGroup | None] = Field(description="a group is null while its rule isn't fixed")
    occupations: list[BacktestOccupation] = Field(default_factory=list)


class BacktestOut(BaseModel):
    model_config = STRICT
    window: BacktestWindow
    caveats: list[str]
    status: str = Field(description="file status from backtest.json: final | preliminary | mock")
