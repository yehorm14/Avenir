import { useEffect, useState } from "react";
import { api } from "../api";
import type { CareerDetail, CareerSummary, ExplainResponse, MatchRequest } from "../types";
import {
  Breakdown, ConfidenceBadge, ScoreRing, ScoreStack, Spinner, SyntheticBanner, money, nationOf, signed,
} from "../components/ui";
import { MAX_WATCH } from "../store";

interface Props {
  soc: string;
  request: MatchRequest | null;
  watching: string[];
  onToggleWatch: (soc: string, title: string) => void;
  onBack: () => void;
  onOpen: (soc: string) => void;
  onPath: (soc: string) => void;
  onPay: (soc: string) => void;
  onProof: () => void;
  backLabel: string;
}

const SUGGESTIONS = ["Why is this ranked here?", "Will AI change this job?", "What's my backup plan?", "How much could I earn?", "What should I study?"];
const NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"];

export function Career({ soc, request, watching, onToggleWatch, onBack, onOpen, onPath, onPay, onProof, backLabel }: Props) {
  const [d, setD] = useState<CareerDetail | null>(null);
  const [a, setA] = useState<CareerSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [ans, setAns] = useState<ExplainResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [focus, setFocus] = useState<string | null>(null);
  const [nation, setNation] = useState(nationOf(request?.region ?? "UK-wide"));

  useEffect(() => {
    setD(null);
    setA(null);
    setAns(null);
    api.career(soc).then(setD, (e) => setErr(String(e.message ?? e)));
  }, [soc]);

  useEffect(() => {
    if (!request) return;
    api.analyse({ ...request, soc }).then(setA, () => setA(null));
  }, [soc, request]);

  const ask = async (question: string) => {
    if (!request || !question.trim()) return;
    setQ(question);
    setAsking(true);
    try {
      setAns(await api.explain({ ...request, soc, question }));
    } catch (e) {
      setAns(null);
      setErr(String((e as Error).message));
    } finally {
      setAsking(false);
    }
  };

  if (err && !d) return <main className="page narrow"><div className="notice warn">Couldn't load this career ({err}).</div></main>;
  if (!d) return <Spinner />;

  const f = d.figures;
  const on = watching.includes(soc);
  const srcName = (id: string) => d.sources.find((s) => s.id === id)?.name ?? id;
  const routes = d.routes.filter((r) => r.nation === nation || r.nation === "UK");

  return (
    <main className="page narrow">
      <button className="back" onClick={onBack}>‹ {backLabel}</button>
      <p className="eyebrow">{f.sector ?? "Career"}{f.priority ? " · UK priority occupation" : ""}</p>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <h1 className="title">{d.title}</h1>
        <div className="row" style={{ marginTop: 8, gap: 8 }}>
          <button className="btn small" onClick={() => onPath(d.soc)}>Build my path ›</button>
          <button
            className={`btn small ${on ? "on" : "soft"}`}
            disabled={!on && watching.length >= MAX_WATCH}
            onClick={() => onToggleWatch(d.soc, d.title)}
          >
            {on ? "Following" : "Follow"}
          </button>
        </div>
      </div>
      <p className="lede">{d.summary}</p>
      <div className="row" style={{ marginTop: 14, gap: 10 }}>
        {a?.confidence && <ConfidenceBadge c={a.confidence} />}
        <span className="tiny">SOC 2020 {d.soc} · {d.soc_title}</span>
      </div>

      <div className="tiles" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        <div className="card tile">
          <div className="k">Median pay</div>
          {f.pay_median === null ? <div className="v nodata">No data</div> : <div className="v">{money(f.pay_median)}</div>}
          <div className="s">{f.pay_p25 !== null && f.pay_p75 !== null ? `Middle half ${money(f.pay_p25)} to ${money(f.pay_p75)}` : "Sample too small to publish"}{f.pay_quality === "use with caution" ? " · use with caution" : ""}</div>
          {f.pay_median !== null && <button className="hedge-link" style={{ fontSize: 13, marginTop: 4 }} onClick={() => onPay(d.soc)}>Over time, in real terms ›</button>}
        </div>
        <div className="card tile">
          <div className="k">Jobs by 2035</div>
          {f.growth_2035_pct === null ? <div className="v nodata">No data</div> : <div className="v">{signed(f.growth_2035_pct)}%</div>}
          <div className="s">Projected change, Skills England 2026</div>
        </div>
        <div className="card tile">
          <div className="k">Hard to fill now</div>
          {f.ssv_latest === null ? <div className="v nodata">No data</div> : <div className="v">{f.ssv_latest}%</div>}
          <div className="s">of vacancies, {f.latest_edition}</div>
        </div>
        <div className="card tile">
          <div className="k">AI exposure</div>
          {f.ai_exposure === null ? <div className="v nodata">No data</div> : <div className="v">{f.ai_exposure.toFixed(2)}</div>}
          <div className="s">0 = no tasks, 1 = all tasks (ILO)</div>
        </div>
      </div>

      {a && (
        <section className="card" style={{ display: "grid", gap: 16 }}>
          {a.rank === 0 && (
            <div className="notice warn">
              This career sits below our interest cut-off for you, so it is not in your picks. You can still explore it.
            </div>
          )}
          <div className="career-top">
            <div>
              <h2 className="h3">{a.rank > 0 ? `Number ${a.rank} of the careers that fit you` : "How it scores for you"}</h2>
              <p className="small muted" style={{ margin: "4px 0 0" }}>{a.trade_off}</p>
            </div>
            <ScoreRing score={a.score} size={64} />
          </div>
          <ScoreStack career={a} />
          <Breakdown career={a} />
        </section>
      )}

      <section className="sec">
        <div className="first-step">
          <p className="eyebrow">Your first step this month</p>
          <p>{d.first_step}</p>
        </div>
      </section>

      {a?.stress && (
        <section className="sec">
          <h2 className="h2">Stress test</h2>
          <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>
            What if things go the wrong way? A pick holds if it stays in your top {a.stress.keep_within}.
          </p>
          <div className="list">
            {a.stress.scenarios.map((s) => (
              <div className="scen" key={s.id}>
                <span>
                  <b style={{ fontWeight: 600 }}>{s.label}</b>
                  <span className="small muted" style={{ display: "block" }}>{s.description}</span>
                </span>
                <span className={`delta ${s.delta < 0 ? "neg" : ""}`}>{s.delta === 0 ? "±0" : signed(s.delta)}</span>
                <span className={s.holds ? "badge-ok" : "badge-no"}>
                  {s.rank === null ? "Hidden" : s.holds ? `Holds · #${s.rank}` : `Drops · #${s.rank}`}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {a?.hedge && (
        <section className="sec">
          <h2 className="h2">Hedge career</h2>
          <div className="card" style={{ display: "grid", gap: 10 }}>
            <p className="small muted" style={{ margin: 0 }}>If {d.title.toLowerCase()} gets harder, this uses similar strengths but carries different risks.</p>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h3 className="h3">{a.hedge.title}</h3>
              <button className="btn soft small" onClick={() => onOpen(a.hedge!.soc)}>See analysis ›</button>
            </div>
            <div className="mini">
              <div className="panel">
                <h4>Shares</h4>
                {a.hedge.shared.length ? a.hedge.shared.join(", ") : <span className="nodata">Similar interests</span>}
              </div>
              <div className="panel">
                <h4>Spreads the risk</h4>
                {a.hedge.diversifies.join(". ")}
              </div>
            </div>
            <p className="tiny" style={{ margin: 0 }}>
              Similarity {a.hedge.similarity.toFixed(2)}: half interest-profile correlation, half shared subjects and experience.
            </p>
          </div>
        </section>
      )}

      {a?.confidence && (
        <section className="sec">
          <h2 className="h2">How sure are we?</h2>
          <div className="card" style={{ display: "grid", gap: 10 }}>
            <ConfidenceBadge c={a.confidence} />
            <ul style={{ margin: 0, paddingLeft: 18 }} className="small">
              {a.confidence.reasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          </div>
        </section>
      )}

      <section className="sec">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 18 }}>
          <h2 className="h2">Ways in</h2>
          <div className="seg" role="tablist" aria-label="Nation">
            {NATIONS.map((n) => (
              <button key={n} role="tab" aria-selected={nation === n} className={nation === n ? "on" : ""} onClick={() => setNation(n)}>
                {n === "Northern Ireland" ? "NI" : n}
              </button>
            ))}
          </div>
        </div>
        <p className="small muted" style={{ marginTop: -6 }}>Typical level: {d.study_level}</p>
        <div className="list">
          {routes.length === 0 && <div className="list-row"><span className="nodata">No routes recorded yet.</span></div>}
          {routes.map((r) => (
            <div className="list-row" key={r.nation + r.type + r.name}>
              <span><span className={`tag ${r.type === "University" ? "blue" : r.type.includes("Apprenticeship") ? "green" : "orange"}`}>{r.type}</span></span>
              <span>
                <span style={{ fontWeight: 500 }}>{r.name}</span>
                {r.detail && <span className="small muted" style={{ display: "block" }}>{r.detail}</span>}
              </span>
              <span className="small muted">{r.level}</span>
            </div>
          ))}
        </div>
        {d.notes.map((n) => <p className="tiny" key={n} style={{ marginTop: 12 }}>{n}</p>)}
      </section>

      {d.courses.length > 0 && (
        <section className="sec">
          <h2 className="h2">Example courses</h2>
          <div className="list">
            {d.courses.map((c) => (
              <div className="list-row" key={c.subject}>
                <span className="small muted">{c.qualification}</span>
                <span style={{ fontWeight: 500 }}>{c.subject}</span>
                <span style={{ textAlign: "right" }}>
                  {c.median_earnings_15m === null ? <span className="nodata small">No data</span> : <b>{money(c.median_earnings_15m)}</b>}
                  <span className="tiny" style={{ display: "block" }}>median, 15 months after</span>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {f.ai_tasks.length > 0 && (
        <section className="sec">
          <h2 className="h2">Where AI could change the work</h2>
          <div className="card" style={{ display: "grid", gap: 12 }}>
            {f.ai_tasks.map((t) => (
              <div className="pbar" key={t.task} style={{ gridTemplateColumns: "1fr 120px 40px" }}>
                <span>{t.task}</span>
                <span className="track"><span className="fill" style={{ width: `${t.score * 100}%`, display: "block", background: "var(--c-ai)" }} /></span>
                <span className="v">{t.score.toFixed(2)}</span>
              </div>
            ))}
            <p className="tiny" style={{ margin: 0 }}>Exposure means AI could change a task, not that the job disappears. Estimates are contested.</p>
          </div>
        </section>
      )}

      <section className="sec">
        <h2 className="h2">Skills to build</h2>
        <div className="chips">
          {d.skills.map((s) => <span className="chip" key={s} style={{ cursor: "default" }}>{s}</span>)}
        </div>
      </section>

      {d.track.length > 0 && (
        <section className="sec">
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
            <h2 className="h2">Our track record here</h2>
            <button className="btn ghost small" onClick={onProof}>How we grade ourselves ›</button>
          </div>
          {d.track_synthetic && <SyntheticBanner />}
          <div className="trackrec" style={{ marginTop: 14 }}>
            {d.track.map((t) => (
              <div key={t.year}>
                <b>{t.year}</b>
                <div className="tiny">Our signal</div>
                <div className="bar"><i style={{ width: `${t.signal_pct}%`, background: "var(--c-future)" }} /></div>
                <div className="tiny">4 years later</div>
                <div className="bar"><i style={{ width: `${t.outcome_pct ?? 0}%`, background: "var(--c-head)" }} /></div>
                <div className="tiny">{t.employment_change_pct === null ? "no data" : `${signed(t.employment_change_pct)}% jobs`}</div>
              </div>
            ))}
          </div>
          {d.bridge && d.bridge !== "direct" && (
            <p className="tiny" style={{ marginTop: 10 }}>
              Before 2021 this job was coded SOC 2010 {d.soc2010} ({d.bridge === "split" ? "split into several codes" : d.bridge === "new" ? "no direct equivalent" : "renumbered"}), so older years are bridged.
            </p>
          )}
        </section>
      )}

      <section className="sec">
        <h2 className="h2">Ask about this result</h2>
        <div className="card ask">
          {!request ? (
            <p className="muted" style={{ margin: 0 }}>Take the quiz first, so we have a result to explain.</p>
          ) : (
            <>
              <form className="ask-input" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask anything about this result" maxLength={300} aria-label="Your question" />
                <button className="btn small" disabled={asking || !q.trim()}>{asking ? "…" : "Ask"}</button>
              </form>
              <div className="chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip" style={{ fontSize: 14, padding: "6px 14px" }} onClick={() => ask(s)}>{s}</button>
                ))}
              </div>
              {ans && (
                <div style={{ display: "grid", gap: 14 }}>
                  <p className="answer" style={{ margin: 0 }}>
                    {ans.answer.split(/(\[E\d+\])/).map((part, i) => {
                      const m = part.match(/^\[(E\d+)\]$/);
                      return m ? (
                        <button key={i} className="cite" onMouseEnter={() => setFocus(m[1])} onFocus={() => setFocus(m[1])} onClick={() => setFocus(m[1])}>{m[1]}</button>
                      ) : (
                        <span key={i}>{part}</span>
                      );
                    })}
                  </p>
                  <details>
                    <summary className="small muted" style={{ cursor: "pointer" }}>
                      Evidence used · {ans.mode === "ai" ? "written by AI, checked by our validator" : "written from a template, no AI"}
                    </summary>
                    <ul className="evidence" style={{ marginTop: 10 }}>
                      {ans.evidence.filter((e) => ans.cited.includes(e.id)).map((e) => (
                        <li key={e.id} className={focus === e.id ? "hit" : ""}>
                          <b>{e.id}</b>{e.text} <span className="tiny">({srcName(e.source_id)})</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      <section className="sec">
        <h2 className="h3" style={{ marginBottom: 12 }}>Sources</h2>
        <ul className="sources small">
          {d.onet_url && (
            <li className="muted">
              Interest profile: <a href={d.onet_url} target="_blank" rel="noreferrer">O*NET {d.onet_code} {d.onet_title}</a>
            </li>
          )}
          {d.sources.filter((s) => s.scored && s.url).map((s) => (
            <li key={s.id} className="muted">
              <a href={s.url!} target="_blank" rel="noreferrer">{s.name}</a> · {s.publisher}{s.edition ? ` · ${s.edition}` : ""}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
