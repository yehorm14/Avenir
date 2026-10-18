import { useEffect, useRef, useState } from "react";
import type { Career, CareerSummary, Metric } from "./types";
import { api } from "./store";
import { money, SalaryChart } from "./Charts";
import { careerEvidence } from "./careerEvidence";
import "./jobs.css";

const work: Record<string, string> = {
  "5241": "Install, test and repair electrical systems.",
  "5315": "Install and repair water and heating systems.",
  "2134": "Develop, test and maintain software applications.",
  "3544": "Clean and analyse data to support decisions.",
  "2133": "Analyse business requirements and design IT systems.",
  "2135":
    "Protect networks and systems, investigate incidents and reduce security risks.",
  "2141": "Design websites, interfaces and digital experiences.",
  "2142": "Create visual communication for print and digital media.",
  "2451": "Design buildings and coordinate their delivery.",
  "2452": "Plan how land, buildings and infrastructure are developed.",
  "3120": "Produce technical drawings and building models.",
  "2121": "Design and supervise infrastructure projects.",
  "2123": "Design and maintain electrical engineering systems.",
  "3113": "Support engineering design, testing and maintenance.",
  "2453": "Estimate and manage construction costs.",
  "2454": "Assess buildings, land and property.",
  "2433":
    "Model risk, study economic conditions or analyse statistics, depending on the role.",
  "2422":
    "Analyse financial data and investments to support financial decisions.",
  "2421": "Prepare financial accounts, audit records and advise on tax.",
  "2254":
    "Produce diagnostic images or deliver radiotherapy, depending on the specialism.",
  "2313": "Teach secondary-school subjects and assess pupils’ progress.",
};

const ashe = {
  label: "ONS ASHE, Table 14",
  url: "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14",
};
const cpih = {
  label: "ONS CPIH",
  url: "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23",
};
const demandSource = {
  label: "Skills England, Occupations in demand 2025",
  url: "https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025",
};
function Source({ source }: { source: { label: string; url: string } }) {
  return (
    <a href={source.url} target="_blank" rel="noreferrer">
      {source.label}
    </a>
  );
}
function metricValue(m?: Metric) {
  return m?.status === "pending" || m?.flags.includes("suppressed")
    ? null
    : (m?.value ?? null);
}
function metric(career: Career, key: string) {
  return metricValue(career.metrics[key]);
}
function observation(m?: Metric) {
  if (!m) return "No observation";
  return `${m.as_of || "Year unavailable"}${m.flags.includes("historical_observation") ? " · last available" : ""}${m.flags.includes("provisional") ? " · provisional" : ""}${m.flags.includes("imputed_parent") ? " · wider-group estimate" : ""}`;
}
const number = (n: number | null | undefined) =>
  n == null ? "Not available" : Math.round(n).toLocaleString("en-GB");
const priority = (career: { soc: string }) => {
  // Infrastructure trades are the user's editorial priority; the demand label
  // remains the source's actual classification, including negative findings.
  if (career.soc === "5241") return 0;
  if (career.soc === "5315") return 1;
  const status = careerEvidence[career.soc]?.demand;
  return status === "Critical"
    ? 2
    : status === "Elevated"
      ? 3
      : status === "Sector priority"
        ? 4
        : 5;
};

