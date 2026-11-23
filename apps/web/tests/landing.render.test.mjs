import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

// Bundle the real Landing component (CSS ignored) and render it to HTML on the server:
// no browser, network or provider keys needed.
const root = fileURLToPath(new URL('..', import.meta.url));
const dir = await mkdtemp(path.join(tmpdir(), 'avenir-landing-'));
const out = path.join(dir, 'landing.mjs');
await build({
  entryPoints: [path.join(root, 'src/Landing.tsx')],
  outfile: out,
  bundle: true,
  format: 'esm',
  platform: 'node',
  jsx: 'automatic',
  loader: { '.css': 'empty' },
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  logLevel: 'silent',
});
// Resolve react from the app's own node_modules, not the temp directory.
const bundled = (await readFile(out, 'utf8')).replace(
  /from "(react|react-dom\/server|react\/jsx-runtime)"/g,
  (_, name) => `from "${pathToFileURL(createRequire(path.join(root, 'package.json')).resolve(name)).href}"`,
);
await writeFile(out, bundled);
const { default: Landing } = await import(pathToFileURL(out).href);
const { renderToStaticMarkup } = createRequire(path.join(root, 'package.json'))('react-dom/server');
const React = createRequire(path.join(root, 'package.json'))('react');
test.after(() => rm(dir, { recursive: true, force: true }));

const metric = (value, extra = {}) => ({
  value, low: null, high: null, unit: '', as_of: '2025', source: 'ons_ashe_t14',
  confidence: 'high', flags: [], status: 'ok', note: '', extra: {}, ...extra,
});
const career = (soc, title, metrics) => ({ soc, title, summary: '', sector: '', metrics, history: [] });
const careers = [
  career('2134', 'Programmers', { pay_median: metric(52000), demand_trend: metric(0.02), exposure: metric(0.4, { source: 'ilo_wp140', as_of: '2023' }), jobs: metric(300) }),
  career('2422', 'Finance managers', { pay_median: metric(61000), demand_trend: metric(0.01), exposure: metric(0.3, { source: 'ilo_wp140', as_of: '2023' }), jobs: metric(200) }),
];
const noop = () => {};
const render = (list) =>
  renderToStaticMarkup(
    React.createElement(Landing, {
      careers: list, onChoose: noop, onDashboard: noop, onAmira: noop, onJobs: noop, onPlan: noop,
      nation: 'Scotland', location: 'Glasgow', onNation: noop, onLocation: noop,
    }),
  );

test('hero title is short and not the old all-capital headline', () => {
  const html = render(careers);
  const h1 = html.match(/<h1[^>]*>(.*?)<\/h1>/s)[1];
  assert.equal(h1, 'Compare careers on the evidence');
  assert.ok(h1.split(' ').length <= 6);
});

test('hero exposes a sample comparison with source and year on every figure', () => {
  const html = render(careers);
  const sample = html.match(/<section class="hero-sample".*?<\/section>/s)[0];
  assert.match(sample, /Sample evidence comparison/);
  assert.match(sample, /Programmers/);
  assert.match(sample, /Finance managers/);
  assert.match(sample, /ONS ASHE · 2025/);
  assert.match(sample, /ILO Working Paper 140 · 2023/);
  // 3 measures x 2 roles, each with a labelled source
  assert.equal((sample.match(/<small>/g) ?? []).length, 6);
});

test('journey runs discover, compare, then save and export, as keyboard-reachable buttons', () => {
  const html = render(careers);
  const journey = html.match(/<ol class="ed-journey".*?<\/ol>/s)[0];
  const order = ['Discover', 'Compare', 'Save and export'].map((t) => journey.indexOf(`<strong>${t}</strong>`));
  assert.ok(order.every((i) => i >= 0) && order[0] < order[1] && order[1] < order[2]);
  assert.equal((journey.match(/<button/g) ?? []).length, 3);
  assert.match(journey, /Try a sample comparison/);
});

test('with no evidence loaded the sample shows an honest empty state, not blank cells', () => {
  const html = render([]);
  assert.match(html, /The sample figures are not available right now/);
  assert.doesNotMatch(html, /<section class="hero-sample"[^>]*>.*?<table/s);
  assert.match(html, /Compare careers on the evidence/);
});
