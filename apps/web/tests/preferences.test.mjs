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
