import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';

const { normalisePreferences } = await loadSource('preferences');

test('malformed saved state recovers to a usable new plan', () => {
  const state = normalisePreferences({ selected: '2451', checked: null, saved: {}, weights: null, discovery: [] });
  assert.deepEqual(state.selected, []);
  assert.deepEqual(state.saved, []);
  assert.deepEqual(state.checked, []);
  assert.equal(state.discovery, undefined);
  assert.equal(state.weights.interest, 45);
});

test('valid ranked choices, routes and notes survive a round trip', () => {
  const state = normalisePreferences({ selected: ['2451', '2134'], completed: true, routes: { '2451': 'apprenticeship' }, notes: { '2451': 'Try a drawing project' }, checked: ['2451-0'], saved: ['iet-events'] });
  assert.deepEqual(state.selected, ['2451', '2134']);
  assert.equal(state.routes['2451'], 'apprenticeship');
  assert.equal(state.notes['2451'], 'Try a drawing project');
  assert.deepEqual(normalisePreferences(JSON.parse(JSON.stringify(state))), state);
});

test('invalid weights and duplicate choices cannot corrupt ranking', () => {
  const state = normalisePreferences({ selected: ['2451', '2451', null, 'oops', '2134', '2121', '2313'], weights: { pay: -10, interest: Infinity, need: 25 }, nation: 'Unknown', step: -2 });
  assert.deepEqual(state.selected, ['2451', '2134', '2121']);
  assert.equal(state.weights.pay, 30);
  assert.equal(state.weights.interest, 45);
  assert.equal(state.weights.need, 25);
  assert.equal(state.nation, 'Scotland');
  assert.equal(state.step, 0);
});

test('discovery drafts recover only valid text and supported modes', () => {
  const state = normalisePreferences({ discovery: { mode: 'known', answers: { direction: 'Architect', subjects: 7 }, step: 1, tags: ['maths', null] } });
  assert.equal(state.discovery.mode, 'known');
  assert.deepEqual(state.discovery.answers, { direction: 'Architect' });
  assert.deepEqual(state.discovery.tags, ['maths']);
});

test('the clinical-career substitution caveat survives saving and reloading', () => {
  const notice = 'Your requested clinical career is not in this career collection. Medical radiographer is a related '
    + 'healthcare option, not an exact match; its training and day-to-day work differ.';
  const state = normalisePreferences({ discovery: { mode: 'known', answers: { direction: 'Doctor' }, notices: [notice] } });

  assert.ok(notice.length > 120);
  assert.deepEqual(state.discovery.notices, [notice]);
  assert.deepEqual(normalisePreferences(JSON.parse(JSON.stringify(state))).discovery.notices, [notice]);
});

test('notice validation rejects malformed or oversized entries without changing accepted caveats', () => {
  const notice = 'The published estimate covers a wider occupation group; check the source before comparing roles.';
  const state = normalisePreferences({ discovery: { mode: 'explore', notices: [null, 7, {}, '', '   ', 'x'.repeat(2001), notice, notice] } });

  assert.deepEqual(state.discovery.notices, [notice]);
});

test('saved notice collections have a bounded number of complete entries', () => {
  const notices = Array.from({ length: 25 }, (_, index) => `Source caveat ${index}: ${'x'.repeat(180)}`);
  const state = normalisePreferences({ discovery: { mode: 'explore', notices } });

  assert.equal(state.discovery.notices.length, 20);
  assert.equal(state.discovery.notices[0], notices[0]);
  assert.equal(state.discovery.notices[19], notices[19]);
});
