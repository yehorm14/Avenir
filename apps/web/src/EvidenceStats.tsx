import { useEffect, useState } from "react";
import {
  BACKTEST_RULE_LINE,
  EXCLUDED_CRISIS_LABEL,
  FIT_TAGS_LINE,
  HEDGE_INTRO,
  fetchEvidencePack,
  sourceLine,
  sourcesFor,
  type EvidencePackView,
} from "./evidencePack";
import "./evidenceStats.css";

type State = {
  soc: string;
  status: "loading" | "ready" | "hidden";
  pack: EvidencePackView | null;
};

function SourceLine({
  pack,
  hints,
}: {
  pack: EvidencePackView;
  hints: string[];
}) {
  const sources = sourcesFor(pack, hints);
  return (
    <small className="dashboard-stats-source">
      {sources.length ? (
        sources.map((source, index) => (
          <span key={source.key}>
            {index > 0 && " · "}
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.name}
              </a>
            ) : (
              source.name
            )}
            {source.asOf && ` · ${source.asOf}`}
            {source.licence && ` · ${source.licence}`}
          </span>
        ))
      ) : (
        <span>{sourceLine(sources)}</span>
      )}
    </small>
  );
}

/** "Statistics for this role": the ML owner's analysis for one occupation, numbers only from the payload. */
export default function EvidenceStats({
  soc,
  priceLabel,
}: {
  soc: string;
  priceLabel?: string;
}) {
  const [state, setState] = useState<State>({
    soc,
    status: "loading",
    pack: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState({ soc, status: "loading", pack: null });
    void fetchEvidencePack(
      soc,
      (input, init) => fetch(input, init),
      controller.signal,
    ).then((pack) => {
      if (controller.signal.aborted) return;
      setState({ soc, status: pack ? "ready" : "hidden", pack });
    });
    return () => controller.abort();
  }, [soc]);

  if (state.status === "hidden") return null;
  if (state.status !== "ready" || !state.pack || state.soc !== soc)
    return (
      <section
        className="dashboard-stats"
        aria-busy="true"
        aria-label="Statistics for this role"
      >
        <h2>Statistics for this role</h2>
        <div className="dashboard-stats-skeleton" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </section>
    );

  const pack = state.pack;
  return (
    <section className="dashboard-stats" aria-label="Statistics for this role">
      <h2>Statistics for this role</h2>
      {pack.summary && <p>{pack.summary}</p>}
      {pack.metricLines.length > 0 && (
        <dl className="dashboard-stats-metrics">
          {pack.metricLines.map((line) => (
            <div key={line.label}>
              <dt>{line.label}</dt>
              <dd>
                <span>{line.display}</span>
                <small>{line.provenance}</small>
              </dd>
            </div>
          ))}
        </dl>
      )}

      <section className="dashboard-stats-section" data-section="hedges">
        <h3>Hedge careers</h3>
        <p>{HEDGE_INTRO}</p>
        {pack.hedges.length ? (
          <ul className="dashboard-stats-hedges">
            {pack.hedges.map((hedge) => (
              <li key={hedge.soc}>
                <strong>{hedge.title}</strong>
                <span>
                  {hedge.pay ?? "Pay not supplied"} ·{" "}
                  {hedge.trend ?? "Trend not supplied"}
                </span>
                {hedge.evidence && <p>{hedge.evidence}</p>}
              </li>
            ))}
          </ul>
        ) : (
          <p>No hedge career is supplied for this occupation.</p>
        )}
      </section>

      <section className="dashboard-stats-section" data-section="backtest">
        <h3>Historical rule checks for this role</h3>
        <p>
          {pack.backtest.summary ??
            pack.backtest.note ??
            "No backtest summary is supplied for this occupation."}
        </p>
        {pack.backtest.summary && pack.backtest.note && (
          <small>{pack.backtest.note}</small>
        )}
        <small>{BACKTEST_RULE_LINE}</small>
      </section>

      <section className="dashboard-stats-section" data-section="crises">
        <h3>Crisis checks</h3>
        {pack.crises.length ? (
          <table className="dashboard-stats-table">
            <thead>
              <tr>
                <th scope="col">Crisis</th>
                <th scope="col">Period</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {pack.crises.map((crisis) => (
                <tr
                  key={`${crisis.name}-${crisis.period}`}
                  className={crisis.excluded ? "is-excluded" : undefined}
                >
                  <th scope="row">{crisis.name}</th>
                  <td>{crisis.period}</td>
                  <td>
                    {crisis.result}
                    {crisis.excluded && <small>{EXCLUDED_CRISIS_LABEL}</small>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No crisis checks are supplied for this occupation.</p>
        )}
        <small>
          Checks that failed the placebo test are shown for transparency and
          excluded from recommendations.
        </small>
      </section>

      {pack.fitTags && (
        <section className="dashboard-stats-section" data-section="fit">
          <h3>Interest fit</h3>
          {pack.fitTags.length ? (
            <ul className="dashboard-stats-chips">
              {pack.fitTags.map((tag) => (
                <li key={tag}>{tag}</li>
              ))}
            </ul>
          ) : (
            <p>No interest tags are supplied for this occupation.</p>
          )}
          <small>Interest tags {FIT_TAGS_LINE}.</small>
          <SourceLine pack={pack} hints={["fit", "affinity"]} />
        </section>
      )}

      <section className="dashboard-stats-section" data-section="history">
        <h3>Pay history</h3>
        {pack.history.length ? (
          <table className="dashboard-stats-table">
            <thead>
              <tr>
                <th scope="col">Year</th>
                <th scope="col">Real pay</th>
                <th scope="col">Nominal pay</th>
                <th scope="col">Employee jobs</th>
              </tr>
            </thead>
            <tbody>
              {pack.history.map((row) => (
                <tr key={row.year}>
                  <th scope="row">{row.year}</th>
                  <td>{row.payReal}</td>
                  <td>{row.payNominal}</td>
                  <td>{row.jobs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No pay history is supplied for this occupation.</p>
        )}
        <small>
          {pack.historyNote ??
            `Real pay is in ${priceLabel ?? "constant"} prices; nominal pay is as published. Full-time employees; history, not a forecast.`}
        </small>
      </section>

      <SourceLine pack={pack} hints={[]} />

      {pack.caveats.length > 0 && (
        <section className="dashboard-stats-section" data-section="caveats">
          <h3>Caveats</h3>
          <ul className="dashboard-stats-caveats">
            {pack.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}
