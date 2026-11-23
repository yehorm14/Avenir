import { useState } from "react";
import type { Career, Page, Preferences } from "./types";
import { allOpportunities, getCareerContent } from "./content";
import { money, percent } from "./Charts";
import { Icon } from "./icons";
import { CareerGuide } from "./Guides";
import { metricLabel } from "./metricLabel";
import { demandTrendLabel, planPrioritySummary } from "./planDocument";

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
          <p className="fine-print">Saved in this browser.</p>
          {!prefs.completed && (
            <p className="fine-print">{planPrioritySummary(prefs)}</p>
          )}
        </div>
        <button className="button secondary" onClick={onExport}>
          <Icon name="download" size={17} /> Download plan
        </button>
      </header>
      <div className="decision-grid decision-grid--simple">
        <section className="decision-main">
          <h2>{primary.title}</h2>
          <div className="decision-evidence">
            <div>
              <span>Median annual pay</span>
              <strong>{money(metric(primary, "pay_median"))}</strong>
              <small data-testid="plan-pay-source">
                {metricLabel(primary.metrics.pay_median).text}
              </small>
              {metric(primary, "pay_median") == null && (
                <small>
                  {metricLabel(primary.metrics.pay_median).unavailableReason}{" "}
                  Not zero.
                </small>
              )}
            </div>
            <div>
              <span>{demandTrendLabel(primary.metrics.demand_trend)}</span>
              <strong>
                {percent(metric(primary, "demand_trend"))}
                <small> / year</small>
              </strong>
              <small data-testid="plan-trend-source">
                {metricLabel(primary.metrics.demand_trend).text}
              </small>
              {metric(primary, "demand_trend") == null && (
                <small>
                  {metricLabel(primary.metrics.demand_trend).unavailableReason}{" "}
                  Not zero.
                </small>
              )}
            </div>
          </div>
          <p className="fine-print">
            Pay is a workforce median for employees, not a starting salary.
            Employment trends describe the past, not future vacancies. The
            pathway and first steps are curated examples to check, not a
            prediction.
          </p>
          <div className="decision-chat">
            <div className="decision-chat-heading">
              <h3>Why explore this career?</h3>
              <span>Prepared guide</span>
            </div>
            <CareerGuide key={primary.soc} career={primary} embedded />
          </div>
        </section>
        <details className="decision-actions decision-actions--compact">
          <summary>
            <strong>This month</strong>
            <span>
              {done} of {steps.length} done
            </span>
            <Icon name="chevron" size={16} />
          </summary>
          <ul className="decision-action-list">
            {steps.map((s, i) => {
              const id = `${primary.soc}-${i}`,
                checked = prefs.checked.includes(id);
              return (
                <li key={id}>
                  <label className={`task-check ${checked ? "is-done" : ""}`}>
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
                </li>
              );
            })}
          </ul>
        </details>
      </div>
      <button
        className="text-button decision-pathway"
        onClick={() => go("path")}
      >
        View pathway <Icon name="chevron" size={15} />
      </button>
      {saved.length > 0 && (
        <section className="decision-saved">
          <div className="section-header">
            <h2>Saved opportunities</h2>
            <span>{saved.length} saved</span>
          </div>
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
        </section>
      )}
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
