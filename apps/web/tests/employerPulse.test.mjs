import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadSource } from './load-source.mjs';
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
} = await loadSource('employerPulseModel');

const metric = (value, overrides = {}) => ({
  value,
  low: null,
  high: null,
  unit: 'GBP/year',
  as_of: '2025',
  source: 'ons_ashe_t14',
  confidence: 'medium',
  flags: ['employees_only', 'provisional'],
  status: 'preliminary',
  note: '',
  extra: {},
  ...overrides,
});
const trend = (value) =>
  metric(value, {
    unit: 'fraction/year',
    as_of: '2022-2025',
    extra: { absolute_trend: value, typical_occupation_trend: 0.01 },
  });
const career = (soc, title, pay, growth, overrides = {}) => ({
  soc,
  title,
  summary: '',
  sector: '',
  family: '',
  skills: [],
  metrics: { pay_median: metric(pay), demand_trend: trend(growth) },
  history: [
    { year: 2023, pay_median: pay - 2000, pay_median_real: pay - 1000, jobs_k: null, flags: [] },
    { year: 2025, pay_median: pay, pay_median_real: pay, jobs_k: null, flags: [] },
  ],
  evidence_metadata: { price_label: '2024/25 prices' },
  hedges: [],
  ...overrides,
});
const careers = [
  career('2134', 'Programmers and software development professionals', 56914, 0.0262),
  career('2422', 'Finance and investment analysts and advisers', 50330, 0.0684),
  career('3544', 'Data analysts', 38572, 0.1058),
  career('2433', 'Actuaries, economists and statisticians', 53342, 0.2332),
  career('2133', 'IT business analysts, architects and systems designers', 60288, 0.0713),
];

test('each tab maps to the occupation the app already uses', () => {
  assert.equal(resolveTabCareer('finance', careers).career.soc, '2422');
  assert.equal(resolveTabCareer('technology', careers).career.soc, '2134');
  assert.equal(resolveTabCareer('data', careers).career.soc, '3544');
  assert.equal(resolveTabCareer('finance', careers).fellBack, false);
});

test('finance falls back to actuaries, economists and statisticians when 2422 has no pay', () => {
  const suppressed = careers.map((item) =>
    item.soc === '2422'
      ? { ...item, metrics: { ...item.metrics, pay_median: metric(null, { flags: ['suppressed'] }) } }
      : item,
  );
  const resolved = resolveTabCareer('finance', suppressed);
  assert.equal(resolved.career.soc, '2433');
  assert.equal(resolved.fellBack, true);
  assert.equal(buildEmployerPulse(suppressed, 'finance').headline.soc, '2433');
});

test('the headline formats real API figures with source, year and status', () => {
  const model = buildEmployerPulse(careers, 'technology');
  assert.equal(model.status, 'ready');
  assert.equal(model.headline.pay, '£56,914');
  assert.equal(model.headline.payLabel, 'ONS ASHE · 2025 · provisional');
  assert.equal(model.headline.trend, '+2.6% / year');
  assert.equal(model.headline.trendLabel, 'Employment trend vs typical');
  assert.equal(model.headline.priceLabel, '2024/25 prices');
  assert.equal(model.headline.history.length, 2);
  assert.equal(formatTrend(-0.1468), '-14.7% / year');
  assert.equal(formatTrend(null), null);
  assert.equal(payLabel(metric(1, { flags: [] })), 'ONS ASHE · 2025');
});

test('the roles list links every role to its dashboard page', () => {
  const model = buildEmployerPulse(careers, 'finance');
  assert.deepEqual(
    model.roles.map((role) => role.soc),
    ['2134', '2422', '3544', '2433', '2133'],
  );
  assert.equal(model.roles[0].href, '#/computer-science/2134');
  assert.equal(model.roles[1].href, '#/finance/2422');
  assert.equal(model.roles[2].pay, '£38,572');
  assert.equal(model.roles[3].trend, '+23.3% / year');
  assert.equal(roleHref('2433'), '#/finance/2433');
});

const employerRaw = JSON.parse(
  await readFile(new URL('../public/employers/blackrock.json', import.meta.url), 'utf8'),
);
const employerData = parseEmployerData(employerRaw);

test('the employer file parses and a broken file is rejected', () => {
  assert.ok(employerData);
  assert.equal(employerData.employer, 'BlackRock');
  assert.equal(employerData.as_of, '2026-10-18');
  assert.equal(parseEmployerData(null), null);
  assert.equal(parseEmployerData({ employer: 'BlackRock' }), null);
  const broken = structuredClone(employerRaw);
  delete broken.career_ladder_uk.levels[0].low;
  assert.equal(parseEmployerData(broken), null);
  const unsourced = structuredClone(employerRaw);
  delete unsourced.share.url;
  assert.equal(parseEmployerData(unsourced), null);
});

