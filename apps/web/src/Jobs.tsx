import { useState } from "react";
import type { Career } from "./types";
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
function metric(career: Career, key: string) {
  const m = career.metrics[key];
  return m?.status === "pending" || m?.flags.includes("suppressed")
    ? null
    : (m?.value ?? null);
}
function employment(career: Career) {
  return [...career.history].reverse().find((point) => point.jobs_k != null);
}
const number = (n: number | null | undefined) =>
  n == null ? "Not available" : Math.round(n).toLocaleString("en-GB");
const priority = (career: Career) => {
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
  careers,
  onExplore,
}: {
  careers: Career[];
  onExplore: (career: Career) => void;
}) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("demand");
  const [selected, setSelected] = useState<Career | null>(null);
  if (selected)
    return (
      <JobProfile
        key={selected.soc}
        career={selected}
        onBack={() => {
          setSelected(null);
          window.scrollTo(0, 0);
        }}
        onExplore={() => onExplore(selected)}
      />
    );
  const rows = careers
    .filter((career) =>
      `${career.title} ${career.sector}`
        .toLowerCase()
        .includes(search.toLowerCase()),
    )
    .sort((a, b) => {
      if (sort === "pay")
        return (
          (metric(b, "pay_median") ?? -1) - (metric(a, "pay_median") ?? -1)
        );
      if (sort === "name") return a.title.localeCompare(b.title);
      return priority(a) - priority(b) || a.title.localeCompare(b.title);
    });
  return (
    <section className="jobs-directory">
      <header className="jobs-heading">
        <h1>Jobs</h1>
        <small>Evidence checked 18 October 2026</small>
      </header>
      <div className="jobs-controls">
        <label className="search">
          <span className="sr-only">Search careers</span>
          <input
            type="search"
            placeholder="Search jobs"
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
      <div className="jobs-table table-scroll">
        <table>
          <thead>
            <tr>
              <th>Career</th>
              <th>UK demand</th>
              <th>Pay</th>
              <th>Employees</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((career) => {
              const evidence = careerEvidence[career.soc];
              const jobs = employment(career);
              return (
                <tr
                  key={career.soc}
                  className={priority(career) < 2 ? "priority-job" : ""}
                >
                  <th scope="row" className="job-name">
                    <button
                      onClick={() => {
                        setSelected(career);
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
                      {evidence?.shortage ? "MAC 2026" : "Skills England 2025"}
                    </small>
                  </td>
                  <td>{money(metric(career, "pay_median"))}</td>
                  <td>
                    {number(jobs?.jobs_k == null ? null : jobs.jobs_k * 1000)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {!rows.length && <p className="jobs-source-note">No matching careers.</p>}
      <p className="jobs-source-note">
        Pay and employment: full-time employees, 2025; provisional.
        Self-employed workers are excluded. Pay is the annual median, not a
        starting salary. <Source source={ashe} />.
      </p>
      <p className="jobs-source-note">
        Electricians and plumbers appear first because of infrastructure needs
        identified by the Migration Advisory Committee. Demand categories
        measure recruitment pressure, not confirmed vacancies or guaranteed
        employment. <Source source={demandSource} />. Select a career for the
        evidence and outlook.
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
  const latest = employment(career);
  const pay = career.metrics.pay_median;
  const sources = [
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
        <h1>{career.title}</h1>
        <p className="job-profile-summary">
          {work[career.soc] ?? career.summary}
        </p>
      </header>
      <dl className="job-facts">
        <div>
          <dt>Pay, {pay?.as_of ?? "2025"}</dt>
          <dd>{money(metric(career, "pay_median"))}</dd>
          <small>
            {pay?.low != null && pay.high != null
              ? `Middle 50%: ${money(pay.low)}–${money(pay.high)}`
              : "Range unavailable"}
          </small>
        </div>
        <div>
          <dt>Employees, {latest?.year ?? "2025"}</dt>
          <dd>
            {number(latest?.jobs_k == null ? null : latest.jobs_k * 1000)}
          </dd>
          <small>Full-time. Not vacancies.</small>
        </div>
        <div>
          <dt>Demand, {evidence?.demandYear ?? "2025"}</dt>
          <dd>{evidence?.demand ?? "Not assessed"}</dd>
          <small>Skills England index</small>
        </div>
        <div>
          <dt>Two-year pay</dt>
          <dd>{nominal == null ? "Enter salary" : money(nominal)}</dd>
          <small>Planning estimate · assumptions below</small>
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
      <SalaryChart careers={[career]} />
      <section className="job-scenario">
        <div className="scenario-header">
          <h2>Two-year pay estimate</h2>
          <span>Scenario, not an earnings statistic</span>
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
        <h2>2026–2031 outlook</h2>
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
          This is a qualitative outlook for the next five years. Published
          projections retain their original dates and coverage; none is extended
          to 2031. Employment totals, net growth and replacement hiring are
          different measures; none is a count of vacancies available to a new
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
          ASHE figures cover full-time employees, excluding self-employment. The
          2025 observations are provisional. Historical occupation mappings and
          the 2021 code break are marked in the chart.
        </p>
      </section>
      {career.soc === "5315" ? (
        <a
          className="button secondary"
          href="https://nationalcareers.service.gov.uk/job-profiles/plumber"
          target="_blank"
          rel="noreferrer"
        >
          Training routes
        </a>
      ) : (
        <button className="button primary" onClick={onExplore}>
          Explore career
        </button>
      )}
    </article>
  );
}
