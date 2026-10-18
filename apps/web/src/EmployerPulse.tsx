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
  type EmployerSection,
  type EmployerView,
  type OfficialFact,
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
              className={row.missing ? "is-missing" : undefined}
              aria-label={`${row.level}: ${row.range}${row.reports ? `, ${row.reports}` : ""}`}
            >
              <span className="pulse-ladder-level">
                {row.level}
                {row.official ? (
                  <i className="pulse-official-mark" title="BlackRock title">
                    BlackRock title
                  </i>
                ) : null}
              </span>
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
                {row.missing ? null : (
                  <rect
                    x={`${row.lowPct}%`}
                    width={`${Math.max(row.highPct - row.lowPct, 1)}%`}
                    y="3"
                    height="12"
                    rx="6"
                    className="pulse-ladder-bar"
                  />
                )}
              </svg>
              <span className="pulse-ladder-figures">
                {row.missing ? <small>{row.range}</small> : <b>{row.range}</b>}
                {row.reports ? <small>{row.reports}</small> : null}
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
        Pay: <Source link={ladder.source} />. {ladder.note} Job titles as
        BlackRock names them: <Source link={ladder.titlesSource} />.
      </figcaption>
      <p className="pulse-story">
        <b>{ladder.story.label}:</b> {ladder.story.value}{" "}
        <Cite fact={ladder.story} />
      </p>
    </figure>
  );
}

function Cite({ fact }: { fact: OfficialFact }) {
  return (
    <small className="pulse-cite">
      <a href={fact.source.href} target="_blank" rel="noreferrer">
        {fact.cite}
      </a>
    </small>
  );
}

function OfficialList({ facts }: { facts: OfficialFact[] }) {
  return (
    <ul className="pulse-official-list">
      {facts.map((fact) => (
        <li key={fact.label}>
          <b>{fact.label}</b>
          {fact.label === fact.value ? null : <span> {fact.value}</span>}
          {fact.note ? <span> {fact.note}</span> : null} <Cite fact={fact} />
        </li>
      ))}
    </ul>
  );
}

function WaysInForYou({
  employer,
  title,
}: {
  employer: EmployerView;
  title: string;
}) {
  const official = employer.official;
  const glassdoor = employer.waysIn;
  return (
    <section className="pulse-ways-in" aria-labelledby="pulse-ways-in-title">
      <h3 id="pulse-ways-in-title">{title}</h3>
      <ol className="pulse-ways-grid">
        {official.waysIn.map((way) => (
          <li key={way.label}>
            <b>
              {way.href ? (
                <a href={way.href} target="_blank" rel="noreferrer">
                  {way.label}
                </a>
              ) : (
                way.label
              )}
            </b>
            {way.tag ? <span className="pulse-tag">{way.tag}</span> : null}
            <span>{way.value}</span>
            {way.details.length ? (
              <ul>
                {way.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            ) : null}
            <Cite fact={way} />
          </li>
        ))}
        <li>
          <b>Internships</b>
          <ul>
            {glassdoor.items.map((item) => (
              <li key={item.title}>
                <a href={item.href} target="_blank" rel="noreferrer">
                  {item.title}
                </a>
              </li>
            ))}
          </ul>
          <small className="pulse-cite">
            <Source link={glassdoor.source} />, listed on {employer.asOf}.
            Listings change and close.
          </small>
        </li>
      </ol>
      <p className="pulse-degree">
        <b>
          {official.degreeSubject.label}: {official.degreeSubject.value}
        </b>{" "}
        <Cite fact={official.degreeSubject} />
      </p>
    </section>
  );
}

function PayWorks({ employer }: { employer: EmployerView }) {
  const median = employer.official.medianPay;
  return (
    <>
      <OfficialList facts={employer.official.payWorks} />
      <p className="pulse-median">
        {median.label}: {median.value}. {median.note} <Cite fact={median} />
      </p>
    </>
  );
}

function PayFairness({ employer }: { employer: EmployerView }) {
  const gap = employer.official.payGap;
  const global = employer.official.payFairnessGlobal;
  return (
    <>
      <p className="pulse-section-sub">
        {gap.title}: {gap.scope}.
      </p>
      <dl className="pulse-gap-rows">
        {gap.rows.map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd>
              <b>{row.value}</b>
              <small className="pulse-cite">
                <a href={gap.source.href} target="_blank" rel="noreferrer">
                  {row.cite}
                </a>
              </small>
            </dd>
          </div>
        ))}
      </dl>
      <figure className="pulse-quartiles">
        <figcaption>Women and men in each pay quarter (UK)</figcaption>
        <ul>
          {gap.quartiles.map((quarter) => (
            <li
              key={quarter.quarter}
              aria-label={`${quarter.quarter} pay quarter: ${quarter.women}% women, ${quarter.men}% men`}
            >
              <span>{quarter.quarter}</span>
              <span className="pulse-quartile-bar" aria-hidden="true">
                <i style={{ width: `${quarter.women}%` }} />
              </span>
              <small>
                {quarter.women}% women · {quarter.men}% men
              </small>
            </li>
          ))}
        </ul>
        <small className="pulse-cite">
          <a href={gap.source.href} target="_blank" rel="noreferrer">
            {gap.quartilesCite}
          </a>
        </small>
      </figure>
      <p className="pulse-section-sub">{gap.reason}.</p>
      <p className="pulse-section-sub">
        <b>
          {global.label}: {global.value}.
        </b>{" "}
        {global.note} <Cite fact={global} />
      </p>
    </>
  );
}

function OfficialSection({
  section,
  employer,
}: {
  section: EmployerSection;
  employer: EmployerView;
}) {
  const body =
    section.id === "pay-works" ? (
      <PayWorks employer={employer} />
    ) : section.id === "pay-fairness" ? (
      <PayFairness employer={employer} />
    ) : section.id === "company" ? (
      <OfficialList facts={employer.official.company} />
    ) : section.id === "benefits" ? (
      <OfficialList facts={employer.official.benefits} />
    ) : null;
  return (
    <section className="pulse-more-section">
      <h4>{section.title}</h4>
      {body}
    </section>
  );
}

function MainSection({
  section,
  employer,
}: {
  section: EmployerSection;
  employer: EmployerView;
}) {
  if (section.id === "ways-in")
    return <WaysInForYou employer={employer} title={section.title} />;
  if (section.id === "facts") return <EmployerFacts employer={employer} />;
  if (section.id === "ladder") return <CareerLadder ladder={employer.ladder} />;
  return null;
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
          {employer.sections
            .filter((section) => !section.more)
            .map((section) => (
              <MainSection
                key={section.id}
                section={section}
                employer={employer}
              />
            ))}
          <details className="pulse-more">
            <summary>More about working at {employer.name}</summary>
            <div className="pulse-more-grid">
              {employer.sections
                .filter((section) => section.more)
                .map((section) => (
                  <OfficialSection
                    key={section.id}
                    section={section}
                    employer={employer}
                  />
                ))}
            </div>
          </details>
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

      <footer className="pulse-footer">
        <p>{model.footer}</p>
        <h3>Sources</h3>
        <ul className="pulse-sources">
          {model.footerLinks.map((link) => (
            <li key={link.label}>
              <Source link={link} />
            </li>
          ))}
        </ul>
      </footer>
    </section>
  );
}
