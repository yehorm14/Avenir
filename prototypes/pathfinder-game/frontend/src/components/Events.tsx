import { useState } from "react";
import type { CareerSummary } from "../types";
import { signed } from "./ui";

function Bar({ label, value, base, color }: { label: string; value: number; base: number; color: string }) {
  return (
    <div className="ebar">
      <span>{label}</span>
      <span className="t">
        <i style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: color }} />
        <span className="base" style={{ left: `${Math.max(0, Math.min(100, base))}%` }} title="Before the event" />
      </span>
      <b style={{ fontVariantNumeric: "tabular-nums" }}>{Math.round(value)}</b>
    </div>
  );
}

/** Random events from the stress test. You split your effort between this pick and your backup,
 *  and see how the party copes. Scores come from the same formula as the rest of the app. */
export function Events({ a, onOpen }: { a: CareerSummary; onOpen: (soc: string) => void }) {
  const st = a.stress;
  const hedge = a.hedge;
  const [split, setSplit] = useState(hedge ? 70 : 100);
  if (!st) return null;
  const w = split / 100;
  const mix = (pick: number, backup: number | null) => (backup === null || !hedge ? pick : w * pick + (1 - w) * backup);
  const base = mix(st.baseline, st.hedge_baseline);
  const rows = st.scenarios.map((s) => ({ ...s, party: mix(s.score, s.hedge_score) }));
  const worst = Math.min(...rows.map((r) => r.party));
  const drop = base - worst;
  const rating = drop < 4 ? { t: "Sturdy", c: "green" } : drop < 8 ? { t: "Wobbly", c: "orange" } : { t: "Fragile", c: "red" };

  return (
    <div style={{ display: "grid", gap: 14 }}>
      {hedge ? (
        <div className="card" style={{ display: "grid", gap: 12 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="small muted">Your backup</div>
              <button className="hedge-link" onClick={() => onOpen(hedge.soc)}>{hedge.title} ›</button>
              <span className="tiny" style={{ marginLeft: 8 }}>{hedge.diversifies[0]}</span>
            </div>
            <span className={`resil tag ${rating.c}`} title="Worst event compared with your starting score">
              {rating.t}: worst case {Math.round(worst)} from {Math.round(base)}
            </span>
          </div>
          <label className="slider">
            <span className="slider-head">
              <span>Split your effort</span>
              <b>{split}% {a.title.toLowerCase()} · {100 - split}% {hedge.title.toLowerCase()}</b>
            </span>
            <input type="range" min={0} max={100} step={10} value={split} onChange={(e) => setSplit(Number(e.target.value))} aria-label="Effort split between your pick and your backup" />
          </label>
        </div>
      ) : (
        <div className="notice">No backup career in your matches spreads the risk, so events show your pick alone.</div>
      )}

      <div className="list">
        {rows.map((r) => (
          <div className="event" key={r.id}>
            <div>
              <b>{r.label}</b>
              <span className="small muted" style={{ display: "block" }}>{r.description}</span>
            </div>
            <div className="event-bars">
              <Bar label={a.title.length > 14 ? "Your pick" : a.title} value={r.score} base={st.baseline} color="var(--c-I)" />
              {hedge && r.hedge_score !== null && <Bar label="Backup" value={r.hedge_score} base={st.hedge_baseline ?? 0} color="var(--c-S)" />}
              {hedge && <Bar label="Party" value={r.party} base={base} color="var(--accent)" />}
            </div>
            <span className="tiny">
              Your pick {r.delta === 0 ? "is unaffected" : `${signed(r.delta)} points`}
              {r.rank === null ? " and drops out of your matches" : ` and ranks #${r.rank} for you`}.
            </span>
          </div>
        ))}
      </div>
      <p className="tiny" style={{ margin: 0 }}>
        A game score from our own formula, not a forecast. The tick on each bar marks the score before the event.
      </p>
    </div>
  );
}
