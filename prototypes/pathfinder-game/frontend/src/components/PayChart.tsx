import { useEffect, useMemo, useRef, useState } from "react";
import type { Band, PayCareer } from "../types";

export const SERIES_COLORS = ["var(--c-I)", "var(--c-S)", "var(--c-A)", "var(--c-pay)"];

function useNarrow() {
  const [n, setN] = useState(() => window.innerWidth < 560);
  useEffect(() => {
    const on = () => setN(window.innerWidth < 560);
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return n;
}

const pounds = (n: number) => `£${Math.round(n).toLocaleString("en-GB")}`;
const k = (n: number) => `£${Math.round(n / 1000)}k`;

function niceStep(raw: number): number {
  for (const s of [1000, 2000, 2500, 5000, 10000, 20000, 25000, 50000]) if (raw <= s) return s;
  return 100000;
}

interface Props {
  careers: PayCareer[];
  mode: "real" | "nominal";
  focus: number;
  year: number | null;
  onYear: (y: number | null) => void;
  baseYear: number;
}

/** Median lines for each career, the middle-half band for the focused one, and, when showing
 *  today's money, the unadjusted line (dashed) so the gap inflation opens is visible. */
export function PayChart({ careers, mode, focus, year, onYear, baseYear }: Props) {
  const narrow = useNarrow();
  // A narrower, taller drawing on phones keeps the labels readable instead of shrinking the whole chart.
  const [W, H, L, R, T, B] = narrow ? [380, 340, 46, 14, 14, 32] : [720, 340, 58, 18, 16, 34];
  const ref = useRef<SVGSVGElement>(null);
  const withData = careers.filter((c) => c.series.length > 0);
  const years = withData[0]?.series.map((p) => p.year) ?? [];
  const y0 = years[0], y1 = years[years.length - 1];
  const band = (p: { nominal: Band; real: Band }) => (mode === "real" ? p.real : p.nominal);

  const { lo, hi, ticks } = useMemo(() => {
    const vals: number[] = [];
    withData.forEach((c, i) => {
      c.series.forEach((p) => {
        vals.push(band(p).median);
        if (i === focus) vals.push(band(p).p25, band(p).p75);
        if (mode === "real" && i === focus) vals.push(p.nominal.median);
      });
    });
    if (!vals.length) return { lo: 0, hi: 1, ticks: [0, 1] };
    const step = niceStep((Math.max(...vals) - Math.min(...vals)) / 4);
    const lo = Math.max(0, Math.floor(Math.min(...vals) / step) * step);
    const hi = Math.ceil(Math.max(...vals) / step) * step;
    const t: number[] = [];
    for (let v = lo; v <= hi + 1; v += step) t.push(v);
    return { lo, hi, ticks: t };
  }, [careers, mode, focus, H, T, B]);

  if (!withData.length) return null;
  const x = (yr: number) => L + ((yr - y0) / (y1 - y0)) * (W - L - R);
  const y = (v: number) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const line = (c: PayCareer, pick: (p: PayCareer["series"][number]) => number) => c.series.map((p) => `${x(p.year).toFixed(1)},${y(pick(p)).toFixed(1)}`).join(" ");
  const focusC = withData[Math.min(focus, withData.length - 1)];
  const bandPath = focusC.series.map((p) => `${x(p.year).toFixed(1)},${y(band(p).p75).toFixed(1)}`).join(" ") + " " +
    [...focusC.series].reverse().map((p) => `${x(p.year).toFixed(1)},${y(band(p).p25).toFixed(1)}`).join(" ");

  const setFromPointer = (clientX: number) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const vx = ((clientX - r.left) / r.width) * W;
    const yr = Math.round(y0 + ((vx - L) / (W - L - R)) * (y1 - y0));
    onYear(Math.max(y0, Math.min(y1, yr)));
  };

  const hov = year !== null ? years.includes(year) ? year : null : null;
  const hoverPts = hov === null ? [] : withData.map((c, i) => ({ c, i, p: c.series.find((s) => s.year === hov)! }));
  const left = hov === null ? 0 : (x(hov) / W) > 0.5 ? 27 : 73; // sits on the far side, so it never hides the point you're reading
  const label = mode === "real" ? `${baseYear} prices` : "money of the day";

  return (
    <div className="paychart" tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") onYear(Math.max(y0, (hov ?? y1) - 1));
        else if (e.key === "ArrowRight") onYear(Math.min(y1, (hov ?? y0 - 1) + 1));
        else if (e.key === "Escape") onYear(null);
      }}
      aria-label={`Pay by year, ${y0} to ${y1}, in ${label}. Use the left and right arrow keys to read each year.`}
    >
      <svg ref={ref} viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`Median pay and middle-half spread, in ${label}`}
        onPointerMove={(e) => setFromPointer(e.clientX)} onPointerDown={(e) => setFromPointer(e.clientX)} onPointerLeave={() => onYear(null)}
        style={{ touchAction: "pan-y", display: "block" }}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="var(--line)" strokeWidth="1" />
            <text x={L - 8} y={y(t) + 4} textAnchor="end" fontSize={narrow ? 13 : 12} fill="var(--text-3)">{k(t)}</text>
          </g>
        ))}
        {years.map((yr, i) => (i % 2 === 0) && (
          <text key={yr} x={x(yr)} y={H - 10} textAnchor="middle" fontSize={narrow ? 13 : 12} fill="var(--text-3)">{narrow ? `’${String(yr).slice(2)}` : yr}</text>
        ))}
        <polygon points={bandPath} fill={SERIES_COLORS[focus % 4]} fillOpacity="0.14" />
        {mode === "real" && (
          <polyline points={line(focusC, (p) => p.nominal.median)} fill="none" stroke={SERIES_COLORS[focus % 4]} strokeWidth="2" strokeDasharray="5 5" strokeOpacity="0.7" />
        )}
        {withData.map((c, i) => (
          <polyline key={c.soc} points={line(c, (p) => band(p).median)} fill="none" stroke={SERIES_COLORS[i % 4]} strokeWidth={i === focus ? 3 : 2.2} strokeLinejoin="round" strokeLinecap="round" opacity={i === focus ? 1 : 0.85} />
        ))}
        {hov !== null && (
          <g>
            <line x1={x(hov)} x2={x(hov)} y1={T} y2={H - B} stroke="var(--text-3)" strokeWidth="1" strokeDasharray="3 3" />
            {hoverPts.map(({ c, i, p }) => <circle key={c.soc} cx={x(hov)} cy={y(band(p).median)} r="5" fill={SERIES_COLORS[i % 4]} stroke="var(--surface)" strokeWidth="2" />)}
          </g>
        )}
        {hov === null && withData.map((c, i) => {
          const p = c.series[c.series.length - 1];
          return <circle key={c.soc} cx={x(p.year)} cy={y(band(p).median)} r="4.5" fill={SERIES_COLORS[i % 4]} stroke="var(--surface)" strokeWidth="2" />;
        })}
      </svg>
      {hov !== null && (
        <div className="paytip" style={{ left: `${left}%` }}>
          <b>{hov}</b>
          {hoverPts.map(({ c, i, p }) => (
            <div key={c.soc} className="tiprow">
              <span className="sw" style={{ background: SERIES_COLORS[i % 4] }} />
              <span>{c.title}</span>
              <b>{pounds(band(p).median)}</b>
              <span className="tiny">{k(band(p).p25)} to {k(band(p).p75)}</span>
            </div>
          ))}
          <div className="tiny">In {label}. CPI {hoverPts[0].p.cpi}.</div>
        </div>
      )}
    </div>
  );
}
