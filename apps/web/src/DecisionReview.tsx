import { useEffect, useId, useState } from "react";
import { Attributions } from "./Attributions";
import "./decisionReview.css";

type Confidence = "high" | "medium" | "low";
type ComponentScore = { score: number | null; confidence: Confidence };
type ComponentKey =
  | "fit"
  | "expected_return"
  | "risk"
  | "market_risk"
  | "disruption_risk";
type Components = Record<ComponentKey, ComponentScore>;
type EvidenceCareer = {
  soc2020: string;
  title: string;
  metrics: Record<string, { value: number | null; status: string }>;
};
type Pick = {
  tier: "ambitious" | "safe" | "balanced";
  career: EvidenceCareer;
  components: Components;
  vs_first_idea: Record<string, number | null>;
  reasons: string[];
};
type Recommendation = {
  first_idea: EvidenceCareer | null;
  first_idea_candidates?: { soc2020: string; title: string }[];
  first_idea_components: Components | null;
  picks: Pick[];
  hedge: {
    for_soc: string;
    career: EvidenceCareer;
    shared_skills: string[];
    why: string | null;
    evidence?: string | null;
    risk_delta: number | null;
    status: string;
  } | null;
  notices: string[];
  explanation?: { text: string; ai_written: boolean };
};
type SourceStatus = {
  name: string;
  status: "live" | "snapshot" | "mock" | "missing";
  quality?: string | null;
  as_of?: string | null;
};
type Envelope = {
  ok: boolean;
  data: Recommendation | null;
  error?: { message?: string } | null;
  meta?: { sources?: SourceStatus[]; as_of?: string | null };
};
type Result = {
  key: string;
  status: "loading" | "error" | "ready";
  envelope?: Envelope;
  message?: string;
};
type Props = {
  tags: string[];
  firstIdea: string;
  nation: string;
  onInspect: (soc: string) => void;
};

const tiers = {
  ambitious: "High earnings",
  safe: "Lower risk",
  balanced: "Balanced",
};
const measures: { key: ComponentKey; label: string; direction: string }[] = [
  { key: "fit", label: "Interest fit", direction: "Higher fits more closely" },
  {
    key: "expected_return",
    label: "Earnings index",
    direction: "Higher ranks earnings evidence",
  },
  { key: "risk", label: "Combined risk", direction: "Lower ranks lower risk" },
  {
    key: "market_risk",
    label: "Market risk",
    direction: "Lower ranks lower risk",
  },
  {
    key: "disruption_risk",
    label: "AI task exposure",
    direction: "Lower ranks lower exposure",
  },
];
const sourceNames: Record<string, string> = {
  ml_occupations: "Occupation evidence",
  ml_history: "Pay and employment history",
  ml_hedges: "Shared skills evidence",
  ml_fit: "Interest affinities",
  ml_backtest: "Historical checks",
  ml_crises: "Crisis measures",
  ml_sources: "Source registry",
  ml_eval: "Evaluation evidence",
  catalogue: "Career catalogue",
  routes: "Training routes",
  adzuna: "Adzuna job adverts",
};
const sourceStates = {
  live: "Live",
  snapshot: "Snapshot",
  mock: "Sample data",
  missing: "Unavailable",
};
const number = (value: number) =>
  value.toLocaleString("en-GB", { maximumFractionDigits: 1 });

function Score({
  component,
  delta,
  compare,
}: {
  component?: ComponentScore | null;
  delta?: number | null;
  compare: boolean;
}) {
  const score = component?.score;
  return (
    <>
      <strong className="decision-review__score">
        {score == null ? (
          "Unavailable"
        ) : (
          <>
            {number(score)} <span>/ 100</span>
          </>
        )}
      </strong>
      {component && (
        <span className="decision-review__confidence">
          {component.confidence[0].toUpperCase() +
            component.confidence.slice(1)}{" "}
          confidence
        </span>
      )}
      {compare && (
        <span className="decision-review__delta">
          {delta == null
            ? "Comparison unavailable"
            : delta === 0
              ? "Same as first idea"
              : `${number(Math.abs(delta))} points ${delta > 0 ? "higher" : "lower"}`}
        </span>
      )}
    </>
  );
}

