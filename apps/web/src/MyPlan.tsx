import { useState } from "react";
import type { Career, Page, Preferences } from "./types";
import { allOpportunities, getCareerContent } from "./content";
import { money, percent } from "./Charts";
import { Icon } from "./icons";
import { metricCaveats } from "./planDocument";

export default function MyPlan({
  careers,
  prefs,
  update,
  go,
  onExport,
  onReset,
}: {
  careers: Career[];
  prefs: Preferences;
  update: (change: Partial<Preferences>) => void;
  go: (page: Page) => void;
  onExport: () => void;
  onReset: () => void;
}) {
  const [confirmReset, setConfirmReset] = useState(false);
  const primary = careers[0];
  const content = getCareerContent(primary.soc, primary.family);
  const steps = content.firstSteps.slice(0, 3);
  const done = steps.filter((_, i) =>
    prefs.checked.includes(`${primary.soc}-${i}`),
  ).length;
  const route = prefs.routes[primary.soc] ?? "university";
  const saved = allOpportunities.filter((o) => prefs.saved.includes(o.id));
  const metric = (c: Career, key: string) => {
    const m = c.metrics[key];
    return !m || m.status === "pending" || m.flags?.includes("suppressed")
      ? null
      : m.value;
  };
  return (
    <section className="decision-plan">
      <header className="page-heading">
        <div>
          <h1>My plan</h1>
          <p className="page-description">
            Your current direction, the alternatives, and what to try next.
          </p>
        </div>
        <button className="button secondary" onClick={onExport}>
          <Icon name="download" size={17} /> Download plan
        </button>
      </header>
      <div className="decision-grid">
        <section className="decision-main">
          <div className="decision-status">
            <span className="status-dot" /> Explore first
          </div>
          <h2>{primary.title}</h2>
          <p>{content.intro}</p>
          <div className="decision-evidence">
            <div>
              <span>Median annual pay</span>
              <strong>{money(metric(primary, "pay_median"))}</strong>
              <small>
                ONS ASHE {primary.metrics.pay_median?.as_of}
                <br />
                Full-time employees; not starting pay
                <br />
                {metricCaveats(primary.metrics.pay_median)}
              </small>
            </div>
            <div>
              <span>Employment trend</span>
              <strong>
                {percent(metric(primary, "demand_trend"))}
                <small> / year</small>
              </strong>
              <small>
                {primary.metrics.demand_trend?.as_of}
                <br />
                Historical evidence, not a forecast
                <br />
                {metricCaveats(primary.metrics.demand_trend)}
              </small>
            </div>
          </div>
          <label className="decision-note">
            <span>Why is this worth exploring for you?</span>
            <textarea
              maxLength={2000}
              rows={3}
              value={prefs.notes[primary.soc] ?? ""}
              onChange={(e) =>
                update({
                  notes: { ...prefs.notes, [primary.soc]: e.target.value },
                })
              }
              placeholder="What attracts you? What would you like to find out before deciding?"
            />
          </label>
          <div className="decision-route">
            <h3>Route to explore</h3>
            <div className="segmented">
              <button
                aria-pressed={route === "university"}
                onClick={() =>
                  update({
                    routes: { ...prefs.routes, [primary.soc]: "university" },
                  })
                }
              >
                University
              </button>
              <button
                aria-pressed={route === "apprenticeship"}
                onClick={() =>
                  update({
                    routes: {
                      ...prefs.routes,
                      [primary.soc]: "apprenticeship",
                    },
                  })
                }
              >
                Earn & learn
              </button>
            </div>
            <p>
              {route === "apprenticeship"
                ? "Compare paid training routes and their entry requirements. Availability varies by career and nation."
                : content.broadDegree}
            </p>
          </div>
          <div className="decision-buttons">
            <button className="button primary" onClick={() => go("path")}>
              Explore pathway <Icon name="arrow" size={17} />
            </button>
            <button className="text-button" onClick={() => go("matches")}>
              Revisit choices
            </button>
          </div>
        </section>
        <section className="decision-actions">
          <div className="section-header">
            <h2>This month</h2>
            <span>
              {done} of {steps.length} done
            </span>
          </div>
          <p>Try the work before committing to the title.</p>
          <div
            className="decision-progress"
            role="progressbar"
            aria-label="Next actions completed"
            aria-valuemin={0}
            aria-valuemax={steps.length}
            aria-valuenow={done}
          >
            <span style={{ width: `${(done / steps.length) * 100}%` }} />
          </div>
          {steps.map((s, i) => {
            const id = `${primary.soc}-${i}`,
              checked = prefs.checked.includes(id);
            return (
              <label
                className={`task-check ${checked ? "is-done" : ""}`}
                key={id}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() =>
                    update({
                      checked: checked
                        ? prefs.checked.filter((k) => k !== id)
                        : [...prefs.checked, id],
                    })
                  }
                />
                <span>{s}</span>
              </label>
            );
          })}
          <button className="text-button" onClick={() => go("opportunities")}>
            Find a place to start <Icon name="chevron" size={15} />
          </button>
          <label className="decision-nation">
            <span>Plan routes for</span>
            <select
              value={prefs.nation}
              onChange={(e) => update({ nation: e.target.value })}
            >
              <option>Scotland</option>
              <option>England</option>
              <option>Wales</option>
              <option>Northern Ireland</option>
            </select>
          </label>
        </section>
      </div>
      <section className="decision-alternatives">
        <div className="section-header">
          <h2>Keep your alternatives in view</h2>
          <button className="text-button" onClick={() => go("matches")}>
            Edit ranking
          </button>
        </div>
        <div className="decision-comparison table-scroll">
          <table>
            <caption className="sr-only">
              Your ranked career choices and evidence
            </caption>
            <thead>
              <tr>
                <th>Choice</th>
                <th>Median annual pay</th>
                <th>Employment trend</th>
                <th>Task exposure</th>
              </tr>
            </thead>
            <tbody>
              {careers.map((c, i) => (
                <tr key={c.soc}>
                  <th scope="row">
                    <span className="tiny">
                      {i === 0 ? "First choice" : `Alternative ${i}`}
                    </span>
                    <strong>{c.title}</strong>
                  </th>
                  <td>
                    {money(metric(c, "pay_median"))}
                    <small>
                      {c.metrics.pay_median?.as_of}
                      <br />
                      {metricCaveats(c.metrics.pay_median)}
                    </small>
                  </td>
                  <td>
                    {percent(metric(c, "demand_trend"))}
                    <small>
                      {c.metrics.demand_trend?.as_of}; per year
                      <br />
                      {metricCaveats(c.metrics.demand_trend)}
                    </small>
                  </td>
                  <td>
                    {metric(c, "exposure") == null
                      ? "Not available"
                      : `${Math.round(metric(c, "exposure")! * 100)} / 100`}
                    <small>Research estimate</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="fine-print">
          ONS ASHE earnings and employment; ILO task exposure. Pay excludes
          self-employed workers. Exposure is not a probability of job loss. Open
          the evidence to inspect coverage, uncertainty and historical results.
        </p>
        <button className="text-button" onClick={() => go("evidence")}>
          Inspect the evidence <Icon name="chevron" size={15} />
        </button>
      </section>
      <section className="decision-saved">
        <div className="section-header">
          <h2>Saved opportunities</h2>
          <span>{saved.length} saved</span>
        </div>
        {saved.length ? (
          <ul>
            {saved.map((o) => (
              <li key={o.id}>
                <div>
                  <a href={o.url} target="_blank" rel="noreferrer">
                    {o.title} <Icon name="external" size={13} />
                  </a>
                  <small>
                    {o.location} · {o.kind}
                  </small>
                </div>
                <button
                  className="text-button"
                  aria-label={`Remove saved ${o.title}`}
                  onClick={() =>
                    update({ saved: prefs.saved.filter((id) => id !== o.id) })
                  }
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>
            Save a workshop, community or work experience organiser to keep it
            with your plan.
          </p>
        )}
        <p className="fine-print">
          Check dates, eligibility and availability with the organiser. These
          are discovery links, not bookings or confirmed openings.
        </p>
      </section>
      <details className="decision-storage">
        <summary>About your saved plan</summary>
        <p>
          Your choices, notes and progress are stored in this browser. They are
          not synced to an account. The downloaded plan is a readable file you
          can share or print as PDF.
        </p>
        <button className="text-button" onClick={() => setConfirmReset(true)}>
          Clear saved plan
        </button>
        {confirmReset && (
          <div className="reset-confirm" role="alert">
            <p>
              Clear your choices, answers, notes, progress and saved
              opportunities from this browser?
            </p>
            <button
              className="button secondary"
              onClick={() => setConfirmReset(false)}
            >
              Keep plan
            </button>
            <button className="button secondary" onClick={onReset}>
              Clear this plan
            </button>
          </div>
        )}
      </details>
    </section>
  );
}
