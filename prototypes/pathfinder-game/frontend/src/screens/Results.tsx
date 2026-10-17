import type { CareerSummary, MatchResponse, Weights } from "../types";
import {
  Breakdown, COLOR, ConfidenceBadge, LETTER_NAME, ProfileBars, SIGNALS, ScoreRing, ScoreStack, Spinner, moneyK, signed,
} from "../components/ui";
import { DEFAULT_WEIGHTS, MAX_WATCH } from "../store";

interface Props {
  result: MatchResponse | null;
  error: string | null;
  weights: Weights;
  onWeights: (w: Weights) => void;
  region: string;
  watching: string[];
  onToggleWatch: (soc: string, title: string) => void;
  onOpen: (soc: string) => void;
  onPath: (soc: string) => void;
  onRadar: () => void;
  onPay: (soc: string) => void;
  onRetake: () => void;
  onEditAbout: () => void;
}

function Factsheet({ c, idx, watching, onToggleWatch, onOpen, onPath, onPay }: {
  c: CareerSummary; idx: number; watching: string[];
  onToggleWatch: (soc: string, title: string) => void; onOpen: (soc: string) => void; onPath: (soc: string) => void; onPay: (soc: string) => void;
}) {
  const on = watching.includes(c.soc);
  const full = !on && watching.length >= MAX_WATCH;
  const f = c.figures;
  return (
    <article className="card career" style={{ animationDelay: `${idx * 70}ms` }}>
      <div className="career-top">
        <div>
          <div className="rank">
            Party member {c.rank} · {c.sector ?? "Other"}
            {c.priority && <span className="tag blue" style={{ marginLeft: 8 }}>UK priority</span>}
          </div>
          <h2 className="h2">{c.title}</h2>
          <p className="small muted" style={{ margin: "4px 0 10px" }}>{c.summary}</p>
          {c.confidence && <ConfidenceBadge c={c.confidence} />}
        </div>
        <ScoreRing score={c.score} />
      </div>

      <div className="stats">
        <div>
          <div className="k">Median pay</div>
          <div className={`v ${f.pay_median === null ? "nodata" : ""}`}>{moneyK(f.pay_median)}</div>
          <div className="s">{f.pay_p25 !== null && f.pay_p75 !== null ? `${moneyK(f.pay_p25)} to ${moneyK(f.pay_p75)}` : "ONS ASHE"}</div>
          {f.pay_median !== null && <button className="hedge-link" style={{ fontSize: 12, marginTop: 2 }} onClick={() => onPay(c.soc)}>Over time, real terms ›</button>}
        </div>
        <div>
          <div className="k">Jobs by 2035</div>
          <div className={`v ${f.growth_2035_pct === null ? "nodata" : ""}`}>{f.growth_2035_pct === null ? "No data" : `${signed(f.growth_2035_pct)}%`}</div>
          <div className="s">{f.region_multiplier !== 1 ? `Regional demand ×${f.region_multiplier}` : "UK-wide"}</div>
        </div>
        <div>
          <div className="k">AI exposure</div>
          <div className={`v ${f.ai_exposure === null ? "nodata" : ""}`}>{f.ai_exposure === null ? "No data" : f.ai_exposure.toFixed(2)}</div>
          <div className="s">0 none · 1 all tasks</div>
        </div>
      </div>

      <p className="trade">{c.trade_off}</p>
      <ScoreStack career={c} />
      <Breakdown career={c} />

      <div className="mini">
        {c.stress && (
          <div className="panel">
            <h4>Events</h4>
            <div className="dots" aria-hidden>
              {c.stress.scenarios.map((s) => <i key={s.id} className={s.holds ? "" : "off"} title={s.label} />)}
            </div>
            <div>
              Holds in <b>{c.stress.holds} of {c.stress.total}</b> events
              {c.stress.scenarios.some((s) => !s.holds) && (
                <span className="muted"> · drops under {c.stress.scenarios.filter((s) => !s.holds).map((s) => s.label.toLowerCase()).join(", ")}</span>
              )}
            </div>
          </div>
        )}
        <div className="panel">
          <h4>Backup</h4>
          {c.hedge ? (
            <>
              <button className="hedge-link" onClick={() => onOpen(c.hedge!.soc)}>{c.hedge.title} ›</button>
              <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>{c.hedge.diversifies[0]}</div>
            </>
          ) : (
            <span className="nodata">No career in your matches spreads the risk.</span>
          )}
        </div>
      </div>

      <div className="panel path-preview">
        <h4>Quest map</h4>
        <div>{c.degree_role || "Routes in"}</div>
        {c.degrees.length > 0 && <div className="pills">{c.degrees.map((d) => <span className="tag" key={d}>{d}</span>)}</div>}
        <button className="hedge-link" onClick={() => onPath(c.soc)} style={{ justifySelf: "start" }}>Open the quest map: degrees, skills, guilds, mentors ›</button>
      </div>

      <div className="career-actions">
        <span className="tiny">SOC 2020 {c.soc} · {c.soc_title}</span>
        <div className="row" style={{ gap: 8 }}>
          <button
            className={`btn small ${on ? "on" : "soft"}`}
            onClick={() => onToggleWatch(c.soc, c.title)}
            disabled={full}
            title={full ? `You can follow up to ${MAX_WATCH} careers` : undefined}
            aria-pressed={on}
          >
            {on ? "Following" : "Follow"}
          </button>
          <button className="btn soft small" onClick={() => onOpen(c.soc)}>Full analysis</button>
          <button className="btn small" onClick={() => onPath(c.soc)}>Open quest map ›</button>
        </div>
      </div>
    </article>
  );
}

