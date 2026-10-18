export type Metric = {
  value: number | null;
  low: number | null;
  high: number | null;
  unit: string;
  as_of: string;
  source: string;
  confidence: string;
  flags: string[];
  status: string;
  note: string;
  extra: Record<string, unknown>;
};
export type HistoryPoint = {
  year: number;
  pay_median: number | null;
  pay_median_real: number | null;
  jobs_k: number | null;
  flags: string[];
};
export type EvidenceMetadata = {
  schema_version?: string;
  price_base?: string;
  price_label?: string;
};
export type Career = {
  soc: string;
  title: string;
  summary: string;
  sector: string;
  family: string;
  skills: string[];
  metrics: Record<string, Metric>;
  history: HistoryPoint[];
  evidence_metadata?: EvidenceMetadata;
  hedges: {
    soc2020: string;
    title: string;
    shared_skills: string[];
    status: string;
    evidence?: string;
  }[];
  score?: number;
  fit?: number;
  pay_score?: number;
  need_score?: number;
  reasons?: string[];
  sources?: { name: string; url: string }[];
  jobs_observation?: Metric;
  match_supported?: boolean;
  pathway_available?: boolean;
};
/** `GET /api/careers/{soc}/evidence-pack`. Every field is optional: the UI reads it defensively. */
export type EvidencePackMetric = Partial<Metric> & {
  label?: string;
  display?: string;
  caveats?: string[];
};
export type EvidencePackHedge = {
  soc?: string;
  title?: string;
  pay_display?: string;
  trend_display?: string;
  evidence?: string;
};
export type EvidencePackCrisis = {
  name?: string;
  period?: string;
  placebo_passed?: boolean;
  excluded_from_recommendations?: boolean;
  result?: string | null;
};
export type EvidencePackHistoryPoint = {
  year?: number;
  pay_real?: number | null;
  pay_nominal?: number | null;
  jobs_k?: number | null;
};
export type EvidencePackSource = {
  key?: string;
  name?: string;
  url?: string;
  as_of?: string;
  licence?: string;
};
export type EvidencePack = {
  title?: string;
  summary?: string;
  metrics?: Record<string, EvidencePackMetric | undefined>;
  history?: EvidencePackHistoryPoint[];
  history_note?: string;
  hedges?: EvidencePackHedge[];
  backtest?: { summary?: string; tiers?: unknown } | null;
  backtest_note?: string;
  crises?: EvidencePackCrisis[];
  fit_tags?: string[] | null;
  demand?: unknown;
  starting_pay?: unknown;
  sources?: EvidencePackSource[];
};
/** `POST /api/guide` provenance fields; all optional for older backends. */
export type GuideProvenanceFields = {
  mode?: "llm_grounded" | "prepared_demo" | string;
  ai_written?: boolean;
  model?: string | null;
  based_on?: string[];
  checks?: string;
  note?: string;
};
/** A link the API built for a guide reply: an in-app `#/...` route or a source URL. */
export type GuideLink = { label: string; href: string };
/** The career path the API builds from its own data when a question asks for one. */
export type GuidePath = {
  routes: { label: string; summary: string }[];
  courses: { label: string; href?: string }[];
  skills: string[];
  grades_note: string;
  first_step: string;
};
/** The quiz profile sent with a guide question (only when the backend accepts it). */
export type GuideProfile = {
  tags: string[];
  weights: Weights;
  selected: string[];
  free_text: string | null;
};
export type CareerSummary = {
  soc: string;
  title: string;
  sector: string;
  pay: Metric;
  jobs: Metric;
  match_supported: boolean;
};
export type Weights = { pay: number; interest: number; need: number };
export type Bootstrap = {
  careers: Career[];
  evidence_metadata?: EvidenceMetadata;
  tags: unknown;
  sources: unknown;
  backtest: Record<string, unknown>;
  crises: unknown[];
  data_status: {
    mode: string;
    fit: string;
    fit_method?: string;
    fit_evaluation?: { note?: string };
    hedges: string;
  };
};
export type Preferences = {
  routes: Record<string, "university" | "apprenticeship">;
  notes: Record<string, string>;
  discovery?: {
    mode: "known" | "explore";
    answers: Record<string, string>;
    step: number;
    tags?: string[];
    targetSoc?: string | null;
    referenceSoc?: string | null;
    summary?: string;
    notices?: string[];
  };
  answers: Record<string, number>;
  step: number;
  completed: boolean;
  selected: string[];
  weights: Weights;
  location: string;
  nation: string;
  checked: string[];
  saved: string[];
};
export type Page =
  | "discover"
  | "computer-science"
  | "finance"
  | "conversation"
  | "quiz"
  | "jobs"
  | "matches"
  | "overview"
  | "path"
  | "opportunities"
  | "guides"
  | "evidence";
