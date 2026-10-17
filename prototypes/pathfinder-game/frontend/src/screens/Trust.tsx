import { useEffect, useState } from "react";
import { api } from "../api";
import type { DiscoverEval, Source, TrustReport } from "../types";
import { Spinner } from "../components/ui";

export function Trust({ onClear }: { onClear: () => void }) {
  const [list, setList] = useState<Source[] | null>(null);
  const [rep, setRep] = useState<TrustReport | null>(null);
  const [disc, setDisc] = useState<DiscoverEval | null>(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    api.sources().then(setList, () => setList([]));
    api.trust().then(setRep, () => setRep(null));
    api.discoverEval().then(setDisc, () => setDisc(null));
  }, []);

  return (
    <main className="page narrow">
      <p className="eyebrow">Trust</p>
      <h1 className="title">Every number has a home.</h1>
      <p className="lede">Where our figures come from, how we test the AI, and what happens to your data.</p>
      <div className="notice warn" style={{ marginTop: 28 }}>
        This build runs on a demo snapshot. Figures are illustrative until each row has been checked against its source, and
        the track record is synthetic.
      </div>

      <section className="sec">
        <h2 className="h2">Your data</h2>
        <div className="card" style={{ display: "grid", gap: 12 }}>
          <ul className="small" style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }}>
            <li>No account, no name, no email, no school, no location beyond the region you pick.</li>
            <li>Your answers are sent to be scored and are never stored on our servers.</li>
            <li>Your interest profile is worked out for each request, shown to you, then forgotten. AI never ranks careers.</li>
            <li>Answers and your watchlist are kept on this device so you can come back. You can wipe them now.</li>
            <li>No analytics, no ads, no third-party scripts. Designed against the ICO Children's Code.</li>
          </ul>
          <div className="row">
            <button className="btn soft small" onClick={() => { onClear(); setCleared(true); }} disabled={cleared}>
              {cleared ? "Cleared" : "Clear my data on this device"}
            </button>
          </div>
        </div>
      </section>

      <section className="sec">
        <h2 className="h2">AI evaluation</h2>
        {!rep ? <Spinner /> : (
          <div className="card" style={{ display: "grid", gap: 14 }}>
            <div className="grid-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div>
                <div className="big-stat">{rep.validator_passed}/{rep.validator_cases}</div>
                <div className="small muted">Validator cases: unsafe answers rejected, grounded ones accepted</div>
              </div>
              <div>
                <div className="big-stat">{rep.routing_passed}/{rep.routing_cases}</div>
                <div className="small muted">Fallback cases: questions sent to the right evidence</div>
              </div>
            </div>
            <details>
              <summary className="small muted" style={{ cursor: "pointer" }}>See every case</summary>
              <ul className="evidence" style={{ marginTop: 10 }}>
                {rep.cases.map((c) => (
                  <li key={c.id} className="hit">
                    <b style={{ color: c.passed ? "var(--green)" : "var(--red)" }}>{c.passed ? "✓" : "✗"}</b>
                    “{c.input}” · expected {c.expected}, got {c.got}
                  </li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </section>

      {disc && (
        <section className="sec">
          <h2 className="h2">Discovery matcher</h2>
          <div className="list">
            {disc.results.map((r) => (
              <div className="list-row" key={r.name} style={{ gridTemplateColumns: "1fr auto auto" }}>
                <span style={{ fontWeight: 500 }}>{r.name}</span>
                <span className="small">Top 1: <b>{Math.round(r.accuracy_at_1 * 100)}%</b></span>
                <span className="small">Top 3: <b>{Math.round(r.accuracy_at_3 * 100)}%</b></span>
              </div>
            ))}
          </div>
          <p className="tiny" style={{ marginTop: 12 }}>{disc.note} n = {disc.results[0]?.n}.</p>
        </section>
      )}

      <section className="sec">
        <h2 className="h2">Sources</h2>
        {!list ? <Spinner /> : (
          <div className="list">
            {list.map((s) => (
              <div className="list-row" key={s.id} style={{ gridTemplateColumns: "1fr auto" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>
                    {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : s.name}
                  </div>
                  <div className="small muted">{s.gives}</div>
                  <div className="tiny">
                    {s.publisher} · {s.coverage} · {s.licence}
                    {s.edition ? ` · ${s.edition}` : ""}
                  </div>
                </div>
                <div className="row" style={{ gap: 6, justifyContent: "flex-end" }}>
                  <span className={`tag ${s.scored ? "blue" : ""}`}>{s.scored ? "Scored" : "Not scored"}</span>
                  {s.scored && <span className="tag">{s.mode === "live" ? "Live" : "Snapshot"}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="sec">
        <h2 className="h3" style={{ marginBottom: 8 }}>For reviewers</h2>
        <p className="small muted">
          The full scoring specification (<code>docs/scoring-spec.md</code>) and our Children's Code assessment
          (<code>docs/childrens-code-assessment.md</code>) are in the project repository, written for external review.
        </p>
      </section>
    </main>
  );
}