export function Results({ result, error, weights, onWeights, region, watching, onToggleWatch, onOpen, onPath, onPay, onRadar, onRetake, onEditAbout }: Props) {
  if (error) {
    return (
      <main className="page narrow">
        <div className="notice warn">The app can't reach its backend ({error}). Start it with <code>./run.sh</code> in the project folder, keep that terminal open, then refresh this page.</div>
      </main>
    );
  }
  if (!result) return <Spinner />;

  const total = SIGNALS.reduce((s, x) => s + weights[x.key], 0) || 1;
  const isDefault = SIGNALS.every((s) => Math.abs(weights[s.key] - DEFAULT_WEIGHTS[s.key]) < 1e-6);
  const names = result.code.split("").map((l) => LETTER_NAME[l as keyof typeof LETTER_NAME]);
  const n = result.results.length;

  return (
    <main className="page">
      <div className="results-head">
        <div>
          <p className="eyebrow">Your party{region !== "UK-wide" ? ` · ${region}` : ""}</p>
          <h1 className="title">
            {n > 0 ? "Meet your party." : "No strong matches yet."}
          </h1>
          <p className="lede" style={{ marginTop: 12 }}>
            Your interests lean <b style={{ color: "var(--text)" }}>{names.slice(0, 2).join(" and ")}</b>, then {names[2]}. We
            checked {result.considered} careers and hid {result.hidden_low_fit} that don't fit them well enough.
          </p>
        </div>
        <div className="row no-print">
          <button className="btn soft small" onClick={onRadar}>Opportunities radar</button>
          <button className="btn soft small" onClick={onEditAbout}>Edit gear</button>
          <button className="btn soft small" onClick={() => window.print()}>Print for your adviser</button>
          <button className="btn soft small" onClick={onRetake}>Respec</button>
        </div>
      </div>

      <div className="layout">
        <div style={{ display: "grid", gap: 16 }}>
          {result.notes.map((note) => <div className="notice warn" key={note}>{note}</div>)}
          {result.results.map((c, idx) => (
            <Factsheet key={c.soc} c={c} idx={idx} watching={watching} onToggleWatch={onToggleWatch} onOpen={onOpen} onPath={onPath} onPay={onPay} />
          ))}
          {result.more.length > 0 && (
            <div className="card" style={{ padding: 22 }}>
              <h2 className="h3" style={{ marginBottom: 10 }}>Also worth a look</h2>
              <div className="hits">
                {result.more.map((c) => (
                  <div className="hit" key={c.soc}>
                    <span>
                      <b>{c.title}</b>
                      <span className="tiny" style={{ display: "block" }}>Score {Math.round(c.score)} · {c.trade_off}</span>
                    </span>
                    <button className="btn ghost small" onClick={() => onOpen(c.soc)}>Look ›</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="aside">
          <div className="card" style={{ padding: 24 }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 18 }}>
              <h2 className="h3">What matters to you</h2>
              {!isDefault && <button className="btn ghost small" onClick={() => onWeights(DEFAULT_WEIGHTS)}>Reset</button>}
            </div>
            <div style={{ display: "grid", gap: 16 }}>
              {SIGNALS.map((s) => (
                <label className="slider" key={s.key}>
                  <span className="slider-head">
                    <span>
                      <span style={{ display: "inline-block", width: 9, height: 9, borderRadius: 3, background: COLOR[s.key], marginRight: 8 }} />
                      {s.label}
                    </span>
                    <b>{Math.round((weights[s.key] / total) * 100)}%</b>
                  </span>
                  <input
                    type="range" min={0} max={100} step={5}
                    value={Math.round(weights[s.key] * 100)}
                    onChange={(e) => onWeights({ ...weights, [s.key]: Number(e.target.value) / 100 })}
                    aria-label={s.label}
                  />
                </label>
              ))}
            </div>
            <p className="tiny" style={{ marginTop: 16, marginBottom: 0 }}>
              Interest fit is always checked first: careers below {result.fit_threshold} are hidden whatever the weights.
            </p>
          </div>

          <div className="card" style={{ padding: 24 }}>
            <h2 className="h3" style={{ marginBottom: 14 }}>Your interests</h2>
            <ProfileBars profile={result.profile} />
          </div>
        </aside>
      </div>
    </main>
  );
}
