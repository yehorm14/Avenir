import type { Career, HistoryPoint, Metric } from "./types";

/** View model for the Home page "Employer pulse" card.
 * Occupation figures come from the careers served by the app's own API (ONS ASHE).
 * Employer figures come from /employers/blackrock.json: BlackRock's own reports and
 * careers site (source, page and date on each item, under `official`), plus public
 * Glassdoor UK and Levels.fyi pages read on the date in its `as_of` field.
 * Nothing here is invented and no figure is derived or converted.
 */
export type PulseTab = "finance" | "technology" | "data";

export const pulseTabs: { id: PulseTab; label: string; socs: string[] }[] = [
  // Finance and investment analysts and advisers; actuaries, economists and
  // statisticians are the fallback when the first occupation has no pay figure.
  { id: "finance", label: "Finance", socs: ["2422", "2433"] },
  { id: "technology", label: "Technology", socs: ["2134"] },
  { id: "data", label: "Data", socs: ["3544"] },
];

/** Roles shown in the "Roles they hire" list, in display order. */
export const pulseRoleSocs = ["2134", "2422", "3544", "2433", "2133"];

/** Relative URL of the employer file served from apps/web/public. */
export const employerDataUrl = "employers/blackrock.json";

/** ONS occupation (SOC) to the matching BlackRock job title on Glassdoor UK. */
export const employerRoleMatches: Record<string, string> = {
  "2134": "Software Engineer",
  "2422": "Investment Analyst",
  "2133": "Business Analyst",
};

export const levelsFyiAttribution = {
  label: "Levels.fyi",
  href: "https://www.levels.fyi",
};

const onsAsheUrl =
  "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14";

const dashboardRoutes: Record<string, string> = {
  "2134": "computer-science",
  "3544": "computer-science",
  "2133": "computer-science",
  "2135": "computer-science",
  "2422": "finance",
  "2421": "finance",
  "2433": "finance",
};

const sourceNames: Record<string, string> = {
  ons_ashe_t14: "ONS ASHE",
  ons_cpih: "ONS CPIH",
};

export const unavailableNote = "Data unavailable";
export const employerUnavailableNote = "Employer figures unavailable";

/* ---------- Employer file (raw shape) ---------- */

type SourceRef = { source: string; url: string; note?: string };
type Range = { low: number; high: number; reports: number };

export type EmployerData = {
  employer: string;
  as_of: string;
  facts: ({ label: string; value: string } & SourceRef)[];
  share: {
    ticker: string;
    price_usd: number;
    change_5y_usd: number;
    change_5y_pct: number;
  } & SourceRef;
  career_ladder_uk: SourceRef & { levels: ({ level: string } & Range)[] };
  roles_uk: SourceRef & { roles: ({ title: string } & Range)[] };
  entry_routes: SourceRef & { items: string[] };
  uk_offices: SourceRef & { items: { city: string; reports: number }[] };
  compensation_rating: { value: number; out_of: number } & SourceRef;
  official: OfficialData;
};

/** A fact from BlackRock's own reports or careers site; `source` is a key of `official.sources`. */
export type OfficialFactRaw = {
  label: string;
  value: string;
  note?: string;
  tag?: string;
  details?: string[];
  href?: string;
  source: string;
  page?: string;
  date?: string;
};

type PayGapQuartile = { quarter: string; women_pct: number; men_pct: number };

export type OfficialData = {
  sources: Record<string, { label: string; url: string; note?: string }>;
  ways_in: OfficialFactRaw[];
  degree_subject: OfficialFactRaw;
  career_titles: { items: string[]; source: string };
  career_story: OfficialFactRaw;
  company: OfficialFactRaw[];
  pay_works: OfficialFactRaw[];
  median_pay: OfficialFactRaw;
  pay_gap_uk: {
    source: string;
    snapshot: string;
    scope: string;
    hourly: { median_pct: number; mean_pct: number; page: string };
    bonus: { median_pct: number; mean_pct: number; page: string };
    received_bonus: { women_pct: number; men_pct: number; page: string };
    quartiles: { page: string; items: PayGapQuartile[] };
    trend: {
      page: string;
      from_year: number;
      from_median_pct: number;
      to_year: number;
      to_median_pct: number;
    };
    graduate_class: { women_pct: number; year: number; page: string };
    reason: string;
  };
  pay_fairness_global: OfficialFactRaw;
  benefits: OfficialFactRaw[];
};

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const isNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);
const isString = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0;
const hasSource = (value: unknown): boolean =>
  isObject(value) && isString(value.source) && isString(value.url);
