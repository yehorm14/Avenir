import type { Career, Metric } from "./types";

/** Display names for the evidence source ids carried on every metric. */
export const sourceNames: Record<string, string> = {
  ons_ashe_t14: "ONS ASHE",
  ons_cpih: "ONS CPIH",
  ilo_wp140: "ILO Working Paper 140",
  dfe_ai_uk_2023: "DfE UK AI exposure study",
  ons_online_job_adverts: "ONS / Adzuna job adverts",
  ons_aps_2016_age: "ONS Annual Population Survey",
};

/** Who each source describes. ILO exposure is international research mapped to UK job groups. */
const sourceGeography: Record<string, string> = {
  ons_ashe_t14: "UK",
  ons_cpih: "UK",
  ilo_wp140: "international research mapped to UK jobs",
  dfe_ai_uk_2023: "UK",
  ons_online_job_adverts: "UK",
  ons_aps_2016_age: "UK",
};

/** Short estimation labels for flags that change how a figure should be read. */
const estimationLabels: Record<string, string> = {
  provisional: "provisional",
  imputed_parent: "wider-group estimate",
  bridged_soc2010: "older codes mapped to today's",
  bridged_soc2000: "older codes mapped to today's",
  ons_indicative_counts: "indicative counts",
  category_level: "broad category",
  historical_observation: "last available",
  employees_only: "employees only",
  multi_isco: "several international codes",
  sources_disagree: "sources disagree",
  mock: "sample data",
};

export type MetricLabel = {
  /** False when the value is missing, pending or withheld. Zero is a real value and stays available. */
  available: boolean;
  source: string;
  period: string;
  geography: string;
  estimation: string[];
  /** One line, e.g. "ONS ASHE · 2025 · UK · provisional · employees only". */
  text: string;
  /** Why a value is absent, so "Not available" is never mistaken for zero. */
  unavailableReason: string;
};

export function metricAvailable(metric?: Metric): boolean {
  return (
    !!metric &&
    metric.value != null &&
    metric.status !== "pending" &&
    !metric.flags?.includes("suppressed")
  );
}

export function metricLabel(metric?: Metric): MetricLabel {
  if (!metric) {
    return {
      available: false,
      source: "",
      period: "",
      geography: "",
      estimation: [],
      text: "No supplied observation",
      unavailableReason: "No figure is supplied for this role.",
    };
  }
  const available = metricAvailable(metric);
  const source = sourceNames[metric.source] ?? metric.source;
  const period = metric.as_of || "period unavailable";
  const geography = sourceGeography[metric.source] ?? "";
  const estimation = [
    ...new Set(
      (metric.flags ?? [])
        .map((flag) => estimationLabels[flag])
        .filter(Boolean),
    ),
  ];
  const text = [source, period, geography, ...estimation]
    .filter(Boolean)
    .join(" · ");
  const unavailableReason = available
    ? ""
    : metric.flags?.includes("suppressed")
      ? "Withheld because the estimate is unreliable."
      : metric.status === "pending"
        ? "Not yet supplied."
        : "No figure is supplied for this role.";
  return {
    available,
    source,
    period,
    geography,
    estimation,
    text,
    unavailableReason,
  };
}

/** The distinct source and period behind one metric across a set of careers, e.g. for a table caption. */
export function sourcePeriodSummary(
  careers: Pick<Career, "metrics">[],
  key: string,
): string {
  const seen = new Set<string>();
  for (const career of careers) {
    const metric = career.metrics[key];
    if (!metric) continue;
    const label = metricLabel(metric);
    seen.add(
      [label.source, label.period, label.geography].filter(Boolean).join(" · "),
    );
  }
  return [...seen].join("; ") || "no supplied observation";
}
