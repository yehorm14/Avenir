/** Primary-source context checked 18 October 2026. Published horizons stay intact.
 * Outlooks are qualitative planning context, not 2031 employment forecasts.
 * NCS salary bands describe starter to experienced roles, never a two-year outcome.
 */
type Source = { label: string; url: string };
export type CareerEvidence = {
  demand:
    | "Critical"
    | "Elevated"
    | "Sector priority"
    | "Not in high demand"
    | "Not assessed";
  demandYear: string;
  demandReason: string;
  demandSource: Source;
  outlook: {
    title: string;
    summary: string;
    drivers: string[];
    risks: string[];
    source: Source;
    period: string;
  };
  salary?: { low: number; high: number; source: Source; role: string };
  shortage?: { label: string; reason: string; source: Source };
};

const skillsBase =
  "https://www.gov.uk/government/publications/skills-england-annual-skills-report-and-sectoral-skills-needs-assessments-2026/";
const demandSource: Source = {
  label: "Skills England: Occupations in Demand 2025 — UK (some indicators GB)",
  url: "https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025/explore",
};
const priority2030: Source = {
  label: "Skills England: Assessment of priority skills to 2030",
  url: "https://www.gov.uk/government/publications/assessment-of-priority-skills-to-2030/assessment-of-priority-skills-to-2030",
};
const digitalSource: Source = {
  label: "Skills England: Digital and technologies assessment 2026",
  url: `${skillsBase}sector-skills-needs-assessment-digital-and-technologies`,
};
const financeSource: Source = {
  label: "Skills England: Financial services assessment 2026",
  url: `${skillsBase}sector-skills-needs-assessment-financial-services`,
};
const creativeSource: Source = {
  label: "Skills England: Creative industries assessment 2026",
  url: `${skillsBase}sector-skills-needs-assessment-creative-industries`,
};
const constructionSource: Source = {
  label: "CITB: UK Construction Workforce Outlook 2026–2030",
  url: "https://www.citb.co.uk/cwo/index.html",
};
const shortageSource: Source = {
  label: "Migration Advisory Committee: Temporary Shortage List, July 2026",
  url: "https://www.gov.uk/government/publications/temporary-shortage-list-stage-2-report/temporary-shortage-list-stage-2-report-accessible",
};

// Exact classifications from the release's "Occupations by demand" data table.
const demand: Record<string, CareerEvidence["demand"]> = {
  "2133": "Critical",
  "2254": "Critical",
  "3544": "Critical",
  "3120": "Critical",
  "3113": "Critical",
  "2422": "Elevated",
  "2121": "Elevated",
  "2134": "Elevated",
  "5241": "Elevated",
  "2123": "Elevated",
  "2135": "Elevated",
  "2453": "Elevated",
  "2454": "Elevated",
  "2313": "Elevated",
  "2452": "Elevated",
  "2433": "Not in high demand",
  "5315": "Not in high demand",
  "2421": "Not in high demand",
  "2142": "Not in high demand",
  "2141": "Not in high demand",
  "2451": "Not in high demand",
};

