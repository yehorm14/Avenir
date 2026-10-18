import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { historySegments } = await loadSource('historySegments');
const point = (year, value = 40) => ({ year, pay_median: value, pay_median_real: value, jobs_k: value, flags: [] });
const years = (points, key = 'pay_median') => historySegments(points, key).map(segment => segment.map(p => p.year));

test('omitted years break the line instead of interpolating evidence', () => {
  assert.deepEqual(years([point(2015), point(2017), point(2018)]), [[2015], [2017, 2018]]);
});
test('null observations break every measure', () => {
  for (const key of ['pay_median', 'pay_median_real', 'jobs_k']) {
    assert.deepEqual(years([point(2018), point(2019, null), point(2020)], key), [[2018], [2020]]);
  }
});
test('the 2021 jobs classification break remains disconnected', () => {
  assert.deepEqual(years([point(2019), point(2020), point(2021), point(2022)], 'jobs_k'), [[2019, 2020], [2021, 2022]]);
});
test('pay retains a bridge only when both adjacent observations exist', () => {
  assert.deepEqual(years([point(2020), point(2021), point(2022)]), [[2020], [2020, 2021, 2022]]);
  assert.deepEqual(years([point(2019), point(2021), point(2022)]), [[2019], [2021, 2022]]);
});
