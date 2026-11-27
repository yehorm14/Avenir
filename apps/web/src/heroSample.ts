import type { Career, Metric } from "./types";
import type { MetricLabel } from "./metricLabel";
import { demandTrendLabel } from "./planDocument";

/** The two example roles compared in the Home hero (Computer Science and Finance). */
export const sampleSocs = ["2134", "2422"] as const;

export type SampleCell = {
  career: string;
  /** Display value, or "Not available" when the figure is missing or withheld. */
  value: string;
  available: boolean;
  /** Source and year for this figure, e.g. "ONS ASHE · 2025 · UK · provisional". */
  source: string;
};

export type SampleRow = { key: string; label: string; cells: SampleCell[] };

const rows: {
  key: string;
  label: string;
  show: (value: number) => string;
}[] = [
  {
    key: "pay_median",
    label: "Median annual pay",
    show: (v) =>
      new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(v),
  },
  {
    key: "demand_trend",
    label: "Employment trend, per year",
    show: (v) => `${v > 0 ? "+" : ""}${(v * 100).toFixed(1)}%`,
  },
  {
    key: "exposure",
    label: "Automation exposure",
    show: (v) => `${Math.round(v * 100)} / 100`,
  },
];

/**
 * A compact, source-labelled comparison of the two example roles for the Home hero.
 * Built from the careers already loaded (the offline snapshot works without provider keys);
 * returns [] when either role is missing so the page can show an honest empty state.
 */
export function heroSample(
  careers: Career[],
  describe: (metric?: Metric) => MetricLabel,
): SampleRow[] {
  const pair = sampleSocs.flatMap((soc) => {
    const career = careers.find((candidate) => candidate.soc === soc);
    return career ? [career] : [];
  });
  if (pair.length !== sampleSocs.length) return [];
  return rows.map((row) => {
    const metrics = pair.map((career) => career.metrics[row.key]);
    const labels = metrics.map(describe);
    const trendLabels =
      row.key === "demand_trend"
        ? metrics.flatMap((metric, index) =>
            labels[index].available ? [demandTrendLabel(metric)] : [],
          )
        : [];
    const separateTrendLabels = new Set(trendLabels).size > 1;
    return {
      key: row.key,
      label:
        trendLabels.length && !separateTrendLabels
          ? `${trendLabels[0]}, per year`
          : row.label,
      cells: pair.map((career, index) => {
        const metric = metrics[index];
        const label = labels[index];
        const trendDescription = separateTrendLabels
          ? `${demandTrendLabel(metric)} · `
          : "";
        return {
          career: career.title,
          value: label.available
            ? row.show(metric.value as number)
            : "Not available",
          available: label.available,
          source: label.available
            ? `${trendDescription}${label.text}`
            : label.unavailableReason,
        };
      }),
    };
  });
}