const isRange = (value: unknown): boolean =>
  isObject(value) &&
  isNumber(value.low) &&
  isNumber(value.high) &&
  isNumber(value.reports) &&
  value.low <= value.high;

/** Validates the employer file; returns null when anything required is missing. */
export function parseEmployerData(raw: unknown): EmployerData | null {
  if (!isObject(raw) || !isString(raw.employer) || !isString(raw.as_of))
    return null;
  const { facts, share, career_ladder_uk, roles_uk } = raw;
  const { entry_routes, uk_offices, compensation_rating } = raw;
  const ok =
    Array.isArray(facts) &&
    facts.every(
      (fact) => hasSource(fact) && isString(fact.label) && isString(fact.value),
    ) &&
    hasSource(share) &&
    isObject(share) &&
    isString(share.ticker) &&
    isNumber(share.price_usd) &&
    isNumber(share.change_5y_usd) &&
    isNumber(share.change_5y_pct) &&
    hasSource(career_ladder_uk) &&
    isObject(career_ladder_uk) &&
    Array.isArray(career_ladder_uk.levels) &&
    career_ladder_uk.levels.length > 0 &&
    career_ladder_uk.levels.every(
      (level) => isRange(level) && isString(level.level),
    ) &&
    hasSource(roles_uk) &&
    isObject(roles_uk) &&
    Array.isArray(roles_uk.roles) &&
    roles_uk.roles.every((role) => isRange(role) && isString(role.title)) &&
    hasSource(entry_routes) &&
    isObject(entry_routes) &&
    Array.isArray(entry_routes.items) &&
    entry_routes.items.every(isString) &&
    hasSource(uk_offices) &&
    isObject(uk_offices) &&
    Array.isArray(uk_offices.items) &&
    uk_offices.items.every(
      (item) => isObject(item) && isString(item.city) && isNumber(item.reports),
    ) &&
    hasSource(compensation_rating) &&
    isObject(compensation_rating) &&
    isNumber(compensation_rating.value) &&
    isNumber(compensation_rating.out_of) &&
    isOfficial(raw.official);
  return ok ? (raw as unknown as EmployerData) : null;
}

const hasNumbers = (value: unknown, keys: string[]): boolean =>
  isObject(value) && keys.every((key) => isNumber(value[key]));

/** Official facts: every item names a known source; quartiles add up to 100%. */
function isOfficial(value: unknown): boolean {
  if (!isObject(value) || !isObject(value.sources)) return false;
  const sources = value.sources;
  const sourceOk = Object.values(sources).every(
    (source) =>
      isObject(source) && isString(source.label) && isString(source.url),
  );
  const isFact = (fact: unknown) =>
    isObject(fact) &&
    isString(fact.label) &&
    isString(fact.value) &&
    isString(fact.source) &&
    isObject(sources[fact.source]);
  const isFactList = (list: unknown) =>
    Array.isArray(list) && list.length > 0 && list.every(isFact);
  const gap = value.pay_gap_uk;
  const titles = value.career_titles;
  return (
    sourceOk &&
    isFactList(value.ways_in) &&
    isFact(value.degree_subject) &&
    isObject(titles) &&
    Array.isArray(titles.items) &&
    titles.items.every(isString) &&
    isString(titles.source) &&
    isObject(sources[titles.source]) &&
    isFact(value.career_story) &&
    isFactList(value.company) &&
    isFactList(value.pay_works) &&
    isFact(value.median_pay) &&
    isFact(value.pay_fairness_global) &&
    isFactList(value.benefits) &&
    isObject(gap) &&
    isString(gap.source) &&
    isObject(sources[gap.source]) &&
    isString(gap.snapshot) &&
    isString(gap.scope) &&
    isString(gap.reason) &&
    hasNumbers(gap.hourly, ["median_pct", "mean_pct"]) &&
    hasNumbers(gap.bonus, ["median_pct", "mean_pct"]) &&
    hasNumbers(gap.received_bonus, ["women_pct", "men_pct"]) &&
    hasNumbers(gap.trend, [
      "from_year",
      "from_median_pct",
      "to_year",
      "to_median_pct",
    ]) &&
    hasNumbers(gap.graduate_class, ["women_pct", "year"]) &&
    isObject(gap.quartiles) &&
    Array.isArray(gap.quartiles.items) &&
    gap.quartiles.items.length === 4 &&
    gap.quartiles.items.every(
      (item) =>
        hasNumbers(item, ["women_pct", "men_pct"]) &&
        isString(item.quarter) &&
        isObject(item) &&
        isNumber(item.women_pct) &&
        isNumber(item.men_pct) &&
        item.women_pct + item.men_pct === 100,
    )
  );
}

