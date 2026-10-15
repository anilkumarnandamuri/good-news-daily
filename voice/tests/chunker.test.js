import test from 'node:test';
import assert from 'node:assert/strict';
import { chunkText, cleanText, storyText, selectStories } from '../src/gn-voice.js';

test('chunks English and Telugu punctuation and retains all words', () => {
  const text = 'మంచి వార్తలు. అందరికీ నమస్కారం। మరో వార్త॥ Hello world! A final question?';
  assert.deepEqual(chunkText(text), ['మంచి వార్తలు.', 'అందరికీ నమస్కారం।', 'మరో వార్త॥', 'Hello world!', 'A final question?']);
  const long = 'This summary has enough words to span many smaller utterances while preserving the original order of every word.';
  const chunks = chunkText(long, 32);
  assert.ok(chunks.every(c => c.length <= 32));
  assert.equal(chunks.join(' '), long);
});

test('preserves decimal numbers, abbreviations, and initials when chunking', () => {
  assert.deepEqual(chunkText('The team raised $3.5 million.'), ['The team raised $3.5 million.']);
  assert.deepEqual(
    chunkText('Dr. Rao and Mr. Smith visited the U.S. and raised $4.2 million. The second sentence.'),
    ['Dr. Rao and Mr. Smith visited the U.S. and raised $4.2 million.', 'The second sentence.']
  );
});

test('handles whitespace, markup, missing text and long unbroken Telugu', () => {
  assert.equal(cleanText('<p>Hello</p>\n world '), 'Hello world');
  assert.deepEqual(chunkText(null), []);
  assert.throws(() => chunkText('text', 1), RangeError);
  const word = 'శ్రీ'.repeat(80);
  const chunks = chunkText(word, 20);
  assert.equal(chunks.join(''), word);
  assert.ok(chunks.every(c => c.length <= 20 && !c.startsWith('్')));
});

test('uses explicit summaries, only falls back to a matching source language', () => {
  const story = { sum_te: 'తెలుగు', summary: 'English summary', lang: 'en-US' };
  assert.equal(storyText(story, 'te'), 'తెలుగు');
  assert.equal(storyText(story, 'en'), 'English summary');
  assert.equal(storyText({ summary: 'Hello', lang: 'en' }, 'te'), '');
});

test('Today’s 5 preserves feed order and rejects ambiguous IDs', () => {
  const items = Array.from({ length: 8 }, (_, id) => ({ id: String(id) }));
  assert.deepEqual(selectStories({ items }).map(s => s.id), ['0', '1', '2', '3', '4']);
  assert.equal(selectStories(items, 0).length, 8);
  assert.throws(() => selectStories({}), TypeError);
  assert.throws(() => selectStories([{ id: 'a' }, { id: 'a' }]), /Duplicate/);
  assert.throws(() => selectStories([{}]), /id/);
});
