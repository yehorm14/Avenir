import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { Inflation, MarketRow, PayResponse } from "../types";
import { PayChart, SERIES_COLORS } from "../components/PayChart";
import { Spinner, SyntheticBanner, signed } from "../components/ui";
import { usePersistent } from "../store";

interface Props {
  partySocs: string[];
  onPath: (soc: string) => void;
}

const FALLBACK = ["2135", "2422", "2232"];
const MAX = 4;
const pounds = (n: number) => `£${Math.round(n).toLocaleString("en-GB")}`;
const TONE = { "Beat inflation": "green", "Kept pace": "blue", "Fell behind": "orange" } as const;

function Calculator({ first, last }: { first: number; last: number }) {
  const [amount, setAmount] = useState(50000);
  const [from, setFrom] = useState(first);
  const [res, setRes] = useState<Inflation | null>(null);
  const years = Array.from({ length: last - 2010 + 1 }, (_, i) => 2010 + i).reverse();

  useEffect(() => {
    const a = Math.max(0, Math.min(10_000_000, Math.round(Number(amount) || 0)));
    const t = window.setTimeout(() => api.inflation(a, from, last).then(setRes, () => setRes(null)), 200);
    return () => window.clearTimeout(t);
  }, [amount, from, last]);

  const need = res?.equivalent ?? 0;
  const pct = need > 0 ? Math.min(100, (Number(amount) / need) * 100) : 100;
  return (
    <div className="card" style={{ display: "grid", gap: 16 }}>
      <div>
        <h2 className="h3">Is it still the same money?</h2>
        <p className="small muted" style={{ margin: "4px 0 0" }}>Prices rise, so the same pay buys less each year.</p>
      </div>
      <div className="row" style={{ gap: 10 }}>
        <label className="calc-field">
          <span className="tiny">In {from} you earned</span>
          <span className="money-input"><i>£</i><input type="number" inputMode="numeric" min={0} max={10000000} step={1000} value={amount} onChange={(e) => setAmount(Number(e.target.value))} aria-label="Amount in pounds" /></span>
        </label>
        <label className="calc-field">
          <span className="tiny">Year</span>
          <select className="mini-sel" value={from} onChange={(e) => setFrom(Number(e.target.value))} aria-label="From year">
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
      </div>
      {res && (
        <>
          <p style={{ margin: 0, fontSize: 19, lineHeight: 1.4, fontWeight: 500, letterSpacing: "-0.015em" }}>{res.sentence}</p>
          <div className="calc-bars" aria-hidden>
            <div><span className="tiny">{pounds(Number(amount) || 0)} today</span><div className="cb"><i style={{ width: `${pct}%`, background: "var(--orange)" }} /></div></div>
            <div><span className="tiny">{pounds(need)} to match the {from} buying power</span><div className="cb"><i style={{ width: "100%", background: "var(--accent)" }} /></div></div>
          </div>
          <p className="tiny" style={{ margin: 0 }}>Prices rose {res.change_pct}% between {res.from_year} and {res.to_year}. {res.note}</p>
        </>
      )}
    </div>
  );
}

function CpiBars({ data }: { data: PayResponse["cpi"] }) {
  const rows = data.filter((d) => d.change_pct !== null && d.year >= 2016);
  const max = Math.max(...rows.map((r) => r.change_pct as number), 1);
  return (
    <div className="cpibars" role="img" aria-label="Inflation each year">
      {rows.map((r) => (
        <div key={r.year} title={`${r.year}: prices up ${r.change_pct}%`}>
          <span className="v">{r.change_pct}%</span>
          <i style={{ height: `${Math.max(4, ((r.change_pct as number) / max) * 70)}px`, background: (r.change_pct as number) >= 5 ? "var(--orange)" : "var(--accent)" }} />
          <span className="y">{String(r.year).slice(2)}</span>
        </div>
      ))}
    </div>
  );
}