/* ---------- Formatting ---------- */

export function formatPay(value: number | null | undefined): string {
  return value == null
    ? "Not available"
    : new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(value);
}

/** 43000 -> "£43k". */
export function formatK(value: number): string {
  return `£${Math.round(value / 1000)}k`;
}

/** "£43k–£66k". */
export function formatKRange(low: number, high: number): string {
  return `${formatK(low)}–${formatK(high)}`;
}

export function formatReports(count: number): string {
  return `${new Intl.NumberFormat("en-GB").format(count)} ${count === 1 ? "report" : "reports"}`;
}

export function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

const months = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/** "2026-10-18" -> "18 Oct 2026" (no time zone involved). */
export function formatIsoDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) return iso;
  const month = months[Number(match[2]) - 1];
  return month ? `${Number(match[3])} ${month} ${match[1]}` : iso;
}

/** "+2.6% / year" for a fraction-per-year trend. */
export function formatTrend(value: number | null | undefined): string | null {
  return value == null
    ? null
    : `${value > 0 ? "+" : ""}${(value * 100).toFixed(1)}% / year`;
}

/* ---------- Employer view ---------- */

export type SourceLink = { label: string; href: string };

export type LadderRow = {
  level: string;
  range: string;
  reports: string;
  /** True when the level is one of BlackRock's own career titles. */
  official: boolean;
  /** True when Glassdoor UK has no salary range for this title. */
  missing: boolean;
  low: number | null;
  high: number | null;
  /** Bar position as a percentage of the chart's scale. */
  lowPct: number;
  highPct: number;
};

export type EmployerFact = {
  label: string;
  value: string;
  note: string | null;
  source: SourceLink;
};

/** Card sections in display order; `more` ones sit inside the "More about working at" details. */
export type EmployerSection = {
  id:
    | "ways-in"
    | "facts"
    | "ladder"
    | "pay-works"
    | "pay-fairness"
    | "company"
    | "benefits";
  title: string;
  more: boolean;
};

export type EmployerView = {
  sections: EmployerSection[];
  waysIn: { items: { title: string; href: string }[]; source: SourceLink };
  official: OfficialView;
  name: string;
  asOf: string;
  ladder: {
    title: string;
    rows: LadderRow[];
    ticks: { label: string; pct: number }[];
    source: SourceLink;
    note: string;
    titlesSource: SourceLink;
    story: OfficialFact;
  };
  facts: EmployerFact[];
  share: {
    ticker: string;
    price: string;
    change: string;
    changeUsd: string;
    positive: boolean;
    headline: string;
    note: string;
    source: SourceLink;
    attribution: SourceLink;
  };
};

const isLevelsFyi = (source: string) => /levels\.fyi/i.test(source);

/** Any Levels.fyi figure is credited to "Levels.fyi" with a link to its home page. */
function sourceLink(ref: SourceRef): SourceLink {
  return isLevelsFyi(ref.source)
    ? levelsFyiAttribution
    : { label: ref.source, href: ref.url };
}

export function buildLadder(data: EmployerData): EmployerView["ladder"] {
  const titles = data.official.career_titles;
  const levels = [...data.career_ladder_uk.levels].sort(
    (a, b) => a.low - b.low || a.high - b.high,
  );
  const step = 100000;
  const scaleMax =
    Math.ceil(Math.max(...levels.map((level) => level.high)) / step) * step;
  const pct = (value: number) => Math.round((value / scaleMax) * 1000) / 10;
  const ticks = [];
  for (let value = 0; value <= scaleMax; value += step)
    ticks.push({ label: formatK(value), pct: pct(value) });
  return {
    title: `Career ladder at ${data.employer} (UK)`,
    rows: [
      ...levels.map((level) => ({
        level: level.level,
        range: formatKRange(level.low, level.high),
        reports: formatReports(level.reports),
        official: titles.items.includes(level.level),
        missing: false,
        low: level.low,
        high: level.high,
        lowPct: pct(level.low),
        highPct: pct(level.high),
      })),
      ...titles.items
        .filter((title) => !levels.some((level) => level.level === title))
        .map((title) => ({
          level: title,
          range: noSalaryData,
          reports: "",
          official: true,
          missing: true,
          low: null,
          high: null,
          lowPct: 0,
          highPct: 0,
        })),
    ],
    ticks,
    source: sourceLink(data.career_ladder_uk),
    note: data.career_ladder_uk.note ?? "",
    titlesSource: officialLink(data.official, titles.source),
    story: buildOfficialFact(data.official, data.official.career_story),
  };
}

