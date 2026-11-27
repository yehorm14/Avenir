import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';
import { loadSource } from './load-source.mjs';
const { outputFiles } = await build({
  entryPoints: [fileURLToPath(new URL('../src/heroSample.ts', import.meta.url))],
  bundle: true,
  write: false,
  format: 'esm',
});
const { heroSample, sampleSocs } = await import(
  `data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`
);
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

test('the sample distinguishes relative trends from absolute figures', () => {
  const relative = metric(0.021, { extra: { typical_occupation_trend: 0.04 } });
  const pair = [career('2134', 'Programmers', { demand_trend: relative }), careers[1]];
  const mixed = heroSample(pair, describe)[1];
  assert.equal(mixed.label, 'Employment trend, per year');
  assert.match(mixed.cells[0].source, /^Employment trend vs typical · /);
  assert.match(mixed.cells[1].source, /^Employment trend · /);

  pair[1] = career('2422', 'Finance managers', { demand_trend: relative });
  const bothRelative = heroSample(pair, describe)[1];
  assert.equal(bothRelative.label, 'Employment trend vs typical, per year');
  assert.match(bothRelative.cells[0].source, /^ONS ASHE/);
});
