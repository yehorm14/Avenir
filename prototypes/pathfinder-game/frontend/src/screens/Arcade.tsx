import { useEffect, useState } from "react";
import { api } from "../api";
import type { GameReveal, GameRound } from "../types";
import { Spinner, SyntheticBanner, signed } from "../components/ui";

export function Arcade({ onProof }: { onProof: () => void }) {
  const [years, setYears] = useState<number[] | null>(null);
  const [round, setRound] = useState<GameRound | null>(null);
  const [picks, setPicks] = useState<string[]>([]);
  const [reveal, setReveal] = useState<GameReveal | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [score, setScore] = useState({ played: 0, wins: 0 });

  useEffect(() => {
    api.backtest(false).then((s) => setYears(s.years.map((y) => y.year)), (e) => setErr(String(e.message ?? e)));
  }, []);

  const start = async (year: number) => {
    setBusy(true);
    setReveal(null);
    setPicks([]);
    try {
      setRound(await api.gameRound(year, Math.floor(Math.random() * 1_000_000)));
    } catch (e) {
      setErr(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  };

  const toggle = (soc: string) =>
    setPicks((p) => (p.includes(soc) ? p.filter((x) => x !== soc) : p.length < 3 ? [...p, soc] : p));

  const lock = async () => {
    if (!round || picks.length !== 3) return;
    setBusy(true);
    try {
      const r = await api.gameReveal(round.year, round.seed, picks);
      setReveal(r);
      setScore((s) => ({ played: s.played + 1, wins: s.wins + (r.result === "win" ? 1 : 0) }));
    } catch (e) {
      setErr(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  };

  if (err && !years) return <main className="page narrow"><div className="notice warn">Couldn't load the arcade ({err}).</div></main>;
  if (!years) return <Spinner />;

  return (
    <main className="page narrow">
      <p className="eyebrow">Arcade</p>
      <h1 className="title">Call the year.</h1>
      <p className="lede">
        Travel back in time. You'll see ten careers as they looked then, with only the data that existed. Pick the three you
        think grew most over the next four years, then see how you did against our algorithm.
      </p>
      {score.played > 0 && <p className="small muted" style={{ marginTop: 14 }}>You've beaten the algorithm in {score.wins} of {score.played} rounds this visit.</p>}

      <div className="years" style={{ marginTop: 28 }}>
        {years.map((y) => (
          <button key={y} className={`year ${round?.year === y ? "on" : ""}`} onClick={() => start(y)} disabled={busy}>
            <div className="y">{y}</div>
            <div className="m">Play this year</div>
          </button>
        ))}
        <button className="year" onClick={() => start(years[Math.floor(Math.random() * years.length)])} disabled={busy}>
          <div className="y">Random</div>
          <div className="m">Surprise me</div>
        </button>
      </div>

      {busy && !round && <Spinner />}

      {round && !reveal && (
        <section className="sec">
          {round.synthetic && <div style={{ marginBottom: 16 }}><SyntheticBanner /></div>}
          <h2 className="h2">It's {round.year}.</h2>
          <p className="muted" style={{ marginTop: 6 }}>
            Pick the {round.picks_needed} careers you think will grow most by {round.outcome_year}.{" "}
            <b style={{ color: "var(--text)" }}>{picks.length} of {round.picks_needed} chosen.</b>
          </p>
          <div className="degree-grid" style={{ marginTop: 16 }}>
            {round.candidates.map((c) => (
              <button key={c.soc} className={`cand ${picks.includes(c.soc) ? "on" : ""}`} onClick={() => toggle(c.soc)} aria-pressed={picks.includes(c.soc)}>
                <span className="t">{c.title}</span>
                <span className="d">{c.sector}</span>
                <span className="d">
                  {c.ssv === null ? "No shortage data" : `${c.ssv}% of vacancies hard to fill`} ·{" "}
                  {c.projection_10y_pct === null ? "no projection" : `${signed(c.projection_10y_pct)}% projected`}
                </span>
              </button>
            ))}
          </div>
          <div className="row" style={{ marginTop: 20 }}>
            <button className="btn large" onClick={lock} disabled={picks.length !== 3 || busy}>Lock in my picks</button>
            <span className="small muted">Hint: the algorithm weighs shortages and projections. You may weigh other things.</span>
          </div>
        </section>
      )}

      {reveal && (
        <section className="sec">
          {reveal.synthetic && <div style={{ marginBottom: 16 }}><SyntheticBanner>{reveal.note.replace(/^SYNTHETIC DATA: /, "")}</SyntheticBanner></div>}
          <h2 className="h2">{reveal.result === "win" ? "You beat the algorithm." : reveal.result === "tie" ? "A tie." : "The algorithm edged it."}</h2>
          <p className="muted" style={{ marginTop: 6 }}>{reveal.verdict}</p>

          <div className="vs" style={{ marginTop: 18 }}>
            <div className={`card ${reveal.result === "win" ? "win" : ""}`}>
              <div className="small muted">You</div>
              <div className="big">{signed(reveal.you.avg_change)}%</div>
              <div className="tiny">{reveal.you.beat_median} of 3 beat the median</div>
            </div>
            <div className={`card ${reveal.result === "lose" ? "win" : ""}`}>
              <div className="small muted">Algorithm</div>
              <div className="big">{signed(reveal.algorithm.avg_change)}%</div>
              <div className="tiny">{reveal.algorithm.beat_median} of 3 beat the median</div>
            </div>
            <div className="card">
              <div className="small muted">Best possible</div>
              <div className="big">{signed(reveal.best.avg_change)}%</div>
              <div className="tiny">Hindsight picks</div>
            </div>
          </div>

          <div className="list" style={{ marginTop: 18 }}>
            {reveal.rows.map((r) => (
              <div className="scen" key={r.soc}>
                <span>
                  <b style={{ fontWeight: 600 }}>{r.title}</b>
                  <span className="who" style={{ marginLeft: 8 }}>
                    {r.picked_by_you && <span className="tag blue">You</span>}
                    {r.picked_by_algorithm && <span className="tag">Algorithm</span>}
                    {r.best && <span className="tag green">Top 3</span>}
                  </span>
                  <span className="tiny" style={{ display: "block" }}>{r.sector}</span>
                </span>
                <span className="delta">{signed(r.employment_change_pct)}%</span>
                <span className={r.beat_median ? "badge-ok" : "badge-no"}>{r.beat_median ? "Above median" : "Below median"}</span>
              </div>
            ))}
          </div>
          <p className="tiny" style={{ marginTop: 12 }}>
            Jobs grew {signed(reveal.median_change)}% for the median of these ten between {reveal.year} and {reveal.outcome_year}. {reveal.synthetic ? "" : reveal.note}
          </p>

          <div className="row" style={{ marginTop: 20 }}>
            <button className="btn" onClick={() => start(reveal.year)}>Play {reveal.year} again</button>
            <button className="btn soft" onClick={() => start(years[Math.floor(Math.random() * years.length)])}>Another year</button>
            <button className="btn ghost" onClick={onProof}>How we grade ourselves ›</button>
          </div>
        </section>
      )}
    </main>
  );
}