export function PayScreen({ partySocs, onPath }: Props) {
  const [chosen, setChosen] = usePersistent<string[] | null>("cp.pay.socs", null);
  const [mode, setMode] = usePersistent<"real" | "nominal">("cp.pay.mode", "real");
  const [focus, setFocus] = useState(0);
  const [year, setYear] = useState<number | null>(null);
  const [data, setData] = useState<PayResponse | null>(null);
  const [rows, setRows] = useState<MarketRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const socs = (chosen ?? (partySocs.length ? partySocs : FALLBACK)).slice(0, MAX);

  useEffect(() => {
    api.market("UK-wide").then((m) => setRows(m.rows), () => setRows([]));
  }, []);
  useEffect(() => {
    setErr(null);
    api.pay(socs).then(setData, (e) => setErr(String(e.message ?? e)));
  }, [socs.join(",")]);

  const titles = useMemo(() => Object.fromEntries(rows.map((r) => [r.soc, r.title])), [rows]);
  const addable = rows.filter((r) => !socs.includes(r.soc)).sort((a, b) => a.title.localeCompare(b.title));
  const remove = (soc: string) => { setChosen(socs.filter((s) => s !== soc)); setFocus(0); };

  const careers = data?.careers ?? [];
  const f = Math.min(focus, Math.max(0, careers.filter((c) => c.series.length).length - 1));
  const base = data?.base_year ?? 2025;
  const label = mode === "real" ? `${base} prices` : "money of the day";

  return (
    <main className="page">
      <p className="eyebrow">Pay and inflation</p>
      <h1 className="title">What your pay is really worth.</h1>
      <p className="lede">
        £50,000 ten years ago and £50,000 now is not the same pay: prices went up, so it buys less. This puts every year in one
        year's money, and shows how wide pay really is, not just the middle.
      </p>

      {data?.synthetic && <div style={{ marginTop: 24 }}><SyntheticBanner>{data.note.replace(/^SYNTHETIC DATA: /, "")}</SyntheticBanner></div>}

      <div className="two" style={{ marginTop: 24, alignItems: "start" }}>
        {data ? <Calculator first={data.first_year} last={data.last_year} /> : <Spinner />}
        <div className="card" style={{ display: "grid", gap: 10 }}>
          <h2 className="h3">Why this happens</h2>
          <p className="small muted" style={{ margin: 0 }}>Prices rose most in 2022 and 2023. Pay that rose less than prices bought less than the year before.</p>
          {data && <CpiBars data={data.cpi} />}
          <p className="tiny" style={{ margin: 0 }}>Prices up each year (CPI), %.</p>
        </div>
      </div>

      <section className="sec" style={{ marginTop: 48 }}>
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
          <h2 className="h2">Pay over time</h2>
          <div className="seg" role="tablist" aria-label="Which pounds">
            <button role="tab" aria-selected={mode === "real"} className={mode === "real" ? "on" : ""} onClick={() => setMode("real")}>Today's money</button>
            <button role="tab" aria-selected={mode === "nominal"} className={mode === "nominal" ? "on" : ""} onClick={() => setMode("nominal")}>Money of the day</button>
          </div>
        </div>
        <p className="muted small" style={{ marginTop: 0, marginBottom: 14 }}>
          {mode === "real"
            ? `Every year in ${base} prices, so the lines show real buying power. The dashed line is the same pay unadjusted, and the gap between them is what inflation took.`
            : "Pounds as they were paid each year. Looks like growth, but it ignores that prices rose too."}{" "}
          The shaded band is the middle half of full-time employees.
        </p>

        <div className="pills" style={{ marginBottom: 12 }}>
          {socs.map((s, i) => (
            <span key={s} className={`chip on ${i === f ? "focus" : ""}`} style={{ cursor: "default", display: "inline-flex", gap: 8, alignItems: "center", background: "var(--surface)", color: "var(--text)", borderColor: SERIES_COLORS[i % 4], borderWidth: i === f ? 2 : 1 }}>
              <span className="sw" style={{ width: 10, height: 10, borderRadius: 3, background: SERIES_COLORS[i % 4] }} />
              <button className="plain" onClick={() => setFocus(i)} aria-pressed={i === f} title="Show the spread band for this career">{titles[s] ?? careers.find((c) => c.soc === s)?.title ?? s}</button>
              {socs.length > 1 && <button className="plain" onClick={() => remove(s)} aria-label={`Remove ${titles[s] ?? s}`}>✕</button>}
            </span>
          ))}
          {socs.length < MAX && (
            <select className="mini-sel" value="" onChange={(e) => e.target.value && setChosen([...socs, e.target.value])} aria-label="Add a career to compare">
              <option value="">Compare another career…</option>
              {addable.map((r) => <option key={r.soc} value={r.soc}>{r.title}</option>)}
            </select>
          )}
          {chosen !== null && <button className="btn ghost small" onClick={() => { setChosen(null); setFocus(0); }}>Use my party</button>}
        </div>

        {err && !data && <div className="notice warn">Couldn't load pay data ({err}).</div>}
        {!data && !err && <Spinner />}
        {data && (
          <div className="card" style={{ padding: "18px 18px 10px", position: "relative" }}>
            {careers.some((c) => c.series.length) ? (
              <PayChart careers={careers} mode={mode} focus={f} year={year} onYear={setYear} baseYear={base} />
            ) : (
              <p className="muted" style={{ margin: 12 }}>ONS publishes no pay figure for these careers, so there is nothing to chart.</p>
            )}
            <p className="tiny" style={{ margin: "6px 6px 8px" }}>Median pay for full-time employees, in {label}. Hover or use the arrow keys to read a year.</p>
          </div>
        )}
      </section>

      {data && (
        <section className="sec" style={{ marginTop: 40 }}>
          <h2 className="h2">The verdict, career by career</h2>
          <div className="pay-grid" style={{ marginTop: 14 }}>
            {careers.map((c, i) => (
              <article className="card" key={c.soc} style={{ display: "grid", gap: 10, alignContent: "start" }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <h3 className="h3"><span className="sw" style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: SERIES_COLORS[i % 4], marginRight: 8 }} />{c.title}</h3>
                  {c.summary && <span className={`tag ${TONE[c.summary.verdict]}`}>{c.summary.verdict}</span>}
                </div>
                {c.summary ? (
                  <>
                    <p className="small" style={{ margin: 0 }}>{c.summary.sentence}</p>
                    <div className="stats">
                      <div><div className="k">{c.summary.first_year}</div><div className="v">{pounds(c.summary.median_then)}</div><div className="s">on the payslip</div></div>
                      <div><div className="k">Same in {c.summary.last_year} money</div><div className="v">{pounds(c.summary.median_then_today)}</div><div className="s">buying power</div></div>
                      <div><div className="k">{c.summary.last_year}</div><div className="v">{pounds(c.summary.median_now)}</div><div className="s">on the payslip</div></div>
                    </div>
                    <p className="small" style={{ margin: 0 }}>
                      <b>Spread:</b> the middle half now spans {pounds(c.summary.spread_now)}, {c.summary.spread_change_pct >= 0 ? "wider" : "narrower"} than in {c.summary.first_year} ({signed(Math.round(c.summary.spread_change_pct))}% in real terms).
                      {c.summary.spread_change_pct > 5 ? " Where you land in the range matters more than it used to." : ""}
                    </p>
                    {c.quality === "use with caution" && <p className="tiny" style={{ margin: 0, color: "var(--orange)" }}>ONS flags this estimate "use with caution".</p>}
                  </>
                ) : (
                  <p className="small nodata" style={{ margin: 0 }}>No data. ONS does not publish a reliable pay figure for this occupation, so we don't make one up.</p>
                )}
                <button className="hedge-link" style={{ justifySelf: "start", fontSize: 14 }} onClick={() => onPath(c.soc)}>Open the quest map ›</button>
              </article>
            ))}
          </div>

          <details className="card" style={{ marginTop: 16 }}>
            <summary className="small" style={{ cursor: "pointer", fontWeight: 600 }}>See the numbers</summary>
            <div className="scroll-x" style={{ marginTop: 12 }}>
              <table className="tbl">
                <thead>
                  <tr><th>Year</th><th className="num">CPI</th>{careers.filter((c) => c.series.length).map((c) => <th key={c.soc} className="num">{c.title}: median, {mode === "real" ? `${base} money` : "on the day"} (middle half)</th>)}</tr>
                </thead>
                <tbody>
                  {(careers.find((c) => c.series.length)?.series ?? []).map((p, idx) => (
                    <tr key={p.year}>
                      <td>{p.year}</td>
                      <td className="num">{p.cpi}</td>
                      {careers.filter((c) => c.series.length).map((c) => {
                        const b = mode === "real" ? c.series[idx].real : c.series[idx].nominal;
                        return <td className="num" key={c.soc}>{pounds(b.median)} <span className="tiny">({Math.round(b.p25 / 1000)}k to {Math.round(b.p75 / 1000)}k)</span></td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <p className="tiny" style={{ marginTop: 14 }}>
            Median, not average: a few very high earners pull an average up, so the median is the pay of the person in the middle.
            The middle half runs from the 25th to the 75th percentile. Careers guidance, not financial advice.
          </p>
        </section>
      )}
    </main>
  );
}
