import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const {
  normaliseEvidencePack,
  fetchEvidencePack,
  sourcesFor,
  sourceLine,
  provenanceLine,
  EXCLUDED_CRISIS_LABEL,
  BACKTEST_RULE_LINE,
  FIT_TAGS_LINE,
  HEDGE_INTRO,
} = await loadSource('evidencePack');

const fixture = () => ({
  title: 'Programmers and software development professionals',
  summary: 'Pay and jobs history for this occupation.',
  metrics: {
    pay_median: { label: 'Median pay', value: 52000, display: '£52,000', unit: 'GBP/year', source: 'ons_ashe_t14', as_of: '2024', status: 'observed', flags: [], caveats: ['Full-time employees only.'] },
    exposure: { label: 'Automation exposure', value: 0.61, display: '61 / 100', unit: 'score 0-1', source: 'ilo_wp140', as_of: '2025', status: 'observed', flags: [], caveats: ['Research estimate; not job loss.', 'Full-time employees only.'] },
  },
  history: [
    { year: 2022, pay_real: 50100.4, pay_nominal: 47000, jobs_k: 410.2 },
    { year: 2023, pay_real: null, pay_nominal: 49000, jobs_k: null },
  ],
  history_note: 'Real pay in 2024/25 prices (CPIH).',
  hedges: [
    { soc: '2133', title: 'IT business analysts', pay_display: '£49,000', trend_display: '+1.2% / year', evidence: 'Jobs rose while this role dipped in 2020.' },
    { soc: '3544', title: 'Data analysts', pay_display: '£41,000', trend_display: '+2.0% / year', evidence: 'Pay held in 2022.' },
    { soc: '2135', title: 'Cyber security professionals', pay_display: '£55,000', trend_display: '+3.1% / year', evidence: 'Adverts held in the tech slump.' },
    { soc: '2421', title: 'Fourth hedge', pay_display: '£1', trend_display: '0%', evidence: 'Should be cut to three.' },
  ],
  backtest: { summary: 'The pay rule ranked this role in the top tier in 3 of 5 years.' },
  crises: [
    { name: 'COVID', period: '2019–2021', placebo_passed: true, excluded_from_recommendations: false, result: 'Jobs fell 2%.' },
    { name: '2008 crisis', period: '2008–2010', placebo_passed: false, excluded_from_recommendations: true, result: null },
  ],
  fit_tags: ['problem solving', 'building things'],
  sources: [
    { key: 'ons_ashe_t14', name: 'ONS ASHE Table 14', url: 'https://www.ons.gov.uk/', as_of: '2024', licence: 'OGL' },
    { key: 'ml_fit_affinity', name: 'Affinity model', as_of: '2026' },
    { key: 'bad', name: 'Unsafe link', url: 'javascript:alert(1)' },
  ],
});

