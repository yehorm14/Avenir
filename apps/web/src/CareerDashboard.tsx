import { useEffect, useState } from "react";
import type { Career, Metric } from "./types";
import { money, percent, SalaryChart } from "./Charts";
import { careerEvidence } from "./careerEvidence";
import { metricCaveats } from "./planDocument";
import DashboardNextSteps from "./DashboardNextSteps";
import "./careerDashboard.css";

type Area = "cs" | "finance";
type Props = {
  area: Area;
  careers: Career[];
  onPlan: (career: Career) => void;
  onGuide: (career: Career) => void;
  saved: string[];
  onToggleSave: (id: string) => void;
  sourceRegistry?: Record<string, { name?: string; url?: string }>;
};

const areas = {
  cs: {
    title: "Computer science",
    route: "computer-science",
    roles: ["2134", "3544", "2133", "2135"],
  },
  finance: {
    title: "Finance",
    route: "finance",
    roles: ["2422", "2421", "2433"],
  },
};
const sourceNames: Record<string, string> = {
  ons_ashe_t14: "ONS ASHE",
  ons_cpih: "ONS CPIH",
  ilo_wp140: "ILO Working Paper 140",
  dfe_ai_uk_2023: "DfE UK AI exposure study",
  ons_online_job_adverts: "ONS / Adzuna job adverts",
  ons_aps_2016_age: "ONS Annual Population Survey",
};
const measureNames: Record<string, string> = {
  pay_median: "Median annual pay",
  pay_p10: "Pay, 10th percentile",
  pay_p90: "Pay, 90th percentile",
  real_pay_change_10y: "Real pay change",
  jobs: "Employee jobs",
  demand_trend: "Employee-job trend",
  demand_trend_2011_19: "Earlier employee-job trend",
  exposure: "Automation exposure",
  exposure_uk: "UK exposure cross-check",
  resilience_covid: "COVID employment resilience",
  resilience_cost_of_living: "Cost-of-living pay resilience",
  resilience_tech_slump: "Tech-slump adverts resilience",
  resilience_2008: "2008 crisis resilience",
  young_worker_share: "Workers aged 16–24",
};
const roleDescriptions: Record<string, string> = {
  "2134": "Develop, test and maintain software applications.",
  "3544": "Clean and analyse data to support decisions.",
  "2133": "Analyse business requirements and design IT systems.",
  "2135":
    "Protect networks and systems, investigate incidents and reduce security risks.",
  "2422":
    "Analyse financial data and investments to support financial decisions.",
  "2421": "Prepare financial accounts, audit records and advise on tax.",
  "2433":
    "Model risk, study economic conditions or analyse statistics, depending on the role.",
};

function available(metric?: Metric) {
  return !metric ||
    metric.status === "pending" ||
    metric.flags.includes("suppressed")
    ? null
    : metric.value;
}

function observation(metric?: Metric) {
  if (!metric) return "No supplied observation";
  return `${sourceNames[metric.source] ?? metric.source} · ${metric.as_of || "Year unavailable"}${metric.flags.includes("historical_observation") ? " · last available" : ""}${metric.flags.includes("provisional") ? " · provisional" : ""}`;
}

function headlineCaveat(metric?: Metric) {
  if (!metric) return "";
  return metricCaveats({
    ...metric,
    flags: metric.flags.filter(
      (flag) => flag !== "provisional" && flag !== "multi_isco",
    ),
  });
}

function displayMetric(metric: Metric, number = available(metric)): string {
  if (number == null) return "Not available";
  if (metric.unit === "GBP/year") return money(number);
  if (metric.unit === "thousand jobs")
    return `${Math.round(number * 1000).toLocaleString("en-GB")} jobs`;
  if (metric.unit.startsWith("fraction"))
    return `${(number * 100).toFixed(1)}%${metric.unit.endsWith("/year") ? " / year" : ""}`;
  if (metric.unit === "score 0-1") return `${number.toFixed(3)} / 1`;
  return `${number.toFixed(3)} ${metric.unit}`;
}

function Source({ source }: { source: { label: string; url: string } }) {
  return (
    <a href={source.url} target="_blank" rel="noreferrer">
      {source.label}
    </a>
  );
}