export default function Jobs({
  onExplore,
}: {
  careers: Career[];
  onExplore: (career: Career) => void;
}) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("demand");
  const [catalogue, setCatalogue] = useState<CareerSummary[] | null>(null);
  const [catalogueError, setCatalogueError] = useState("");
  const [catalogueAttempt, setCatalogueAttempt] = useState(0);
  const [selectedSoc, setSelectedSoc] = useState<string | null>(null);
  const [selected, setSelected] = useState<Career | null>(null);
  const [profileError, setProfileError] = useState("");
  const [profileAttempt, setProfileAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setCatalogueError("");
    api<CareerSummary[]>("catalogue", undefined, controller.signal)
      .then(setCatalogue)
      .catch((error: Error) => {
        if (!controller.signal.aborted) setCatalogueError(error.message);
      });
    return () => controller.abort();
  }, [catalogueAttempt]);
  useEffect(() => {
    if (!selectedSoc) return;
    const controller = new AbortController();
    setSelected(null);
    setProfileError("");
    api<Career>(`careers/${selectedSoc}`, undefined, controller.signal)
      .then((career) => {
        if (!controller.signal.aborted) setSelected(career);
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setProfileError(error.message);
      });
    return () => controller.abort();
  }, [selectedSoc, profileAttempt]);
  const goBack = () => {
    const previousSoc = selectedSoc;
    setSelectedSoc(null);
    setSelected(null);
    window.requestAnimationFrame(() => {
      document.getElementById(`job-${previousSoc}`)?.focus();
    });
  };
  if (selectedSoc) {
    if (selected)
      return (
        <JobProfile
          key={selected.soc}
          career={selected}
          onBack={goBack}
          onExplore={() => onExplore(selected)}
        />
      );
    return (
      <section className="job-profile" aria-busy={!profileError}>
        <button className="job-back text-button" onClick={goBack}>
          All jobs
        </button>
        <h1>
          {catalogue?.find((career) => career.soc === selectedSoc)?.title ??
            "Career evidence"}
        </h1>
        {profileError ? (
          <div className="jobs-message" role="alert">
            <p>{profileError}</p>
            <button
              className="button secondary"
              onClick={() => setProfileAttempt((attempt) => attempt + 1)}
            >
              Try again
            </button>
          </div>
        ) : (
          <p className="jobs-message" role="status">
            Loading career evidence…
          </p>
        )}
      </section>
    );
  }
  const query = search.trim().toLowerCase();
  const rows = (catalogue ?? [])
    .filter((career) =>
      `${career.title} ${career.sector} ${career.soc}`
        .toLowerCase()
        .includes(query),
    )
    .sort((a, b) => {
      if (sort === "pay")
        return (
          (metricValue(b.pay) ?? -1) - (metricValue(a.pay) ?? -1) ||
          a.title.localeCompare(b.title)
        );
      if (sort === "name") return a.title.localeCompare(b.title);
      return priority(a) - priority(b) || a.title.localeCompare(b.title);
    });
  return (
    <section
      className="jobs-directory"
      aria-busy={!catalogue && !catalogueError}
    >
      <header className="jobs-heading">
        <h1>Jobs</h1>
        <small>Compare UK pay, employment and demand evidence</small>
      </header>
      <div className="jobs-controls">
        <label className="search">
          <span className="sr-only">Search careers</span>
          <input
            type="search"
            placeholder="Search jobs, sectors or SOC codes"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <select
          aria-label="Sort careers"
          value={sort}
          onChange={(event) => setSort(event.target.value)}
        >
          <option value="demand">UK priorities</option>
          <option value="pay">Highest pay</option>
          <option value="name">A–Z</option>
        </select>
      </div>
      {catalogueError ? (
        <div className="jobs-message" role="alert">
          <p>{catalogueError}</p>
          <button
            className="button secondary"
            onClick={() => setCatalogueAttempt((attempt) => attempt + 1)}
          >
            Try again
          </button>
        </div>
      ) : !catalogue ? (
        <p className="jobs-message" role="status">
          Loading careers…
        </p>
      ) : (
        <>
          <p className="jobs-count" role="status">
            {query
              ? `${rows.length} of ${catalogue.length} occupations`
              : `${catalogue.length} occupations`}
          </p>
          {rows.length ? (
            <>
              <p className="jobs-scroll-hint">
                Scroll across for demand, pay and employee jobs.
              </p>
              <div
                className="jobs-table table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Occupation evidence table"
              >
                <table>
                  <caption className="sr-only">
                    UK occupations with published annual median pay and employee
                    jobs. Select a career to view its evidence.
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Career</th>
                      <th scope="col">UK demand</th>
                      <th scope="col">Pay</th>
                      <th scope="col">Employee jobs</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((career) => {
                      const evidence = careerEvidence[career.soc];
                      const jobs = metricValue(career.jobs);
                      return (
                        <tr
                          key={career.soc}
                          className={priority(career) < 2 ? "priority-job" : ""}
                        >
                          <th scope="row" className="job-name">
                            <button
                              id={`job-${career.soc}`}
                              onClick={() => {
                                setSelectedSoc(career.soc);
                                window.scrollTo(0, 0);
                              }}
                            >
                              {career.title}
                            </button>
                            <small>{career.sector}</small>
                          </th>
                          <td>
                            <span className="demand-label">
                              {evidence?.shortage?.label ??
                                (evidence?.demand === "Not in high demand"
                                  ? "Not high"
                                  : (evidence?.demand ?? "Not assessed"))}
                            </span>
                            <small className="demand-subtitle">
                              {evidence
                                ? evidence.shortage
                                  ? "MAC 2026"
                                  : "Skills England 2025"
                                : "No classification supplied"}
                            </small>
                          </td>
                          <td>
                            {money(metricValue(career.pay))}
                            <small>{observation(career.pay)}</small>
                          </td>
                          <td>
                            {number(jobs == null ? null : jobs * 1000)}
                            <small>{observation(career.jobs)}</small>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="jobs-message">
              <h2>No matching occupations</h2>
              <p>Try a different job title, sector or four-digit SOC code.</p>
              <button
                className="button secondary"
                onClick={() => setSearch("")}
              >
                Clear search
              </button>
            </div>
          )}
        </>
      )}
      <p className="jobs-source-note">
        Pay is the annual median for full-time employees, not a starting salary.
        Employee-job estimates exclude self-employment. Each figure shows its
        own observation year. Older employee-job counts are marked last
        available; missing and suppressed figures stay unavailable.{" "}
        <Source source={ashe} />.
      </p>
      <p className="jobs-source-note">
        Electricians and plumbers appear first because of infrastructure needs
        identified by the Migration Advisory Committee. Demand classifications
        measure recruitment pressure, not vacancies or guaranteed employment.{" "}
        <Source source={demandSource} />. Personalised matching covers 20
        careers; you can browse pay and employment evidence for every occupation
        listed here.
      </p>
    </section>
  );
}

function JobProfile({
  career,
  onBack,
  onExplore,
}: {
  career: Career;
  onBack: () => void;
  onExplore: () => void;
}) {
  const evidence = careerEvidence[career.soc];
  const [startingPay, setStartingPay] = useState(
    evidence?.salary?.low?.toString() ?? "",
  );
  const [increase, setIncrease] = useState("5");
  const [inflation, setInflation] = useState("2");
  const start = Number(startingPay),
    growth = Number(increase),
    prices = Number(inflation);
  const valid =
    startingPay.trim() !== "" &&
    increase.trim() !== "" &&
    inflation.trim() !== "" &&
    Number.isFinite(start) &&
    start > 0 &&
    start <= 1000000 &&
    Number.isFinite(growth) &&
    growth >= -20 &&
    growth <= 30 &&
    Number.isFinite(prices) &&
    prices >= 0 &&
    prices <= 20;
  const nominal = valid ? start * (1 + growth / 100) ** 2 : null;
  const real = nominal == null ? null : nominal / (1 + prices / 100) ** 2;
  const jobs = career.jobs_observation ?? career.metrics.jobs;
  const employeeJobs = metricValue(jobs);
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);
  const pay = career.metrics.pay_median;
  const sources = [
    ...(career.sources ?? []).map((source) => ({
      label: source.name,
      url: source.url,
    })),
    ashe,
    cpih,
    evidence?.demandSource,
    evidence?.shortage?.source,
    evidence?.salary?.source,
    evidence?.outlook.source,
  ]
    .filter((source): source is { label: string; url: string } => !!source)
    .filter(
      (source, index, all) =>
        all.findIndex((item) => item.url === source.url) === index,
    );
  return (
    <article className="job-profile">
      <button className="job-back text-button" onClick={onBack}>
        All jobs
      </button>
      <header className="job-profile-header">
        <h1 ref={headingRef} tabIndex={-1}>
          {career.title}
        </h1>
        <p className="job-profile-summary">
          {work[career.soc] ?? career.summary}
        </p>
      </header>
      <dl className="job-facts">
        <div>
          <dt>Pay, {observation(pay)}</dt>
          <dd>{money(metric(career, "pay_median"))}</dd>
          {pay?.flags.includes("imputed_parent") && <small>{pay.note}</small>}
          <small>
            {pay?.low != null && pay.high != null
              ? `Middle 50%: ${money(pay.low)}–${money(pay.high)}`
              : "Range unavailable"}
          </small>
        </div>
        <div>
          <dt>Employee jobs, {observation(jobs)}</dt>
          <dd>{number(employeeJobs == null ? null : employeeJobs * 1000)}</dd>
          <small>{jobs?.note || "Employees only. Not vacancies."}</small>
        </div>
        <div>
          <dt>Demand{evidence ? `, ${evidence.demandYear}` : ""}</dt>
          <dd>{evidence?.demand ?? "Not assessed"}</dd>
          <small>
            {evidence ? "Skills England index" : "No classification supplied"}
          </small>
        </div>
        <div>
          <dt>Your pay scenario</dt>
          <dd>{nominal == null ? "Enter salary" : money(nominal)}</dd>
          <small>Calculated from your assumptions</small>
        </div>
      </dl>
      <section className="job-demand-section">
        <h2>UK demand</h2>
        {evidence?.shortage && (
          <>
            <h3>{evidence.shortage.label}</h3>
            <p>
              {evidence.shortage.reason}{" "}
              <Source source={evidence.shortage.source} />.
            </p>
          </>
        )}
        <p>
          {evidence?.demandReason ??
            "No verified demand classification is included for this occupation."}{" "}
          {evidence && <Source source={evidence.demandSource} />}
        </p>
      </section>
      <PublishedEvidence career={career} />
      <SalaryChart careers={[career]} />
      <section className="job-scenario">
        <div className="scenario-header">
          <h2>Your pay scenario</h2>
          <span>Two years after paid work begins</span>
        </div>
        {evidence?.salary ? (
          <p>
            {evidence.salary.role}: {money(evidence.salary.low)} starter to{" "}
            {money(evidence.salary.high)} experienced.{" "}
            <Source
              source={{
                ...evidence.salary.source,
                label: "National Careers Service",
              }}
            />
            . This range does not specify years of experience.
          </p>
        ) : (
          <p>
            Enter a starting salary to calculate a scenario. No verified
            entry-pay range is included for this occupation.
          </p>
        )}
        <div className="scenario-inputs">
          <label>
            Starting salary (£)
            <input
              type="number"
              min="1"
              max="1000000"
              step="500"
              value={startingPay}
              onChange={(event) => setStartingPay(event.target.value)}
            />
          </label>
          <label>
            Annual pay increase (%)
            <input
              type="number"
              min="-20"
              max="30"
              step="0.5"
              value={increase}
              onChange={(event) => setIncrease(event.target.value)}
            />
          </label>
          <label>
            Annual inflation (%)
            <input
              type="number"
              min="0"
              max="20"
              step="0.5"
              value={inflation}
              onChange={(event) => setInflation(event.target.value)}
            />
          </label>
        </div>
        <div className="scenario-results">
          <dl>
            <dt>Nominal, after 2 years</dt>
            <dd>{money(nominal)}</dd>
          </dl>
          <dl>
            <dt>In today’s money</dt>
            <dd>{money(real)}</dd>
          </dl>
        </div>
        <p className="jobs-source-note">
          Starting pay × (1 + annual increase)²; real pay also divides by (1 +
          inflation)². The default 5% increase and 2% inflation are assumptions,
          not forecasts. Two years starts when paid work begins; training and
          apprenticeship pay can differ. Figures are before tax.
        </p>
        {!valid && (
          <p role="status" className="jobs-source-note">
            Enter a positive salary, a pay increase from −20% to 30%, and
            inflation from 0% to 20%.
          </p>
        )}
      </section>
      <section className="job-outlook">
        <h2>Sector outlook</h2>
        {evidence ? (
          <>
            <h3>{evidence.outlook.title}</h3>
            <p>{evidence.outlook.summary}</p>
            <p className="outlook-period">
              Published evidence: {evidence.outlook.period}.{" "}
              <Source source={evidence.outlook.source} />.
            </p>
            <div className="outlook-columns">
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
          </>
        ) : (
          <p>No verified occupation-specific outlook is included.</p>
        )}
        <p className="jobs-source-note">
          Published scenarios retain their original dates and geographic
          coverage. Employment totals, net growth and replacement hiring measure
          different things; none is a count of vacancies available to a new
          applicant.
        </p>
      </section>
      <section className="job-sources">
        <h2>Sources</h2>
        <ol>
          {sources.map((source) => (
            <li key={source.url}>
              <Source source={source} />
            </li>
          ))}
        </ol>
        <p className="jobs-source-note">
          ASHE pay figures cover full-time employees, excluding self-employment.
          Employee-job coverage is described alongside each supplied metric.
          Observations marked provisional may be revised. Historical occupation
          mappings and the 2021 code break are marked in the chart.
        </p>
      </section>
      {!career.match_supported && (
        <p className="jobs-coverage">
          Personalised matching currently covers 20 careers. This profile is
          available for evidence browsing; detailed skills and study routes have
          not been added yet.
        </p>
      )}
      {career.soc === "5315" ? (
        <a
          className="button secondary"
          href="https://nationalcareers.service.gov.uk/job-profiles/plumber"
          target="_blank"
          rel="noreferrer"
        >
          Training routes
        </a>
      ) : career.match_supported ? (
        <button className="button primary" onClick={onExplore}>
          Explore career
        </button>
      ) : null}
    </article>
  );
}

const metricLabels: Record<string, string> = {
  pay_median: "Annual median pay",
  pay_p10: "Pay, 10th percentile",
  pay_p90: "Pay, 90th percentile",
  real_pay_change_10y: "Real pay change",
  jobs: "Employee jobs",
  demand_trend: "Employee-job trend",
  demand_trend_2011_19: "Earlier employee-job trend",
  exposure: "AI task exposure",
  exposure_uk: "UK exposure cross-check",
  resilience_covid: "COVID employment resilience",
  resilience_cost_of_living: "Cost-of-living pay resilience",
  resilience_tech_slump: "Tech-slump adverts resilience",
  resilience_2008: "2008 crisis resilience",
  young_worker_share: "Workers aged 16–24",
};
const flagNotes: Record<string, string> = {
  historical_observation:
    "This is an older observation; the latest estimate is unavailable.",
  bridged_soc2010:
    "Figures before 2021 are estimated from the older SOC 2010 occupation codes using the ONS crosswalk.",
  bridged_soc2000:
    "Figures before 2011 are estimated from the older SOC 2000 occupation codes using two ONS crosswalks.",
  recoded_2021:
    "Occupation codes changed in 2021, so job counts before and after 2021 are not directly comparable.",
  provisional: "This observation is provisional and may be revised.",
  covid_year:
    "2020 figures are affected by the pandemic: low survey response and furlough.",
  employees_only:
    "Covers employees only; self-employed and freelance workers are not included.",
  suppressed: "ONS withheld this estimate because it was too unreliable.",
  cv_high:
    "This estimate has a sampling error of 10 to 20 percent; treat it with caution.",
  multi_isco:
    "This occupation spans several international job codes; the score is their weighted average and the range shows how much they differ.",
  imputed_parent:
    "No direct figure exists; this is estimated from the wider occupation group.",
  pending_source: "The data source for this figure has not been loaded yet.",
  mock: "This is sample data, not a real figure.",
  category_level:
    "Measured for a broad job-advert category, not for this exact occupation.",
  sources_disagree:
    "Two independent research estimates disagree for this job, so the range is wider.",
};
function metricDisplay(m: Metric, value = metricValue(m)): string {
  if (value == null) return "Not available";
  if (m.unit === "GBP/year") return money(value);
  if (m.unit === "thousand jobs") return `${number(value * 1000)} jobs`;
  if (m.unit.startsWith("fraction"))
    return `${(value * 100).toFixed(1)}%${m.unit.endsWith("/year") ? " / year" : ""}`;
  return `${value.toFixed(3)}${m.unit === "score 0-1" ? " / 1" : ` ${m.unit}`}`;
}
function EvidenceMeasure({ name, measure }: { name: string; measure: Metric }) {
  const flags = measure.flags.map((flag) => flagNotes[flag]).filter(Boolean);
  return (
    <div className="job-evidence-measure">
      <dt>
        {metricLabels[name] ?? name.replaceAll("_", " ")}{" "}
        <span>{observation(measure)}</span>
      </dt>
      <dd>{metricDisplay(measure)}</dd>
      {measure.low != null &&
        measure.high != null &&
        metricValue(measure) != null && (
          <p>
            Supplied range: {metricDisplay(measure, measure.low)} to{" "}
            {metricDisplay(measure, measure.high)}
          </p>
        )}
      <p>{measure.note}</p>
      {measure.status === "preliminary" && <p>Preliminary estimate.</p>}
      {flags.map((note) => (
        <p className="job-evidence-caveat" key={note}>
          {note}
        </p>
      ))}
      {typeof measure.extra.adverts_category === "string" && (
        <p>Job-advert category: {measure.extra.adverts_category}.</p>
      )}
    </div>
  );
}
function PublishedEvidence({ career }: { career: Career }) {
  const headline = ["demand_trend", "exposure"];
  return (
    <section className="job-evidence">
      <h2>What the evidence shows</h2>
      <p className="jobs-source-note">
        Observed employment trends describe the past. AI exposure describes
        tasks that technology could affect; it is not a forecast of job losses.
      </p>
      <dl className="job-evidence-grid">
        {headline.map((key) =>
          career.metrics[key] ? (
            <EvidenceMeasure
              key={key}
              name={key}
              measure={career.metrics[key]}
            />
          ) : null,
        )}
      </dl>
      <details className="job-evidence-details">
        <summary>
          All supplied measures ({Object.keys(career.metrics).length})
        </summary>
        <dl className="job-evidence-grid">
          {Object.entries(career.metrics)
            .filter(([key]) => !headline.includes(key))
            .map(([key, measure]) => (
              <EvidenceMeasure key={key} name={key} measure={measure} />
            ))}
        </dl>
      </details>
    </section>
  );
}