const software: CareerEvidence["outlook"] = {
  title: "Software demand reaches beyond the tech sector",
  summary:
    "The 2025–2030 scenario estimates 87,000 additional programmers and software development professionals across seven priority sectors. This is additional employment in the scenario, not current vacancies or a guarantee of entry-level hiring.",
  drivers: [
    "Cross-sector digital demand",
    "Financial-services technology",
    "Transferable computing foundations",
  ],
  risks: [
    "Historical-trend assumptions",
    "Changing technical tasks",
    "Growth does not guarantee entry-level hiring",
  ],
  source: priority2030,
  period: "2025–2030 published scenario",
};
const digital: CareerEvidence["outlook"] = {
  title: "Digital-sector scenarios through 2035",
  summary:
    "The 2026 sector assessment models growth through 2035, with a substantially lower alternative scenario. It describes England’s sector-wide skills needs, not future employment for this occupation or vacancies in a particular region.",
  drivers: [
    "Digital adoption across industries",
    "Systems, data and security requirements",
    "Higher-level technical learning",
  ],
  risks: [
    "AI adoption makes the outlook uncertain",
    "Routine tasks may change or shrink",
    "A sector-wide scenario cannot predict local hiring",
  ],
  source: digitalSource,
  period: "England skills-planning assessment, 2025–2035 scenarios",
};
const finance: CareerEvidence["outlook"] = {
  title: "Financial-services skills needs through 2035",
  summary:
    "The 2026 assessment models 22.5% growth in selected financial-services priority occupations during 2025–2035, and highlights digital literacy and adaptability. This England sector scenario does not forecast employment for investment analysts or accountants as separate occupations.",
  drivers: [
    "Digitalisation within financial services",
    "Financial analysis and numeracy",
    "Adaptability alongside technical knowledge",
  ],
  risks: [
    "The report does not forecast every finance occupation",
    "AI adoption changes the mix of tasks",
    "Different roles and regions can move in different directions",
  ],
  source: financeSource,
  period: "England skills-planning assessment, 2025–2035 scenario",
};
const quantitative: CareerEvidence["outlook"] = {
  ...finance,
  title: "Separate actuarial, economics and statistical careers",
  summary:
    "This occupation group combines actuaries, economists and statisticians. Their training routes and sectors differ; financial-services growth cannot be applied to the whole group. No combined employment forecast is supplied here.",
};
const construction: CareerEvidence["outlook"] = {
  title: "Construction needs both new entrants and replacement workers",
  summary:
    "CITB estimates 41,200 extra workers a year across UK construction in 2026–2030, covering growth and replacement needs. This is whole-sector recruitment demand, not 41,200 new jobs in this occupation. It informs a 2026–2031 plan without extending the forecast to 2031.",
  drivers: [
    "Construction activity and project pipelines",
    "Replacing workers leaving the industry",
    "Different regional and occupational needs",
  ],
  risks: [
    "Demand varies by region and type of work",
    "Recruitment need is different from net job growth",
    "Whole-sector totals do not establish a shortage in every trade",
  ],
  source: constructionSource,
  period: "2026–2030 UK construction forecast; no 2031 extension",
};
const engineering: CareerEvidence["outlook"] = {
  title: "Engineering skills serve several priority industries",
  summary:
    "Electrical engineers and engineering technicians appear in four priority sectors in the 2025 assessment. For a 2026–2031 plan, compare disciplines and employers; the published horizon ends in 2030 and does not guarantee local vacancies.",
  drivers: [
    "Advanced manufacturing",
    "Defence and digital technologies",
    "Clean-energy projects",
  ],
  risks: [
    "Sector assumptions may change",
    "Disciplines have different requirements",
    "Training takes time",
  ],
  source: priority2030,
  period:
    "2025–2030 priority-sector assessment; qualitative context for 2026–2031",
};
const creative: CareerEvidence["outlook"] = {
  title: "Design work is changing as production tools improve",
  summary:
    "The 2026 creative-industries assessment describes generative AI changing concepting, visualisation and editing, alongside pressure on some entry-level work. For 2026–2031, focus on research, judgement and a portfolio that shows your process. Sector scenarios through 2035 are not a forecast for every designer.",
  drivers: [
    "Digital products and communication",
    "New production and visualisation tools",
    "Creative judgement and audience understanding",
  ],
  risks: [
    "Some entry-level and freelance tasks face pressure",
    "Changing tools require continued learning",
    "Sector growth can coexist with difficulty in individual roles",
  ],
  source: creativeSource,
  period:
    "England skills-planning assessment, 2025–2035; qualitative context for 2026–2031, not a Scotland-specific forecast",
};
const health: CareerEvidence["outlook"] = {
  title: "Imaging demand depends on workforce and service plans",
  summary:
    "NHS England’s 2023 long-term plan identified diagnostic radiography among allied-health professions facing projected shortfalls. This is England-specific planning, not a UK vacancy count or a 2026–2031 forecast. Check current training places and local employers before choosing a route.",
  drivers: [
    "Clinical imaging services",
    "Training and clinical-placement capacity",
    "Workforce retention",
  ],
  risks: [
    "The source is an older conditional workforce plan",
    "England’s plan does not describe every UK nation",
    "Diagnostic and therapeutic radiography have distinct routes",
  ],
  source: {
    label: "NHS England: Long Term Workforce Plan 2023",
    url: "https://www.england.nhs.uk/long-read/nhs-long-term-workforce-plan-2/",
  },
  period: "2023 plan, long-term horizon to 2036/37; qualitative context only",
};
const teaching: CareerEvidence["outlook"] = {
  title: "Pupil numbers and teaching demand are different measures",
  summary:
    "DfE’s 2026 projections show state-funded secondary pupils in England falling from 3.216 million in 2026 to 2.967 million in 2031. That is a pupil forecast, not a teacher-employment forecast: vacancies also depend on subjects, location and workforce turnover.",
  drivers: [
    "Subject and location requirements",
    "Replacing teachers who leave",
    "Changing pupil cohorts",
  ],
  risks: [
    "National pupil numbers do not predict a local vacancy",
    "Population and migration assumptions can change",
    "England’s projections do not cover Scotland, Wales or Northern Ireland",
  ],
  source: {
    label: "DfE: National pupil projections 2026 — England",
    url: "https://explore-education-statistics.service.gov.uk/find-statistics/national-pupil-projections/2026",
  },
  period: "2026–2031 pupil projection; not a jobs forecast",
};

