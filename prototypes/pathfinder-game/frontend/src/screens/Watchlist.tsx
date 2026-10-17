import { useEffect, useState } from "react";
import { api } from "../api";
import type { ChangesResponse } from "../types";
import { Spinner } from "../components/ui";
import { MAX_WATCH, type Watched } from "../store";

interface Props {
  list: Watched[];
  onOpen: (soc: string) => void;
  onRemove: (soc: string) => void;
  onExplore: () => void;
}

const ARROW = { up: "↑", down: "↓", same: "→", "no data": "–" } as const;

export function Watchlist({ list, onOpen, onRemove, onExplore }: Props) {
  const [data, setData] = useState<ChangesResponse | null>(null);
  const key = list.map((w) => w.soc).join(",");

  useEffect(() => {
    if (!list.length) return;
    api.changes(list.map((w) => w.soc)).then(setData, () => setData(null));
  }, [key]);

  return (
    <main className="page narrow">
      <p className="eyebrow">Watchlist</p>
      <h1 className="title">What changed.</h1>
      <p className="lede">
        Follow up to {MAX_WATCH} careers. When a new report comes out, you'll see what moved. Your list stays on this device.
      </p>

      {list.length === 0 ? (
        <div className="card empty" style={{ marginTop: 40 }}>
          <div className="icon">☆</div>
          <h2 className="h3">Nothing followed yet</h2>
          <p className="muted small">Tap Follow on any career in your shortlist.</p>
          <button className="btn" onClick={onExplore} style={{ marginTop: 8 }}>Go to your shortlist</button>
        </div>
      ) : !data ? (
        <Spinner />
      ) : (
        <>
          <p className="small muted" style={{ marginTop: 40 }}>
            Hard-to-fill vacancies, {data.previous_edition} compared with {data.latest_edition}. Pay from {data.pay_edition}.
          </p>
          <div className="list">
            {data.items.map((it) => {
              const w = list.find((x) => x.soc === it.soc);
              const isNew = w && w.edition !== data.latest_edition;
              const cls = it.direction === "no data" ? "nodata" : it.direction;
              return (
                <div className="watch-row" key={it.soc}>
                  <div className={`trend ${cls}`} aria-hidden>{ARROW[it.direction]}</div>
                  <div>
                    <button className="btn ghost" style={{ padding: 0, fontSize: 19, fontWeight: 600, color: "var(--text)" }} onClick={() => onOpen(it.soc)}>
                      {it.title}
                    </button>
                    {isNew && <span className="tag blue" style={{ marginLeft: 8 }}>New report</span>}
                    <div className="small muted">
                      {it.message}
                      {it.previous !== null && it.latest !== null && ` (${it.previous}% → ${it.latest}%)`}
                    </div>
                    <div className="small muted">{it.pay_message}</div>
                    <div className="tiny">
                      Jobs by 2035: {it.growth_2035_pct === null ? "no data" : `${it.growth_2035_pct > 0 ? "+" : ""}${it.growth_2035_pct}%`}
                      {it.priority ? " · UK priority" : ""}
                    </div>
                  </div>
                  <button className="btn ghost small" onClick={() => onRemove(it.soc)} aria-label={`Stop following ${it.title}`}>Remove</button>
                </div>
              );
            })}
          </div>
          <p className="tiny" style={{ marginTop: 14 }}>
            ↑ harder to fill means employers need more people with these skills. ↓ means the shortage is easing.
          </p>
        </>
      )}
    </main>
  );
}