/* ---------- Official BlackRock facts ---------- */

export const noSalaryData = "no UK salary data";

export type OfficialFact = {
  label: string;
  value: string;
  note: string | null;
  tag: string | null;
  details: string[];
  href: string | null;
  /** "BlackRock 2026 Proxy Statement, p.37, 31 Dec 2025". */
  cite: string;
  source: SourceLink;
};

function officialLink(official: OfficialData, id: string): SourceLink {
  const source = official.sources[id];
  return { label: source.label, href: source.url };
}

export function buildOfficialFact(
  official: OfficialData,
  fact: OfficialFactRaw,
): OfficialFact {
  const source = officialLink(official, fact.source);
  return {
    label: fact.label,
    value: fact.value,
    note: fact.note ?? null,
    tag: fact.tag ?? null,
    details: fact.details ?? [],
    href: fact.href ?? null,
    cite: [source.label, fact.page, fact.date].filter(Boolean).join(", "),
    source,
  };
}

export type PayGapView = {
  title: string;
  scope: string;
  rows: { label: string; value: string; cite: string }[];
  quartiles: { quarter: string; women: number; men: number }[];
  quartilesCite: string;
  reason: string;
  source: SourceLink;
};

export function buildPayGap(official: OfficialData): PayGapView {
  const gap = official.pay_gap_uk;
  const source = officialLink(official, gap.source);
  const cite = (page: string) => `${source.label}, ${page}`;
  return {
    title: "Pay fairness (UK)",
    scope: `${gap.scope}, snapshot ${gap.snapshot}`,
    rows: [
      {
        label: "Hourly pay gap",
        value: `median ${gap.hourly.median_pct}%, mean ${gap.hourly.mean_pct}%`,
        cite: cite(gap.hourly.page),
      },
      {
        label: "Bonus gap",
        value: `median ${gap.bonus.median_pct}%, mean ${gap.bonus.mean_pct}%`,
        cite: cite(gap.bonus.page),
      },
      {
        label: "Received a bonus",
        value: `${gap.received_bonus.women_pct}% of women, ${gap.received_bonus.men_pct}% of men`,
        cite: cite(gap.received_bonus.page),
      },
      {
        label: "Median gap trend",
        value: `${gap.trend.from_median_pct}% (${gap.trend.from_year}) to ${gap.trend.to_median_pct}% (${gap.trend.to_year})`,
        cite: cite(gap.trend.page),
      },
      {
        label: `${gap.graduate_class.year} UK graduate analyst class`,
        value: `${gap.graduate_class.women_pct}% women`,
        cite: cite(gap.graduate_class.page),
      },
    ],
    quartiles: gap.quartiles.items.map((item) => ({
      quarter: item.quarter,
      women: item.women_pct,
      men: item.men_pct,
    })),
    quartilesCite: cite(gap.quartiles.page),
    reason: `The report's stated reason (its claim, not ours): ${gap.reason.charAt(0).toLowerCase()}${gap.reason.slice(1)}`,
    source,
  };
}

export type OfficialView = {
  waysIn: OfficialFact[];
  degreeSubject: OfficialFact;
  company: OfficialFact[];
  payWorks: OfficialFact[];
  medianPay: OfficialFact;
  payGap: PayGapView;
  payFairnessGlobal: OfficialFact;
  benefits: OfficialFact[];
  sources: SourceLink[];
};

/** Official source links, one per document; "(link to verify)" when only the site is known. */
export function officialSources(official: OfficialData): SourceLink[] {
  const seen = new Set<string>();
  return Object.values(official.sources)
    .map((source) => ({
      label: source.note?.includes("(verify)")
        ? `${source.label} (link to verify)`
        : source.label,
      href: source.url,
    }))
    .filter((source) => {
      if (seen.has(source.label)) return false;
      seen.add(source.label);
      return true;
    });
}

export function buildOfficial(official: OfficialData): OfficialView {
  const fact = (raw: OfficialFactRaw) => buildOfficialFact(official, raw);
  return {
    waysIn: official.ways_in.map(fact),
    degreeSubject: fact(official.degree_subject),
    company: official.company.map(fact),
    payWorks: official.pay_works.map(fact),
    medianPay: fact(official.median_pay),
    payGap: buildPayGap(official),
    payFairnessGlobal: fact(official.pay_fairness_global),
    benefits: official.benefits.map(fact),
    sources: officialSources(official),
  };
}