const salary = (
  slug: string,
  role: string,
  low: number,
  high: number,
): NonNullable<CareerEvidence["salary"]> => ({
  low,
  high,
  role,
  source: {
    label: "National Careers Service: starter–experienced annual pay guide",
    url: `https://nationalcareers.service.gov.uk/job-profiles/${slug}`,
  },
});
const entry = (
  soc: string,
  outlook: CareerEvidence["outlook"],
  pay?: CareerEvidence["salary"],
  shortage?: CareerEvidence["shortage"],
): CareerEvidence => ({
  demand: demand[soc] ?? "Not assessed",
  demandYear: "2025",
  demandReason:
    demand[soc] === "Not in high demand"
      ? "The official 2025 assessment classifies this occupation as “Not in high demand”. This does not mean there are no opportunities or no future shortages."
      : "The official 2025 assessment combines labour-market indicators for this occupation. It describes current demand pressure, not guaranteed employment or a live vacancy count.",
  demandSource,
  outlook,
  ...(pay ? { salary: pay } : {}),
  ...(shortage ? { shortage } : {}),
});

export const careerEvidence: Record<string, CareerEvidence> = {
  "2134": entry(
    "2134",
    software,
    salary("software-developer", "Software developer", 30000, 75000),
  ),
  "3544": entry(
    "3544",
    digital,
    salary(
      "data-analyst-statistician",
      "Data analyst-statistician (example role)",
      28000,
      65000,
    ),
  ),
  "2133": entry("2133", digital),
  "2135": entry("2135", digital),
  "2141": entry("2141", creative),
  "2142": entry("2142", creative),
  "2451": entry("2451", construction),
  "2452": entry("2452", construction),
  "3120": entry("3120", construction),
  "2121": entry(
    "2121",
    construction,
    salary("civil-engineer", "Civil engineer", 29000, 63000),
  ),
  "2123": entry(
    "2123",
    engineering,
    salary(
      "electrical-engineer",
      "Electrical engineer (not installation electrician)",
      27000,
      58000,
    ),
  ),
  "3113": entry("3113", engineering),
  "2453": entry("2453", construction),
  "2454": entry("2454", construction),
  "2433": entry(
    "2433",
    quantitative,
    salary(
      "actuary",
      "Actuary example; economists and statisticians have different pay guides",
      32000,
      70000,
    ),
  ),
  "2422": entry(
    "2422",
    finance,
    salary(
      "investment-analyst",
      "Investment analyst (example role)",
      28000,
      75000,
    ),
  ),
  "2421": entry("2421", finance),
  "2254": entry(
    "2254",
    health,
    salary(
      "radiographer",
      "Radiographer; UK nation and specialism affect pay",
      32000,
      48000,
    ),
  ),
  "5241": entry(
    "5241",
    construction,
    salary("electrician", "Qualified electrician", 26000, 45000),
    {
      label: "Shortage evidence",
      reason:
        "MAC’s July 2026 assessment finds relatively strong historical shortage evidence, elevated job advertising and substantial expected future demand. This is separate from the 2025 Elevated demand classification.",
      source: shortageSource,
    },
  ),
  "5315": entry(
    "5315",
    construction,
    salary(
      "plumber",
      "Plumber; heating and ventilation roles may differ",
      24000,
      46000,
    ),
    {
      label: "Future shortage risk",
      reason:
        "MAC’s July 2026 assessment finds mixed historical shortage evidence but a risk of future shortages, with an ageing workforce and training barriers. High self-employment complicates employee-based evidence.",
      source: shortageSource,
    },
  ),
  "2313": entry(
    "2313",
    teaching,
    salary(
      "secondary-school-teacher",
      "Secondary school teacher (England)",
      34000,
      53000,
    ),
  ),
};
