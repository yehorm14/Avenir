import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { heroSample, sampleSocs } = await loadSource('heroSample');
const { metricLabel: describe } = await loadSource('metricLabel');

const metric = (value, extra = {}) => ({
  value, low: null, high: null, unit: '', as_of: '2025', source: 'ons_ashe_t14',
  confidence: 'high', flags: [], status: 'ok', note: '', extra: {}, ...extra,
});
const career = (soc, title, metrics) => ({ soc, title, metrics });

const careers = [
  career('2134', 'Programmers', {
    pay_median: metric(52000, { flags: ['provisional'] }),
    demand_trend: metric(0.021, { source: 'ons_ashe_t14', as_of: '2022-2025' }),
    exposure: metric(0.42, { source: 'ilo_wp140', as_of: '2023' }),
  }),
  career('2422', 'Finance managers', {
    pay_median: metric(61000),
    demand_trend: metric(-0.004),
    exposure: metric(null, { status: 'pending' }),
  }),
];

test('sample comparison has one source and year label per figure', () => {
  const rows = heroSample(careers, describe);
  assert.deepEqual(rows.map((r) => r.key), ['pay_median', 'demand_trend', 'exposure']);
  const pay = rows[0].cells[0];
  assert.equal(pay.value, '£52,000');
  assert.match(pay.source, /ONS ASHE/);
  assert.match(pay.source, /2025/);
  assert.match(pay.source, /provisional/);
  assert.equal(rows[1].cells[0].value, '+2.1%');
  assert.equal(rows[1].cells[1].value, '-0.4%');
  assert.match(rows[2].cells[0].source, /ILO Working Paper 140 · 2023/);
});

test('a missing figure reads as Not available with a reason, never as zero', () => {
  const cell = heroSample(careers, describe)[2].cells[1];
  assert.equal(cell.available, false);
  assert.equal(cell.value, 'Not available');
  assert.equal(cell.source, 'Not yet supplied.');
});

test('returns no rows when an example role is missing, so the page shows its empty state', () => {
  assert.deepEqual(heroSample([], describe), []);
  assert.deepEqual(heroSample([careers[0]], describe), []);
  assert.deepEqual([...sampleSocs], ['2134', '2422']);
});
