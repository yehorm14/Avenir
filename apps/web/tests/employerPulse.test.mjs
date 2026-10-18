import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { loadSource } from "./load-source.mjs";
const {
  buildEmployerPulse,
  buildFacts,
  buildLadder,
  buildShare,
  employerUnavailableNote,
  formatIsoDate,
  formatK,
  formatKRange,
  formatReports,
  formatTrend,
  matchEmployerRole,
  parseEmployerData,
  payLabel,
  resolveTabCareer,
  roleHref,
  unavailableNote,
} = await loadSource("employerPulseModel");

const metric = (value, overrides = {}) => ({
  value,
  low: null,
  high: null,
  unit: "GBP/year",
  as_of: "2025",
  source: "ons_ashe_t14",
  confidence: "medium",
  flags: ["employees_only", "provisional"],
  status: "preliminary",
  note: "",
  extra: {},
  ...overrides,
});
const trend = (value) =>
  metric(value, {
    unit: "fraction/year",
    as_of: "2022-2025",
    extra: { absolute_trend: value, typical_occupation_trend: 0.01 },
  });
const career = (soc, title, pay, growth, overrides = {}) => ({
  soc,
  title,
  summary: "",
  sector: "",
  family: "",
  skills: [],
  metrics: { pay_median: metric(pay), demand_trend: trend(growth) },
  history: [
    {
      year: 2023,
      pay_median: pay - 2000,
      pay_median_real: pay - 1000,
      jobs_k: null,
      flags: [],
    },
    {
      year: 2025,
      pay_median: pay,
      pay_median_real: pay,
      jobs_k: null,
      flags: [],
    },
  ],
  evidence_metadata: { price_label: "2024/25 prices" },
  hedges: [],
  ...overrides,
});
const careers = [
  career(
    "2134",
    "Programmers and software development professionals",
    56914,
    0.0262,
  ),
  career("2422", "Finance and investment analysts and advisers", 50330, 0.0684),
  career("3544", "Data analysts", 38572, 0.1058),
  career("2433", "Actuaries, economists and statisticians", 53342, 0.2332),
  career(
    "2133",
    "IT business analysts, architects and systems designers",
    60288,
    0.0713,
  ),
];

test("each tab maps to the occupation the app already uses", () => {
  assert.equal(resolveTabCareer("finance", careers).career.soc, "2422");
  assert.equal(resolveTabCareer("technology", careers).career.soc, "2134");
  assert.equal(resolveTabCareer("data", careers).career.soc, "3544");
  assert.equal(resolveTabCareer("finance", careers).fellBack, false);
});

test("finance falls back to actuaries, economists and statisticians when 2422 has no pay", () => {
  const suppressed = careers.map((item) =>
    item.soc === "2422"
      ? {
          ...item,
          metrics: {
            ...item.metrics,
            pay_median: metric(null, { flags: ["suppressed"] }),
          },
        }
      : item,
  );
  const resolved = resolveTabCareer("finance", suppressed);
  assert.equal(resolved.career.soc, "2433");
  assert.equal(resolved.fellBack, true);
  assert.equal(buildEmployerPulse(suppressed, "finance").headline.soc, "2433");
});

test("the headline formats real API figures with source, year and status", () => {
  const model = buildEmployerPulse(careers, "technology");
  assert.equal(model.status, "ready");
  assert.equal(model.headline.pay, "£56,914");
  assert.equal(model.headline.payLabel, "ONS ASHE · 2025 · provisional");
  assert.equal(model.headline.trend, "+2.6% / year");
  assert.equal(model.headline.trendLabel, "Employment trend vs typical");
  assert.equal(model.headline.priceLabel, "2024/25 prices");
  assert.equal(model.headline.history.length, 2);
  assert.equal(formatTrend(-0.1468), "-14.7% / year");
  assert.equal(formatTrend(null), null);
  assert.equal(payLabel(metric(1, { flags: [] })), "ONS ASHE · 2025");
});

