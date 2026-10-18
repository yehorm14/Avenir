/** View model for the "Statistics for this role" panel.
 * Every number comes from the evidence-pack payload; nothing is estimated here.
 * The functions are pure so the test runner can load them without a DOM.
 */
import type {
  EvidencePack,
  EvidencePackCrisis,
  EvidencePackHedge,
  EvidencePackHistoryPoint,
  EvidencePackSource,
} from "./types";

export type HedgeView = {
  soc: string;
  title: string;
  pay: string | null;
  trend: string | null;
  evidence: string | null;
};
export type CrisisView = {
  name: string;
  period: string;
  result: string;
  placeboPassed: boolean | null;
  excluded: boolean;
};
export type HistoryRow = {
  year: number;
  payReal: string;
  payNominal: string;
  jobs: string;
};
export type SourceView = {
  key: string;
  name: string;
  url: string | null;
  asOf: string | null;
  licence: string | null;
};
export type EvidencePackView = {
  title: string | null;
  summary: string | null;
  hedges: HedgeView[];
  backtest: { summary: string | null; note: string | null };
  crises: CrisisView[];
  fitTags: string[] | null;
  history: HistoryRow[];
  historyNote: string | null;
  sources: SourceView[];
  caveats: string[];
  metricLines: { label: string; display: string; provenance: string }[];
};

export const EXCLUDED_CRISIS_LABEL = "Failed placebo check: excluded";
export const BACKTEST_RULE_LINE =
  "Simple rules evaluated later, not a personalised forecast.";
export const FIT_TAGS_LINE = "from the supplied affinity model (20 roles)";
export const HEDGE_INTRO =
  "Careers that held up when this one dipped, in the historical data";

const text = (value: unknown): string | null =>
  typeof value === "string" && value.trim() ? value.trim() : null;
const list = <T>(value: unknown): T[] => (Array.isArray(value) ? value : []);
/** A display string, or the `display` field of a metric object. */
const shown = (value: unknown): string | null =>
  typeof value === "string"
    ? text(value)
    : value && typeof value === "object"
      ? text((value as Record<string, unknown>).display)
      : null;
const SOURCE_SHORT: Record<string, string> = {
  ons_ashe_t14: "ONS ASHE",
  ilo_wp140: "ILO WP140",
  ons_online_job_adverts: "ONS job adverts",
  cpih: "ONS CPIH",
};
const sourceShort = (value: unknown): string | null => {
  const s = text(value);
  return s ? (SOURCE_SHORT[s] ?? s) : null;
};
const record = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;

export function gbp(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? `£${Math.round(value).toLocaleString("en-GB")}`
    : "Not available";
}
export function jobsFromThousands(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.round(value * 1000).toLocaleString("en-GB")
    : "Not available";
}

function hedgeView(raw: EvidencePackHedge, index: number): HedgeView | null {
  const title = text(raw?.title);
  if (!title) return null;
  return {
    soc: text(raw.soc) ?? `hedge-${index}`,
    title,
    pay:
      text(raw.pay_display) ??
      (shown((raw as Record<string, unknown>).pay)
        ? `${shown((raw as Record<string, unknown>).pay)} median pay`
        : null),
    trend:
      text(raw.trend_display) ??
      (shown((raw as Record<string, unknown>).trend)
        ? `${shown((raw as Record<string, unknown>).trend)} a year vs typical`
        : null),
    evidence: text((raw as Record<string, unknown>).why) ?? text(raw.evidence),
  };
}

function crisisView(raw: EvidencePackCrisis, index: number): CrisisView | null {
  const name = text(raw?.name);
  if (!name) return null;
  const excluded =
    raw.excluded_from_recommendations === true || raw.placebo_passed === false;
  return {
    name,
    period: text(raw.period) ?? `crisis-${index}`,
    result: shown(raw.result) ?? "No result supplied",
    placeboPassed:
      typeof raw.placebo_passed === "boolean" ? raw.placebo_passed : null,
    excluded,
  };
}

function historyRow(raw: EvidencePackHistoryPoint): HistoryRow | null {
  if (typeof raw?.year !== "number" || !Number.isFinite(raw.year)) return null;
  return {
    year: raw.year,
    payReal: gbp(
      raw.pay_real ?? (raw as Record<string, unknown>).pay_median_real,
    ),
    payNominal: gbp(
      raw.pay_nominal ?? (raw as Record<string, unknown>).pay_median_nominal,
    ),
    jobs: jobsFromThousands(raw.jobs_k),
  };
}

