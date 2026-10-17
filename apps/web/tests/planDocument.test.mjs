import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { buildPlanDocument } = await loadSource('planDocument');
const { normalisePreferences } = await loadSource('preferences');

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