test("the roles list links every role to its dashboard page", () => {
  const model = buildEmployerPulse(careers, "finance");
  assert.deepEqual(
    model.roles.map((role) => role.soc),
    ["2134", "2422", "3544", "2433", "2133"],
  );
  assert.equal(model.roles[0].href, "#/computer-science/2134");
  assert.equal(model.roles[1].href, "#/finance/2422");
  assert.equal(model.roles[2].pay, "£38,572");
  assert.equal(model.roles[3].trend, "+23.3% / year");
  assert.equal(roleHref("2433"), "#/finance/2433");
});

const employerRaw = JSON.parse(
  await readFile(
    new URL("../public/employers/blackrock.json", import.meta.url),
    "utf8",
  ),
);
const employerData = parseEmployerData(employerRaw);

test("the employer file parses and a broken file is rejected", () => {
  assert.ok(employerData);
  assert.equal(employerData.employer, "BlackRock");
  assert.equal(employerData.as_of, "2026-10-18");
  assert.equal(parseEmployerData(null), null);
  assert.equal(parseEmployerData({ employer: "BlackRock" }), null);
  const broken = structuredClone(employerRaw);
  delete broken.career_ladder_uk.levels[0].low;
  assert.equal(parseEmployerData(broken), null);
  const unsourced = structuredClone(employerRaw);
  delete unsourced.share.url;
  assert.equal(parseEmployerData(unsourced), null);
});

test("the career ladder is ordered by pay and formatted in £k with report counts", () => {
  const shuffled = structuredClone(employerRaw);
  shuffled.career_ladder_uk.levels.reverse();
  const ladder = buildLadder(parseEmployerData(shuffled));
  assert.equal(ladder.title, "Career ladder at BlackRock (UK)");
  assert.deepEqual(
    ladder.rows.map((row) => row.level),
    [
      "Summer analyst (intern)",
      "Analyst",
      "Associate",
      "Vice President",
      "Director",
      "Managing Director",
      "Senior Managing Director",
    ],
  );
  assert.deepEqual(
    ladder.rows.map((row) => row.range),
    [
      "£38k–£55k",
      "£43k–£66k",
      "£62k–£96k",
      "£95k–£145k",
      "£160k–£235k",
      "£211k–£448k",
      "no UK salary data",
    ],
  );
  assert.deepEqual(
    ladder.rows.map((row) => row.official),
    [false, true, true, true, true, true, true],
  );
  assert.equal(ladder.rows[6].missing, true);
  assert.equal(ladder.rows[6].low, null);
  assert.equal(ladder.titlesSource.href, "https://careers.blackrock.com/");
  assert.match(
    ladder.story.value,
    /joined in 1994 as an analyst in the Portfolio Analytics Group/,
  );
  assert.equal(
    ladder.story.cite,
    "BlackRock 2026 Proxy Statement, p.46, FY2025",
  );
  assert.equal(ladder.rows[2].reports, "527 reports");
  assert.equal(ladder.rows[5].highPct, 89.6);
  assert.deepEqual(
    ladder.ticks.map((tick) => tick.label),
    ["£0k", "£100k", "£200k", "£300k", "£400k", "£500k"],
  );
  assert.equal(
    ladder.source.label,
    "Glassdoor UK, self-reported salaries (base pay ranges)",
  );
  assert.match(ladder.note, /Self-reported by employees; ranges, not offers/);
  assert.equal(formatK(43000), "£43k");
  assert.equal(formatKRange(211000, 448000), "£211k–£448k");
  assert.equal(formatReports(1), "1 report");
});