function DetailedMeasure({ name, metric }: { name: string; metric: Metric }) {
  const caveats = metricCaveats(metric);
  const historicalNotes = [
    metric.flags.includes("bridged_soc2000") &&
      "Older SOC 2000 occupation codes are mapped to today's occupation; this is an estimate.",
    metric.flags.includes("bridged_soc2010") &&
      "Older SOC 2010 occupation codes are mapped to today's occupation; this is an estimate.",
    metric.flags.includes("recoded_2021") &&
      "The 2021 occupation-code change breaks comparisons across the coding periods.",
    metric.flags.includes("covid_year") &&
      "Pandemic survey response and furlough affect the 2020 observation.",
    metric.flags.includes("employees_only") &&
      "Employees only; self-employed workers are excluded.",
  ].filter(Boolean);
  return (
    <div className="dashboard-measure">
      <dt>{measureNames[name] ?? name.replaceAll("_", " ")}</dt>
      <dd>{displayMetric(metric)}</dd>
      <p className="dashboard-provenance">{observation(metric)}</p>
      {available(metric) != null &&
        metric.low != null &&
        metric.high != null && (
          <p>
            Supplied range: {displayMetric(metric, metric.low)} to{" "}
            {displayMetric(metric, metric.high)}.
          </p>
        )}
      <p>{metric.note}</p>
      <p>
        {metric.status} · {metric.confidence} confidence.
      </p>
      {caveats && <p>{caveats}</p>}
      {historicalNotes.map((note) => (
        <p key={String(note)}>{note}</p>
      ))}
      {typeof metric.extra.adverts_category === "string" && (
        <p>Job-advert category: {metric.extra.adverts_category}.</p>
      )}
    </div>
  );
}

