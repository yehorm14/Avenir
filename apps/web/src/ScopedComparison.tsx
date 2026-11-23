import { useEffect, useId, useState } from "react";
import type { CSSProperties } from "react";
import type { Career, Metric, Weights } from "./types";
import { money, percent } from "./Charts";
import {
  isRelativeDemand,
  demandTrendLabel,
  metricCaveats,
} from "./planDocument";
import { metricLabel, sourcePeriodSummary } from "./metricLabel";
import { api } from "./store";
import "./scopedComparison.css";

type Props = {
  area: "cs" | "finance";
  careers: Career[];
  selectedSoc?: string;
  onSelect: (soc: string) => void;
  onPlan: (career: Career, weights?: Weights) => void;
};
type Result = {
  key: string;
  status: "loading" | "ready" | "error";
  careers?: Career[];
  message?: string;
};

function observed(metric?: Metric) {
  return !metric ||
    metric.status === "pending" ||
    metric.flags.includes("suppressed")
    ? null
    : metric.value;
}

function exposure(career: Career) {
  const value = observed(career.metrics.exposure);
  return value == null ? "Not available" : `${(value * 100).toFixed(0)} / 100`;
}

export default function ScopedComparison({
  area,
  careers,
  selectedSoc,
  onSelect,
  onPlan,
}: Props) {
  const id = useId();
  const [pay, setPay] = useState(50);
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const socs = careers.map((career) => career.soc).join(",");
  const requestKey = `${area}:${socs}:${pay}:${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    setResult({ key: requestKey, status: "loading" });
    const timer = window.setTimeout(() => {
      api<{ results: Career[] }>(
        "matches",
        { tags: [], weights: { pay, interest: 0, need: 100 - pay } },
        controller.signal,
      )
        .then((response) => {
          if (controller.signal.aborted) return;
          if (!Array.isArray(response.results))
            throw new Error("The comparison was incomplete. Please try again.");
          const supported = new Set(socs.split(","));
          setResult({
            key: requestKey,
            status: "ready",
            careers: response.results.filter((career) =>
              supported.has(career.soc),
            ),
          });
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setResult({
            key: requestKey,
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "The comparison could not load. Please try again.",
          });
        });
    }, 150);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [requestKey, pay, socs]);

  // A changed priority or subject hides the previous result immediately.
  const current = result?.key === requestKey ? result : null;
  const ranked = current?.status === "ready" ? (current.careers ?? []) : [];
  const top = ranked.find((career) => career.score != null);
  const comparison =
    ranked.find((career) => career.soc === selectedSoc && career !== top) ??
    ranked.find((career) => career !== top);
  const tied =
    top &&
    ranked.some((career) => career !== top && career.score === top.score);
  const loading = !current || current.status === "loading";

  return (
    <section className="scoped-comparison" aria-labelledby={`${id}-title`}>
      <header className="scoped-comparison-heading">
        <div>
          <h2 id={`${id}-title`}>Choose what to explore first</h2>
          <p>
            Compare these {area === "cs" ? "computing" : "finance"} roles
            against the evidence that matters to you.
          </p>
        </div>
        <span className="scoped-comparison-scope">
          {careers.length} roles · no interest profile used
        </span>
      </header>

      <fieldset className="scoped-comparison-priorities">
        <legend>Your priorities</legend>
        <div className="scoped-comparison-controls">
          <div className="scoped-comparison-slider">
            <label htmlFor={`${id}-priority`}>
              Pay {pay}% <span>Historical employment trend {100 - pay}%</span>
            </label>
            <input
              id={`${id}-priority`}
              type="range"
              min={0}
              max={100}
              step={5}
              value={pay}
              style={{ "--range": `${pay}%` } as CSSProperties}
              aria-valuetext={`${pay}% pay, ${100 - pay}% historical employment trend`}
              aria-describedby={`${id}-priority-note`}
              onChange={(event) => setPay(Number(event.target.value))}
            />
            <div className="scoped-comparison-slider-labels" aria-hidden="true">
              <span>Employment trend</span>
              <span>Pay</span>
            </div>
          </div>
          <div
            className="scoped-comparison-presets"
            aria-label="Priority presets"
          >
            {[
              { label: "Higher pay", value: 100 },
              { label: "Employment trend", value: 0 },
              { label: "Balanced", value: 50 },
            ].map((preset) => (
              <button
                type="button"
                key={preset.label}
                aria-pressed={pay === preset.value}
                onClick={() => setPay(preset.value)}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
        <p id={`${id}-priority-note`}>
          Employment trends describe the past, not future vacancies. Pay is the
          workforce median, not starting pay.
        </p>
      </fieldset>

      <div className="scoped-comparison-result" aria-busy={loading}>
        {loading && (
          <p role="status" className="scoped-comparison-message">
            Comparing your priorities…
          </p>
        )}
        {current?.status === "error" && (
          <div className="scoped-comparison-message" role="alert">
            <p>{current.message}</p>
            <p>
              Your occupation evidence is still available in the Evidence tab.
            </p>
            <button
              className="button secondary"
              type="button"
              onClick={() => setAttempt((value) => value + 1)}
            >
              Retry comparison
            </button>
          </div>
        )}
        {current?.status === "ready" && !top && (
          <p role="status" className="scoped-comparison-message">
            There is not enough supplied pay or employment evidence to suggest a
            first role for these priorities. Explore the occupation evidence and
            routes instead.
          </p>
        )}
        {top && (
          <>
            <div
              className="scoped-comparison-recommendation"
              aria-live="polite"
            >
              <div>
                <span>
                  {tied
                    ? "Joint highest comparison index"
                    : "Explore first for these priorities"}
                </span>
                <h3>{top.title}</h3>
                <p>
                  {money(observed(top.metrics.pay_median))} median annual pay
                  and {percent(observed(top.metrics.demand_trend))} / year{" "}
                  {isRelativeDemand(top.metrics.demand_trend)
                    ? "employment trend relative to the typical occupation."
                    : "historical employment trend."}
                </p>
                {comparison && (
                  <p>
                    Compare with {comparison.title.toLowerCase()}:{" "}
                    {money(observed(comparison.metrics.pay_median))} median pay
                    and {percent(observed(comparison.metrics.demand_trend))} /
                    year
                    {isRelativeDemand(comparison.metrics.demand_trend)
                      ? " relative to the typical occupation"
                      : ""}
                    . Consider the work, routes and task exposure below before
                    choosing.
                  </p>
                )}
              </div>
              <button
                className="button primary"
                type="button"
                onClick={() =>
                  onPlan(top, { pay, interest: 0, need: 100 - pay })
                }
              >
                Build my plan
              </button>
            </div>

            <p
              className="scoped-comparison-sources"
              data-testid="source-period"
            >
              <strong>Evidence used:</strong> pay,{" "}
              {sourcePeriodSummary(ranked, "pay_median")}; employment trend,{" "}
              {sourcePeriodSummary(ranked, "demand_trend")}; AI task exposure,{" "}
              {sourcePeriodSummary(ranked, "exposure")}. A figure shown as “Not
              available” is missing, not zero.
            </p>
            <div
              className="scoped-comparison-table-wrap"
              tabIndex={0}
              role="region"
              aria-label="Career evidence comparison"
            >
              <table className="scoped-comparison-table">
                <caption className="sr-only">
                  {area === "cs" ? "Computing" : "Finance"} roles in comparison
                  order for {pay}% pay and {100 - pay}% historical employment
                  trend
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Occupation</th>
                    <th scope="col">Median annual pay</th>
                    <th scope="col">
                      {demandTrendLabel(careers[0]?.metrics.demand_trend)}
                    </th>
                    <th scope="col">AI task exposure</th>
                    <th scope="col">Comparison index</th>
                    <th scope="col">
                      <span className="sr-only">Explore occupation</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ranked.map((career) => (
                    <tr
                      key={career.soc}
                      className={
                        career.soc === selectedSoc ? "is-viewing" : undefined
                      }
                    >
                      <th scope="row">
                        {career.title}
                        {career.soc === selectedSoc && (
                          <small>Currently viewing</small>
                        )}
                      </th>
                      <td>
                        {money(observed(career.metrics.pay_median))}
                        <small>
                          {metricLabel(career.metrics.pay_median).text}
                        </small>
                        {!metricLabel(career.metrics.pay_median).available && (
                          <small>
                            {
                              metricLabel(career.metrics.pay_median)
                                .unavailableReason
                            }
                          </small>
                        )}
                      </td>
                      <td>
                        {percent(observed(career.metrics.demand_trend))}
                        {observed(career.metrics.demand_trend) != null &&
                          " / year"}
                        <small>
                          {metricLabel(career.metrics.demand_trend).text}
                        </small>
                        {!metricLabel(career.metrics.demand_trend)
                          .available && (
                          <small>
                            {
                              metricLabel(career.metrics.demand_trend)
                                .unavailableReason
                            }
                          </small>
                        )}
                        {metricCaveats(career.metrics.demand_trend) && (
                          <small>
                            {metricCaveats(career.metrics.demand_trend)}
                          </small>
                        )}
                      </td>
                      <td>
                        {exposure(career)}
                        <small>
                          {metricLabel(career.metrics.exposure).text}
                        </small>
                        {!metricLabel(career.metrics.exposure).available && (
                          <small>
                            {
                              metricLabel(career.metrics.exposure)
                                .unavailableReason
                            }
                          </small>
                        )}
                        {metricCaveats(career.metrics.exposure) && (
                          <small>
                            {metricCaveats(career.metrics.exposure)}
                          </small>
                        )}
                      </td>
                      <td>
                        {career.score == null
                          ? "Unavailable"
                          : `${career.score.toFixed(1)} / 100`}
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => onSelect(career.soc)}
                          aria-label={`Explore ${career.title}`}
                        >
                          Explore
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="scoped-comparison-exposure-note">
              ILO exposure is independent research context and is excluded from
              this ranking. It estimates tasks AI could affect, not the
              probability of losing a job. All supplied figures are preliminary.
            </p>
          </>
        )}
      </div>

      <details className="scoped-comparison-method">
        <summary>How this comparison works</summary>
        <p>
          The existing decision service combines pay and historical employment
          trend percentile ranks using your weights. Indices compare the 20-role
          supported collection; this view keeps only the roles in this field and
          preserves their order. An index is not a probability or an earnings
          forecast. Missing inputs are excluded from the weighted mean. Equal
          indices keep the service’s order.
        </p>
        <p>
          No personal interest match or completed quiz is assumed. ONS figures
          cover employees and exclude self-employment; the employment trend uses
          its stated period. Relative trends compare each occupation’s job-count
          path with the typical occupation’s path before estimating annual
          growth; a positive value can coexist with falling employment. Open
          Evidence for source links, research ranges, coverage and caveats. You
          choose the role and route to explore.
        </p>
      </details>
    </section>
  );
}