test('the career ladder is ordered by pay and formatted in £k with report counts', () => {
  const shuffled = structuredClone(employerRaw);
  shuffled.career_ladder_uk.levels.reverse();
  const ladder = buildLadder(parseEmployerData(shuffled));
  assert.equal(ladder.title, 'Career ladder at BlackRock (UK)');
  assert.deepEqual(
    ladder.rows.map((row) => row.level),
    ['Summer analyst (intern)', 'Analyst', 'Associate', 'Vice President', 'Director', 'Managing Director'],
  );
  assert.deepEqual(
    ladder.rows.map((row) => row.range),
    ['£38k–£55k', '£43k–£66k', '£62k–£96k', '£95k–£145k', '£160k–£235k', '£211k–£448k'],
  );
  assert.equal(ladder.rows[2].reports, '527 reports');
  assert.equal(ladder.rows[5].highPct, 89.6);
  assert.deepEqual(
    ladder.ticks.map((tick) => tick.label),
    ['£0k', '£100k', '£200k', '£300k', '£400k', '£500k'],
  );
  assert.equal(ladder.source.label, 'Glassdoor UK, self-reported salaries (base pay ranges)');
  assert.match(ladder.note, /Self-reported by employees; ranges, not offers/);
  assert.equal(formatK(43000), '£43k');
  assert.equal(formatKRange(211000, 448000), '£211k–£448k');
  assert.equal(formatReports(1), '1 report');
});

test('facts and share tile carry their values, notes and sources', () => {
  const facts = buildFacts(employerData);
  assert.deepEqual(
    facts.map((fact) => [fact.label, fact.value]),
    [
      ['Employees worldwide', '25,000'],
      ['Founded', '1988'],
      ['Open jobs in the UK', '45'],
      ['Compensation rating', '3.5/5'],
      ['UK offices', 'London and Edinburgh'],
    ],
  );
  assert.deepEqual(facts[0].source, { label: 'Levels.fyi', href: 'https://www.levels.fyi' });
  assert.equal(facts[2].note, 'Listings on 18 Oct 2026; not a hiring plan');
  assert.equal(facts[2].source.href, 'https://www.glassdoor.co.uk/Jobs/BlackRock-Jobs-E9331.htm');
  assert.equal(facts[4].note, 'London: 2,428 reports · Edinburgh: 744 reports');
  const share = buildShare(employerData);
  assert.equal(share.headline, 'BLK $1,134.38 · +23.98% over five years');
  assert.equal(share.changeUsd, '+$219.41');
  assert.match(share.note, /^Share price, not pay\./);
  assert.match(share.note, /not a forecast/);
  assert.equal(share.source.href, 'https://www.tradingview.com/symbols/BLK/');
  assert.equal(share.attribution.href, 'https://www.levels.fyi');
  assert.equal(formatIsoDate('2026-10-18'), '18 Oct 2026');
});

test('ONS roles show the matching BlackRock range where one exists', () => {
  const model = buildEmployerPulse(careers, 'finance', employerData);
  const bySoc = Object.fromEntries(model.roles.map((role) => [role.soc, role.employer]));
  assert.equal(bySoc['2134'].title, 'Software Engineer');
  assert.equal(bySoc['2134'].range, '£65k–£95k');
  assert.equal(bySoc['2422'].title, 'Investment Analyst');
  assert.equal(bySoc['2422'].range, '£44k–£100k');
  assert.equal(bySoc['2133'].title, 'Business Analyst');
  assert.equal(bySoc['2133'].reports, '23 reports');
  assert.equal(bySoc['3544'], null);
  assert.equal(bySoc['2433'], null);
  assert.equal(matchEmployerRole('2134', null), null);
  assert.equal(model.employer.waysIn.items.length, 4);
  assert.equal(
    model.employer.waysIn.items[0].href,
    'https://www.glassdoor.co.uk/Jobs/BlackRock-Jobs-E9331.htm',
  );
  assert.equal(model.employerNote, null);
  assert.equal(
    model.footer,
    'Employer figures: Glassdoor UK and Levels.fyi, self-reported, as of 18 Oct 2026; share price via TradingView. Occupation pay: ONS ASHE, full-time employees. Updated: pay 2025; employment trend 2022-2025.',
  );
  assert.ok(model.footerLinks.some((link) => link.href === 'https://www.levels.fyi'));
});

test('without the employer file the ONS parts stay and a note says so', () => {
  const model = buildEmployerPulse(careers, 'technology', null);
  assert.equal(model.status, 'ready');
  assert.equal(model.headline.soc, '2134');
  assert.equal(model.employer, null);
  assert.equal(model.employerNote, employerUnavailableNote);
  assert.equal(model.employerNote, 'Employer figures unavailable');
  assert.ok(model.roles.every((role) => role.employer === null));
  assert.doesNotMatch(model.footer, /Glassdoor|Levels\.fyi/);
  assert.deepEqual(model.footerLinks.map((link) => link.label), ['ONS ASHE']);
});

test('without the API the occupation parts are unavailable', () => {
  const model = buildEmployerPulse([], 'finance', employerData);
  assert.equal(model.status, 'unavailable');
  assert.equal(model.headline, null);
  assert.equal(model.note, unavailableNote);
  assert.deepEqual(model.roles, []);
  assert.ok(model.employer);
  assert.doesNotMatch(model.footer, /Updated/);
});

test('no invented or illustrative content remains in the model', async () => {
  const source = await readFile(new URL('../src/employerPulseModel.ts', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /illustrative/i);
  assert.doesNotMatch(source, /1,200/);
  const model = buildEmployerPulse(careers, 'data', employerData);
  assert.doesNotMatch(JSON.stringify(model), /illustrative/i);
  assert.equal(model.illustrative, undefined);
});