test("facts and share tile carry their values, notes and sources", () => {
  const facts = buildFacts(employerData);
  assert.deepEqual(
    facts.map((fact) => [fact.label, fact.value]),
    [
      ["Employees worldwide", "about 24,900"],
      ["Founded", "1988"],
      ["Open jobs in the UK", "45"],
      ["Compensation rating", "3.5/5"],
      ["UK offices", "London and Edinburgh"],
    ],
  );
  assert.deepEqual(facts[0].source, {
    label: "BlackRock 2026 Proxy Statement",
    href: "https://ir.blackrock.com/",
  });
  assert.equal(
    facts[0].note,
    "In more than 30 countries, at 31 Dec 2025 (p.37)",
  );
  assert.deepEqual(facts[1].source, {
    label: "Levels.fyi",
    href: "https://www.levels.fyi",
  });
  assert.equal(facts[2].note, "Listings on 18 Oct 2026; not a hiring plan");
  assert.equal(
    facts[2].source.href,
    "https://www.glassdoor.co.uk/Jobs/BlackRock-Jobs-E9331.htm",
  );
  assert.equal(facts[4].note, "London: 2,428 reports · Edinburgh: 744 reports");
  const share = buildShare(employerData);
  assert.equal(share.headline, "BLK $1,134.38 · +23.98% over five years");
  assert.equal(share.changeUsd, "+$219.41");
  assert.doesNotMatch(share.note, /share price, not pay/i);
  assert.match(share.note, /not a forecast/);
  assert.equal(share.source.href, "https://www.tradingview.com/symbols/BLK/");
  assert.equal(share.attribution.href, "https://www.levels.fyi");
  assert.equal(formatIsoDate("2026-10-18"), "18 Oct 2026");
});

test("ONS roles show the matching BlackRock range where one exists", () => {
  const model = buildEmployerPulse(careers, "finance", employerData);
  const bySoc = Object.fromEntries(
    model.roles.map((role) => [role.soc, role.employer]),
  );
  assert.equal(bySoc["2134"].title, "Software Engineer");
  assert.equal(bySoc["2134"].range, "£65k–£95k");
  assert.equal(bySoc["2422"].title, "Investment Analyst");
  assert.equal(bySoc["2422"].range, "£44k–£100k");
  assert.equal(bySoc["2133"].title, "Business Analyst");
  assert.equal(bySoc["2133"].reports, "23 reports");
  assert.equal(bySoc["3544"], null);
  assert.equal(bySoc["2433"], null);
  assert.equal(matchEmployerRole("2134", null), null);
  assert.equal(model.employer.waysIn.items.length, 4);
  assert.equal(
    model.employer.waysIn.items[0].href,
    "https://www.glassdoor.co.uk/Jobs/BlackRock-Jobs-E9331.htm",
  );
  assert.equal(model.employerNote, null);
  assert.equal(
    model.footer,
    "Employer figures: BlackRock's own reports and careers site (page and date on each figure); Glassdoor UK and Levels.fyi, self-reported, as of 18 Oct 2026; share price via TradingView. USD figures are not converted. Occupation pay: ONS ASHE, full-time employees. Updated: pay 2025; employment trend 2022-2025.",
  );
  assert.ok(
    model.footerLinks.some((link) => link.href === "https://www.levels.fyi"),
  );
  const labels = model.footerLinks.map((link) => link.label);
  for (const name of [
    "BlackRock 2026 Proxy Statement",
    "BlackRock 2025 Annual Report",
    "BlackRock UK Gender Pay Gap Report 2023 (link to verify)",
    "BlackRock Strategic Funds annual report 2026 (link to verify)",
    "careers.blackrock.com",
    "Glassdoor UK salaries",
    "Levels.fyi",
    "TradingView",
    "ONS ASHE",
  ])
    assert.ok(labels.includes(name), name);
  assert.equal(new Set(labels).size, labels.length);
});

const official = employerData.official;
const view = buildEmployerPulse(careers, "finance", employerData).employer;

