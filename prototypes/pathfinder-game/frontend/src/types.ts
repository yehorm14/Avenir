// Mirrors backend/app/models.py (the OpenAPI contract at /openapi.json).

export type Letter = "R" | "I" | "A" | "S" | "E" | "C";
export type ComponentKey = "interest" | "demand_future" | "demand_now" | "pay" | "ai_resilience" | "head_start";

export type Weights = Record<ComponentKey, number>;

export interface QuizItem {
  id: string;
  type: Letter;
  text: string;
}

export interface Quiz {
  scale: string[];
  items: QuizItem[];
  subjects: string[];
  skills: string[];
  regions: string[];
  note: string;
}

export interface Component {
  key: ComponentKey;
  label: string;
  value: number | null;
  weight: number;
  effective_weight: number;
  contribution: number;
  detail: string;
  source_id: string;
}

export interface Confidence {
  level: "High" | "Medium" | "Low";
  score: number;
  reasons: string[];
}

export interface Scenario {
  id: string;
  label: string;
  description: string;
  score: number;
  delta: number;
  rank: number | null;
  holds: boolean;
  hedge_score: number | null;
}

export interface StressTest {
  baseline: number;
  worst: number;
  holds: number;
  total: number;
  keep_within: number;
  scenarios: Scenario[];
  hedge_baseline: number | null;
}

export interface Hedge {
  soc: string;
  title: string;
  sector: string | null;
  similarity: number;
  interest_fit: number;
  score: number;
  shared: string[];
  diversifies: string[];
}

export interface KeyFigures {
  pay_median: number | null;
  pay_p25: number | null;
  pay_p75: number | null;
  growth_2035_pct: number | null;
  ssv_latest: number | null;
  ai_exposure: number | null;
  region_multiplier: number;
}

export interface CareerSummary {
  soc: string;
  title: string;
  soc_title: string;
  summary: string;
  score: number;
  rank: number;
  interest_fit: number;
  components: Component[];
  figures: KeyFigures;
  trade_off: string;
  missing: string[];
  sector: string | null;
  priority: boolean | null;
  family: string;
  degree_role: string;
  degrees: string[];
  confidence: Confidence | null;
  stress: StressTest | null;
  hedge: Hedge | null;
}

export interface MatchResponse {
  profile: Record<Letter, number>;
  code: string;
  flat_profile: boolean;
  region: string;
  results: CareerSummary[];
  more: CareerSummary[];
  considered: number;
  hidden_low_fit: number;
  fit_threshold: number;
  weights: Weights;
  notes: string[];
}

export interface MatchRequest {
  answers: Record<string, number>;
  subjects: string[];
  skills: string[];
  region: string;
  weights: Weights;
  limit?: number;
}

export interface Route {
  type: string;
  name: string;
  level: string | null;
  detail: string | null;
  nation: string;
  source_id: string;
}

export interface Course {
  subject: string;
  qualification: string;
  median_earnings_15m: number | null;
  source_id: string;
}

export interface Source {
  id: string;
  name: string;
  publisher: string;
  url: string | null;
  licence: string;
  gives: string;
  coverage: string;
  scored: boolean;
  mode: string;
  edition: string | null;
}

export interface TrackPoint {
  year: number;
  signal_pct: number;
  outcome_pct: number | null;
  employment_change_pct: number | null;
}

export interface CareerDetail {
  soc: string;
  title: string;
  soc_title: string;
  summary: string;
  study_level: string;
  routes: Route[];
  courses: Course[];
  skills: string[];
  first_step: string;
  onet_code: string | null;
  onet_title: string | null;
  onet_url: string | null;
  riasec: Record<Letter, number>;
  figures: {
    growth_2035_pct: number | null;
    priority: boolean | null;
    sector: string | null;
    ssv_latest: number | null;
    ssv_previous: number | null;
    latest_edition: string;
    previous_edition: string;
    pay_median: number | null;
    pay_p25: number | null;
    pay_p75: number | null;
    pay_quality: string | null;
    pay_edition: string | null;
    ai_exposure: number | null;
    ai_tasks: { task: string; score: number }[];
  };
  soc2010: string | null;
  bridge: string | null;
  track: TrackPoint[];
  track_synthetic: boolean;
  sources: Source[];
  notes: string[];
}

