import { useMemo, useRef, useState } from "react";
import type { Career } from "./types";
import { SalaryChart, money, percent } from "./Charts";
import EmployerPulse from "./EmployerPulse";
import "./landing.css";

const subjects = [
  {
    area: "cs" as const,
    name: "Computer Science",
    soc: "2134",
    description: "Software development, data analysis and cyber security.",
    action: "Explore CS",
  },
  {
    area: "finance" as const,
    name: "Finance",
    soc: "2422",
    description: "Investment analysis, accountancy and quantitative work.",
    action: "Explore finance",
  },
];

const metricValue = (career: Career | undefined, key: string) => {
  const m = career?.metrics[key];
  return !m || m.status === "pending" || m.flags?.includes("suppressed")
    ? null
    : (m.value as number);
};

const comparison = [
  {
    key: "pay_median",
    label: "Median annual pay",
    note: "Full-time employees. Not a starting salary.",
    show: (v: number | null) => money(v),
    scale: (v: number) => v,
  },
  {
    key: "jobs",
    label: "Employee jobs in the UK",
    note: "Jobs, not vacancies. ONS calls these counts indicative.",
    show: (v: number | null) =>
      v === null
        ? "Not available"
        : Math.round(v * 1000).toLocaleString("en-GB"),
    scale: (v: number) => v,
  },
  {
    key: "demand_trend",
    label: "Employment trend, per year",
    note: "Compared with the typical occupation. History, not a forecast.",
    show: (v: number | null) => percent(v),
    scale: (v: number) => Math.max(v, 0),
  },
  {
    key: "exposure",
    label: "Automation exposure, out of 100",
    note: "A research estimate. Not the chance of losing the job.",
    show: (v: number | null) =>
      v === null ? "Not available" : `${Math.round(v * 100)} / 100`,
    scale: (v: number) => v,
  },
] as const;

const steps = [
  {
    title: "Look at the evidence",
    text: "Open a subject and see real UK figures for each job: pay, how many people are employed, how employment has been changing, and how exposed its tasks are to automation.",
    detail:
      "Start in Jobs. Each occupation shows its pay, the number of employee jobs and how employment has changed, next to an estimate of how exposed its tasks are to automation. Every figure names its source, and the page says plainly when something is history rather than a forecast.",
  },
  {
    title: "Weigh what matters to you",
    text: "Compare careers by balancing pay against the recent employment trend. There is no single right balance, so you set it and see how the order changes.",
    detail:
      "Move the priorities to say how much pay matters compared with the recent employment trend. The list of careers re-orders as you move them, so you can see which careers stay near the top whatever you choose and which only rise under one balance. The weighting is yours, not ours.",
  },
  {
    title: "Choose a first role to explore",
    text: "Pick the role you want to look at first. You can also take a short quiz or a guided conversation if you are not sure where to begin.",
    detail:
      "Pick a role to read about in depth. If you are not sure where to begin, the short quiz or the guided conversation helps you narrow things down. Neither one decides for you: they point you to roles worth looking at first.",
  },
  {
    title: "Plan your next step",
    text: "Get a route in (university or earn-and-learn), the skills to practise, example courses, and opportunities to try the work. Your plan is saved in your browser.",
    detail:
      "Turn your choice into a plan: ways in (such as university or earn-and-learn), the skills to practise, example courses and opportunities to try the work. Your plan stays in your browser, so you can come back to it and change it as you learn more.",
  },
];

function StepTimeline() {
  const [active, setActive] = useState(0);
  const track = useRef<HTMLDivElement>(null);
  const pick = (clientX: number) => {
    const box = track.current?.getBoundingClientRect();
    if (!box) return;
    const ratio = Math.min(1, Math.max(0, (clientX - box.left) / box.width));
    setActive(Math.round(ratio * (steps.length - 1)));
  };
  return (
    <div className="step-timeline">
      <div
        className="step-track"
        ref={track}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          pick(e.clientX);
        }}
        onPointerMove={(e) => {
          if (e.buttons === 1) pick(e.clientX);
        }}
      >
        <span className="step-line" aria-hidden="true" />
        <span
          className="step-line fill"
          aria-hidden="true"
          style={{ width: `${(active / (steps.length - 1)) * 100}%` }}
        />
        {steps.map((step, index) => (
          <button
            key={step.title}
            type="button"
            className={`step-dot${index === active ? " on" : ""}${index < active ? " done" : ""}`}
            style={{ left: `${(index / (steps.length - 1)) * 100}%` }}
            aria-label={`Step ${index + 1}: ${step.title}`}
            aria-pressed={index === active}
            onMouseEnter={() => setActive(index)}
            onFocus={() => setActive(index)}
          ></button>
        ))}
      </div>
      <div className="step-out" aria-live="polite">
        <h3>{steps[active].title}</h3>
        <p>{steps[active].detail}</p>
      </div>
    </div>
  );
}

const limits = [
  "It does not predict your future, your pay, or whether you will get a job.",
  "Scores are not a chance of success.",
  "The quiz is not a psychological test.",
  "Courses and routes are examples. Check eligibility with each provider.",
  "No account or tracking: your plan stays in this browser.",
];

