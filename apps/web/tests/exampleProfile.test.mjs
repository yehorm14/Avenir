import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { amiraAnswers, isExampleProfile, exampleSteps } = await loadSource('exampleProfile');
const { normalisePreferences, initial } = await loadSource('preferences');

const amiraPrefs = () => normalisePreferences({
  completed: true,
  selected: ['2451'],
  discovery: { mode: 'known', answers: amiraAnswers, step: 5 },
});

test('Amira example is recognised after it is saved and reloaded from storage', () => {
  assert.equal(isExampleProfile(amiraPrefs()), true);
  assert.equal(isExampleProfile(normalisePreferences(JSON.parse(JSON.stringify(amiraPrefs())))), true);
});

test('a visitor profile, an edited answer or an incomplete quiz is not labelled as the example', () => {
  assert.equal(isExampleProfile(initial), false);
  const edited = amiraPrefs();
  edited.discovery.answers.direction = 'Teacher';
  assert.equal(isExampleProfile(edited), false);
  const incomplete = { ...amiraPrefs(), completed: false };
  assert.equal(isExampleProfile(incomplete), false);
  const explore = amiraPrefs();
  explore.discovery.mode = 'explore';
  assert.equal(isExampleProfile(explore), false);
});

test('starting a fresh session returns to the empty state, so the example label disappears', () => {
  const fresh = structuredClone(initial);
  assert.equal(isExampleProfile(fresh), false);
  assert.deepEqual(fresh.selected, []);
  assert.deepEqual(fresh.checked, []);
});

test('the guided journey goes quiz and matches, then evidence, then plan', () => {
  assert.deepEqual(exampleSteps.map((step) => step.page), ['matches', 'evidence', 'overview']);
});

test('the sample answers carry no personal details beyond a first name, school year and city', () => {
  assert.deepEqual(Object.keys(amiraAnswers).sort(), ['direction', 'interests', 'skills', 'subjects', 'values']);
});