test("official BlackRock facts parse, and each names a known source with page or date", () => {
  const facts = [
    ...official.ways_in,
    official.degree_subject,
    official.career_story,
    ...official.company,
    ...official.pay_works,
    official.median_pay,
    official.pay_fairness_global,
    ...official.benefits,
  ];
  for (const fact of facts) {
    const source = official.sources[fact.source];
    assert.ok(source, fact.label);
    assert.match(source.url, /^https:\/\//);
  }
  const dated = facts.filter((fact) => fact.source !== "careers");
  assert.ok(dated.every((fact) => fact.page || fact.date));
  const byLabel = Object.fromEntries(
    official.company.map((fact) => [fact.label, fact]),
  );
  assert.equal(byLabel["Employees by region"].page, "p.38");
  assert.match(
    byLabel["Employees by region"].value,
    /Americas 40%.*31%.*Asia Pacific 29%/,
  );
  assert.equal(byLabel.Offices.value, "154 offices in 88 cities");
  assert.equal(byLabel.Offices.page, "p.83");
  assert.equal(byLabel["Market value"].date, "16 Oct 2026 close");
  assert.match(byLabel["Market value"].value, /\$175\.68B.*\$1,134\.38/);
  assert.match(
    byLabel["Assets under management"].note,
    /\$14,041,518 million.*\$11,551,251 million/,
  );
  assert.equal(byLabel["Assets under management"].page, "p.18");
  assert.match(byLabel.Revenue.note, /\$24,216m.*\$20,407m/);
  assert.match(byLabel["Technology (Aladdin)"].note, /users across Aladdin/);
  assert.equal(byLabel["Outside the United States"].page, "pp.20, 31");
  const broken = structuredClone(employerRaw);
  broken.official.company[0].source = "nowhere";
  assert.equal(parseEmployerData(broken), null);
  const noOfficial = structuredClone(employerRaw);
  delete noOfficial.official;
  assert.equal(parseEmployerData(noOfficial), null);
  assert.equal(
    view.official.sources.find(
      (source) => source.label === "BlackRock 2026 Proxy Statement",
    ).href,
    "https://ir.blackrock.com/",
  );
});

test("Ways in for you comes first, with the official routes and the degree rule", () => {
  assert.equal(view.sections[0].id, "ways-in");
  assert.equal(view.sections[0].title, "Ways in for you");
  assert.equal(view.sections[0].more, false);
  assert.ok(view.sections.filter((section) => section.more).length >= 3);
  assert.equal(Object.keys(view)[0], "sections");
  assert.equal(Object.keys(view)[1], "waysIn");
  const [smartStart, analyst, later] = view.official.waysIn;
  assert.equal(smartStart.label, "Smart Start");
  assert.match(smartStart.value, /school leavers aged 16 to 24/);
  assert.equal(smartStart.tag, "(2023)");
  assert.equal(
    smartStart.cite,
    "BlackRock UK Gender Pay Gap Report 2023, p.6, 2023",
  );
  assert.equal(analyst.label, "2027 Full-Time Analyst Programme, EMEA");
  assert.ok(
    analyst.details.includes(
      "Deadlines: London 30 Sep 2026 (closed), Edinburgh 30 Oct 2026",
    ),
  );
  assert.ok(
    analyst.details.some((detail) => /any degree subject/.test(detail)),
  );
  assert.match(
    analyst.href,
    /careers\.blackrock\.com\/job\/london\/2027-full-time-analyst-program-emea/,
  );
  assert.match(later.value, /18 months or more/);
  assert.equal(later.cite, "BlackRock 2026 Proxy Statement, p.38, FY2025");
  assert.equal(
    `${view.official.degreeSubject.label}: ${view.official.degreeSubject.value}`,
    "Degree subject: any (Analyst Programme 2027)",
  );
  assert.equal(view.waysIn.items.length, 4);
});

test("median employee pay is global and says it is not a starting or UK salary", () => {
  const median = view.official.medianPay;
  assert.equal(median.label, "Median employee pay (global)");
  assert.equal(median.value, "$153,770 in 2025");
  assert.match(median.note, /not a starting or UK salary/);
  assert.match(median.note, /including bonus and stock/);
  assert.equal(median.cite, "BlackRock 2026 Proxy Statement, p.104, 2025");
  assert.ok(view.official.payWorks.every((fact) => !/£|\$\d/.test(fact.value)));
});

test("UK pay gap quarters add up to 100% and match the 2023 report", () => {
  const gap = official.pay_gap_uk;
  assert.equal(gap.snapshot, "5 April 2023");
  for (const quarter of gap.quartiles.items)
    assert.equal(quarter.women_pct + quarter.men_pct, 100, quarter.quarter);
  assert.deepEqual(
    gap.quartiles.items.map((quarter) => quarter.women_pct),
    [54, 48, 40, 30],
  );
  assert.deepEqual(
    gap.quartiles.items.map((quarter) => quarter.men_pct),
    [46, 52, 60, 70],
  );
  const payGap = view.official.payGap;
  assert.deepEqual(
    payGap.rows.map((row) => row.value),
    [
      "median 20%, mean 16%",
      "median 25%, mean 70%",
      "97% of women, 97% of men",
      "25% (2019) to 20% (2023)",
      "56.7% women",
    ],
  );
  assert.equal(
    payGap.rows[3].cite,
    "BlackRock UK Gender Pay Gap Report 2023, p.3",
  );
  assert.match(payGap.reason, /^The report's stated reason/);
  assert.match(payGap.reason, /fewer women in senior roles/);
  assert.match(view.official.payFairnessGlobal.note, /99 cents per \$1\.00/);
  const uneven = structuredClone(employerRaw);
  uneven.official.pay_gap_uk.quartiles.items[0].men_pct = 47;
  assert.equal(parseEmployerData(uneven), null);
});

test('no "Illustrative" text and no "you should" in the employer card', async () => {
  const files = [
    "../src/EmployerPulse.tsx",
    "../src/employerPulseModel.ts",
    "../public/employers/blackrock.json",
  ];
  for (const file of files) {
    const text = await readFile(new URL(file, import.meta.url), "utf8");
    assert.doesNotMatch(text, /illustrative/i, file);
    assert.doesNotMatch(text, /you should/i, file);
  }
  assert.doesNotMatch(JSON.stringify(view), /illustrative/i);
});

test("without the employer file the ONS parts stay and a note says so", () => {
  const model = buildEmployerPulse(careers, "technology", null);
  assert.equal(model.status, "ready");
  assert.equal(model.headline.soc, "2134");
  assert.equal(model.employer, null);
  assert.equal(model.employerNote, employerUnavailableNote);
  assert.equal(model.employerNote, "Employer figures unavailable");
  assert.ok(model.roles.every((role) => role.employer === null));
  assert.doesNotMatch(model.footer, /Glassdoor|Levels\.fyi/);
  assert.deepEqual(
    model.footerLinks.map((link) => link.label),
    ["ONS ASHE"],
  );
});

test("without the API the occupation parts are unavailable", () => {
  const model = buildEmployerPulse([], "finance", employerData);
  assert.equal(model.status, "unavailable");
  assert.equal(model.headline, null);
  assert.equal(model.note, unavailableNote);
  assert.deepEqual(model.roles, []);
  assert.ok(model.employer);
  assert.doesNotMatch(model.footer, /Updated/);
});

test("no invented or illustrative content remains in the model", async () => {
  const source = await readFile(
    new URL("../src/employerPulseModel.ts", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(source, /illustrative/i);
  assert.doesNotMatch(source, /1,200/);
  const model = buildEmployerPulse(careers, "data", employerData);
  assert.doesNotMatch(JSON.stringify(model), /illustrative/i);
  assert.equal(model.illustrative, undefined);
});

test("the card copy has no challenge, partner or most-wanted text, and every figure has a source", async () => {
  const text = JSON.stringify(view);
  assert.doesNotMatch(text, /challenge|partner|most wanted|hackathon|guts/i);
  for (const file of [
    "../src/EmployerPulse.tsx",
    "../src/employerPulseModel.ts",
  ]) {
    const source = await readFile(new URL(file, import.meta.url), "utf8");
    assert.doesNotMatch(
      source,
      /challenge partner|most wanted|hackathon|GUTS/i,
      file,
    );
    assert.doesNotMatch(
      source,
      /BlackRock title|Listings change and close/,
      file,
    );
  }
  for (const fact of view.facts) assert.ok(fact.source.href, fact.label);
  for (const fact of [
    ...view.official.waysIn,
    ...view.official.company,
    ...view.official.payWorks,
    ...view.official.benefits,
    view.official.medianPay,
    view.ladder.story,
  ])
    assert.ok(fact.source.href, fact.label);
  assert.ok(view.ladder.source.href && view.share.source.href);
});
