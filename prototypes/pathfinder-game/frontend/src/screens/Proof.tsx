import { useEffect, useState } from "react";
import { api } from "../api";
import type { BacktestSummary, Replay, ReplayRow } from "../types";
import { Spinner, SyntheticBanner, signed } from "../components/ui";

const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)}%`);

function Rows({ rows, expectBeat, onOpen }: { rows: ReplayRow[]; expectBeat: boolean; onOpen: (soc: string) => void }) {
  return (
    <div className="list">
      {rows.map((r) => (
        <div className="scen" key={r.soc}>
          <span>
            <button className="hedge-link" style={{ color: "var(--text)" }} onClick={() => onOpen(r.soc)}>{r.title}</button>
            <span className="tiny" style={{ display: "block" }}>
              Then: {r.ssv ?? "—"}% hard to fill · {r.projection_10y_pct === null ? "no projection" : `${signed(r.projection_10y_pct)}% projected`}
              {r.bridge !== "direct" && r.bridge !== "recoded" ? ` · code ${r.bridge}` : ""}
            </span>
          </span>
          <span className="delta">{r.employment_change_pct === null ? "—" : `${signed(r.employment_change_pct)}%`}</span>
          <span className={r.beat_median === expectBeat ? "badge-ok" : "badge-no"} title={r.beat_median === expectBeat ? "Our call was right" : "Our call was wrong"}>
            {r.beat_median ? "Beat median" : "Below median"}
          </span>
        </div>
      ))}
    </div>
  );
}

export function Proof({ onOpen }: { onOpen: (soc: string) => void }) {
  const [clean, setClean] = useState(false);
  const [sum, setSum] = useState<BacktestSummary | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [rep, setRep] = useState<Replay | null>(null);

  useEffect(() => {
    api.backtest(clean).then((s) => {
      setSum(s);
      setYear((y) => y ?? s.years[0]?.year ?? null);
    });
  }, [clean]);

  useEffect(() => {
    if (year === null) return;
    setRep(null);
    api.replay(year, clean).then(setRep);
  }, [year, clean]);

  if (!sum) return <Spinner />;

  const pickRandom = () => {
    const ys = sum.years.map((y) => y.year).filter((y) => y !== year);
    setYear(ys[Math.floor(Math.random() * ys.length)]);
  };

  return (
    <main className="page">
      <p className="eyebrow">Proof</p>
      <h1 className="title">We grade our own signal.</h1>
      <p className="lede">
        For each past year we rebuild our demand signal from the data published that year, with no peeking ahead, then check
        what happened to jobs {sum.horizon_years} years later.
      </p>

      {sum.synthetic && <div style={{ marginTop: 28 }}><SyntheticBanner>{sum.caveats[0]}</SyntheticBanner></div>}

      <div className="grid-3" style={{ marginTop: 28 }}>
        <div className="card">
          <div className="k small muted">Top-third hit rate</div>
          <div className="big-stat" style={{ marginTop: 8 }}>{pct(sum.pooled_hit_rate)}</div>
          <p className="tiny" style={{ marginBottom: 0 }}>Our top third beat the median job growth this often. Chance is 50%.</p>
        </div>
        <div className="card">
          <div className="k small muted">Average rank correlation</div>
          <div className="big-stat" style={{ marginTop: 8 }}>{sum.mean_spearman === null ? "—" : sum.mean_spearman.toFixed(2)}</div>
          <p className="tiny" style={{ marginBottom: 0 }}>Spearman, signal against employment change. 0 is no link, 1 is perfect.</p>
        </div>
        <div className="card">
          <div className="k small muted">Occupation-years graded</div>
          <div className="big-stat" style={{ marginTop: 8 }}>{sum.pooled_n}</div>
          <p className="tiny" style={{ marginBottom: 0 }}>Few, and confounded. Indicative, not proof.</p>
        </div>
      </div>
      <p className="small" style={{ marginTop: 18 }}>{sum.verdict}</p>

      <div className="row" style={{ justifyContent: "space-between", marginTop: 48, marginBottom: 16 }}>
        <h2 className="h2">Pick a past year</h2>
        <div className="row">
          <label className="small row" style={{ gap: 8, cursor: "pointer" }}>
            <input type="checkbox" checked={clean} onChange={(e) => setClean(e.target.checked)} />
            Exclude bridged codes
          </label>
          <button className="btn soft small" onClick={pickRandom}>Random year</button>
        </div>
      </div>
      <div className="years" role="tablist">
        {sum.years.map((y) => (
          <button key={y.year} role="tab" aria-selected={year === y.year} className={`year ${year === y.year ? "on" : ""}`} onClick={() => setYear(y.year)}>
            <div className="y">{y.year}</div>
            <div className="m">to {y.outcome_year} · hit {pct(y.hit_rate)}</div>
          </button>
        ))}
      </div>

      {!rep ? <Spinner /> : (
        <section style={{ marginTop: 28 }}>
          <p className="muted">
            In {rep.year}, this is what Pathfinder would have said, using only data published then. By {rep.outcome_year}, the
            median career grew {rep.median_change === null ? "—" : `${signed(rep.median_change)}%`}. Green means our call was right.
          </p>
          <div className="mini" style={{ gap: 20 }}>
            <div>
              <h3 className="h3" style={{ marginBottom: 12 }}>Our top 5 in {rep.year}</h3>
              <Rows rows={rep.top} expectBeat onOpen={onOpen} />
            </div>
            <div>
              <h3 className="h3" style={{ marginBottom: 12 }}>Our bottom 5 in {rep.year}</h3>
              <Rows rows={rep.bottom} expectBeat={false} onOpen={onOpen} />
            </div>
          </div>
          <p className="tiny" style={{ marginTop: 12 }}>
            {rep.year}: {rep.metrics.n} careers graded · rank correlation {rep.metrics.spearman?.toFixed(2) ?? "—"} · top third
            averaged {rep.metrics.top_third_change === null ? "—" : `${signed(rep.metrics.top_third_change)}%`} against{" "}
            {rep.metrics.bottom_third_change === null ? "—" : `${signed(rep.metrics.bottom_third_change)}%`} for the bottom third.
          </p>
        </section>
      )}

      <section className="sec">
        <h2 className="h3" style={{ marginBottom: 12 }}>What this can and can't tell you</h2>
        <ul className="small muted" style={{ paddingLeft: 18, display: "grid", gap: 6 }}>
          {sum.caveats.slice(sum.synthetic ? 1 : 0).map((c) => <li key={c}>{c}</li>)}
        </ul>
      </section>
    </main>
  );
}