export default function DecisionReview({
  tags,
  firstIdea,
  nation,
  onInspect,
}: Props) {
  const headingId = useId();
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const reference = firstIdea.trim();
  const body = JSON.stringify({
    profile: {
      interests: tags,
      nation: nation
        .trim()
        .toLowerCase()
        .replace(/[\s-]+/g, "_"),
      automation_worry: 0.5,
    },
    first_idea: reference,
  });
  const requestKey = `${attempt}:${body}`;

  useEffect(() => {
    if (!reference) return;
    const controller = new AbortController();
    setResult({ key: requestKey, status: "loading" });
    async function load() {
      let serverMessage: string | undefined;
      try {
        const response = await fetch("/api/v1/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
          signal: controller.signal,
        });
        const envelope: Envelope = await response.json();
        if (!response.ok || !envelope.ok || !envelope.data) {
          serverMessage = envelope.error?.message;
          throw new Error("Comparison unavailable");
        }
        if (!controller.signal.aborted)
          setResult({ key: requestKey, status: "ready", envelope });
      } catch {
        if (controller.signal.aborted) return;
        setResult({
          key: requestKey,
          status: "error",
          message:
            serverMessage ||
            "The comparison could not load. Check your connection and retry.",
        });
      }
    }
    void load();
    return () => controller.abort();
  }, [body, reference, requestKey]);

  // A changed profile hides the previous response immediately, before the effect runs.
  const current = result?.key === requestKey ? result : null;
  const data = current?.envelope?.data;
  const sources = current?.envelope?.meta?.sources ?? [];
  const evidenceCareers = data
    ? [
        data.first_idea,
        ...data.picks.map((pick) => pick.career),
        data.hedge?.career,
      ].filter((career): career is EvidenceCareer => !!career)
    : [];
  const metrics = evidenceCareers.flatMap((career) =>
    Object.values(career.metrics ?? {}),
  );
  const hasSample =
    sources.some((source) => source.status === "mock") ||
    metrics.some((metric) => metric.status === "mock");
  const hasMissing =
    sources.some((source) => source.status === "missing") ||
    metrics.some(
      (metric) => metric.value == null || metric.status === "pending",
    );
  const hasPreliminary =
    sources.some((source) => source.quality === "preliminary") ||
    metrics.some((metric) => metric.status === "preliminary");

  return (
    <section className="decision-review" aria-labelledby={headingId}>
      <header className="decision-review__heading">
        <h2 id={headingId}>Compare the trade-offs</h2>
        <p>
          Fixed rules compare earnings, risk and interest fit using the supplied
          evidence. These indices help you compare options; they are not
          forecasts or probabilities. Lower risk does not guarantee a secure
          career.
        </p>
      </header>
      {!reference ? (
        <p className="decision-review__state" role="status">
          Select a first career idea to compare the alternatives.
        </p>
      ) : current?.status === "error" ? (
        <div className="decision-review__state" role="alert">
          <p>{current.message}</p>
          <button
            type="button"
            className="decision-review__retry"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Retry comparison
          </button>
        </div>
      ) : !data ? (
        <p className="decision-review__state" role="status" aria-live="polite">
          Comparing the available evidence…
        </p>
      ) : (
        <>
          <div className="decision-review__context">
            <p>
              {data.first_idea
                ? `First idea: ${data.first_idea.title}. Differences below are index points against this reference.`
                : data.first_idea_candidates?.length
                  ? `“${reference}” matches several careers. A first-idea comparison is unavailable until the role is specific.`
                  : `No exact reference match for “${reference}”. First-idea comparisons are unavailable.`}
            </p>
            {!tags.length && (
              <p>Select interests to make the fit comparison more personal.</p>
            )}
            {(hasSample || hasMissing || hasPreliminary) && (
              <p className="decision-review__quality">
                {[
                  hasSample && "Sample evidence included",
                  hasMissing && "Some inputs unavailable",
                  hasPreliminary && "Preliminary evidence",
                ]
                  .filter(Boolean)
                  .join(" · ")}
                . See sources and method below.
              </p>
            )}
          </div>
          {data.picks.length > 0 ? (
            <div
              className="decision-review__table-wrap"
              tabIndex={0}
              role="region"
              aria-label="Career comparison table; scroll horizontally if needed"
            >
              <table className="decision-review__table">
                <caption>
                  Indices from 0 to 100 within the model’s career collection.
                  Differences are against your first idea.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Evidence index</th>
                    {data.first_idea && (
                      <th scope="col" className="decision-review__reference">
                        <span className="decision-review__tier">
                          First idea
                        </span>
                        <button
                          type="button"
                          onClick={() => onInspect(data.first_idea!.soc2020)}
                          aria-label={`Inspect ${data.first_idea.title}`}
                        >
                          {data.first_idea.title}
                        </button>
                      </th>
                    )}
                    {data.picks.map((pick) => (
                      <th scope="col" key={pick.career.soc2020}>
                        <span className="decision-review__tier">
                          {tiers[pick.tier]}
                        </span>
                        <button
                          type="button"
                          onClick={() => onInspect(pick.career.soc2020)}
                          aria-label={`Inspect ${pick.career.title}`}
                        >
                          {pick.career.title}
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {measures.map((measure) => (
                    <tr key={measure.key}>
                      <th scope="row">
                        {measure.label}
                        <span className="decision-review__direction">
                          {measure.direction}
                        </span>
                      </th>
                      {data.first_idea && (
                        <td className="decision-review__reference">
                          <Score
                            component={
                              data.first_idea_components?.[measure.key]
                            }
                            compare={false}
                          />
                        </td>
                      )}
                      {data.picks.map((pick) => (
                        <td key={pick.career.soc2020}>
                          <Score
                            component={pick.components[measure.key]}
                            delta={pick.vs_first_idea[measure.key]}
                            compare={!!data.first_idea}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="decision-review__state">
              No alternatives meet the current fit and evidence requirements.
              Try adding interests or comparing a different first idea.
            </p>
          )}
          {data.picks.length > 0 && data.picks.length < 3 && (
            <p className="decision-review__shortfall">
              The evidence supports {data.picks.length} alternative
              {data.picks.length === 1 ? "" : "s"} for this profile. The engine
              returns fewer options when its fit or evidence requirements are
              not met.
            </p>
          )}
          <div className="decision-review__hedge">
            <h3>Related alternative</h3>
            {data.hedge ? (
              <>
                <button
                  type="button"
                  className="decision-review__career-link"
                  onClick={() => onInspect(data.hedge!.career.soc2020)}
                >
                  {data.hedge.career.title}
                </button>
                <span className="decision-review__hedge-status">
                  {data.hedge.status === "mock"
                    ? "Sample data"
                    : data.hedge.status}
                  {data.hedge.evidence === "estimate"
                    ? " · estimated skills link"
                    : ""}
                </span>
                {data.hedge.risk_delta != null && (
                  <p>
                    Risk index difference: {number(data.hedge.risk_delta)}{" "}
                    points against{" "}
                    {data.picks.find(
                      (pick) => pick.career.soc2020 === data.hedge!.for_soc,
                    )?.career.title ?? "the lead option"}
                    . A lower index is not a guarantee of employment.
                  </p>
                )}
                <p>
                  {data.hedge.shared_skills.length
                    ? `Shared skills: ${data.hedge.shared_skills.join(", ")}.`
                    : "No shared skills are listed in the supplied evidence."}
                </p>
                {data.hedge.why && <p>{data.hedge.why}</p>}
              </>
            ) : (
              <p>
                No related alternative with a lower risk index was found in the
                available evidence.
              </p>
            )}
          </div>
          <div className="decision-review__details">
            {data.picks.length > 0 && (
              <details>
                <summary>Why these options?</summary>
                <div className="decision-review__detail-body">
                  {data.picks.map((pick) => (
                    <div key={pick.career.soc2020}>
                      <h3>{pick.career.title}</h3>
                      {pick.reasons.length ? (
                        <ul>
                          {pick.reasons.map((reason, index) => (
                            <li key={`${index}:${reason}`}>{reason}</li>
                          ))}
                        </ul>
                      ) : (
                        <p>No additional reasons were supplied.</p>
                      )}
                    </div>
                  ))}
                  {data.explanation?.text && (
                    <div>
                      <h3>Explanation</h3>
                      <p>{data.explanation.text}</p>
                      {data.explanation.ai_written && (
                        <p>AI-written, check the source.</p>
                      )}
                    </div>
                  )}
                </div>
              </details>
            )}
            <details>
              <summary>Sources and method</summary>
              <div className="decision-review__detail-body">
                <p>
                  The engine first chooses the highest earnings index among
                  eligible careers, then the lowest risk index from the
                  remaining careers, then a balanced comparison. Its fit
                  threshold can leave fewer than three options. These are
                  distinct comparisons, not a ranking of guaranteed outcomes.
                </p>
                <p>
                  Earnings combines current pay and historical real pay. Risk
                  combines historical demand, crisis resilience, shortages and
                  researched AI task exposure. Missing inputs are excluded, and
                  confidence accompanies each index. Automation concern is held
                  at the midpoint; no qualifications were supplied for this
                  comparison. Check exact entry requirements separately.
                </p>
                {sources.length ? (
                  <ul className="decision-review__sources">
                    {sources.map((source, index) => (
                      <li key={`${index}:${source.name}`}>
                        <span>
                          {sourceNames[source.name] ??
                            source.name.replace(/_/g, " ")}
                        </span>
                        <span>
                          {sourceStates[source.status]}
                          {source.quality ? ` · ${source.quality}` : ""}
                          {source.as_of ? ` · ${source.as_of}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Source statuses were not supplied for this response.</p>
                )}
                <Attributions
                  adzuna={sources.some(
                    (s) => s.name === "adzuna" && s.status !== "missing",
                  )}
                />
                {data.notices.length > 0 && (
                  <div>
                    <h3>Evidence caveats</h3>
                    <ul>
                      {data.notices.map((notice, index) => (
                        <li key={`${index}:${notice}`}>{notice}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </details>
          </div>
        </>
      )}
    </section>
  );
}
