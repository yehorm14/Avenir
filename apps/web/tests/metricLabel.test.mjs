import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadSource } from './load-source.mjs';
const { metricLabel, metricAvailable, sourcePeriodSummary } = await loadSource('metricLabel');
const { buildPlanDocument } = await loadSource('planDocument');
const { normalisePreferences } = await loadSource('preferences');
const fixture = JSON.parse(await readFile(new URL('./fixtures/metrics.json', import.meta.url), 'utf8'));

test('snapshot-derived pay shows source, period, geography and estimation labels', () => {
  const label = metricLabel(fixture.snapshot.pay_median);
  assert.equal(label.available, true);
  assert.equal(label.source, 'ONS ASHE');
  assert.equal(label.period, '2025');
  assert.equal(label.geography, 'UK');
  assert.deepEqual(label.estimation, ['employees only', 'provisional']);
  assert.equal(label.text, 'ONS ASHE · 2025 · UK · employees only · provisional');
});

test('trend and exposure keep their own period and source, in the same format everywhere', () => {
  assert.match(metricLabel(fixture.snapshot.demand_trend).text, /^ONS ASHE · 2022-2025 · UK · .*indicative counts/);
  assert.match(metricLabel(fixture.snapshot.exposure).text, /^ILO Working Paper 140 · 2025 · international research/);
});

test('a missing or withheld value is unavailable with a reason, never zero', () => {
  assert.equal(metricAvailable(fixture.missing), false);
  const label = metricLabel(fixture.missing);
  assert.equal(label.available, false);
  assert.match(label.unavailableReason, /Withheld/);
  assert.equal(metricLabel(undefined).available, false);
  assert.match(metricLabel(undefined).text, /No supplied observation/);
  assert.equal(metricLabel({ ...fixture.missing, flags: [], status: 'pending' }).unavailableReason, 'Not yet supplied.');
});

test('a real zero stays available and is not treated as missing', () => {
  assert.equal(metricAvailable(fixture.zero), true);
  assert.equal(metricLabel(fixture.zero).available, true);
});

test('summary lists each distinct source period once when switching or filtering careers', () => {
  const a = { metrics: { pay_median: fixture.snapshot.pay_median } };
  const b = { metrics: { pay_median: { ...fixture.snapshot.pay_median, value: 40000 } } };
  const c = { metrics: { pay_median: { ...fixture.snapshot.pay_median, as_of: '2024' } } };
  assert.equal(sourcePeriodSummary([a, b], 'pay_median'), 'ONS ASHE · 2025 · UK');
  assert.equal(sourcePeriodSummary([b], 'pay_median'), sourcePeriodSummary([a, b], 'pay_median'));
  assert.equal(sourcePeriodSummary([a, c], 'pay_median'), 'ONS ASHE · 2025 · UK; ONS ASHE · 2024 · UK');
  assert.equal(sourcePeriodSummary([{ metrics: {} }], 'pay_median'), 'no supplied observation');
});

test('the downloaded plan also carries the source period and marks the missing value', () => {
  const html = buildPlanDocument({
    careers: [{ soc: '2134', title: 'Software developer', metrics: { pay_median: fixture.snapshot.pay_median, demand_trend: fixture.missing } }],
    preferences: normalisePreferences({ selected: ['2134'] }),
    content: {},
    opportunities: [],
    sources: { ons_ashe_t14: { name: 'ONS ASHE', url: 'https://www.ons.gov.uk/' } },
  });
  assert.ok(html.includes('2025') && html.includes('ONS ASHE') && html.includes('Not available'));
});
