import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSource } from './load-source.mjs';
const { rateLimitMessage, GUIDE_RATE_LIMITED, VOICE_RATE_LIMITED } = await loadSource('rateLimit');

test('a 429 on the guide asks the reader to try again in a minute', () => {
  assert.equal(rateLimitMessage(429, 'guide'), GUIDE_RATE_LIMITED);
  assert.match(GUIDE_RATE_LIMITED, /try again in a minute/i);
});

test('a 429 on text to speech says the voice is resting and points to the text', () => {
  assert.equal(rateLimitMessage(429, 'tts'), VOICE_RATE_LIMITED);
  assert.match(VOICE_RATE_LIMITED, /voice is resting/i);
  assert.match(VOICE_RATE_LIMITED, /read the text/i);
});

test('other 429s get a generic message and other statuses get none', () => {
  assert.match(rateLimitMessage(429, 'matches'), /too many requests/i);
  assert.equal(rateLimitMessage(500, 'guide'), null);
  assert.equal(rateLimitMessage(200, 'tts'), null);
});