function sourceView(raw: EvidencePackSource, index: number): SourceView | null {
  const name = text(raw?.name) ?? text(raw?.key);
  if (!name) return null;
  const url = text(raw.url);
  return {
    key: text(raw.key) ?? `source-${index}`,
    name,
    url: url && /^https?:\/\//i.test(url) ? url : null,
    asOf: text(raw.as_of),
    licence: text(raw.licence),
  };
}

/** "source · year · status" line for a number, matching the dashboard convention. */
export function provenanceLine(parts: (string | null | undefined)[]): string {
  const kept = parts.map((part) => text(part)).filter(Boolean);
  return kept.length ? kept.join(" · ") : "Source not supplied";
}

/** Sources whose key or name mentions one of the hints, or every source when none match. */
export function sourcesFor(view: EvidencePackView, hints: string[]) {
  const matched = view.sources.filter((source) =>
    hints.some(
      (hint) =>
        source.key.toLowerCase().includes(hint) ||
        source.name.toLowerCase().includes(hint),
    ),
  );
  return matched.length ? matched : view.sources;
}

export function sourceLine(sources: SourceView[]): string {
  if (!sources.length) return "Source not supplied";
  return sources
    .map((source) => provenanceLine([source.name, source.asOf]))
    .join(" · ");
}

export function normaliseEvidencePack(raw: unknown): EvidencePackView | null {
  const pack = record(raw) as EvidencePack | null;
  if (!pack) return null;
  const metrics = record(pack.metrics) ?? {};
  const caveats = new Set<string>();
  const metricLines: EvidencePackView["metricLines"] = [];
  for (const [key, entry] of Object.entries(metrics)) {
    const metric = record(entry);
    if (!metric) continue;
    for (const caveat of list<unknown>(metric.caveats)) {
      const line = text(caveat);
      if (line) caveats.add(line);
    }
    const unit = text(metric.unit) ?? "";
    const score = typeof metric.value === "number" ? metric.value : null;
    const display =
      unit.startsWith("score 0-1") && score !== null
        ? `${Math.round(score * 100)} / 100 (research estimate, not job-loss risk)`
        : text(metric.display);
    if (display)
      metricLines.push({
        label: text(metric.label) ?? key.replaceAll("_", " "),
        display,
        provenance: provenanceLine([
          sourceShort(metric.source),
          text(metric.as_of),
          text(metric.status),
        ]),
      });
  }
  const backtest = record(pack.backtest);
  return {
    title: text(pack.title),
    summary: text(pack.summary),
    hedges: list<EvidencePackHedge>(pack.hedges)
      .map(hedgeView)
      .filter((hedge): hedge is HedgeView => hedge !== null)
      .slice(0, 3),
    backtest: {
      summary: backtest ? text(backtest.summary) : null,
      note: text(pack.backtest_note),
    },
    crises: list<EvidencePackCrisis>(pack.crises)
      .map(crisisView)
      .filter((crisis): crisis is CrisisView => crisis !== null),
    fitTags: Array.isArray(pack.fit_tags)
      ? (pack.fit_tags as unknown[])
          .map((tag) => text(tag) ?? text(record(tag)?.label))
          .filter((tag): tag is string => tag !== null)
      : null,
    history: list<EvidencePackHistoryPoint>(
      Array.isArray(pack.history) ? pack.history : record(pack.history)?.points,
    )
      .map(historyRow)
      .filter((row): row is HistoryRow => row !== null),
    historyNote:
      text(pack.history_note) ??
      (text(record(pack.history)?.price_base)
        ? `Real pay in ${text(record(pack.history)?.price_base)}; nominal pay as published. Full-time employees; history, not a forecast.`
        : null),
    sources: list<EvidencePackSource>(pack.sources)
      .map(sourceView)
      .filter((source): source is SourceView => source !== null),
    caveats: [...caveats],
    metricLines,
  };
}

type FetchLike = (
  input: string,
  init?: { signal?: AbortSignal },
) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

/** Null means "hide the panel": 404, any other error status, bad JSON or a network failure. */
export async function fetchEvidencePack(
  soc: string,
  fetchImpl: FetchLike,
  signal?: AbortSignal,
): Promise<EvidencePackView | null> {
  try {
    const response = await fetchImpl(
      `/api/careers/${encodeURIComponent(soc)}/evidence-pack`,
      { signal },
    );
    if (!response.ok) return null;
    const body = (await response.json().catch(() => null)) as unknown;
    const envelope = record(body);
    if (envelope && envelope.ok === false) return null;
    const data =
      envelope && typeof envelope.ok === "boolean" && "data" in envelope
        ? envelope.data
        : body;
    return normaliseEvidencePack(data);
  } catch {
    return null;
  }
}
