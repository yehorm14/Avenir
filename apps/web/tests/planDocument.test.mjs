import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { buildPlanDocument, resolvePlanRoute, metricCaveats, isRelativeDemand, demandTrendLabel, evidencePriceLabel } = await loadSource('planDocument');
const { normalisePreferences } = await loadSource('preferences');
const { getCareerContent } = await loadSource('content');

const input = () => ({
  careers: [{ soc: '2451', title: 'Architect', metrics: { pay_median: { value: 48000, source: 'ons', as_of: '2024', note: 'Full-time employees only' }, demand_trend: { value: null, source: 'ons', as_of: '2021–2025' } } }],
  preferences: normalisePreferences({ selected: ['2451'], routes: { '2451': 'apprenticeship' }, notes: { '2451': 'Test my interest in design' }, checked: ['2451-0'], saved: ['workshop'] }),
  content: { '2451': { intro: 'Design places.', firstSteps: ['Try drawing', 'Talk to a practitioner'], universities: [] } },
  opportunities: [{ id: 'workshop', title: 'Design workshop', url: 'https://example.org/workshop', location: 'Online' }],
  sources: { ons: { name: 'ONS earnings', url: 'https://www.ons.gov.uk/' } },
});

test('shareable brief carries selected route, personal reasons, actions and saved links', () => {
  const html = buildPlanDocument(input());
  for (const text of ['Architect', 'Earn and learn', 'Test my interest in design', 'Completed', 'Try drawing', 'Design workshop', 'https://example.org/workshop']) assert.ok(html.includes(text), text);
});

test('brief preserves the actual evidence year and missing value', () => {
  const html = buildPlanDocument(input());
  assert.ok(html.includes('2024'));
  assert.ok(html.includes('48,000'));
  assert.ok(html.includes('Not available'));
  assert.ok(html.includes('Full-time employees only'));
  assert.ok(html.includes('ONS earnings'));
});

test('downloaded document escapes personal text and rejects executable source URLs', () => {
  const plan = input();
  plan.preferences.notes['2451'] = '<script>alert("x")</script>';
  plan.opportunities[0].url = 'javascript:alert(1)';
  plan.sources.ons.url = 'javascript:alert(2)';
  const html = buildPlanDocument(plan);
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('javascript:'));
});

for (const [soc, title, expectedRoute, expectedLabel] of [
  ['5241', 'Electrician', 'apprenticeship', 'Earn and learn'],
  ['2451', 'Architect', 'university', 'University'],
]) {
  test(`${title} defaults to the available training route in the plan and export`, () => {
    const content = getCareerContent(soc);
    const plan = input();
    plan.careers[0] = { ...plan.careers[0], soc, title };
    plan.preferences = normalisePreferences({ selected: [soc] });
    plan.content = { [soc]: content };

    assert.equal(resolvePlanRoute(content), expectedRoute);
    assert.ok(buildPlanDocument(plan).includes(`<strong>Route to explore:</strong> ${expectedLabel}.`));
  });
}

test('an explicit saved route takes precedence over the career default', () => {
  assert.equal(resolvePlanRoute(getCareerContent('5241'), 'university'), 'university');
  assert.equal(resolvePlanRoute(getCareerContent('2451'), 'apprenticeship'), 'apprenticeship');
});

test('relative employment labels follow metric metadata, including a zero baseline', () => {
  assert.equal(isRelativeDemand?.({ as_of: '2022-2025', extra: {} }), false);
  assert.equal(isRelativeDemand?.({ as_of: '2022-2025', extra: { typical_occupation_trend: 0 } }), true);
  assert.equal(demandTrendLabel?.({ extra: { typical_occupation_trend: 0.03 } }), 'Employment trend vs typical');
  assert.equal(demandTrendLabel?.({ as_of: '2021-2025' }), 'Employment trend');
});

test('price labels preserve supplied tax-year metadata and legacy fallback', () => {
  assert.equal(evidencePriceLabel?.({ evidence_metadata: { price_label: '2024/25 prices' } }), '2024/25 prices');
  assert.equal(evidencePriceLabel?.({}), 'April 2025 prices');
});

test('new source caveats identify low-purity mapping, indicative counts and incomplete coverage', () => {
  const text = metricCaveats({ flags: ['bridged_low_purity', 'ons_indicative_counts', 'partial_sources', 'fallback_all_employees'] });
  for (const expected of ['may not describe this job', 'indicative, not accurate estimates', 'Part of the source data is missing', 'full- and part-time']) {
    assert.ok(text.includes(expected), expected);
  }
});

test('export keeps relative demand distinct from absolute growth and carries its interval', () => {
  const plan = input();
  plan.careers[0].metrics.demand_trend = {
    value: -0.02, low: -0.05, high: 0.01, unit: 'fraction/year', source: 'ons', as_of: '2022-2025',
    flags: ['ons_indicative_counts'], extra: { absolute_trend: 0.01, typical_occupation_trend: 0.03 },
    note: 'Yearly job change relative to the typical occupation.',
  };
  const html = buildPlanDocument(plan);
  for (const text of ['Employment trend vs typical', '2022-2025', '-2.0% / year', 'relative to the typical occupation', '-5.0% / year', '1.0% / year', 'indicative, not accurate estimates']) {
    assert.ok(html.includes(text), text);
  }
});

test('a direct plan without comparison weights does not invent personal priorities', () => {
  const plan = input();
  const header = buildPlanDocument(plan).split('<section>')[0];
  assert.ok(header.includes('No personal interest profile applied'));
  assert.ok(!header.includes('Interest 45%'));
  assert.ok(!header.includes('Pay 30%'));
});

test('a direct comparison plan exports actual pay and trend weights without interest matching', () => {
  const plan = input();
  plan.preferences.weights = { pay: 75, interest: 0, need: 25 };
  const header = buildPlanDocument(plan).split('<section>')[0];
  for (const text of ['Pay 75%', 'Historical employment trend 25%', 'No interest profile used']) assert.ok(header.includes(text), text);
  assert.ok(!header.includes('Interest 0%'));
});

test('a completed discovery plan retains its actual three-priority summary', () => {
  const plan = input();
  plan.preferences.completed = true;
  const header = buildPlanDocument(plan).split('<section>')[0];
  for (const text of ['Pay 30%', 'Interest 45%', 'Historical demand 25%']) assert.ok(header.includes(text), text);
  assert.ok(!header.includes('No interest profile used'));
});