const cities: Record<string, string[]> = {
  Scotland: ["Glasgow", "Edinburgh", "Aberdeen", "Dundee", "Inverness"],
  England: [
    "London",
    "Manchester",
    "Birmingham",
    "Leeds",
    "Liverpool",
    "Bristol",
    "Newcastle",
    "Sheffield",
  ],
  Wales: ["Cardiff", "Swansea", "Newport"],
  "Northern Ireland": ["Belfast", "Derry"],
};

/** A ticker of occupations ranked by recent employment growth, like a market tape. */
function DemandTicker({ careers }: { careers: Career[] }) {
  const rows = useMemo(
    () =>
      careers
        .map((career) => ({
          soc: career.soc,
          title: career.title,
          pay: metricValue(career, "pay_median"),
          trend: metricValue(career, "demand_trend"),
        }))
        .filter(
          (row): row is typeof row & { trend: number } => row.trend !== null,
        )
        .sort((a, b) => b.trend - a.trend)
        .slice(0, 12),
    [careers],
  );
  if (!rows.length) return null;
  const items = (suffix: string) =>
    rows.map((row) => (
      <span className="tick" key={`${row.soc}${suffix}`}>
        <b>{row.title}</b>
        <span>{money(row.pay)}</span>
        <em className={row.trend >= 0 ? "up" : "down"}>
          {row.trend >= 0 ? "▲" : "▼"} {percent(row.trend)}
        </em>
      </span>
    ));
  return (
    <div className="ed-ticker">
      <div
        className="ed-ticker-label"
        title="ONS ASHE employment trend 2022-2025 vs the typical occupation; history, not the official Occupations in Demand rating"
      >
        Fastest-growing · ONS 2022–25
      </div>
      <div
        className="ed-ticker-window"
        role="region"
        aria-label="Occupations with the fastest recent employment growth"
      >
        <div className="ed-ticker-track">
          {items("a")}
          <span aria-hidden="true" className="tick-copy">
            {items("b")}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function Landing({
  careers,
  onChoose,
  onDashboard,
  onAmira,
  amiraBusy = false,
  amiraError = "",
  onJobs,
  onPlan,
  nation,
  location,
  onNation,
  onLocation,
  resume,
}: {
  careers: Career[];
  onChoose: (mode: "known" | "explore") => void;
  onDashboard: (area: "cs" | "finance") => void;
  onAmira?: () => void;
  amiraBusy?: boolean;
  amiraError?: string;
  onJobs: () => void;
  onPlan: () => void;
  nation: string;
  location: string;
  onNation: (nation: string) => void;
  onLocation: (location: string) => void;
  resume?: { title: string; onResume: () => void };
}) {
  return (
    <div className="aventier-landing">
      <section className="hero editorial" aria-labelledby="mission-heading">
        <div className="ed-meta">
          <select
            aria-label="City"
            style={{ width: `${location.length * 1.1 + 1}ch` }}
            value={location}
            onChange={(e) => onLocation(e.target.value)}
          >
            {[
              ...(cities[nation] ?? []),
              ...(cities[nation]?.includes(location) ? [] : [location]),
            ].map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
          <span aria-hidden="true" className="ed-sep" />
          <select
            aria-label="Country"
            style={{ width: `${nation.length * 1.1 + 1}ch` }}
            value={nation}
            onChange={(e) => {
              onNation(e.target.value);
              onLocation(cities[e.target.value]?.[0] ?? "");
            }}
          >
            {Object.keys(cities).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
        <p className="ed-label">( AVENIER )</p>
        <h1 id="mission-heading" className="ed-title">
          <span className="serif">Explore your</span> <b>career choices,</b>{" "}
          <span className="serif">see clear</span> <b>path</b>{" "}
          <span className="serif">and</span> <b>opportunities</b>
        </h1>
        <div className="ed-row">
          <p className="ed-lede">
            Avenier puts real UK pay, jobs and automation research for each
            career in one place, shows you the trade-offs, and turns your choice
            into a plan you can start this month.
          </p>
          <nav className="ed-options" aria-label="Where to start">
            <button onClick={onJobs}>
              Analyse the job market <i>→</i>
            </button>
            <button onClick={onPlan}>
              Review my decisions <i>→</i>
            </button>
            <button onClick={() => onChoose("explore")}>
              I'm not sure what to do <i>→</i>
            </button>
          </nav>
        </div>
        <DemandTicker careers={careers} />
        <p className="ed-note">
          Ranked by recent employment growth compared with the typical
          occupation. ONS ASHE, 2022 to 2025. History, not a forecast.
        </p>
      </section>
      <section className="explain-section" aria-labelledby="how-heading">
        <h2 id="how-heading">How it works</h2>
        <StepTimeline />
      </section>
      <section
        className="mission-section subjects-section"
        aria-labelledby="subjects-heading"
      >
        <header className="subjects-heading">
          <h2 id="subjects-heading">Start with a subject</h2>
        </header>
        <article className="amira-journey" aria-labelledby="amira-heading">
          <span className="amira-kicker">Start here</span>
          <h2 id="amira-heading">Amira, 17, S6 in Glasgow</h2>
          <p>
            Good at maths and art. Her first idea is architect, and she is
            worried about AI. See three careers worth exploring next to that
            first idea, a hedge career, how simple rules held up, and her next
            step.
          </p>
          <button
            className="mission-cta mission-cta-primary"
            onClick={onAmira}
            disabled={amiraBusy}
          >
            {amiraBusy ? "Comparing…" : "Try architect"}
          </button>
          {amiraError && (
            <p className="amira-error" role="alert">
              {amiraError}
            </p>
          )}
        </article>
        <EmployerPulse careers={careers} />
        <h2 className="other-journey-heading">
          Another journey: Computer Science and Finance
        </h2>
        <div className="subject-choices" aria-label="Career dashboards">
          {subjects.map((subject) => {
            const career = careers.find((item) => item.soc === subject.soc);
            const pay = career?.metrics.pay_median;
            const available =
              pay?.status !== "pending" && !pay?.flags.includes("suppressed");
            return (
              <article className="subject-choice" key={subject.area}>
                <h2>{subject.name}</h2>
                <p>{subject.description}</p>
                <div className="subject-role">
                  <span>Example career</span>
                  <h3>{career?.title ?? "Career evidence unavailable"}</h3>
                  <strong>{money(available ? pay?.value : null)}</strong>
                  <small>
                    Median annual pay · {pay?.as_of ?? "Year unavailable"} · UK
                  </small>
                </div>
                <button
                  className="mission-cta mission-cta-primary"
                  onClick={() => onDashboard(subject.area)}
                >
                  {subject.action}
                </button>
              </article>
            );
          })}
        </div>
        <p className="subject-source">
          ONS ASHE · Full-time employee pay, provisional. Figures describe the
          example occupations, not graduate earnings.
        </p>
        <div className="other-directions">
          <span>Explore other careers</span>
          <div>
            <button onClick={() => onChoose("known")}>Explore career</button>
            <button onClick={() => onChoose("explore")}>Find careers</button>
          </div>
        </div>
        {resume && (
          <div className="resume-plan">
            <div>
              <span>Your saved plan</span>
              <strong>{resume.title}</strong>
            </div>
            <button
              className="mission-cta mission-cta-secondary"
              onClick={resume.onResume}
            >
              Resume plan
            </button>
          </div>
        )}
      </section>
      <section className="explain-section" aria-labelledby="compare-heading">
        <h2 id="compare-heading">The evidence people weigh when they choose</h2>
        <p className="explain-lead">
          Public UK sources, for the two example roles.
        </p>
        {(() => {
          const pair = subjects.map((subject) =>
            careers.find((item) => item.soc === subject.soc),
          );
          return (
            <>
              <div
                className="compare-table"
                role="table"
                aria-label="Evidence compared"
              >
                <div className="compare-head" role="row">
                  <span role="columnheader">Measure</span>
                  {pair.map((c, i) => (
                    <span role="columnheader" key={subjects[i].soc}>
                      {c?.title ?? subjects[i].name}
                    </span>
                  ))}
                </div>
                {comparison.map((row) => {
                  const values = pair.map((c) => metricValue(c, row.key));
                  const max = Math.max(
                    ...values.map((v) => (v === null ? 0 : row.scale(v))),
                    0,
                  );
                  return (
                    <div className="compare-row" role="row" key={row.key}>
                      <span className="compare-label" role="rowheader">
                        {row.label}
                        <small>{row.note}</small>
                      </span>
                      {values.map((v, i) => (
                        <span className="compare-cell" role="cell" key={i}>
                          <b>{row.show(v)}</b>
                          <i
                            className={`compare-bar bar-${i}`}
                            style={{
                              width:
                                v === null || max === 0
                                  ? "0%"
                                  : `${Math.max(3, (row.scale(v) / max) * 100)}%`,
                            }}
                          />
                        </span>
                      ))}
                    </div>
                  );
                })}
              </div>
              <div className="compare-chart">
                <h3>Pay over time, adjusted for inflation</h3>
                {pair.every(Boolean) && (
                  <SalaryChart careers={pair as Career[]} />
                )}
              </div>
            </>
          );
        })()}
      </section>
      <section className="explain-section" aria-label="Start and limits">
        <details className="not-claim">
          <summary>What this is not</summary>
          <ul className="explain-list">
            {limits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
        <div className="explain-actions">
          <button
            className="mission-cta mission-cta-primary"
            onClick={() => onDashboard("cs")}
          >
            Start with Computer Science
          </button>
          <button
            className="mission-cta mission-cta-secondary"
            onClick={() => onDashboard("finance")}
          >
            Start with Finance
          </button>
          <button
            className="mission-cta mission-cta-secondary"
            onClick={() => onChoose("explore")}
          >
            Not sure yet? Find careers
          </button>
        </div>
      </section>
    </div>
  );
}