export function buildFacts(data: EmployerData): EmployerFact[] {
  const fromFile = data.facts.map((fact) => ({
    label: fact.label,
    value: fact.value,
    note: fact.note ?? null,
    source: sourceLink(fact),
  }));
  const rating = data.compensation_rating;
  const offices = data.uk_offices.items.map((item) => item.city);
  return [
    ...fromFile,
    {
      label: "Compensation rating",
      value: `${rating.value}/${rating.out_of}`,
      note: null,
      source: sourceLink(rating),
    },
    {
      label: "UK offices",
      value:
        offices.length > 1
          ? `${offices.slice(0, -1).join(", ")} and ${offices[offices.length - 1]}`
          : (offices[0] ?? ""),
      note: data.uk_offices.items
        .map((item) => `${item.city}: ${formatReports(item.reports)}`)
        .join(" · "),
      source: sourceLink(data.uk_offices),
    },
  ];
}

export function buildShare(data: EmployerData): EmployerView["share"] {
  const share = data.share;
  const positive = share.change_5y_pct >= 0;
  const change = `${positive ? "+" : ""}${share.change_5y_pct.toFixed(2)}%`;
  const price = formatUsd(share.price_usd);
  return {
    ticker: share.ticker,
    price,
    change,
    changeUsd: `${share.change_5y_usd >= 0 ? "+" : "-"}${formatUsd(Math.abs(share.change_5y_usd))}`,
    positive,
    headline: `${share.ticker} ${price} · ${change} over five years`,
    note: share.note ?? "",
    source: { label: "TradingView", href: share.url },
    attribution: levelsFyiAttribution,
  };
}

export function buildEmployerView(data: EmployerData): EmployerView {
  return {
    sections: [
      { id: "ways-in", title: "Ways in for you", more: false },
      { id: "facts", title: `${data.employer} at a glance`, more: false },
      { id: "ladder", title: "Career ladder", more: false },
      { id: "pay-works", title: "How pay works in finance", more: true },
      { id: "pay-fairness", title: "Pay fairness", more: true },
      { id: "company", title: "The company", more: true },
      { id: "benefits", title: "Benefits", more: true },
    ],
    waysIn: {
      items: data.entry_routes.items.map((title) => ({
        title,
        href: data.entry_routes.url,
      })),
      source: sourceLink(data.entry_routes),
    },
    official: buildOfficial(data.official),
    name: data.employer,
    asOf: formatIsoDate(data.as_of),
    ladder: buildLadder(data),
    facts: buildFacts(data),
    share: buildShare(data),
  };
}

export type EmployerRoleRange = {
  title: string;
  range: string;
  reports: string;
  href: string;
};

/** BlackRock's self-reported UK range for an ONS occupation, when a role matches. */
export function matchEmployerRole(
  soc: string,
  data: EmployerData | null,
): EmployerRoleRange | null {
  const title = employerRoleMatches[soc];
  if (!title || !data) return null;
  const role = data.roles_uk.roles.find((item) => item.title === title);
  return role
    ? {
        title: role.title,
        range: formatKRange(role.low, role.high),
        reports: formatReports(role.reports),
        href: data.roles_uk.url,
      }
    : null;
}

/* ---------- Occupation (ONS) view ---------- */

export type PulseHeadline = {
  soc: string;
  title: string;
  pay: string;
  payLabel: string;
  trend: string | null;
  trendLabel: string;
  trendPositive: boolean | null;
  fellBack: boolean;
  history: HistoryPoint[];
  priceLabel: string;
};

export type PulseRole = {
  soc: string;
  title: string;
  pay: string;
  payYear: string;
  trend: string | null;
  trendPositive: boolean | null;
  trendLabel: string;
  href: string;
  employer: EmployerRoleRange | null;
};

export type EmployerPulseModel = {
  status: "ready" | "unavailable";
  note: string | null;
  tab: PulseTab;
  headline: PulseHeadline | null;
  roles: PulseRole[];
  employer: EmployerView | null;
  employerNote: string | null;
  footer: string;
  footerLinks: SourceLink[];
};

export function metricValue(metric?: Metric): number | null {
  return !metric ||
    metric.status === "pending" ||
    metric.flags?.includes("suppressed")
    ? null
    : metric.value;
}

export function isRelativeTrend(metric?: Metric): boolean {
  return Object.prototype.hasOwnProperty.call(
    metric?.extra ?? {},
    "typical_occupation_trend",
  );
}

