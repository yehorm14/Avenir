import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { buildGuideRequest, guideReplyExtras, safeHref, tagWords } = await loadSource('guideRequest');

const history = [{ role: 'user', content: 'Hi' }];
const quiz = {
  tags: ['maths', 'computers_coding', 'maths', '', 7],
  weights: { pay: 30, interest: 145, need: -4 },
  selected: ['2134', '2451', 'abcd', '2134'],
  freeText: '  I like building things.  ',
  acceptsProfile: true,
};

test('buildGuideRequest adds a clean profile when the backend accepts one and the quiz gave something', () => {
  const body = buildGuideRequest('2134', 'What is the path?', history, quiz);
  assert.deepEqual(body, {
    soc: '2134',
    message: 'What is the path?',
    history,
    profile: {
      tags: ['maths', 'computers_coding'],
      weights: { pay: 30, interest: 100, need: 0 },
      selected: ['2134', '2451'],
      free_text: 'I like building things.',
    },
  });
});

test('buildGuideRequest omits the profile without backend support, without a quiz, or with an empty quiz', () => {
  const plain = { soc: '2134', message: 'Hello', history };
  assert.deepEqual(buildGuideRequest('2134', 'Hello', history, null), plain);
  assert.deepEqual(buildGuideRequest('2134', 'Hello', history, undefined), plain);
  assert.deepEqual(buildGuideRequest('2134', 'Hello', history, { ...quiz, acceptsProfile: false }), plain);
  assert.deepEqual(buildGuideRequest('2134', 'Hello', history, { ...quiz, acceptsProfile: undefined }), plain);
  assert.deepEqual(
    buildGuideRequest('2134', 'Hello', history, { tags: [], weights: quiz.weights, selected: [], acceptsProfile: true }),
    plain,
  );
  assert.equal(buildGuideRequest('2134', 'Hello', history, { ...quiz, freeText: '   ' }).profile.free_text, null);
  assert.equal(tagWords(['computers_coding', 'maths']), 'computers coding, maths');
});

test('guideReplyExtras keeps in-app and http(s) links only, deduplicated, and reads the path defensively', () => {
  const extras = guideReplyExtras({
    profile_used: true,
    links: [
      { label: 'Software developer in Avenier', href: '#/guides/2134' },
      { label: 'ONS ASHE', href: 'https://www.ons.gov.uk/x' },
      { label: 'dup', href: 'https://www.ons.gov.uk/x' },
      { label: 'bad', href: 'javascript:alert(1)' },
      { label: 'no label', href: 'http://example.org/' },
      'nonsense',
    ],
    path: {
      routes: [{ label: 'University', summary: 'Study a degree.' }, { label: '' }],
      courses: [{ label: 'Computer science (BSc)' }, { label: 'Finder', href: 'https://example.org/' }, { label: 'x', href: 'ftp://a' }],
      skills: ['debug software', 'debug software', 3],
      grades_note: 'Avenier holds no entry requirements.',
      first_step: 'Build a small project.',
    },
  });
  assert.equal(extras.profileUsed, true);
  assert.deepEqual(extras.links, [
    { label: 'Software developer in Avenier', href: '#/guides/2134' },
    { label: 'ONS ASHE', href: 'https://www.ons.gov.uk/x' },
    { label: 'no label', href: 'http://example.org/' },
  ]);
  assert.deepEqual(extras.path, {
    routes: [{ label: 'University', summary: 'Study a degree.' }],
    courses: [{ label: 'Computer science (BSc)' }, { label: 'Finder', href: 'https://example.org/' }, { label: 'x' }],
    skills: ['debug software'],
    grades_note: 'Avenier holds no entry requirements.',
    first_step: 'Build a small project.',
  });
  assert.equal(safeHref('#/guides/2134'), true);
  assert.equal(safeHref('#/x y'), false);
  assert.equal(safeHref('https://user:pw@example.org/'), false);
});

test('a reply without the new fields has no links, no path and no profile chip', () => {
  for (const reply of [{ text: 'Prepared answer.' }, null, undefined, 'text', { path: {}, links: 'x' }]) {
    assert.deepEqual(guideReplyExtras(reply), { links: [], path: null, profileUsed: false });
  }
});
