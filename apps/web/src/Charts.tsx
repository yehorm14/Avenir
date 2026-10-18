import { useState } from "react";
import type { Career } from "./types";
import { historySegments } from "./historySegments";
import { evidencePriceLabel } from "./planDocument";
export const money = (v: number | null | undefined) =>
  v == null
    ? "Not available"
    : new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(v);
export const percent = (v: number | null | undefined) =>
  v == null ? "Not available" : `${v > 0 ? "+" : ""}${(v * 100).toFixed(1)}%`;
const colors = ["#6da2f8", "#b49aeb", "#d3b575"];
export function SalaryChart({
  careers,
  compact = false,
}: {
  careers: Career[];
  compact?: boolean;
}) {
  const [mode, setMode] = useState<"real" | "nominal" | "jobs">("real");
  const [hover, setHover] = useState<number | null>(null);
  const key: "pay_median_real" | "pay_median" | "jobs_k" =
    mode === "real"
      ? "pay_median_real"
      : mode === "nominal"
        ? "pay_median"
        : "jobs_k";
  const all = careers.flatMap((c) => c.history || []);
  const priceLabel = evidencePriceLabel(careers[0]);
  const priceBase = careers[0]?.evidence_metadata?.price_base;
  const lowPurityPay = careers.some((career) =>
    career.history?.some((point) => point.flags.includes("bridged_low_purity")),
  );
  const indicativeCounts = careers.some(
    (career) =>
      career.metrics.jobs?.flags.includes("ons_indicative_counts") ||
      career.jobs_observation?.flags.includes("ons_indicative_counts"),
  );
  const years = [...new Set(all.map((p) => p.year))].sort();
  const values = all
    .map((p) => p[key])
    .filter((v): v is number => typeof v === "number");
  if (!values.length || years.length < 2)
    return (
      <div className="empty">
        Historical data isn't available for this career yet.
      </div>
    );
  const W = 720,
    H = compact ? 210 : 285,
    L = 55,
    R = 24,
    T = 20,
    B = 35;
  const y0 = years[0],
    y1 = years[years.length - 1];
  const max = Math.max(...values) * 1.12,
    min = Math.max(0, Math.min(...values) * 0.78),
    range = max - min || 1;
  const x = (v: number) => L + ((v - y0) / (y1 - y0)) * (W - L - R),
    y = (v: number) => T + ((max - v) / range) * (H - T - B);
  const label =
    mode === "jobs"
      ? "Full-time employee jobs, thousands"
      : mode === "real"
        ? `Annual median pay in ${priceLabel}`
        : "Annual median pay in money of the year";
  const chosen = hover ?? y1;
  return (
    <section className={`chart-module ${compact ? "compact" : ""}`}>
      <div className="chart-top">
        <div>
          <h3>{mode === "jobs" ? "Employment over time" : "Pay history"}</h3>
          <p>
            {mode === "real"
              ? `Inflation-adjusted. ${priceLabel}.`
              : mode === "nominal"
                ? "Published annual pay. No inflation adjustment."
                : "Full-time employee jobs. Not vacancies."}
          </p>
        </div>
        <div className="segmented" aria-label="Chart measure">
          {(
            [
              ["real", "Real pay"],
              ["nominal", "Nominal"],
              ["jobs", "Jobs"],
            ] as const
          ).map(([v, l]) => (
            <button
              key={v}
              onClick={() => setMode(v)}
              aria-pressed={mode === v}
            >
              {l}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-readout" aria-live="polite">
        <span>{chosen}</span>
        {careers.map((c, i) => {
          const v = c.history?.find((p) => p.year === chosen)?.[key];
          return (
            <div key={c.soc}>
              <i style={{ background: colors[i % 3] }} />
              <span>{c.title}</span>
              <b>
                {typeof v === "number"
                  ? mode === "jobs"
                    ? `${v.toLocaleString()}k jobs`
                    : money(v)
                  : "Not available"}
              </b>
            </div>
          );
        })}
      </div>
      <div
        className="chart-interactive"
        tabIndex={0}
        role="group"
        aria-label={`${label}. Use left and right arrow keys to inspect a year.`}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
            e.preventDefault();
            setHover(
              Math.max(
                y0,
                Math.min(y1, chosen + (e.key === "ArrowLeft" ? -1 : 1)),
              ),
            );
          }
        }}
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label={`${label}, ${y0} to ${y1}`}
          onMouseMove={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            setHover(
              Math.max(
                y0,
                Math.min(
                  y1,
                  Math.round(
                    y0 +
                      ((((e.clientX - r.left) / r.width) * W - L) /
                        (W - L - R)) *
                        (y1 - y0),
                  ),
                ),
              ),
            );
          }}
          onMouseLeave={() => setHover(null)}
        >
          {[0, 0.25, 0.5, 0.75, 1].map((t) => (
            <g key={t}>
              <line
                x1={L}
                x2={W - R}
                y1={y(min + t * range)}
                y2={y(min + t * range)}
                stroke="#292d35"
              />
              <text x={L - 12} y={y(min + t * range) + 4} textAnchor="end">
                {mode === "jobs"
                  ? Math.round(min + t * range)
                  : `£${Math.round((min + t * range) / 1000)}k`}
              </text>
            </g>
          ))}
          {years
            .filter((_, i) => i % 3 === 0 || i === years.length - 1)
            .map((yr) => (
              <text key={yr} x={x(yr)} y={H - 10} textAnchor="middle">
                {yr}
              </text>
            ))}
          {careers.map((c, i) =>
            historySegments(c.history || [], key).map((s, j) => (
              <polyline
                key={`${c.soc}-${j}`}
                points={s
                  .map((p) => `${x(p.year)},${y(p[key] as number)}`)
                  .join(" ")}
                fill="none"
                stroke={colors[i % 3]}
                strokeWidth="3"
                strokeDasharray={
                  s[s.length - 1]?.flags.some((f) => f.startsWith("bridged_"))
                    ? "5 4"
                    : undefined
                }
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )),
          )}
          {(mode === "jobs" || lowPurityPay) && (
            <>
              <line
                x1={x(2020.5)}
                x2={x(2020.5)}
                y1={T}
                y2={H - B}
                stroke="#5d6675"
                strokeDasharray="3 4"
              />
              <text x={x(2020.5) + 7} y={T + 12}>
                Code change
              </text>
            </>
          )}
          <line
            x1={x(chosen)}
            x2={x(chosen)}
            y1={T}
            y2={H - B}
            stroke="#7d899c"
            strokeDasharray="3 4"
          />
          {careers.map((c, i) => {
            const v = c.history?.find((p) => p.year === chosen)?.[key];
            return typeof v === "number" ? (
              <circle
                key={c.soc}
                cx={x(chosen)}
                cy={y(v)}
                r="5"
                fill={colors[i % 3]}
                stroke="var(--white)"
                strokeWidth="2"
              />
            ) : null;
          })}
        </svg>
      </div>
      <p className="chart-note">
        Source: ONS ASHE, {y0}–{y1}. Preliminary, full-time employees only;
        excludes self-employment.{" "}
        {mode === "jobs"
          ? "Dashed years use older occupation codes; the 2021 code change is marked. Compare trends within each period."
          : `Pre-2021 occupation mappings are estimates. ${lowPurityPay ? "For low-purity mappings the older occupation group mixed several jobs, so pre-2021 values are estimates. " : ""}2020 includes COVID distortions; 2025 is provisional. Real pay uses ${priceBase || "ONS CPIH, April 2025 prices"}.`}
        {mode === "jobs" &&
          indicativeCounts &&
          " ONS says its job counts are indicative, not accurate estimates."}
      </p>
      {!compact && (
        <details className="data-table">
          <summary>Read the chart as a table</summary>
          <div className="table-scroll">
            <table>
              <caption>{label}</caption>
              <thead>
                <tr>
                  <th>Year</th>
                  {careers.map((c) => (
                    <th key={c.soc}>{c.title}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {years.map((yr) => (
                  <tr key={yr}>
                    <th>{yr}</th>
                    {careers.map((c) => {
                      const v = c.history?.find((p) => p.year === yr)?.[key];
                      return (
                        <td key={c.soc}>
                          {typeof v === "number"
                            ? mode === "jobs"
                              ? `${v}k`
                              : money(v)
                            : "Not available"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  );
}