export default function CareerDashboard({ area, careers, ...actions }: Props) {
  const configuration = areas[area];
  const roles = configuration.roles.flatMap((soc) => {
    const career = careers.find((item) => item.soc === soc);
    return career ? [career] : [];
  });
  const [selection, setSelection] = useState<Record<Area, string>>({
    cs: "2134",
    finance: "2422",
  });
  useEffect(() => {
    const syncRole = () => {
      const [route, soc] = window.location.hash.replace(/^#\//, "").split("/");
      if (route !== configuration.route) return;
      const selected =
        roles.find((role) => role.soc === soc)?.soc ?? roles[0]?.soc;
      if (!selected) return;
      setSelection((current) =>
        current[area] === selected ? current : { ...current, [area]: selected },
      );
    };
    syncRole();
    window.addEventListener("hashchange", syncRole);
    return () => window.removeEventListener("hashchange", syncRole);
  }, [area, careers]);
  const career = roles.find((item) => item.soc === selection[area]) ?? roles[0];

  if (!career)
    return (
      <section className="career-dashboard">
        <h1>{configuration.title}</h1>
        <p>The occupation evidence is unavailable. Reload to try again.</p>
      </section>
    );

  const evidence = careerEvidence[career.soc];
  const pay = career.metrics.pay_median;
  const jobs = career.jobs_observation ?? career.metrics.jobs;
  const trend = career.metrics.demand_trend;
  const exposure = career.metrics.exposure;
  const jobsValue = available(jobs);
  const exposureValue = available(exposure);
  const sourceIds = [
    ...new Set(Object.values(career.metrics).map((metric) => metric.source)),
    "ons_cpih",
  ];
  const sources = [
    ...(career.sources ?? []).map((source) => ({
      label: source.name,
      url: source.url,
    })),
    ...sourceIds.flatMap((id) => {
      const source = actions.sourceRegistry?.[id];
      return sourceNames[id] && source?.url
        ? [{ label: source.name ?? sourceNames[id], url: source.url }]
        : [];
    }),
    evidence?.demandSource,
    evidence?.salary?.source,
    evidence?.outlook.source,
  ]
    .filter(
      (source): source is { label: string; url: string } =>
        !!source && /^https:\/\//i.test(source.url),
    )
    .filter(
      (source, index, all) =>
        all.findIndex((item) => item.url === source.url) === index,
    );

  return (
    <article className="career-dashboard">
      <header className="career-dashboard-header">
        <div>
          <h1>{configuration.title}</h1>
        </div>
        <div className="dashboard-header-actions">
          <button
            className="button primary"
            onClick={() => actions.onPlan(career)}
          >
            Build my plan
          </button>
          <button
            className="button secondary"
            onClick={() => actions.onGuide(career)}
          >
            Ask career guide
          </button>
        </div>
      </header>

      <nav className="dashboard-role-switch" aria-label="Choose an occupation">
        {roles.map((role) => (
          <button
            key={role.soc}
            aria-pressed={career.soc === role.soc}
            onClick={() => {
              setSelection((current) => ({ ...current, [area]: role.soc }));
              window.location.hash = `/${configuration.route}/${role.soc}`;
            }}
          >
            {role.title}
          </button>
        ))}
      </nav>

      <div className="dashboard-selected-role" aria-live="polite">
        <h2>{career.title}</h2>
        <p>{roleDescriptions[career.soc] ?? career.summary}</p>
        <small>
          Representative occupation. These figures describe this job, not every{" "}
          {configuration.title.toLowerCase()} graduate.
        </small>
      </div>

      <dl className="dashboard-facts">
        <div>
          <dt>Median annual pay</dt>
          <dd>{money(available(pay))}</dd>
          <p>
            {pay &&
            available(pay) != null &&
            pay.low != null &&
            pay.high != null
              ? `Middle 50%: ${money(pay.low)}–${money(pay.high)}`
              : "Pay range unavailable"}
          </p>
          <small>{observation(pay)}</small>
          <small>Full-time employees; not starting pay.</small>
          {headlineCaveat(pay) && <small>{headlineCaveat(pay)}</small>}
        </div>
        <div>
          <dt>Employee jobs</dt>
          <dd>
            {jobsValue == null
              ? "Not available"
              : Math.round(jobsValue * 1000).toLocaleString("en-GB")}
          </dd>
          <p>Full-time employees; not vacancies.</p>
          <small>{observation(jobs)}</small>
          {headlineCaveat(jobs) && <small>{headlineCaveat(jobs)}</small>}
        </div>
        <div>
          <dt>Employment trend</dt>
          <dd>
            {percent(available(trend))}
            {available(trend) != null && <span> / year</span>}
          </dd>
          <p>Historical trend, not a forecast.</p>
          <small>{observation(trend)}</small>
          {headlineCaveat(trend) && <small>{headlineCaveat(trend)}</small>}
        </div>
        <div>
          <dt>Automation exposure</dt>
          <dd>
            {exposureValue == null
              ? "Not available"
              : (exposureValue * 100).toFixed(0)}
            {exposureValue != null && <span> / 100</span>}
          </dd>
          <p>Research estimate; not job-loss risk.</p>
          <small>{observation(exposure)}</small>
          {exposure &&
            exposure.low != null &&
            exposure.high != null &&
            exposureValue != null && (
              <small>
                Research range: {(exposure.low * 100).toFixed(0)}–
                {(exposure.high * 100).toFixed(0)} / 100.
              </small>
            )}
          {exposure?.flags.includes("multi_isco") && (
            <small>Multiple international job codes mapped.</small>
          )}
          {headlineCaveat(exposure) && (
            <small>{headlineCaveat(exposure)}</small>
          )}
        </div>
      </dl>

      <div className="career-dashboard-layout">
        <div className="career-dashboard-evidence">
          <SalaryChart key={career.soc} careers={[career]} />

          {evidence && (
            <section className="dashboard-demand">
              <div>
                <h2>Demand assessment</h2>
                <strong>{evidence.demand}</strong>
              </div>
              <p>{evidence.demandReason}</p>
              <small>
                <Source source={evidence.demandSource} />
              </small>
            </section>
          )}

          {evidence && (
            <section className="dashboard-outlook">
              <h2>Sector outlook</h2>
              <h3>{evidence.outlook.title}</h3>
              <p>{evidence.outlook.summary}</p>
              <div className="dashboard-outlook-columns">
                <div>
                  <h3>Demand drivers</h3>
                  <ul>
                    {evidence.outlook.drivers.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3>Uncertainty</h3>
                  <ul>
                    {evidence.outlook.risks.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <small>
                {evidence.outlook.period}.{" "}
                <Source source={evidence.outlook.source} />
              </small>
            </section>
          )}
        </div>

        <aside
          className="career-dashboard-rail"
          aria-label="Routes and next steps"
        >
          <section className="dashboard-starting-pay">
            <h2>Starting pay guide</h2>
            {evidence?.salary ? (
              <>
                <p>{evidence.salary.role}</p>
                <dl>
                  <div>
                    <dt>Starter</dt>
                    <dd>{money(evidence.salary.low)}</dd>
                  </div>
                  <div>
                    <dt>Experienced</dt>
                    <dd>{money(evidence.salary.high)}</dd>
                  </div>
                </dl>
                <small>
                  Annual role guide, not a graduate salary or a two-year
                  outcome. The source does not specify years of experience.
                </small>
                <small>
                  <Source source={evidence.salary.source} />
                </small>
              </>
            ) : (
              <p>
                No verified starting-pay guide is supplied for this occupation.
                The workforce median above is not a starting salary.
              </p>
            )}
          </section>
          <DashboardNextSteps
            key={career.soc}
            career={career}
            onPlan={actions.onPlan}
            saved={actions.saved}
            onToggleSave={actions.onToggleSave}
          />
        </aside>
      </div>

      <section className="dashboard-method" aria-label="Evidence details">
        <details>
          <summary>
            Measures and caveats ({Object.keys(career.metrics).length})
          </summary>
          <dl className="dashboard-measures">
            {Object.entries(career.metrics).map(([name, metric]) => (
              <DetailedMeasure key={name} name={name} metric={metric} />
            ))}
          </dl>
        </details>
        <details>
          <summary>Sources and coverage ({sources.length})</summary>
          <p>
            Pay covers full-time employees and excludes self-employment.
            Historic occupation mappings are estimates; the 2021 code change
            breaks the employee-job series. Published outlooks retain their
            original horizon and region. Missing evidence stays unavailable.
          </p>
          <ul>
            {sources.map((source) => (
              <li key={source.url}>
                <Source source={source} />
              </li>
            ))}
          </ul>
        </details>
      </section>
    </article>
  );
}
