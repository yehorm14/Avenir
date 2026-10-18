import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { guideProvenance, MODEL_BADGE, PREPARED_BADGE, FALLBACK_NOTE, AI_LABEL } = await loadSource('guideProvenance');

test('a model-written reply shows the model badge, the model name and its "Based on" lines', () => {
  const view = guideProvenance({
    text: 'Median pay was £52,000 in 2024.',
    mode: 'llm_grounded',
    ai_written: true,
    model: 'example-model-1',
    based_on: ['pay_median: £52,000 (ONS ASHE, 2024)', 'jobs: 410,200 (ONS ASHE, 2024)', ''],
    checks: 'passed',
  });
  assert.equal(view.mode, 'llm_grounded');
  assert.equal(view.badge, MODEL_BADGE);
  assert.equal(view.badge, "Written by the model from this role's evidence");
  assert.equal(view.model, 'example-model-1');
  assert.equal(view.aiWritten, true);
  assert.deepEqual(view.basedOn, ['pay_median: £52,000 (ONS ASHE, 2024)', 'jobs: 410,200 (ONS ASHE, 2024)']);
  assert.equal(view.fallbackNote, null);
  assert.equal(AI_LABEL, 'AI-written, check the source');
});

test('a reply without provenance fields reads as a prepared guide', () => {
  for (const reply of [{ text: 'Prepared answer.' }, null, undefined, 'text']) {
    const view = guideProvenance(reply);
    assert.equal(view.mode, 'prepared_demo');
    assert.equal(view.badge, PREPARED_BADGE);
    assert.equal(view.badge, 'Prepared guide (no model connected)');
    assert.equal(view.model, null);
    assert.deepEqual(view.basedOn, []);
    assert.equal(view.fallbackNote, null);
    assert.equal(view.aiWritten, false);
  }
});

test('a fallback check shows the neutral note and keeps the prepared badge', () => {
  const view = guideProvenance({ mode: 'prepared_demo', checks: 'fallback: number 48,000 not in evidence', based_on: 'not-a-list', model: null });
  assert.equal(view.badge, PREPARED_BADGE);
  assert.equal(view.fallbackNote, FALLBACK_NOTE);
  assert.equal(view.fallbackNote, 'Model reply did not pass the number checks; prepared answer shown.');
  assert.deepEqual(view.basedOn, []);
  assert.equal(guideProvenance({ checks: 'passed' }).fallbackNote, null);
});