test('every section of the panel is built from the fixture, with numbers only from the payload', () => {
  const view = normaliseEvidencePack(fixture());
  assert.ok(view);
  assert.equal(view.title, 'Programmers and software development professionals');
  // Hedges: at most three cards with title, pay, trend and evidence.
  assert.equal(view.hedges.length, 3);
  assert.deepEqual(view.hedges[0], { soc: '2133', title: 'IT business analysts', pay: '£49,000', trend: '+1.2% / year', evidence: 'Jobs rose while this role dipped in 2020.' });
  assert.ok(!view.hedges.some(h => h.title === 'Fourth hedge'));
  assert.ok(HEDGE_INTRO.includes('historical data'));
  // Backtest summary and the fixed rule line.
  assert.equal(view.backtest.summary, 'The pay rule ranked this role in the top tier in 3 of 5 years.');
  assert.equal(BACKTEST_RULE_LINE, 'Simple rules evaluated later, not a personalised forecast.');
  // Crisis rows keep their period and result; excluded rows are flagged.
  assert.equal(view.crises.length, 2);
  assert.deepEqual(view.crises[0], { name: 'COVID', period: '2019–2021', result: 'Jobs fell 2%.', placeboPassed: true, excluded: false });
  assert.equal(view.crises[1].excluded, true);
  assert.equal(view.crises[1].result, 'No result supplied');
  assert.equal(EXCLUDED_CRISIS_LABEL, 'Failed placebo check: excluded');
  // Fit tags as chips with the affinity-model line.
  assert.deepEqual(view.fitTags, ['problem solving', 'building things']);
  assert.ok(FIT_TAGS_LINE.includes('affinity model (20 roles)'));
  // Pay history rows: real, nominal, jobs, with nulls shown as unavailable.
  assert.deepEqual(view.history, [
    { year: 2022, payReal: '£50,100', payNominal: '£47,000', jobs: '410,200' },
    { year: 2023, payReal: 'Not available', payNominal: '£49,000', jobs: 'Not available' },
  ]);
  assert.equal(view.historyNote, 'Real pay in 2024/25 prices (CPIH).');
  // Caveats are deduplicated and sources keep only safe links.
  assert.deepEqual(view.caveats, ['Full-time employees only.', 'Research estimate; not job loss.']);
  assert.equal(view.sources.length, 3);
  assert.equal(view.sources[2].url, null);
  assert.equal(view.sources[0].url, 'https://www.ons.gov.uk/');
  // Every headline number carries source · year · status.
  assert.deepEqual(view.metricLines[0], { label: 'Median pay', display: '£52,000', provenance: 'ONS ASHE · 2024 · observed' });
  assert.equal(provenanceLine([null, '', undefined]), 'Source not supplied');
  // Section source lines pick the matching sources, falling back to all of them.
  assert.deepEqual(sourcesFor(view, ['affinity']).map(s => s.key), ['ml_fit_affinity']);
  assert.equal(sourcesFor(view, ['nothing-matches']).length, 3);
  assert.equal(sourceLine(sourcesFor(view, ['ashe'])), 'ONS ASHE Table 14 · 2024');
});

test('missing or malformed fields degrade to empty sections instead of invented numbers', () => {
  const view = normaliseEvidencePack({ backtest: null, backtest_note: 'Backtest not run for this role.', fit_tags: null, hedges: 'nope', crises: [{}], history: [{ pay_real: 1 }] });
  assert.ok(view);
  assert.equal(view.backtest.summary, null);
  assert.equal(view.backtest.note, 'Backtest not run for this role.');
  assert.equal(view.fitTags, null);
  assert.deepEqual(view.hedges, []);
  assert.deepEqual(view.crises, []);
  assert.deepEqual(view.history, []);
  assert.deepEqual(view.sources, []);
  assert.equal(normaliseEvidencePack(null), null);
  assert.equal(normaliseEvidencePack('text'), null);
  assert.equal(normaliseEvidencePack([1]), null);
});

test('the panel is hidden on 404, on an error envelope and on a network failure', async () => {
  const notFound = async () => ({ ok: false, status: 404, json: async () => ({ detail: 'Not Found' }) });
  assert.equal(await fetchEvidencePack('2134', notFound), null);
  const errorEnvelope = async () => ({ ok: true, status: 200, json: async () => ({ ok: false, error: { message: 'boom' } }) });
  assert.equal(await fetchEvidencePack('2134', errorEnvelope), null);
  const offline = async () => { throw new TypeError('Failed to fetch'); };
  assert.equal(await fetchEvidencePack('2134', offline), null);
  const badJson = async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad'); } });
  assert.equal(await fetchEvidencePack('2134', badJson), null);
});

test('a successful reply is unwrapped from the API envelope and requested for the right SOC', async () => {
  const calls = [];
  const okEnvelope = async (url) => { calls.push(url); return { ok: true, status: 200, json: async () => ({ ok: true, data: fixture() }) }; };
  const view = await fetchEvidencePack('21/34', okEnvelope);
  assert.deepEqual(calls, ['/api/careers/21%2F34/evidence-pack']);
  assert.equal(view.hedges.length, 3);
  const bare = async () => ({ ok: true, status: 200, json: async () => fixture() });
  assert.equal((await fetchEvidencePack('2134', bare)).crises.length, 2);
});
