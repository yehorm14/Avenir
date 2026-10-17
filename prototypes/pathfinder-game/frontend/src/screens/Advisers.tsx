import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { Market, MarketRow } from "../types";
import { Spinner, moneyK, signed } from "../components/ui";

type Key = "title" | "sector" | "growth_2035_pct" | "ssv_latest" | "pay_median" | "ai_exposure" | "data_confidence";

const COLS: { key: Key; label: string; num?: boolean }[] = [
  { key: "title", label: "Career" },
  { key: "sector", label: "Sector" },
  { key: "growth_2035_pct", label: "Jobs by 2035", num: true },
  { key: "ssv_latest", label: "Hard to fill", num: true },
  { key: "pay_median", label: "Median pay", num: true },
  { key: "ai_exposure", label: "AI exposure", num: true },
  { key: "data_confidence", label: "Data" },
];
const CONF_ORDER = { High: 3, Medium: 2, Low: 1 };

export function Advisers({ region: initial, onOpen }: { region: string; onOpen: (soc: string) => void }) {
  const [region, setRegion] = useState(initial);
  const [m, setM] = useState<Market | null>(null);
  const [sort, setSort] = useState<{ key: Key; dir: 1 | -1 }>({ key: "growth_2035_pct", dir: -1 });
  const [priorityOnly, setPriorityOnly] = useState(false);

  useEffect(() => {
    setM(null);
    api.market(region).then(setM);
  }, [region]);

  const rows = useMemo(() => {
    if (!m) return [];
    const val = (r: MarketRow): number | string | null =>
      sort.key === "data_confidence" ? CONF_ORDER[r.data_confidence] : (r[sort.key] as number | string | null);
    return [...m.rows]
      .filter((r) => !priorityOnly || r.priority)
      .sort((a, b) => {
        const va = val(a), vb = val(b);
        if (va === null) return 1;
        if (vb === null) return -1;
        return (va < vb ? -1 : va > vb ? 1 : 0) * sort.dir;
      });
  }, [m, sort, priorityOnly]);

  return (
    <main className="page">
      <p className="eyebrow">For careers advisers</p>
      <h1 className="title">The labour market at a glance.</h1>
      <p className="lede">
        Every career in Pathfinder, with the same evidence pupils see. Use it alongside a pupil's printed picks, for Gatsby
        Benchmark 2: learning from career and labour market information.
      </p>

      <div className="row" style={{ margin: "32px 0 16px", justifyContent: "space-between" }}>
        <select className="select" value={region} onChange={(e) => setRegion(e.target.value)} aria-label="Region">
          {(m?.regions ?? [region]).map((r) => <option key={r} value={r}>{r === "UK-wide" ? "Anywhere in the UK" : r}</option>)}
        </select>
        <label className="small row" style={{ gap: 8, cursor: "pointer" }}>
          <input type="checkbox" checked={priorityOnly} onChange={(e) => setPriorityOnly(e.target.checked)} />
          UK priority occupations only
        </label>
      </div>

      {!m ? <Spinner /> : (
        <div className="card scroll-x" style={{ padding: 0 }}>
          <table className="tbl">
            <thead>
              <tr>
                {COLS.map((c) => (
                  <th
                    key={c.key}
                    className={c.num ? "num" : ""}
                    onClick={() => setSort((s) => ({ key: c.key, dir: s.key === c.key ? (s.dir === 1 ? -1 : 1) : c.num ? -1 : 1 }))}
                    aria-sort={sort.key === c.key ? (sort.dir === 1 ? "ascending" : "descending") : "none"}
                  >
                    {c.label} {sort.key === c.key ? (sort.dir === 1 ? "↑" : "↓") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.soc}>
                  <td>
                    <button className="hedge-link" style={{ fontSize: 14 }} onClick={() => onOpen(r.soc)}>{r.title}</button>
                    {r.priority && <span className="tag blue" style={{ marginLeft: 6 }}>Priority</span>}
                    <span className="tiny" style={{ display: "block" }}>SOC {r.soc} · {r.riasec_code}</span>
                  </td>
                  <td className="small muted">
                    {r.sector}
                    {r.region_multiplier !== 1 && <span className="tiny" style={{ display: "block" }}>regional ×{r.region_multiplier}</span>}
                  </td>
                  <td className="num">{r.growth_2035_pct === null ? <span className="nodata">No data</span> : `${signed(r.growth_2035_pct)}%`}</td>
                  <td className="num">{r.ssv_latest === null ? <span className="nodata">No data</span> : `${r.ssv_latest}%`}</td>
                  <td className="num">{r.pay_median === null ? <span className="nodata">No data</span> : moneyK(r.pay_median)}</td>
                  <td className="num">{r.ai_exposure === null ? <span className="nodata">No data</span> : r.ai_exposure.toFixed(2)}</td>
                  <td><span className={`conf ${r.data_confidence}`}>{r.data_confidence}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="tiny" style={{ marginTop: 14 }}>
        "Data" rates how complete and reliable the evidence is for each career. Regional multipliers adjust demand, not pay.
        Demo snapshot: check figures against the sources before advising.
      </p>
    </main>
  );
}
