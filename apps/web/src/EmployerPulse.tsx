import { useEffect, useState } from "react";
import type { Career, HistoryPoint } from "./types";
import { historySegments } from "./historySegments";
import {
  buildEmployerPulse,
  employerDataUrl,
  formatPay,
  parseEmployerData,
  pulseTabs,
  type EmployerData,
  type EmployerView,
  type PulseTab,
  type SourceLink,
} from "./employerPulseModel";
import "./employerPulse.css";

function PulseChart({
  history,
  priceLabel,
  title,
}: {
  history: HistoryPoint[];
  priceLabel: string;
  title: string;
}) {
  const key = "pay_median_real" as const;
  const points = history.filter((point) => typeof point[key] === "number");
  const years = points.map((point) => point.year);
  const values = points.map((point) => point[key] as number);
  if (points.length < 2)
    return (
      <p className="pulse-chart-empty">
        Historical pay data isn't available for this occupation yet.
      </p>
    );
  const W = 520,
    H = 150,
    L = 46,
    R = 14,
    T = 12,
    B = 24;
  const y0 = years[0],
    y1 = years[years.length - 1];
  const max = Math.max(...values) * 1.08,
    min = Math.max(0, Math.min(...values) * 0.84),
    range = max - min || 1;
  const x = (v: number) => L + ((v - y0) / (y1 - y0 || 1)) * (W - L - R),
    y = (v: number) => T + ((max - v) / range) * (H - T - B);
  const last = points[points.length - 1];
  const bridged = points.some((point) =>
    point.flags.some((flag) => flag.startsWith("bridged_")),
  );
  return (
    <figure className="pulse-chart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${title}: real median pay in ${priceLabel}, ${y0} to ${y1}. ${formatPay(values[0])} in ${y0}, ${formatPay(last[key] as number)} in ${y1}.`}
      >
        {[0, 0.5, 1].map((t) => (
          <g key={t}>
            <line
              x1={L}
              x2={W - R}
              y1={y(min + t * range)}
              y2={y(min + t * range)}
              className="pulse-grid"
            />
            <text x={L - 8} y={y(min + t * range) + 4} textAnchor="end">
              £{Math.round((min + t * range) / 1000)}k
            </text>
          </g>
        ))}
        {[y0, Math.round((y0 + y1) / 2), y1]
          .filter((year, index, all) => all.indexOf(year) === index)
          .map((year) => (
            <text key={year} x={x(year)} y={H - 6} textAnchor="middle">
              {year}
            </text>
          ))}
        {historySegments(history, key).map((segment, index) => (
          <polyline
            key={index}
            points={segment
              .map((point) => `${x(point.year)},${y(point[key] as number)}`)
              .join(" ")}
            fill="none"
            className="pulse-line"
            strokeDasharray={
              segment[segment.length - 1]?.flags.some((flag) =>
                flag.startsWith("bridged_"),
              )
                ? "5 4"
                : undefined
            }
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}
        <circle
          cx={x(last.year)}
          cy={y(last[key] as number)}
          r="4.5"
          className="pulse-dot"
        />
      </svg>
      <figcaption>
        Real median pay, {y0}–{y1}, {priceLabel}. ONS ASHE, full-time employees.
        {bridged ? " Dashed years use estimated older occupation codes." : ""}
      </figcaption>
    </figure>
  );
}

function TrendBadge({
  trend,
  positive,
  label,
}: {
  trend: string | null;
  positive: boolean | null;
  label: string;
}) {
  if (!trend) return null;
  return (
    <span
      className={`pulse-badge ${positive ? "is-up" : "is-down"}`}
      title={label}
    >
      {trend}
      <small>
        {label === "Employment trend vs typical" ? "vs typical" : ""}
      </small>
    </span>
  );
}

function Source({ link }: { link: SourceLink }) {
  return (
    <a href={link.href} target="_blank" rel="noreferrer">
      {link.label}
    </a>
  );
}

function CareerLadder({ ladder }: { ladder: EmployerView["ladder"] }) {
  return (
    <figure className="pulse-ladder" aria-labelledby="pulse-ladder-title">
      <h3 id="pulse-ladder-title">{ladder.title}</h3>
      <p className="pulse-ladder-sub">
        Base pay ranges by level, £k a year, with the number of salary reports
        behind each range.
      </p>
      <div className="pulse-ladder-chart">
        <ol className="pulse-ladder-rows">
          {ladder.rows.map((row) => (
            <li
              key={row.level}
              aria-label={`${row.level}: ${row.range}, ${row.reports}`}
            >
              <span className="pulse-ladder-level">{row.level}</span>
              <svg
                className="pulse-ladder-track"
                width="100%"
                height="18"
                aria-hidden="true"
                focusable="false"
              >
                {ladder.ticks.map((tick) => (
                  <line
                    key={tick.label}
                    x1={`${tick.pct}%`}
                    x2={`${tick.pct}%`}
                    y1="0"
                    y2="18"
                    className="pulse-grid"
                  />
                ))}
                <rect
                  x={`${row.lowPct}%`}
                  width={`${Math.max(row.highPct - row.lowPct, 1)}%`}
                  y="3"
                  height="12"
                  rx="6"
                  className="pulse-ladder-bar"
                />
              </svg>
              <span className="pulse-ladder-figures">
                <b>{row.range}</b>
                <small>{row.reports}</small>
              </span>
            </li>
          ))}
        </ol>
        <div className="pulse-ladder-axis" aria-hidden="true">
          <span className="pulse-ladder-level" />
          <span className="pulse-ladder-ticks">
            {ladder.ticks.map((tick) => (
              <i key={tick.label} style={{ left: `${tick.pct}%` }}>
                {tick.label}
              </i>
            ))}
          </span>
          <span className="pulse-ladder-figures" />
        </div>
      </div>
      <figcaption>
        Source: <Source link={ladder.source} />. {ladder.note}
      </figcaption>
    </figure>
  );
}

function EmployerFacts({ employer }: { employer: EmployerView }) {
  return (
    <dl className="pulse-facts">
      {employer.facts.map((fact) => (
        <div key={fact.label}>
          <dt>{fact.label}</dt>
          <dd>
            <b>{fact.value}</b>
            {fact.note ? <small>{fact.note}</small> : null}
            <small>
              <Source link={fact.source} />
            </small>
          </dd>
        </div>
      ))}
    </dl>
  );
}

function ShareTile({ share }: { share: EmployerView["share"] }) {
  return (
    <div className="pulse-share" aria-label={share.headline}>
      <span className="pulse-share-label">Share price, not pay</span>
      <span className="pulse-share-figures">
        <b>
          {share.ticker} {share.price}
        </b>
        <span className={`pulse-badge ${share.positive ? "is-up" : ""}`}>
          {share.change}
          <small>over five years</small>
        </span>
      </span>
      <small>
        {share.note} Quote: <Source link={share.source} /> via{" "}
        <Source link={share.attribution} />.
      </small>
    </div>
  );
}

function WaysIn({
  waysIn,
  asOf,
}: {
  waysIn: EmployerView["waysIn"];
  asOf: string;
}) {
  return (
    <aside className="pulse-ways" aria-labelledby="pulse-ways-title">
      <h3 id="pulse-ways-title">Ways in</h3>
      <ul>
        {waysIn.items.map((item) => (
          <li key={item.title}>
            <a href={item.href} target="_blank" rel="noreferrer">
              {item.title}
            </a>
          </li>
        ))}
      </ul>
      <small>
        Source: <Source link={waysIn.source} />, listed on {asOf}. Listings
        change and close.
      </small>
    </aside>
  );
}

export default function EmployerPulse({ careers }: { careers: Career[] }) {
  const [tab, setTab] = useState<PulseTab>("finance");
  const [employerData, setEmployerData] = useState<
    EmployerData | null | undefined
  >(undefined);
  useEffect(() => {
    let live = true;
    fetch(employerDataUrl)
      .then((response) => (response.ok ? response.json() : null))
      .then((raw) => live && setEmployerData(parseEmployerData(raw)))
      .catch(() => live && setEmployerData(null));
    return () => {
      live = false;
    };
  }, []);
  const model = buildEmployerPulse(careers, tab, employerData ?? null);
  const headline = model.headline;
  const employer = model.employer;
  return (
    <section className="employer-pulse" aria-labelledby="employer-pulse-title">
      <header className="pulse-header">
        <div className="pulse-brand">
          <span className="pulse-wordmark" aria-hidden="true">
            BlackRock
          </span>
          <div>
            <h2 id="employer-pulse-title">Employer pulse</h2>
            <p>
              Challenge partner · most wanted employer
              {employer ? ` · figures as of ${employer.asOf}` : ""}
            </p>
          </div>
        </div>
        {employer ? <ShareTile share={employer.share} /> : null}
      </header>

      {employer ? (
        <>
          <EmployerFacts employer={employer} />
          <div className="pulse-employer">
            <CareerLadder ladder={employer.ladder} />
            <WaysIn waysIn={employer.waysIn} asOf={employer.asOf} />
          </div>
        </>
      ) : employerData === null ? (
        <p className="pulse-unavailable pulse-employer-note" role="status">
          {model.employerNote}
        </p>
      ) : null}

      <div className="pulse-occupation-head">
        <h3>Pay by occupation, UK (ONS)</h3>
        <div className="segmented pulse-tabs" aria-label="Areas they hire into">
          {pulseTabs.map((item) => (
            <button
              key={item.id}
              aria-pressed={tab === item.id}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="pulse-body">
        <div className="pulse-main" aria-live="polite">
          {headline ? (
            <>
              <span className="pulse-role-label">
                Median annual pay · {headline.title}
                {headline.fellBack ? " (nearest occupation with data)" : ""}
              </span>
              <div className="pulse-headline">
                <strong>{headline.pay}</strong>
                <TrendBadge
                  trend={headline.trend}
                  positive={headline.trendPositive}
                  label={headline.trendLabel}
                />
              </div>
              <small className="pulse-evidence">{headline.payLabel}</small>
              <PulseChart
                history={headline.history}
                priceLabel={headline.priceLabel}
                title={headline.title}
              />
            </>
          ) : (
            <>
              <div className="pulse-skeleton" aria-hidden="true">
                <i className="is-short" />
                <i className="is-tall" />
                <i className="is-wide" />
              </div>
              <p className="pulse-unavailable" role="status">
                {model.note}. The pay figure and chart come from the app's
                evidence API and are not shown without it.
              </p>
            </>
          )}
        </div>

        <aside className="pulse-roles" aria-labelledby="pulse-roles-title">
          <h3 id="pulse-roles-title">Roles they hire</h3>
          {model.roles.length ? (
            <ul>
              {model.roles.map((role) => (
                <li key={role.soc}>
                  <a href={role.href}>
                    <span className="pulse-role-title">{role.title}</span>
                    <span className="pulse-role-figures">
                      <b>{role.pay}</b>
                      <TrendBadge
                        trend={role.trend}
                        positive={role.trendPositive}
                        label={role.trendLabel}
                      />
                    </span>
                    <small>ONS ASHE · {role.payYear} · median</small>
                  </a>
                  {role.employer ? (
                    <p className="pulse-role-employer">
                      At BlackRock (UK, self-reported):{" "}
                      <b>{role.employer.range}</b> · {role.employer.title} ·{" "}
                      {role.employer.reports} ·{" "}
                      <a
                        href={role.employer.href}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Glassdoor UK
                      </a>
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <>
              <div className="pulse-skeleton pulse-skeleton-list" aria-hidden>
                <i className="is-wide" />
                <i className="is-wide" />
                <i className="is-wide" />
              </div>
              <p className="pulse-unavailable">{model.note}</p>
            </>
          )}
        </aside>
      </div>

      <p className="pulse-footer">
        {model.footer} Sources:{" "}
        {model.footerLinks.map((link, index) => (
          <span key={link.href}>
            {index ? " · " : ""}
            <Source link={link} />
          </span>
        ))}
        .
      </p>
    </section>
  );
}