/** Evidence label in the app's "source · year · status" convention. */
export function payLabel(metric?: Metric): string {
  if (!metric) return "No supplied observation";
  return `${sourceNames[metric.source] ?? metric.source} · ${metric.as_of || "Year unavailable"}${metric.flags?.includes("provisional") ? " · provisional" : ""}`;
}

export function roleHref(soc: string): string {
  return `#/${dashboardRoutes[soc] ?? "jobs"}/${soc}`;
}

/** The tab's first occupation with a usable pay figure; `fellBack` when it is not the first candidate. */
export function resolveTabCareer(
  tab: PulseTab,
  careers: Career[],
): { career: Career; fellBack: boolean } | null {
  const socs = pulseTabs.find((item) => item.id === tab)?.socs ?? [];
  for (const [index, soc] of socs.entries()) {
    const career = careers.find((item) => item.soc === soc);
    if (career && metricValue(career.metrics.pay_median) != null)
      return { career, fellBack: index > 0 };
  }
  return null;
}

function trendOf(career: Career) {
  const trend = career.metrics.demand_trend;
  const value = metricValue(trend);
  return {
    trend: formatTrend(value),
    trendPositive: value == null ? null : value >= 0,
    trendLabel: isRelativeTrend(trend)
      ? "Employment trend vs typical"
      : "Employment trend",
  };
}

function footerFor(careers: Career[], employer: EmployerData | null): string {
  const employerPart = employer
    ? `Employer figures: BlackRock's own reports and careers site (page and date on each figure); Glassdoor UK and Levels.fyi, self-reported, as of ${formatIsoDate(employer.as_of)}; share price via TradingView. USD figures are not converted. `
    : "";
  const base = `${employerPart}Occupation pay: ONS ASHE, full-time employees.`;
  const payYears = [
    ...new Set(
      careers
        .map((career) => career.metrics.pay_median?.as_of)
        .filter((year): year is string => !!year),
    ),
  ].sort();
  const trendPeriods = [
    ...new Set(
      careers
        .map((career) => career.metrics.demand_trend?.as_of)
        .filter((period): period is string => !!period),
    ),
  ].sort();
  const updated = [
    payYears.length ? `pay ${payYears.join(", ")}` : "",
    trendPeriods.length ? `employment trend ${trendPeriods.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("; ");
  return updated ? `${base} Updated: ${updated}.` : base;
}

function footerLinksFor(employer: EmployerData | null): SourceLink[] {
  const ons = { label: "ONS ASHE", href: onsAsheUrl };
  if (!employer) return [ons];
  return [
    ...officialSources(employer.official),
    { label: "Glassdoor UK salaries", href: employer.career_ladder_uk.url },
    { label: "Glassdoor UK jobs", href: employer.entry_routes.url },
    levelsFyiAttribution,
    { label: "TradingView", href: employer.share.url },
    ons,
  ];
}

export function buildEmployerPulse(
  careers: Career[],
  tab: PulseTab,
  employerData: EmployerData | null = null,
): EmployerPulseModel {
  const roles = pulseRoleSocs.flatMap((soc) => {
    const career = careers.find((item) => item.soc === soc);
    if (!career) return [];
    const pay = career.metrics.pay_median;
    return [
      {
        soc,
        title: career.title,
        pay: formatPay(metricValue(pay)),
        payYear: pay?.as_of || "Year unavailable",
        href: roleHref(soc),
        employer: matchEmployerRole(soc, employerData),
        ...trendOf(career),
      },
    ];
  });
  const shared = {
    tab,
    roles,
    employer: employerData ? buildEmployerView(employerData) : null,
    employerNote: employerData ? null : employerUnavailableNote,
    footer: footerFor(careers, employerData),
    footerLinks: footerLinksFor(employerData),
  };
  const resolved = resolveTabCareer(tab, careers);
  if (!resolved) {
    return {
      ...shared,
      status: "unavailable",
      note: unavailableNote,
      headline: null,
    };
  }
  const { career, fellBack } = resolved;
  const pay = career.metrics.pay_median;
  return {
    ...shared,
    status: "ready",
    note: null,
    headline: {
      soc: career.soc,
      title: career.title,
      pay: formatPay(metricValue(pay)),
      payLabel: payLabel(pay),
      fellBack,
      history: career.history ?? [],
      priceLabel: career.evidence_metadata?.price_label || "April 2025 prices",
      ...trendOf(career),
    },
  };
}
