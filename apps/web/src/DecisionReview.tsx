import { useEffect, useId, useState } from "react";
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
};
type Pick = {
  tier: "ambitious" | "safe" | "balanced";
  career: EvidenceCareer;
  components: Components;
  vs_first_idea: Record<string, number | null>;
};
type Recommendation = {
  first_idea: EvidenceCareer | null;
  first_idea_components: Components | null;
  picks: Pick[];
};
type Envelope = {
  ok: boolean;
  data: Recommendation | null;
  error?: { message?: string } | null;
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

  return (
    <section className="decision-review" aria-labelledby={headingId}>
      <header className="decision-review__heading">
        <h2 id={headingId}>Compare the trade-offs</h2>
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
          {data.picks.length > 0 ? (
            <div
              className="decision-review__table-wrap"
              tabIndex={0}
              role="region"
              aria-label="Career comparison table; scroll horizontally if needed"
            >
              <table className="decision-review__table">
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
        </>
      )}
    </section>
  );
}