export interface ChangeItem {
  soc: string;
  title: string;
  previous: number | null;
  latest: number | null;
  delta: number | null;
  direction: "up" | "down" | "same" | "no data";
  message: string;
  pay_previous: number | null;
  pay_latest: number | null;
  pay_message: string;
  growth_2035_pct: number | null;
  priority: boolean | null;
}

export interface ChangesResponse {
  latest_edition: string;
  previous_edition: string;
  pay_edition: string | null;
  items: ChangeItem[];
}

export interface Evidence {
  id: string;
  text: string;
  source_id: string;
  topic: string;
}

export interface ExplainResponse {
  answer: string;
  cited: string[];
  evidence: Evidence[];
  mode: "ai" | "template";
  fallback_reason: string | null;
}

export interface YearMetrics {
  year: number;
  outcome_year: number;
  n: number;
  spearman: number | null;
  hit_rate: number | null;
  top_third_change: number | null;
  bottom_third_change: number | null;
  pay_spearman: number | null;
}

export interface BacktestSummary {
  synthetic: boolean;
  note: string;
  horizon_years: number;
  exclude_bridged: boolean;
  years: YearMetrics[];
  pooled_n: number;
  mean_spearman: number | null;
  pooled_hit_rate: number | null;
  verdict: string;
  caveats: string[];
}

export interface ReplayRow {
  soc: string;
  title: string;
  sector: string | null;
  signal: number;
  ssv: number | null;
  projection_10y_pct: number | null;
  employment_change_pct: number | null;
  pay_change_pct: number | null;
  beat_median: boolean | null;
  bridge: string;
}

export interface Replay {
  year: number;
  outcome_year: number;
  synthetic: boolean;
  metrics: YearMetrics;
  median_change: number | null;
  top: ReplayRow[];
  bottom: ReplayRow[];
}

export interface DiscoverResponse {
  method: string;
  hits: { soc: string; title: string; score: number; matched: string[] }[];
}

export interface DiscoverEval {
  note: string;
  results: { name: string; n: number; accuracy_at_1: number; accuracy_at_3: number }[];
}

export interface TrustReport {
  validator_cases: number;
  validator_passed: number;
  routing_cases: number;
  routing_passed: number;
  cases: { id: string; kind: string; input: string; expected: string; got: string; passed: boolean }[];
}

export interface MarketRow {
  soc: string;
  title: string;
  sector: string | null;
  priority: boolean | null;
  growth_2035_pct: number | null;
  ssv_latest: number | null;
  pay_median: number | null;
  ai_exposure: number | null;
  region_multiplier: number;
  data_confidence: "High" | "Medium" | "Low";
  riasec_code: string;
}

export interface Market {
  region: string;
  regions: string[];
  rows: MarketRow[];
}

export interface University {
  name: string;
  nation: string;
  kind: "university" | "college";
  home: boolean;
}

export interface DegreeOption {
  subject: string;
  qualification: string;
  median_earnings_15m: number | null;
  doors: string[];
  about: string;
  builds: string[];
  best_if: string;
  search: string;
  universities: University[];
}

export interface SkillItem {
  skill: string;
  how: string;
  proof: string;
}

export interface Link {
  name: string;
  url: string;
  nation: string | null;
}

export interface TimelineStage {
  stage: string;
  title: string;
  items: string[];
}

