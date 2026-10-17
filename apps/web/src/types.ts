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
export type Career = {
  soc: string;
  title: string;
  summary: string;
  sector: string;
  family: string;
  skills: string[];
  metrics: Record<string, Metric>;
  history: HistoryPoint[];
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
};
export type Weights = { pay: number; interest: number; need: number };
export type Bootstrap = {
  careers: Career[];
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
  | "conversation"
  | "quiz"
  | "matches"
  | "overview"
  | "path"
  | "opportunities"
  | "guides"
  | "evidence";
