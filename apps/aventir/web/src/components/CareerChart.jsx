import { useEffect, useRef, useState } from "react";
import {
  createChart,
  AreaSeries,
  ColorType,
  CrosshairMode,
} from "lightweight-charts";

export const number = (n) => new Intl.NumberFormat("en-GB").format(n);
export const money = (n) =>
  new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);

export function rangePoints(industry, range) {
  const points = industry?.points || [];
  if (range === "ALL" || !points.length) return points;
  const last = new Date(points.at(-1).time);
  last.setUTCFullYear(last.getUTCFullYear() - Number(range[0]));
  return points.filter((p) => p.time >= last.toISOString().slice(0, 10));
}

export function HiringChart({ points, labels, onHover }) {
  const container = useRef(null);
  const hover = useRef(onHover);
  hover.current = onHover;
  useEffect(() => {
    if (!container.current || !points.length) return;
    const chart = createChart(container.current, {
      autoSize: true,
      height: 160,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8c9ba5",
        fontFamily: "DM Sans Variable",
        fontSize: 11,
        attributionLogo: true,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "#ffffff07" },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.18, bottom: 0.08 },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "#00b9e877", labelVisible: false },
        horzLine: { visible: false, labelVisible: false },
      },
      handleScale: {
        mouseWheel: false,
        pinch: true,
        axisPressedMouseMove: false,
      },
      handleScroll: {
        mouseWheel: false,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
    });
    const series = chart.addSeries(AreaSeries, {
      lineColor: "#00b9e8",
      lineWidth: 2,
      topColor: "rgba(0,185,232,0.17)",
      bottomColor: "rgba(0,185,232,0)",
      priceLineVisible: false,
      lastValueVisible: false,
      priceFormat: {
        type: "custom",
        formatter: (n) => `${Math.round(n / 1000)}k`,
        minMove: 1000,
      },
    });
    series.setData(points);
    chart.timeScale().fitContent();
    chart.subscribeCrosshairMove((param) => {
      const point = param.seriesData.get(series);
      if (param.time && point)
        hover.current({
          value: point.value,
          period: labels[param.time] || String(param.time),
        });
      else hover.current(null);
    });
    return () => chart.remove();
  }, [points, labels]);
  return (
    <div
      ref={container}
      className="chart-canvas"
      role="img"
      aria-label={`UK industry vacancies across ${points.length} monthly observations. Latest ${number(points.at(-1)?.value || 0)} vacancies. Use the data table below for exact values.`}
    />
  );
}

export function SkillsChart({ career }) {
  const skills = career.essential.filter((s) => s.kind === "skill").length;
  const knowledge = career.essential.length - skills;
  const rows = [
    ["Essential skills", skills, "cyan"],
    ["Essential knowledge", knowledge, "purple"],
    ["Optional skills & knowledge", career.optional.length, "slate"],
  ];
  const max = Math.max(1, ...rows.map((r) => r[1]));
  return (
    <div className="skills-plot" aria-label="ESCO skill relationship counts">
      {rows.map(([label, value, color]) => (
        <div className="skill-row" key={label}>
          <div>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
          <div className="bar-track">
            <div
              className={`bar-fill ${color}`}
              style={{ width: `${(value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
      <p>
        Skills attached to this occupation, rather than an assessment of your
        abilities.
      </p>
    </div>
  );
}

export function PayChart({ salary }) {
  return (
    <div className="pay-plot">
      <div className="pay-endpoints">
        <div>
          <span>Starter reference</span>
          <strong>{money(salary.min)}</strong>
        </div>
        <div>
          <span>Experienced reference</span>
          <strong>{money(salary.max)}</strong>
        </div>
      </div>
      <div className="salary-line">
        <span />
        <span />
      </div>
      <p>
        Annual pay from the National Careers Service. A reference range, not a
        prediction of your future earnings.
      </p>
      {salary.note && <p>{salary.note}</p>}
    </div>
  );
}

export function Sparkline({ points }) {
  if (!points?.length) return null;
  const values = points.slice(-24).map((p) => p.value);
  const low = Math.min(...values),
    high = Math.max(...values);
  const path = values
    .map(
      (v, i) =>
        `${i === 0 ? "M" : "L"}${(i / Math.max(1, values.length - 1)) * 76},${27 - ((v - low) / (high - low || 1)) * 23}`,
    )
    .join(" ");
  const up = values.at(-1) >= values[0];
  return (
    <svg
      className={`sparkline ${up ? "up" : "down"}`}
      viewBox="0 0 76 30"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}