export interface PathPlan {
  soc: string;
  title: string;
  summary: string;
  study_level: string;
  first_step: string;
  nation: string;
  field: string;
  degree_role: { level: "required" | "preferred" | "flexible" | "optional"; label: string; tone: string; note: string };
  routes: { id: "university" | "apprenticeship"; label: string; available: boolean; summary: string }[];
  default_route: "university" | "apprenticeship";
  degrees: DegreeOption[];
  safe_path: SafePath | null;
  apprenticeship: { summary: string; employers: string[]; routes: Route[]; finders: Link[] } | null;
  school_subjects: string[];
  hard_skills: SkillItem[];
  soft_skills: SkillItem[];
  societies: { name: string; what: string; builds: string[] }[];
  competitions: { name: string; what: string }[];
  alumni: { why: string; find: string[]; who: string[]; tips: string[]; questions: string[]; template: string; template_apprenticeship: string };
  experience: string;
  experience_detail: string;
  timelines: Record<string, TimelineStage[]>;
  funding: Link;
  tools: Link[];
  demo_note: string;
}

export interface GameCandidate {
  soc: string;
  title: string;
  sector: string | null;
  ssv: number | null;
  projection_10y_pct: number | null;
  bridge: string;
}

export interface GameRound {
  year: number;
  outcome_year: number;
  seed: number;
  synthetic: boolean;
  picks_needed: number;
  candidates: GameCandidate[];
}

export interface GameReveal {
  year: number;
  outcome_year: number;
  synthetic: boolean;
  rows: {
    soc: string; title: string; sector: string | null; signal: number; employment_change_pct: number;
    beat_median: boolean; picked_by_you: boolean; picked_by_algorithm: boolean; best: boolean;
  }[];
  median_change: number;
  you: { avg_change: number; beat_median: number };
  algorithm: { avg_change: number; beat_median: number };
  best: { avg_change: number; beat_median: number };
  result: "win" | "tie" | "lose";
  verdict: string;
  note: string;
}

export interface SafePath {
  headline: string;
  most_direct: { subject: string; doors: string[] };
  most_doors: { subject: string; doors: string[] };
  how_to_specialise: string[];
  note: string;
}

export interface Opportunity {
  id: string;
  title: string;
  org: string;
  kind: string;
  stage: string[];
  nations: string[];
  fields: string[];
  format: string;
  cost: string;
  when: string;
  open_months: number[];
  rolling: boolean;
  url: string | null;
  why: string;
  opens: string | null;
  deadline: string | null;
  closing_soon: boolean;
  status: "open" | "soon" | "rolling" | "later";
  matches: string[];
}

export interface Radar {
  today: string;
  month: number;
  stage: string;
  nation: string;
  fields: { id: string; label: string }[];
  all_fields: { id: string; label: string }[];
  digest: { headline: string; open: number; soon: number; rolling: number; later: number; highlights: string[] };
  items: Opportunity[];
  live: boolean;
  note: string;
}

export interface Trend {
  id: string;
  name: string;
  heat: string;
  buzz: string;
  reality: string;
  specialist_name: string;
  specialist_level: string;
  specialist_doors: string;
  safer: { subject: string; why: string; doors: string[] }[];
  fade: string;
  how: string[];
  related: { soc: string; title: string }[];
  evidence_note: string;
}

export interface Band {
  p25: number;
  median: number;
  p75: number;
}

export interface PayPoint {
  year: number;
  nominal: Band;
  real: Band;
  cpi: number;
}

export interface PaySummary {
  first_year: number;
  last_year: number;
  median_then: number;
  median_then_today: number;
  median_now: number;
  nominal_change_pct: number;
  real_change_pct: number;
  verdict: "Beat inflation" | "Kept pace" | "Fell behind";
  spread_now: number;
  spread_then: number;
  spread_change_pct: number;
  sentence: string;
}

export interface PayCareer {
  soc: string;
  title: string;
  quality: string | null;
  series: PayPoint[];
  summary: PaySummary | null;
}

export interface PayResponse {
  base_year: number;
  first_year: number;
  last_year: number;
  cpi: { year: number; index: number; change_pct: number | null }[];
  careers: PayCareer[];
  synthetic: boolean;
  note: string;
}

export interface Inflation {
  amount: number;
  from_year: number;
  to_year: number;
  equivalent: number;
  change_pct: number;
  cpi_from: number;
  cpi_to: number;
  sentence: string;
  note: string;
}
