"""API contract. FastAPI publishes these as the OpenAPI schema at /openapi.json."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiasecLetter = Literal["R", "I", "A", "S", "E", "C"]
ComponentKey = Literal["interest", "demand_future", "demand_now", "pay", "ai_resilience", "head_start"]


class Weights(BaseModel):
    interest: float = Field(0.30, ge=0, le=1)
    demand_future: float = Field(0.20, ge=0, le=1)
    demand_now: float = Field(0.15, ge=0, le=1)
    pay: float = Field(0.15, ge=0, le=1)
    ai_resilience: float = Field(0.10, ge=0, le=1)
    head_start: float = Field(0.10, ge=0, le=1)


class QuizItem(BaseModel):
    id: str
    type: RiasecLetter
    text: str


class Quiz(BaseModel):
    scale: list[str]
    items: list[QuizItem]
    subjects: list[str]
    skills: list[str]
    regions: list[str]
    note: str


class MatchRequest(BaseModel):
    answers: dict[str, int] = Field(
        default_factory=dict, description="Quiz item id to answer, 1 (strongly dislike) to 5 (strongly like)"
    )
    profile: dict[RiasecLetter, float] | None = Field(None, description="Optional RIASEC profile (0 to 1) instead of answers")
    subjects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    region: str = Field("UK-wide", description="UK nation or English region for the regional lens")
    weights: Weights = Field(default_factory=Weights)
    limit: int = Field(3, ge=1, le=5, description="Number of picks (the plan says three)")


class Component(BaseModel):
    key: ComponentKey
    label: str
    value: float | None = Field(description="0 to 1, or null when there is no data")
    weight: float = Field(description="Weight the user asked for, normalised to sum to 1")
    effective_weight: float = Field(description="Weight actually used after skipping missing data")
    contribution: float = Field(description="Points (0 to 100) this signal adds to the score")
    detail: str
    source_id: str


class Confidence(BaseModel):
    level: Literal["High", "Medium", "Low"]
    score: float
    reasons: list[str]


class Scenario(BaseModel):
    id: str
    label: str
    description: str
    score: float
    delta: float
    rank: int | None = Field(description="Rank among careers that fit you, or null if it would be hidden")
    holds: bool
    hedge_score: float | None = Field(None, description="Your backup career's score in the same scenario")


class StressTest(BaseModel):
    baseline: float
    worst: float
    holds: int
    total: int
    keep_within: int
    scenarios: list[Scenario]
    hedge_baseline: float | None = None


class Hedge(BaseModel):
    soc: str
    title: str
    sector: str | None
    similarity: float
    interest_fit: float
    score: float
    shared: list[str]
    diversifies: list[str]


class KeyFigures(BaseModel):
    pay_median: float | None
    pay_p25: float | None
    pay_p75: float | None
    growth_2035_pct: float | None
    ssv_latest: float | None
    ai_exposure: float | None
    region_multiplier: float


class CareerSummary(BaseModel):
    soc: str
    title: str
    soc_title: str
    summary: str
    score: float = Field(description="0 to 100")
    rank: int
    interest_fit: float
    components: list[Component]
    figures: KeyFigures
    trade_off: str
    missing: list[str]
    sector: str | None
    priority: bool | None
    family: str = Field("", description="The career group (field) this belongs to")
    degree_role: str = Field("", description="How much the degree matters for this career")
    degrees: list[str] = Field(default_factory=list, description="Degree subjects to consider")
    confidence: Confidence | None = None
    stress: StressTest | None = None
    hedge: Hedge | None = None


class MatchResponse(BaseModel):
    profile: dict[RiasecLetter, float]
    code: str = Field(description="Your top three interest letters, e.g. ISR")
    flat_profile: bool
    region: str
    results: list[CareerSummary]
    more: list[CareerSummary] = Field(description="The next two matches, without stress test or hedge")
    considered: int
    hidden_low_fit: int
    fit_threshold: float
    weights: Weights
    notes: list[str]


class Route(BaseModel):
    type: str
    name: str
    level: str | None = None
    detail: str | None = None
    nation: str = "England"
    source_id: str


class Course(BaseModel):
    subject: str
    qualification: str
    median_earnings_15m: int | None
    source_id: str


class Task(BaseModel):
    task: str
    score: float


class Figures(BaseModel):
    growth_2035_pct: float | None
    priority: bool | None
    sector: str | None
    ssv_latest: float | None
    ssv_previous: float | None
    latest_edition: str
    previous_edition: str
    pay_median: float | None
    pay_p25: float | None
    pay_p75: float | None
    pay_quality: str | None
    pay_edition: str | None
    ai_exposure: float | None
    ai_tasks: list[Task]


class SourceOut(BaseModel):
    id: str
    name: str
    publisher: str
    url: str | None
    licence: str
    gives: str
    coverage: str
    scored: bool
    mode: str
    edition: str | None


class TrackPoint(BaseModel):
    year: int
    signal_pct: float = Field(description="Percentile of our demand signal that year (0 to 100)")
    outcome_pct: float | None = Field(description="Percentile of employment change 4 years later")
    employment_change_pct: float | None


class CareerDetail(BaseModel):
    soc: str
    title: str
    soc_title: str
    summary: str
    study_level: str
    routes: list[Route]
    courses: list[Course]
    skills: list[str]
    first_step: str
    onet_code: str | None
    onet_title: str | None
    onet_url: str | None
    riasec: dict[RiasecLetter, float]
    figures: Figures
    soc2010: str | None
    bridge: str | None
    track: list[TrackPoint]
    track_synthetic: bool
    sources: list[SourceOut]
    notes: list[str]


class ChangeItem(BaseModel):
    soc: str
    title: str
    previous: float | None
    latest: float | None
    delta: float | None
    direction: Literal["up", "down", "same", "no data"]
    message: str
    pay_previous: float | None
    pay_latest: float | None
    pay_message: str
    growth_2035_pct: float | None
    priority: bool | None


class ChangesResponse(BaseModel):
    latest_edition: str
    previous_edition: str
    pay_edition: str | None
    items: list[ChangeItem]


class AnalyseRequest(MatchRequest):
    soc: str


class ExplainRequest(MatchRequest):
    soc: str
    question: str = Field(min_length=1, max_length=300)


class Evidence(BaseModel):
    id: str
    text: str
    source_id: str
    topic: str


class ExplainResponse(BaseModel):
    answer: str
    cited: list[str]
    evidence: list[Evidence]
    mode: Literal["ai", "template"]
    fallback_reason: str | None = None


# ---------------------------------------------------------------- proof ----


class YearMetrics(BaseModel):
    year: int
    outcome_year: int
    n: int
    spearman: float | None = Field(description="Rank correlation between our signal and employment change")
    hit_rate: float | None = Field(description="Share of our top third that beat the median outcome (chance = 0.5)")
    top_third_change: float | None
    bottom_third_change: float | None
    pay_spearman: float | None


class BacktestSummary(BaseModel):
    synthetic: bool
    note: str
    horizon_years: int
    exclude_bridged: bool
    years: list[YearMetrics]
    pooled_n: int
    mean_spearman: float | None
    pooled_hit_rate: float | None
    verdict: str
    caveats: list[str]


class ReplayRow(BaseModel):
    soc: str
    title: str
    sector: str | None
    signal: float
    ssv: float | None
    projection_10y_pct: float | None
    employment_change_pct: float | None
    pay_change_pct: float | None
    beat_median: bool | None
    bridge: str


class Replay(BaseModel):
    year: int
    outcome_year: int
    synthetic: bool
    metrics: YearMetrics
    median_change: float | None
    top: list[ReplayRow]
    bottom: list[ReplayRow]


# ------------------------------------------------------------- discovery ----


class DiscoverRequest(BaseModel):
    text: str = Field(min_length=3, max_length=400)


class DiscoverHit(BaseModel):
    soc: str
    title: str
    score: float
    matched: list[str]


class DiscoverResponse(BaseModel):
    method: str
    hits: list[DiscoverHit]


class EvalResult(BaseModel):
    name: str
    n: int
    accuracy_at_1: float
    accuracy_at_3: float


class DiscoverEval(BaseModel):
    note: str
    results: list[EvalResult]


# ----------------------------------------------------------------- trust ----


class EvalCase(BaseModel):
    id: str
    kind: str
    input: str
    expected: str
    got: str
    passed: bool


class TrustReport(BaseModel):
    validator_cases: int
    validator_passed: int
    routing_cases: int
    routing_passed: int
    cases: list[EvalCase]


# --------------------------------------------------------------- adviser ----


class MarketRow(BaseModel):
    soc: str
    title: str
    sector: str | None
    priority: bool | None
    growth_2035_pct: float | None
    ssv_latest: float | None
    pay_median: float | None
    ai_exposure: float | None
    region_multiplier: float
    data_confidence: Literal["High", "Medium", "Low"]
    riasec_code: str


class Market(BaseModel):
    region: str
    regions: list[str]
    rows: list[MarketRow]


# ------------------------------------------------------------ path plan ----


class University(BaseModel):
    name: str
    nation: str
    kind: Literal["university", "college"] = "university"
    home: bool = Field(False, description="In the nation the user chose")


class DegreeOption(BaseModel):
    subject: str
    qualification: str
    median_earnings_15m: int | None
    doors: list[str] = Field(default_factory=list, description="Careers in our list that this degree leads to")
    about: str
    builds: list[str]
    best_if: str
    search: str
    universities: list[University]


class SkillItem(BaseModel):
    skill: str
    how: str
    proof: str


class Society(BaseModel):
    name: str
    what: str
    builds: list[str]


class Competition(BaseModel):
    name: str
    what: str


class Link(BaseModel):
    name: str
    url: str
    nation: str | None = None


class AlumniKit(BaseModel):
    why: str
    find: list[str]
    who: list[str]
    tips: list[str]
    questions: list[str]
    template: str
    template_apprenticeship: str


class TimelineStage(BaseModel):
    stage: str
    title: str
    items: list[str]


class RouteChoice(BaseModel):
    id: Literal["university", "apprenticeship"]
    label: str
    available: bool
    summary: str


class DegreeRole(BaseModel):
    level: Literal["required", "preferred", "flexible", "optional"]
    label: str
    tone: str
    note: str


class ApprenticeshipRoute(BaseModel):
    summary: str
    employers: list[str]
    routes: list[Route]
    finders: list[Link]


class CareerRef(BaseModel):
    soc: str
    title: str


class SafeChoice(BaseModel):
    subject: str
    doors: list[str]


class SafePath(BaseModel):
    headline: str
    most_direct: SafeChoice
    most_doors: SafeChoice
    how_to_specialise: list[str]
    note: str


class PathPlan(BaseModel):
    soc: str
    title: str
    summary: str
    study_level: str
    first_step: str
    nation: str
    field: str
    degree_role: DegreeRole
    routes: list[RouteChoice]
    default_route: Literal["university", "apprenticeship"]
    degrees: list[DegreeOption]
    safe_path: SafePath | None = None
    apprenticeship: ApprenticeshipRoute | None
    school_subjects: list[str]
    hard_skills: list[SkillItem]
    soft_skills: list[SkillItem]
    societies: list[Society]
    competitions: list[Competition]
    alumni: AlumniKit
    experience: str
    experience_detail: str
    timelines: dict[str, list[TimelineStage]]
    funding: Link
    tools: list[Link]
    demo_note: str


# ------------------------------------------------------------ arcade game ----


class GameCandidate(BaseModel):
    soc: str
    title: str
    sector: str | None
    ssv: float | None
    projection_10y_pct: float | None
    bridge: str


class GameRound(BaseModel):
    year: int
    outcome_year: int
    seed: int
    synthetic: bool
    picks_needed: int
    candidates: list[GameCandidate]


class GameRequest(BaseModel):
    year: int
    seed: int = Field(ge=0, le=10_000_000)
    picks: list[str] = Field(min_length=3, max_length=3)


class GameRow(BaseModel):
    soc: str
    title: str
    sector: str | None
    signal: float
    employment_change_pct: float
    beat_median: bool
    picked_by_you: bool
    picked_by_algorithm: bool
    best: bool


class GameSide(BaseModel):
    avg_change: float
    beat_median: int


class GameReveal(BaseModel):
    year: int
    outcome_year: int
    synthetic: bool
    rows: list[GameRow]
    median_change: float
    you: GameSide
    algorithm: GameSide
    best: GameSide
    result: Literal["win", "tie", "lose"]
    verdict: str
    note: str


# -------------------------------------------------------------- radar ----

OppStatus = Literal["open", "soon", "rolling", "later"]


class Opportunity(BaseModel):
    id: str
    title: str
    org: str
    kind: str
    stage: list[str]
    nations: list[str]
    fields: list[str]
    format: str
    cost: str
    when: str
    open_months: list[int]
    rolling: bool
    url: str | None
    why: str
    opens: str | None = Field(None, description="ISO date, only when a live feed supplies one")
    deadline: str | None = Field(None, description="ISO date, only when a live feed supplies one")
    closing_soon: bool = False
    status: OppStatus
    matches: list[str] = Field(description="Your fields this opportunity matches")


class FieldInfo(BaseModel):
    id: str
    label: str


class Digest(BaseModel):
    headline: str
    open: int
    soon: int
    rolling: int
    later: int
    highlights: list[str]


class Radar(BaseModel):
    today: str
    month: int
    stage: str
    nation: str
    fields: list[FieldInfo]
    all_fields: list[FieldInfo]
    digest: Digest
    items: list[Opportunity]
    live: bool = Field(description="True only when dated live feeds are connected")
    note: str


class TrendChoice(BaseModel):
    subject: str
    why: str
    doors: list[str]


class Trend(BaseModel):
    id: str
    name: str
    heat: str
    buzz: str
    reality: str
    specialist_name: str
    specialist_level: str
    specialist_doors: str
    safer: list[TrendChoice]
    fade: str
    how: list[str]
    related: list[CareerRef]
    evidence_note: str


# ---------------------------------------------------------------- pay ----


class Band(BaseModel):
    p25: float
    median: float
    p75: float


class PayPoint(BaseModel):
    year: int
    nominal: Band = Field(description="Pounds of that year")
    real: Band = Field(description="Pounds in the base year's prices, after CPI")
    cpi: float


class PaySummary(BaseModel):
    first_year: int
    last_year: int
    median_then: float = Field(description="Median in pounds of the first year")
    median_then_today: float = Field(description="That same median, in last-year prices")
    median_now: float
    nominal_change_pct: float
    real_change_pct: float
    verdict: Literal["Beat inflation", "Kept pace", "Fell behind"]
    spread_now: float = Field(description="Middle half: p75 minus p25, in last-year pounds")
    spread_then: float = Field(description="The same, for the first year, in last-year prices")
    spread_change_pct: float
    sentence: str


class PayCareer(BaseModel):
    soc: str
    title: str
    quality: str | None
    series: list[PayPoint]
    summary: PaySummary | None


class CpiPoint(BaseModel):
    year: int
    index: float
    change_pct: float | None


class PayResponse(BaseModel):
    base_year: int
    first_year: int
    last_year: int
    cpi: list[CpiPoint]
    careers: list[PayCareer]
    synthetic: bool
    note: str


class Inflation(BaseModel):
    amount: float
    from_year: int
    to_year: int
    equivalent: float
    change_pct: float
    cpi_from: float
    cpi_to: float
    sentence: str
    note: str
