'use strict';
// Tests for the JavaScript implementation of dice/1: the engine inside made/dice.html, reached
// through tools/dice.cjs so the test runs the one copy the page and the command line share, and
// the command line itself through child_process. Run with: node --test tests/test_dice.cjs
// The specification is made/dice.md; every anchor below is taken from it or from node:crypto.
// The suite writes temporary record files under the system temp directory for the replay tests
// and removes them again; nothing under the repository is written.
const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

const CLI = path.join(__dirname, '../tools/dice.cjs');
const MADE = path.join(__dirname, '../made');
const FIXTURES = path.join(__dirname, 'dice_fixtures.json');
const Dice = require(CLI);
const TWO_32 = 2 ** 32;
const TWO_53 = 2 ** 53;

// Engine values are created in another vm realm, so their prototypes differ from this file's;
// strict deep equality against literals goes through JSON, as the other .cjs suites here do.
const plain = (x) => JSON.parse(JSON.stringify(x));
const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
const reference = (bytes) => crypto.createHash('sha256').update(Buffer.from(bytes)).digest('hex');
const request = (kind, params, seed = 'test-seed', stream = kind) => ({version: Dice.VERSION, seed, stream, kind, params});
const run = (kind, params, seed, stream) => Dice.run(request(kind, params, seed, stream));
const range = (n) => Array.from({length: n}, (_, i) => i);

// Deep equality for JSON values that also checks key order: arrays by position, objects by their
// key lists in order, numbers exactly unless a tolerance is given (for normals), the rest by ===.
function assertSameJSON(got, want, where, tolerance = 0) {
  if (Array.isArray(want)) {
    assert.ok(Array.isArray(got), where + ' is an array');
    assert.equal(got.length, want.length, where + ' has ' + want.length + ' items');
    want.forEach((item, i) => assertSameJSON(got[i], item, where + '[' + i + ']', tolerance));
  } else if (want !== null && typeof want === 'object') {
    assert.ok(got !== null && typeof got === 'object' && !Array.isArray(got), where + ' is an object');
    assert.deepEqual(Object.keys(got), Object.keys(want), where + ' has the same keys in the same order');
    for (const key of Object.keys(want)) assertSameJSON(got[key], want[key], where + '.' + key, tolerance);
  } else if (typeof want === 'number' && tolerance > 0) {
    assert.equal(typeof got, 'number', where + ' is a number');
    assert.ok(Math.abs(got - want) <= tolerance, where + ': ' + got + ' is not within ' + tolerance + ' of ' + want);
  } else {
    assert.equal(got, want, where);
  }
}

// A small deterministic byte source for the hash cross-check, so a failure repeats exactly.
// xorshift32 with a fixed start; it is a test fixture, not part of dice/1.
function byteSource(start) {
  let x = start >>> 0 || 1;
  return (n) => {
    const out = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
      out[i] = x & 255;
    }
    return out;
  };
}

test('the engine exports the names the spec gives, and the lists are exactly the spec words', () => {
  assert.equal(Dice.VERSION, 'dice/1');
  assert.equal(Dice.ADJECTIVES.length, 64);
  assert.equal(Dice.NOUNS.length, 64);
  assert.equal(Dice.OPERATIONS.length, 12);
  assert.equal(Dice.CONSTRAINTS.length, 6);
  assert.equal(Dice.ADJECTIVES[0], 'quiet'); assert.equal(Dice.ADJECTIVES[63], 'brief');
  assert.equal(Dice.NOUNS[0], 'hour'); assert.equal(Dice.NOUNS[63], 'salt');
  assert.equal(new Set(Dice.ADJECTIVES).size, 64, 'adjectives are distinct');
  assert.equal(new Set(Dice.NOUNS).size, 64, 'nouns are distinct');
  assert.equal(Dice.OPERATIONS[2], 'Change one parameter and report what moved.');
  assert.equal(Dice.OPERATIONS[11], 'Take one number it reports and get the same number a different way.');
  assert.equal(Dice.CONSTRAINTS[4], 'Reproducible from a seed.');
  assert.equal(Dice.CONSTRAINTS[5], 'Finished inside one session.');
  for (const name of ['sha256', 'stream', 'run', 'checks']) assert.equal(typeof Dice[name], 'function');
  // The parameters of each kind, in the spec table's order.
  assert.deepEqual(plain(Dice.KINDS), ['words', 'uniform', 'integer', 'normal', 'coin', 'hex', 'name', 'pick', 'shuffle', 'sample', 'weighted', 'suggest']);
  assert.deepEqual(plain(Dice.PARAMS), {words: ['count'], uniform: ['count'], integer: ['count', 'min', 'max'], normal: ['count'],
    coin: ['count', 'p'], hex: ['words'], name: ['count'], pick: ['pool', 'count'], shuffle: ['pool'], sample: ['pool', 'k'],
    weighted: ['pool', 'weights', 'count'], suggest: ['pool']});
});

test('SHA-256 matches node:crypto for the two test vectors', () => {
  assert.equal(hex(Dice.sha256(new Uint8Array(0))), 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
  assert.equal(hex(Dice.sha256(Uint8Array.from([97, 98, 99]))), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  assert.equal(Dice.sha256(new Uint8Array(0)).length, 32);
});

test('SHA-256 matches node:crypto for every message length from 0 to 200 bytes', () => {
  const bytes = byteSource(0x9e3779b9);
  for (let n = 0; n <= 200; n++) {
    const message = bytes(n);
    assert.equal(hex(Dice.sha256(message)), reference(message), 'length ' + n);
  }
});

test('SHA-256 matches node:crypto for 200 deterministic messages of up to 5000 bytes', () => {
  const bytes = byteSource(0x2545f491);
  const lengths = byteSource(0x1234567);
  for (let i = 0; i < 200; i++) {
    const l = lengths(2);
    const n = ((l[0] << 8) | l[1]) % 5001;
    const message = bytes(n);
    assert.equal(hex(Dice.sha256(message)), reference(message), 'message ' + i + ' of length ' + n);
  }
  assert.throws(() => Dice.sha256('abc'), /Uint8Array/);
  assert.throws(() => Dice.sha256([97, 98, 99]), /Uint8Array/);
});

test('the anchor: words 0, 1, 2 and 8 of seed "a", stream "b", and its first uniform', () => {
  const s = Dice.stream('a', 'b');
  assert.equal(s.seed, 'a');
  assert.equal(s.stream, 'b');
  assert.equal(s.cursor, 0);
  assert.deepEqual([s.word(0), s.word(1), s.word(2), s.word(8)], [3844899584, 819827472, 3336811594, 2212906652]);
  assert.equal(s.cursor, 0, 'word(i) is random access and leaves the cursor alone');
  assert.equal(s.uniform(), 8063338865194572 / TWO_53);
  assert.equal(s.cursor, 2);
  // The key bytes are the spec's 28 bytes; the engine builds them as bytes, so hashing the
  // same bytes directly through node:crypto must give block 0.
  const key = Buffer.concat([Buffer.from([0, 0, 0, 6]), Buffer.from('dice/1'), Buffer.from([0, 0, 0, 1]), Buffer.from('a'),
    Buffer.from([0, 0, 0, 1]), Buffer.from('b'), Buffer.alloc(8)]);
  assert.equal(key.length, 28);
  const digest = crypto.createHash('sha256').update(key).digest();
  assert.equal(digest.readUInt32BE(0), s.word(0));
  assert.equal(digest.readUInt32BE(28), s.word(7));
});

test('the first name of seed "336489" on stream "name" is quiet-hour-15', () => {
  assert.equal(Dice.stream('336489', 'name').name(), 'quiet-hour-15');
});

test('uniform lies in [0, 1), sits on the 2^-53 grid, and takes two words each', () => {
  const s = Dice.stream('u', 'uniform');
  for (let i = 0; i < 2000; i++) {
    const u = s.uniform();
    assert.ok(u >= 0 && u < 1);
    assert.ok(Number.isInteger(u * TWO_53), 'exactly k / 2^53');
  }
  assert.equal(s.cursor, 4000);
  // The formula from the spec, recomputed from the words by hand.
  const t = Dice.stream('u', 'uniform');
  const a = t.word(0), b = t.word(1);
  assert.equal(t.uniform(), ((a >>> 5) * 67108864 + (b >>> 6)) / TWO_53);
});

test('below takes nothing for n = 1, one word for n up to 2^32, two words above, and stays below n', () => {
  const s = Dice.stream('b', 'below');
  assert.equal(s.below(1), 0);
  assert.equal(s.cursor, 0, 'n = 1 takes nothing');
  const first = s.word(0);
  const two = s.below(2);
  assert.equal(two, first >>> 31, 'n = 2 is the top bit of one word');
  assert.equal(s.cursor, 1);
  const w = s.word(1);
  assert.equal(s.below(TWO_32), w, 'n = 2^32 returns the one word it takes');
  assert.equal(s.cursor, 2);
  // n = 2^32 + 1: 33 bits, so two words per attempt and the accepted value is below n.
  for (let i = 0; i < 200; i++) {
    const before = s.cursor;
    const v = s.below(TWO_32 + 1);
    assert.ok(Number.isInteger(v) && v >= 0 && v <= TWO_32);
    assert.ok(s.cursor > before && (s.cursor - before) % 2 === 0, 'two words per attempt');
  }
  // n = 2^53: 53 bits, and (a >>> 11) * 2^32 + b is always below 2^53, so exactly one attempt.
  const before = s.cursor;
  const a = s.word(before), b = s.word(before + 1);
  const big = s.below(TWO_53);
  assert.equal(big, (a >>> 11) * TWO_32 + b);
  assert.equal(s.cursor, before + 2);
  assert.ok(Number.isSafeInteger(big));
  // The result for a small n is the top k bits of the word, rejected when it is n or more.
  const t = Dice.stream('b', 'below');
  let i = 0, v;
  do { v = t.word(i++) >>> 29; } while (v >= 6);
  assert.equal(t.below(6), v);
  assert.equal(t.cursor, i);
  for (let n = 1; n <= 70; n++) for (let k = 0; k < 20; k++) { const x = t.below(n); assert.ok(x >= 0 && x < n && Number.isInteger(x)); }
});

test('between covers its bounds, accepts a range of exactly 2^53 and rejects 2^53 + 1', () => {
  const s = Dice.stream('b', 'between');
  const seen = new Set();
  for (let i = 0; i < 300; i++) { const v = s.between(-3, 3); assert.ok(v >= -3 && v <= 3 && Number.isInteger(v)); seen.add(v); }
  assert.equal(seen.size, 7, 'every value from -3 to 3 appears in 300 draws');
  assert.equal(s.between(7, 7), 7);
  const before = s.cursor;
  assert.equal(s.between(7, 7), 7);
  assert.equal(s.cursor, before, 'a single-value range takes nothing');
  const t = Dice.stream('b', 'between');
  const v = t.between(0, TWO_53 - 1);
  assert.ok(Number.isSafeInteger(v) && v >= 0);
  assert.equal(t.cursor, 2);
  const u = t.between(-(TWO_53 - 1), 0);
  assert.ok(Number.isSafeInteger(u) && u <= 0 && u >= -(TWO_53 - 1));
  assert.throws(() => t.between(-1, TWO_53 - 1), /smaller than 2\^53/);
  assert.throws(() => t.between(-(TWO_53 - 1), 1), /smaller than 2\^53/);
  assert.throws(() => t.between(2, 1), /must not exceed/);
  assert.throws(() => t.between(0, TWO_53), /integer/);
  assert.throws(() => t.between(0.5, 3), /integer/);
  assert.throws(() => t.between(0, '3'), /integer/);
  // between is lo + below(hi - lo + 1), word for word.
  const x = Dice.stream('b', 'formula'), y = Dice.stream('b', 'formula');
  for (let i = 0; i < 50; i++) assert.equal(x.between(10, 25), 10 + y.below(16));
});

test('choice returns an item of the sequence by below(length)', () => {
  const s = Dice.stream('c', 'choice'), t = Dice.stream('c', 'choice');
  const items = ['one', 'two', 'three', 'four', 'five'];
  for (let i = 0; i < 100; i++) assert.equal(s.choice(items), items[t.below(5)]);
  assert.equal(s.choice(['only']), 'only');
  const before = s.cursor;
  s.choice(['only']);
  assert.equal(s.cursor, before, 'a single item takes nothing');
  assert.throws(() => s.choice([]), /at least one/);
  assert.throws(() => s.choice('abc'), /array/);
});

test('shuffle returns a new array that is a permutation, and 0 or 1 items take nothing', () => {
  const s = Dice.stream('s', 'shuffle');
  const items = range(40);
  const out = s.shuffle(items);
  assert.notEqual(out, items, 'a new array');
  assert.deepEqual(plain(items), range(40), 'the input is untouched');
  assert.deepEqual(plain(out).slice().sort((a, b) => a - b), range(40));
  assert.notDeepEqual(plain(out), range(40), 'a 40-item shuffle is not the identity');
  const before = s.cursor;
  assert.deepEqual(plain(s.shuffle([])), []);
  assert.deepEqual(plain(s.shuffle(['x'])), ['x']);
  assert.equal(s.cursor, before);
  // Fisher-Yates from the top, step by step, with the same words.
  const a = Dice.stream('s', 'steps'), b = Dice.stream('s', 'steps');
  const got = a.shuffle(range(10));
  const want = range(10);
  for (let i = 9; i >= 1; i--) { const j = b.below(i + 1); [want[i], want[j]] = [want[j], want[i]]; }
  assert.deepEqual(plain(got), want);
  assert.throws(() => s.shuffle('abc'), /array/);
});

test('sample gives k distinct positions, with k = 0 and k = length allowed', () => {
  const s = Dice.stream('s', 'sample');
  const items = range(30);
  const out = s.sample(items, 10);
  assert.equal(out.length, 10);
  assert.equal(new Set(out).size, 10);
  assert.ok(out.every((v) => v >= 0 && v < 30));
  assert.deepEqual(plain(items), range(30), 'the input is untouched');
  const before = s.cursor;
  assert.deepEqual(plain(s.sample(items, 0)), []);
  assert.equal(s.cursor, before, 'k = 0 takes nothing');
  const all = s.sample(items, 30);
  assert.deepEqual(plain(all).slice().sort((a, b) => a - b), range(30), 'k = length is a permutation');
  // The partial Fisher-Yates from the front, step by step.
  const a = Dice.stream('s', 'steps'), b = Dice.stream('s', 'steps');
  const got = a.sample(range(12), 5);
  const copy = range(12);
  for (let i = 0; i < 5; i++) { const j = i + b.below(12 - i); [copy[i], copy[j]] = [copy[j], copy[i]]; }
  assert.deepEqual(plain(got), copy.slice(0, 5));
  assert.throws(() => s.sample(items, 31), /0 to 30/);
  assert.throws(() => s.sample(items, -1), /0 to 30/);
  assert.throws(() => s.sample(items, 1.5), /integer/);
});

test('weighted never returns a zero-weight item, follows the running sum, and rejects bad weights', () => {
  const s = Dice.stream('w', 'weighted');
  const items = ['never', 'light', 'heavy', 'none'];
  const counts = {never: 0, light: 0, heavy: 0, none: 0};
  for (let i = 0; i < 3000; i++) counts[s.weighted(items, [0, 1, 3, 0])]++;
  assert.equal(counts.never, 0);
  assert.equal(counts.none, 0);
  assert.ok(counts.heavy > counts.light * 2 && counts.heavy < counts.light * 4, 'heavy is about three times light: ' + JSON.stringify(counts));
  assert.equal(s.cursor, 6000, 'two words per draw');
  // The walk, by hand: x = uniform * total, first running sum above x.
  const a = Dice.stream('w', 'walk'), b = Dice.stream('w', 'walk');
  for (let i = 0; i < 200; i++) {
    const x = b.uniform() * 6;
    const want = x < 1 ? 'a' : x < 3 ? 'b' : 'c';
    assert.equal(a.weighted(['a', 'b', 'c'], [1, 2, 3]), want);
  }
  assert.equal(s.weighted(['only'], [2]), 'only');
  assert.throws(() => s.weighted(['a', 'b'], [1]), /one weight per item/);
  assert.throws(() => s.weighted(['a', 'b'], [0, 0]), /more than zero/);
  assert.throws(() => s.weighted(['a', 'b'], [1, -1]), /not negative/);
  assert.throws(() => s.weighted(['a', 'b'], [1, Infinity]), /finite/);
  assert.throws(() => s.weighted(['a', 'b'], [1, NaN]), /finite/);
  assert.throws(() => s.weighted(['a', 'b'], [1, '1']), /finite/);
  assert.throws(() => s.weighted([], []), /at least one/);
});

test('coin is uniform() < p, with the frequency near p and the defaults and limits right', () => {
  const s = Dice.stream('c', 'coin'), t = Dice.stream('c', 'coin');
  let heads = 0;
  for (let i = 0; i < 10000; i++) { const c = s.coin(0.3); assert.equal(typeof c, 'boolean'); assert.equal(c, t.uniform() < 0.3); if (c) heads++; }
  assert.ok(heads > 2700 && heads < 3300, 'about 3000 heads in 10000 at p = 0.3, got ' + heads);
  const u = Dice.stream('c', 'default'), v = Dice.stream('c', 'default');
  let fair = 0;
  for (let i = 0; i < 10000; i++) { const c = u.coin(); assert.equal(c, v.coin(0.5)); if (c) fair++; }
  assert.ok(fair > 4700 && fair < 5300, 'about half at the default p, got ' + fair);
  for (let i = 0; i < 50; i++) { assert.equal(s.coin(0), false); assert.equal(s.coin(1), true); }
  assert.throws(() => s.coin(-0.1), /0 to 1/);
  assert.throws(() => s.coin(1.1), /0 to 1/);
  assert.throws(() => s.coin(NaN), /0 to 1/);
  assert.throws(() => s.coin('0.5'), /0 to 1/);
});

test('normal has mean near 0 and variance near 1 over thousands of draws, four words each', () => {
  const s = Dice.stream('n', 'normal');
  const n = 20000;
  let sum = 0, squares = 0;
  for (let i = 0; i < n; i++) { const z = s.normal(); assert.ok(Number.isFinite(z)); sum += z; squares += z * z; }
  assert.equal(s.cursor, 4 * n);
  const mean = sum / n, variance = squares / n - mean * mean;
  assert.ok(Math.abs(mean) < 0.05, 'mean ' + mean);
  assert.ok(Math.abs(variance - 1) < 0.05, 'variance ' + variance);
  // The Box-Muller formula from the spec, within the tolerance the spec gives for normals.
  const a = Dice.stream('n', 'formula'), b = Dice.stream('n', 'formula');
  for (let i = 0; i < 100; i++) {
    const u = b.uniform(), v = b.uniform();
    assert.ok(Math.abs(a.normal() - Math.sqrt(-2 * Math.log(1 - u)) * Math.cos(2 * Math.PI * v)) < 1e-9);
  }
});

test('hex is 8 lowercase digits per word, n words, with the limits 1 to 64', () => {
  const s = Dice.stream('h', 'hex'), t = Dice.stream('h', 'hex');
  for (const n of [1, 2, 4, 17, 64]) {
    const out = s.hex(n);
    assert.equal(out.length, 8 * n);
    assert.match(out, /^[0-9a-f]+$/);
    let want = '';
    for (let i = 0; i < n; i++) want += t.take().toString(16).padStart(8, '0');
    assert.equal(out, want);
  }
  assert.throws(() => s.hex(0), /1 to 64/);
  assert.throws(() => s.hex(65), /1 to 64/);
  assert.throws(() => s.hex(2.5), /integer/);
  assert.throws(() => s.hex(), /required/);
});

test('name is adjective-noun-number from the lists, three draws in order', () => {
  const s = Dice.stream('n', 'name'), t = Dice.stream('n', 'name');
  for (let i = 0; i < 300; i++) {
    const name = s.name();
    const m = name.match(/^([a-z]+)-([a-z]+)-([1-9][0-9]?)$/);
    assert.ok(m, name);
    assert.ok(Dice.ADJECTIVES.includes(m[1]), m[1]);
    assert.ok(Dice.NOUNS.includes(m[2]), m[2]);
    const number = Number(m[3]);
    assert.ok(number >= 1 && number <= 99);
    assert.equal(name, t.choice(Dice.ADJECTIVES) + '-' + t.choice(Dice.NOUNS) + '-' + t.between(1, 99));
  }
});

test('suggest draws subject, a different partner, operation and constraint and composes the invitation exactly', () => {
  const pool = ['alpha', 'beta', 'gamma', 'delta', 'epsilon'];
  const s = Dice.stream('s', 'suggest'), t = Dice.stream('s', 'suggest');
  for (let i = 0; i < 200; i++) {
    const r = s.suggest(pool);
    assert.deepEqual(Object.keys(r), ['subject', 'partner', 'operation', 'constraint', 'invitation', 'choices']);
    assert.ok(pool.includes(r.subject) && pool.includes(r.partner));
    assert.notEqual(r.subject, r.partner);
    assert.ok(Dice.OPERATIONS.includes(r.operation));
    assert.ok(Dice.CONSTRAINTS.includes(r.constraint));
    assert.equal(r.invitation, r.operation + ' Subject: ' + r.subject + '. Partner: ' + r.partner + '. ' + r.constraint);
    assert.deepEqual(plain(r.choices), ['accept', 'reinterpret', 'decline']);
    // The draws, by hand: s, t (shifted past s), operation, constraint.
    const a = t.below(5); let b = t.below(4); if (b >= a) b++;
    assert.equal(r.subject, pool[a]); assert.equal(r.partner, pool[b]);
    assert.equal(r.operation, t.choice(Dice.OPERATIONS)); assert.equal(r.constraint, t.choice(Dice.CONSTRAINTS));
  }
  // Two items: subject and partner are always the two of them, in some order.
  for (let i = 0; i < 50; i++) { const r = s.suggest(['x', 'y']); assert.deepEqual([r.subject, r.partner].sort(), ['x', 'y']); }
  assert.throws(() => s.suggest(['one']), /2 to 1000/);
  assert.throws(() => s.suggest(['same', 'same']), /distinct/);
  assert.throws(() => s.suggest(['a', 2]), /string/);
  assert.throws(() => s.suggest('ab'), /array/);
});

test('streams are independent of each other, of the seed, and of what else was drawn', () => {
  const a = Dice.stream('seed', 'one'), b = Dice.stream('seed', 'two'), c = Dice.stream('other', 'one');
  const firstA = range(16).map((i) => a.word(i)), firstB = range(16).map((i) => b.word(i)), firstC = range(16).map((i) => c.word(i));
  assert.notDeepEqual(firstA, firstB, 'different stream names');
  assert.notDeepEqual(firstA, firstC, 'different seeds');
  // Drawing on one stream leaves another untouched; a fresh stream of the same name repeats.
  const x = Dice.stream('seed', 'one');
  for (let i = 0; i < 100; i++) b.uniform();
  assert.deepEqual(range(16).map(() => x.take()), firstA);
  assert.deepEqual(range(16).map(() => Dice.stream('seed', 'one').word(0)), Array(16).fill(firstA[0]));
  // Seeds and stream names are length-prefixed, so moving a character across the boundary
  // ("ab" + "c" against "a" + "bc") changes the key.
  assert.notEqual(Dice.stream('ab', 'c').word(0), Dice.stream('a', 'bc').word(0));
});

test('word(i) equals the i-th sequential take, across block boundaries, and does not move the cursor', () => {
  const s = Dice.stream('w', 'words'), t = Dice.stream('w', 'words');
  const taken = range(100).map(() => s.take());
  assert.equal(s.cursor, 100);
  for (let i = 0; i < 100; i++) assert.equal(t.word(i), taken[i]);
  assert.equal(t.cursor, 0);
  for (let i = 99; i >= 0; i--) assert.equal(s.word(i), taken[i], 'random access backwards');
  assert.equal(s.cursor, 100);
  assert.equal(s.word(1000000), s.word(1000000));
  for (const w of taken) assert.ok(Number.isInteger(w) && w >= 0 && w < TWO_32);
  assert.throws(() => s.word(-1), /non-negative/);
  assert.throws(() => s.word(1.5), /non-negative integer/);
});

test('words are unsigned, independent of each other, and take one SHA-256 block per eight', () => {
  const s = Dice.stream('seed with spaces and ünïcödé', 'stream/1');
  const words = range(64).map(() => s.take());
  assert.ok(words.some((w) => w > 2 ** 31), 'some word has the top bit set and is still positive');
  assert.equal(new Set(words).size, 64);
  // A direct recomputation of block 3 from the spec's byte layout through node:crypto.
  const lp = (text) => { const b = Buffer.from(text, 'utf8'); const l = Buffer.alloc(4); l.writeUInt32BE(b.length); return Buffer.concat([l, b]); };
  const counter = Buffer.alloc(8); counter.writeBigUInt64BE(3n);
  const digest = crypto.createHash('sha256').update(Buffer.concat([lp('dice/1'), lp('seed with spaces and ünïcödé'), lp('stream/1'), counter])).digest();
  for (let i = 0; i < 8; i++) assert.equal(words[24 + i], digest.readUInt32BE(i * 4));
});

test('run produces the normalised request and result for every kind, and replays to the same record', () => {
  const pool = [' one ', 'two', 'three ', 'four'];
  const cases = [
    ['words', {count: 3}, {count: 3}],
    ['uniform', {count: 2}, {count: 2}],
    ['integer', {count: 4, min: -2, max: 2}, {count: 4, min: -2, max: 2}],
    ['normal', {count: 2}, {count: 2}],
    ['coin', {count: 5, p: 0.25}, {count: 5, p: 0.25}],
    ['hex', {words: 3}, {words: 3}],
    ['name', {count: 2}, {count: 2}],
    ['pick', {pool, count: 5}, {pool: ['one', 'two', 'three', 'four'], count: 5}],
    ['shuffle', {pool}, {pool: ['one', 'two', 'three', 'four']}],
    ['sample', {pool, k: 2}, {pool: ['one', 'two', 'three', 'four'], k: 2}],
    ['weighted', {pool, weights: [1, 2, 0, 1], count: 4}, {pool: ['one', 'two', 'three', 'four'], weights: [1, 2, 0, 1], count: 4}],
    ['suggest', {pool}, {pool: ['one', 'two', 'three', 'four']}],
  ];
  for (const [kind, params, normalised] of cases) {
    const record = run(kind, params, 'r', 'stream-' + kind);
    assert.deepEqual(Object.keys(record), ['request', 'result']);
    assert.deepEqual(plain(record.request), {version: 'dice/1', seed: 'r', stream: 'stream-' + kind, kind, params: normalised}, kind);
    assert.deepEqual(Object.keys(record.request), ['version', 'seed', 'stream', 'kind', 'params'], kind + ' request keys in order');
    assert.deepEqual(Object.keys(record.request.params), plain(Dice.PARAMS[kind]), kind + ' params in the table order');
    // The same request with its params in another order normalises to the table order.
    const reversed = Object.fromEntries(Object.entries(params).reverse());
    assert.equal(JSON.stringify(Dice.run(request(kind, reversed, 'r', 'stream-' + kind))), JSON.stringify(record), kind + ' params order');
    assert.deepEqual(Dice.run(record.request), record, kind + ' replays');
    assert.equal(JSON.stringify(Dice.run(JSON.parse(JSON.stringify(record)).request)), JSON.stringify(record), kind + ' replays from JSON');
  }
  // The results have the shape and the draws the table promises.
  const s = (kind, params) => Dice.stream('r', 'stream-' + kind);
  const words = run('words', {count: 3}, 'r', 'stream-words');
  assert.deepEqual(plain(words.result), [s('words').word(0), s('words').word(1), s('words').word(2)]);
  assert.deepEqual(plain(run('integer', {count: 1000, min: 1, max: 6}, 'd').result.filter((v) => v < 1 || v > 6)), []);
  assert.equal(run('hex', {words: 3}, 'r').result.length, 24);
  assert.equal(run('name', {count: 2}, 'r').result.length, 2);
  assert.ok(run('pick', {pool, count: 5}, 'r').result.every((item) => ['one', 'two', 'three', 'four'].includes(item)));
  assert.deepEqual(plain(run('shuffle', {pool}, 'r').result).sort(), ['four', 'one', 'three', 'two']);
  assert.equal(new Set(run('sample', {pool, k: 2}, 'r').result).size, 2);
  assert.ok(run('weighted', {pool, weights: [1, 2, 0, 1], count: 200}, 'r').result.every((item) => item !== 'three'));
  assert.ok(run('coin', {count: 5, p: 0.25}, 'r').result.every((v) => typeof v === 'boolean'));
  const sg = run('suggest', {pool}, 'r').result;
  assert.equal(sg.invitation, sg.operation + ' Subject: ' + sg.subject + '. Partner: ' + sg.partner + '. ' + sg.constraint);
  // A record's result is what the same calls on a fresh stream give.
  const t = Dice.stream('r', 'stream-uniform');
  assert.deepEqual(plain(run('uniform', {count: 2}, 'r', 'stream-uniform').result), [t.uniform(), t.uniform()]);
  // The stream is the request's stream, which defaults to nothing: it must be given.
  assert.throws(() => Dice.run({version: 'dice/1', seed: 'r', kind: 'words', params: {count: 1}}), /stream name/);
});

test('run rejects every invalid input in the spec limits, and accepts the edges', () => {
  const good = request('integer', {count: 3, min: 1, max: 6});
  const bad = (change, pattern) => assert.throws(() => Dice.run(change), pattern);
  bad(null, /object/);
  bad([], /object/);
  bad({...good, version: 'dice/2'}, /version/);
  bad({...good, version: undefined}, /version/);
  bad({...good, seed: ''}, /1 to 1000/);
  bad({...good, seed: 'x'.repeat(1001)}, /1 to 1000/);
  bad({...good, seed: 'a\ud800b'}, /lone surrogate/);
  bad({...good, seed: '\udc00'}, /lone surrogate/);
  bad({...good, seed: 7}, /string/);
  bad({...good, stream: ''}, /1 to 1000/);
  bad({...good, stream: 'x'.repeat(1001)}, /1 to 1000/);
  bad({...good, stream: 'bad\udfff'}, /lone surrogate/);
  bad({...good, kind: 'dice'}, /Unknown kind/);
  bad({...good, params: null}, /object/);
  bad({...good, params: []}, /object/);
  // A key the request or its params does not take is an error that names the key.
  bad({...good, extra: 1}, /: The request does not take the key "extra"\.$/);
  bad({...good, result: [1, 2, 3]}, /does not take the key "result"/);
  bad({...good, Seed: 'x'}, /does not take the key "Seed"/);
  bad(request('integer', {count: 3, min: 1, max: 6, bonus: 1}), /: The parameters for integer do not take the key "bonus"\.$/);
  bad(request('words', {count: 3, min: 1}), /parameters for words do not take the key "min"/);
  bad(request('hex', {words: 4, count: 6}), /do not take the key "count"/);
  bad(request('suggest', {pool: ['a', 'b'], k: 1}), /do not take the key "k"/);
  bad(request('coin', {count: 3, p: 0.5, P: 0.5}), /do not take the key "P"/);
  bad(request('integer', {min: 1, max: 6}), /count is required/);
  bad(request('integer', {count: 0, min: 1, max: 6}), /1 to 1000/);
  bad(request('integer', {count: 1001, min: 1, max: 6}), /1 to 1000/);
  bad(request('integer', {count: 1.5, min: 1, max: 6}), /integer/);
  bad(request('integer', {count: '3', min: 1, max: 6}), /integer/);
  bad(request('integer', {count: 3, min: 7, max: 6}), /must not exceed/);
  bad(request('integer', {count: 3, min: 1.5, max: 6}), /integer/);
  bad(request('integer', {count: 3, min: 1}), /max is required/);
  bad(request('integer', {count: 3, min: -1, max: TWO_53 - 1}), /smaller than 2\^53/);
  bad(request('integer', {count: 3, min: 0, max: TWO_53}), /integer/);
  bad(request('integer', {count: 3, min: -TWO_53, max: 0}), /integer/);
  bad(request('hex', {words: 0}), /1 to 64/);
  bad(request('hex', {words: 65}), /1 to 64/);
  bad(request('hex', {}), /words is required/);
  bad(request('coin', {count: 3, p: -0.01}), /0 to 1/);
  bad(request('coin', {count: 3, p: 1.01}), /0 to 1/);
  bad(request('coin', {count: 3, p: NaN}), /0 to 1/);
  bad(request('coin', {count: 3, p: '0.5'}), /0 to 1/);
  bad(request('coin', {count: 3}), /p is required/);
  bad(request('pick', {pool: [], count: 1}), /1 to 1000 items/);
  bad(request('pick', {pool: range(1001).map(String), count: 1}), /1 to 1000 items/);
  bad(request('pick', {pool: 'a\nb', count: 1}), /array/);
  bad(request('pick', {pool: ['a', 2], count: 1}), /string/);
  bad(request('pick', {pool: ['a', '   '], count: 1}), /1 to 300 characters/);
  bad(request('pick', {pool: ['a', 'x'.repeat(301)], count: 1}), /1 to 300 characters/);
  bad(request('pick', {count: 1}), /pool is required/);
  bad(request('sample', {pool: ['a', 'b'], k: 3}), /0 to 2/);
  bad(request('sample', {pool: ['a', 'b'], k: -1}), /0 to 2/);
  bad(request('sample', {pool: ['a', 'b'], k: 0.5}), /integer/);
  bad(request('sample', {pool: ['a', 'b']}), /k is required/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [1], count: 1}), /one number per pool item/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [0, 0], count: 1}), /more than zero/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [1, -1], count: 1}), /not negative/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [1, Infinity], count: 1}), /finite/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [1, '1'], count: 1}), /finite/);
  bad(request('weighted', {pool: ['a', 'b'], weights: '1,1', count: 1}), /one number per pool item/);
  bad(request('weighted', {pool: ['a', 'b'], count: 1}), /weights is required/);
  bad(request('suggest', {pool: ['only']}), /2 to 1000 items/);
  bad(request('suggest', {pool: ['same', 'same']}), /distinct/);
  bad(request('suggest', {pool: ['same', ' same ']}), /distinct/);
  // The edges that are allowed.
  assert.equal(Dice.run({...good, seed: 'x'.repeat(1000)}).result.length, 3);
  assert.equal(Dice.run({...good, seed: '\u{1F3B2}'}).result.length, 3, 'one astral code point is a seed of length 1');
  assert.equal(Dice.run({...good, stream: 'y'.repeat(1000)}).result.length, 3);
  assert.equal(run('integer', {count: 1000, min: 1, max: 6}).result.length, 1000);
  assert.equal(run('integer', {count: 1, min: 0, max: TWO_53 - 1}).result.length, 1);
  assert.equal(run('integer', {count: 1, min: -(TWO_53 - 1), max: 0}).result.length, 1);
  assert.equal(run('integer', {count: 1, min: 4, max: 4}).result[0], 4);
  assert.equal(run('hex', {words: 64}).result.length, 512);
  assert.deepEqual(plain(run('pick', {pool: ['x'.repeat(300)], count: 1}).request.params.pool), ['x'.repeat(300)]);
  assert.equal(run('pick', {pool: [' ' + '\u{1F3B2}'.repeat(300) + ' '], count: 1}).request.params.pool[0].length, 600, '300 astral code points pass the 300-character limit');
  assert.equal(run('sample', {pool: ['a', 'b'], k: 0}).result.length, 0);
  assert.equal(run('sample', {pool: ['a', 'b'], k: 2}).result.length, 2);
  assert.equal(run('coin', {count: 1, p: 0}).result[0], false);
  assert.equal(run('coin', {count: 1, p: 1}).result[0], true);
  assert.equal(run('suggest', {pool: ['a', 'b']}).result.choices.length, 3);
  // A JSON 3.0 is the number 3 once parsed: it passes as an integer and is recorded as 3. Strings
  // and booleans are never numbers.
  const fromJSON = Dice.run(JSON.parse('{"version":"dice/1","seed":"j","stream":"words","kind":"words","params":{"count":3.0}}'));
  assert.equal(JSON.stringify(fromJSON.request.params), '{"count":3}');
  assert.equal(JSON.stringify(fromJSON), JSON.stringify(run('words', {count: 3}, 'j')));
  assert.equal(JSON.stringify(Dice.run(JSON.parse('{"version":"dice/1","seed":"j","stream":"integer","kind":"integer","params":{"count":2.0,"min":-1.0,"max":6.0}}')).request.params), '{"count":2,"min":-1,"max":6}');
  bad(request('integer', {count: true, min: 1, max: 6}), /integer/);
  bad(request('integer', {count: 3, min: '1', max: 6}), /integer/);
  bad(request('integer', {count: 3, min: 1, max: false}), /integer/);
  bad(request('coin', {count: 3, p: true}), /0 to 1/);
  bad(request('sample', {pool: ['a', 'b'], k: '1'}), /integer/);
  bad(request('weighted', {pool: ['a', 'b'], weights: [1, true], count: 1}), /finite/);
});

test('trimming removes exactly the spec set, and the limits count code points', () => {
  // The set, from the spec's "Text rules": U+0009 to U+000D, U+0020, U+00A0, U+1680, U+2000 to
  // U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 and U+FEFF.
  const trimmed = [0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0xA0, 0x1680, ...range(11).map((i) => 0x2000 + i), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000, 0xFEFF];
  // Neighbours that are not in the set, and that Python's str.strip() would remove or keep differently.
  const kept = [0x1C, 0x1D, 0x1E, 0x1F, 0x85, 0x180E, 0x200B, 0x2060, 0xFFFE];
  const pick = (pool) => plain(run('pick', {pool, count: 1}).request.params.pool);
  for (const c of trimmed) {
    const ch = String.fromCodePoint(c);
    assert.deepEqual(pick([ch + 'x' + ch, ch + ch + 'y']), ['x', 'y'], 'U+' + c.toString(16) + ' is trimmed');
    assert.throws(() => run('pick', {pool: [ch], count: 1}), /1 to 300 characters/, 'U+' + c.toString(16) + ' alone is blank');
  }
  for (const c of kept) {
    const ch = String.fromCodePoint(c);
    assert.deepEqual(pick([ch + 'x' + ch, ch]), [ch + 'x' + ch, ch], 'U+' + c.toString(16) + ' is kept');
  }
  const all = trimmed.map((c) => String.fromCodePoint(c)).join('');
  assert.deepEqual(pick([all + 'both ends' + all, all + '\u001Cinside\u001C' + all]), ['both ends', '\u001Cinside\u001C']);
  assert.deepEqual(pick(['\uFEFFa\u3000', '\u001Cb\u0085']), ['a', '\u001Cb\u0085']);
  // Interior characters from the set stay; only the ends are trimmed.
  assert.deepEqual(pick([' a b ', '\ta\u00A0b\n']), ['a b', 'a\u00A0b']);
  // The 300-character limit counts code points: 300 astral characters pass, 301 do not, and a
  // seed or stream of 1000 astral characters passes while 1001 do not.
  const die = '\u{1F3B2}';
  assert.equal(pick([die.repeat(300)])[0].length, 600);
  assert.throws(() => run('pick', {pool: [die.repeat(301)], count: 1}), /1 to 300 characters/);
  assert.equal(Dice.run(request('words', {count: 1}, die.repeat(1000), die.repeat(1000))).result.length, 1);
  assert.throws(() => Dice.run(request('words', {count: 1}, die.repeat(1001))), /1 to 1000/);
  assert.throws(() => Dice.run(request('words', {count: 1}, 'x', die.repeat(1001))), /1 to 1000/);
  // A seed is not trimmed: " a" and "a" are different seeds.
  assert.notEqual(Dice.stream(' a', 'b').word(0), Dice.stream('a', 'b').word(0));
});

test('every record in tests/dice_fixtures.json is reproduced by Dice.run, request and result', () => {
  const fixtures = JSON.parse(fs.readFileSync(FIXTURES, 'utf8'));
  assert.equal(fixtures.version, 'dice/1');
  assert.ok(Array.isArray(fixtures.records) && fixtures.records.length >= 12, 'at least one record per kind');
  const kinds = new Set();
  for (const [i, record] of fixtures.records.entries()) {
    const where = 'record ' + i + ' (' + record.request.kind + ', seed ' + JSON.stringify(record.request.seed).slice(0, 30) + ')';
    assert.deepEqual(Object.keys(record), ['request', 'result'], where);
    const got = Dice.run(record.request);
    assert.deepEqual(Object.keys(got), ['request', 'result'], where);
    // The normalised request must come back exactly, keys in order, including the trimmed pool.
    assertSameJSON(got.request, record.request, where + ' request');
    // Normals to 1e-9 absolute, as the spec allows for ln and cos; everything else exactly.
    assertSameJSON(got.result, record.result, where + ' result', record.request.kind === 'normal' ? 1e-9 : 0);
    // And the record's own request replays to the same record.
    assertSameJSON(Dice.run(got.request), plain(got), where + ' replay', record.request.kind === 'normal' ? 1e-9 : 0);
    kinds.add(record.request.kind);
  }
  assert.deepEqual([...kinds].sort(), [...Dice.KINDS].sort(), 'the fixtures cover every kind');
});

test('6000 rolls of a d6 land each face between 800 and 1200 times', () => {
  const counts = [0, 0, 0, 0, 0, 0, 0];
  for (const roll of run('integer', {count: 1000, min: 1, max: 6}, 'd6', 'rolls').result) counts[roll]++;
  const s = Dice.stream('d6', 'more');
  for (let i = 0; i < 5000; i++) counts[s.between(1, 6)]++;
  assert.equal(counts[0], 0);
  for (let face = 1; face <= 6; face++) assert.ok(counts[face] >= 800 && counts[face] <= 1200, 'face ' + face + ': ' + counts[face]);
  assert.equal(counts.reduce((a, b) => a + b, 0), 6000);
});

test('Dice.checks() runs the spec list and every check passes', () => {
  const results = Dice.checks();
  assert.ok(results.length >= 12);
  const names = results.map((c) => c.name).join('\n');
  for (const word of ['empty', 'abc', 'anchor', 'uniform', 'below(1)', '2^32', '2^32 + 1', '2^53', 'shuffle', 'sample', 'quiet-hour-15', 'replay']) {
    assert.ok(names.includes(word), 'a check mentions ' + word);
  }
  for (const c of results) {
    assert.deepEqual(Object.keys(c), ['name', 'ok', 'detail']);
    assert.equal(typeof c.detail, 'string');
    assert.ok(c.ok, c.name + ': ' + c.detail);
  }
});

// The command line, in a child process, exactly as a session would run it.
const cli = (args, input) => spawnSync(process.execPath, [CLI, ...args], {encoding: 'utf8', input});
const madeListing = () => fs.readdirSync(MADE).filter((n) => n !== 'README.md' && !n.startsWith('.'))
  .filter((n) => fs.statSync(path.join(MADE, n)).isFile()).sort();

test('CLI: the JSON record equals Dice.run for several kinds, with the command line defaults', () => {
  const cases = [
    [['words', 'quiet-hour-15'], request('words', {count: 6}, 'quiet-hour-15')],
    [['uniform', 'quiet-hour-15', '3'], request('uniform', {count: 3}, 'quiet-hour-15')],
    [['integer', 'quiet-hour-15', '1', '6', '10'], request('integer', {count: 10, min: 1, max: 6}, 'quiet-hour-15')],
    [['integer', 'quiet-hour-15', '-5', '5'], request('integer', {count: 6, min: -5, max: 5}, 'quiet-hour-15')],
    [['normal', 'quiet-hour-15', '2'], request('normal', {count: 2}, 'quiet-hour-15')],
    [['coin', 'quiet-hour-15'], request('coin', {count: 6, p: 0.5}, 'quiet-hour-15')],
    [['coin', 'quiet-hour-15', '4', '0.3'], request('coin', {count: 4, p: 0.3}, 'quiet-hour-15')],
    [['hex', 'quiet-hour-15'], request('hex', {words: 4}, 'quiet-hour-15')],
    [['hex', 'quiet-hour-15', '8'], request('hex', {words: 8}, 'quiet-hour-15')],
    [['name', 'quiet-hour-15'], request('name', {count: 6}, 'quiet-hour-15')],
    [['name', '336489', '1'], request('name', {count: 1}, '336489')],
  ];
  for (const [args, req] of cases) {
    const result = cli(args);
    assert.equal(result.status, 0, args.join(' ') + ': ' + result.stderr);
    assert.equal(result.stderr, '');
    assert.deepEqual(JSON.parse(result.stdout), plain(Dice.run(req)), args.join(' '));
    assert.equal(result.stdout, JSON.stringify(Dice.run(req), null, 2) + '\n', 'two-space JSON');
  }
  assert.deepEqual(JSON.parse(cli(['name', '336489', '1']).stdout).result, ['quiet-hour-15']);
});

test('CLI: --plain prints one value per line and --stream names the stream, anywhere on the line', () => {
  const ints = cli(['integer', 'quiet-hour-15', '1', '6', '10', '--plain']);
  assert.equal(ints.status, 0);
  assert.deepEqual(ints.stdout.split('\n'), [...Dice.run(request('integer', {count: 10, min: 1, max: 6}, 'quiet-hour-15')).result.map(String), '']);
  const floats = cli(['--plain', 'uniform', 'quiet-hour-15', '3']);
  assert.deepEqual(floats.stdout.split('\n'), [...Dice.run(request('uniform', {count: 3}, 'quiet-hour-15')).result.map(String), '']);
  assert.ok(floats.stdout.split('\n').slice(0, 3).every((line) => Number(line) >= 0 && Number(line) < 1));
  const one = cli(['hex', 'quiet-hour-15', '--plain']);
  assert.equal(one.stdout, Dice.run(request('hex', {words: 4}, 'quiet-hour-15')).result + '\n');
  const bools = cli(['coin', 'quiet-hour-15', '3', '--plain']);
  assert.ok(bools.stdout.split('\n').slice(0, 3).every((line) => line === 'true' || line === 'false'));
  assert.deepEqual(bools.stdout.split('\n'), [...Dice.run(request('coin', {count: 3, p: 0.5}, 'quiet-hour-15')).result.map((v) => JSON.stringify(v)), '']);
  // Numbers print as this language's JSON writes them, so the lines parse back to the same doubles.
  assert.deepEqual(floats.stdout.trim().split('\n').map(JSON.parse), plain(Dice.run(request('uniform', {count: 3}, 'quiet-hour-15')).result));
  assert.deepEqual(floats.stdout.trim().split('\n'), plain(Dice.run(request('uniform', {count: 3}, 'quiet-hour-15')).result).map((v) => JSON.stringify(v)));
  const named = cli(['uniform', '--stream', 'field', 'quiet-hour-15', '2']);
  assert.equal(named.status, 0);
  const record = JSON.parse(named.stdout);
  assert.equal(record.request.stream, 'field');
  assert.deepEqual(record, plain(Dice.run(request('uniform', {count: 2}, 'quiet-hour-15', 'field'))));
  assert.notDeepEqual(record.result, JSON.parse(cli(['uniform', 'quiet-hour-15', '2']).stdout).result);
  const second = JSON.parse(cli(['suggest', 'quiet-hour-15', '--stream', 'suggest/1']).stdout);
  assert.equal(second.request.stream, 'suggest/1');
});

test('CLI: bad arguments exit nonzero with an error on stderr and nothing on stdout', () => {
  const bad = [
    ['integer', 'seed', '6', '1'],
    ['integer', 'seed', '1'],
    ['words', 'seed', '1.5'],
    ['words', 'seed', '0'],
    ['words', 'seed', '1001'],
    ['words', 'seed', 'six'],
    ['words', 'seed', '1', '2'],
    ['words', ''],
    ['words'],
    ['hex', 'seed', '65'],
    ['coin', 'seed', '3', '1.5'],
    ['coin', 'seed', '3', 'maybe'],
    ['coin', 'seed', '3', '0x0'],
    ['coin', 'seed', '3', ' 0.5'],
    ['coin', 'seed', '3', ''],
    ['coin', 'seed', '3', 'Infinity'],
    ['coin', 'seed', '3', '1e999'],
    ['coin', 'seed', '0x3'],
    ['coin', 'seed', '3.0'],
    ['nope', 'seed'],
    ['words', 'seed', '--stream'],
    ['words', 'seed', '--verbose'],
    ['sample', 'seed', '1'],
    ['pick', 'seed', path.join(os.tmpdir(), 'dice-no-such-pool-file.txt')],
    ['replay'],
    ['replay', CLI],
    ['replay', '--stream', 'x'],
    ['check', 'extra'],
    ['check', '--plain'],
    ['check', '--stream', 'x'],
    ['check', '--stream', 'check'],
    ['--plain', 'check'],
  ];
  for (const args of bad) {
    const result = cli(args);
    assert.equal(result.status, 1, args.join(' '));
    assert.equal(result.stdout, '', args.join(' ') + ' wrote to stdout');
    assert.ok(result.stderr.trim().length > 0, args.join(' ') + ' said nothing');
  }
  assert.match(cli(['check', '--plain']).stderr, /no flags/);
  assert.match(cli(['coin', 'seed', '3', '0x0']).stderr, /decimal number/);
  // No arguments: the usage, on standard error, exit 1, nothing on standard output.
  const none = cli([]);
  assert.equal(none.status, 1, 'no arguments exits 1');
  assert.equal(none.stdout, '', 'no arguments writes nothing to stdout');
  assert.match(none.stderr, /^Usage:/);
  // --help: the usage, on standard output, exit 0.
  const help = cli(['--help']);
  assert.equal(help.status, 0);
  assert.equal(help.stderr, '');
  assert.match(help.stdout, /^Usage:/);
  assert.match(help.stdout, /suggest\s+SEED \[POOL\]/);
  assert.equal(help.stdout, none.stderr, 'the same usage text both ways');
  // Decimal P and WEIGHTS: digits with an optional fraction and exponent, in either order of the
  // optional parts, and leading "+".
  for (const [p, want] of [['0.25', 0.25], ['.25', 0.25], ['1.', 1], ['+0.5', 0.5], ['5e-1', 0.5], ['2.5E-1', 0.25], ['0', 0], ['1', 1]]) {
    const result = cli(['coin', 'seed', '2', p]);
    assert.equal(result.status, 0, p + ': ' + result.stderr);
    assert.equal(JSON.parse(result.stdout).request.params.p, want, p);
  }
});

test('CLI: check prints the checks and exits 0', () => {
  const result = cli(['check']);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const lines = result.stdout.trim().split('\n');
  assert.ok(lines.length >= 13);
  assert.ok(lines.slice(0, -1).every((line) => line.startsWith('ok   ')));
  assert.ok(!result.stdout.includes('FAIL'));
  assert.match(lines[lines.length - 1], /checks, all ok\./);
});

test('CLI: replay recomputes a saved record, and a bare request, to the same JSON', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dice-test-'));
  try {
    const original = cli(['integer', 'quiet-hour-15', '1', '6', '10', '--stream', 'rolls']);
    assert.equal(original.status, 0);
    const recordFile = path.join(dir, 'record.json');
    fs.writeFileSync(recordFile, original.stdout);
    const replayed = cli(['replay', recordFile]);
    assert.equal(replayed.status, 0, replayed.stderr);
    assert.equal(replayed.stdout, original.stdout);
    assert.equal(replayed.stderr, '', 'an intact record replays without a note');
    const requestFile = path.join(dir, 'request.json');
    fs.writeFileSync(requestFile, JSON.stringify(JSON.parse(original.stdout).request));
    const bare = cli(['replay', requestFile]);
    assert.equal(bare.stdout, original.stdout);
    assert.equal(bare.stderr, '', 'a bare request has no saved result to differ from');
    // A record whose saved result was edited is recomputed, not trusted: the recomputed record is
    // printed, a note goes to standard error, and the exit status is still 0.
    const edited = JSON.parse(original.stdout); edited.result = [9, 9, 9];
    fs.writeFileSync(recordFile, JSON.stringify(edited));
    const tampered = cli(['replay', recordFile]);
    assert.equal(tampered.status, 0, 'a differing saved result still exits 0');
    assert.equal(tampered.stdout, original.stdout);
    assert.match(tampered.stderr, /saved result differs/);
    // The same with --plain: the values, and the note.
    const tamperedPlain = cli(['replay', recordFile, '--plain']);
    assert.equal(tamperedPlain.status, 0);
    assert.deepEqual(tamperedPlain.stdout.split('\n'), [...JSON.parse(original.stdout).result.map(String), '']);
    assert.match(tamperedPlain.stderr, /saved result differs/);
    // The comparison is by value: a saved result that is the same numbers written differently
    // (1.0 for 1, or reformatted whitespace) is not a difference.
    const sameValue = original.stdout.replace(/^(\s+)(\d),?$/gm, (line, space, digit) => line.replace(digit, digit + '.0'));
    assert.notEqual(sameValue, original.stdout, 'the rewrite changed the text');
    fs.writeFileSync(recordFile, sameValue);
    const rewritten = cli(['replay', recordFile]);
    assert.equal(rewritten.status, 0);
    assert.equal(rewritten.stdout, original.stdout);
    assert.equal(rewritten.stderr, '', '1.0 and 1 are the same value, so no note');
    // replay refuses --stream: the record names its own stream.
    fs.writeFileSync(recordFile, original.stdout);
    const streamed = cli(['replay', recordFile, '--stream', 'rolls']);
    assert.equal(streamed.status, 1);
    assert.equal(streamed.stdout, '');
    assert.match(streamed.stderr, /--stream/);
    assert.equal(cli(['--stream', 'other', 'replay', recordFile]).status, 1, '--stream before replay is refused too');
    // A record from another version is refused.
    edited.request.version = 'dice/2';
    fs.writeFileSync(recordFile, JSON.stringify(edited));
    const refused = cli(['replay', recordFile]);
    assert.equal(refused.status, 1);
    assert.equal(refused.stdout, '');
    assert.match(refused.stderr, /version/);
    // A record whose request carries a key it does not take is refused, naming the key.
    const extra = JSON.parse(original.stdout); extra.request.note = 'hello';
    fs.writeFileSync(recordFile, JSON.stringify(extra));
    const extraKey = cli(['replay', recordFile]);
    assert.equal(extraKey.status, 1);
    assert.equal(extraKey.stdout, '');
    assert.match(extraKey.stderr, /does not take the key "note"/);
    // --plain works on a replay as well.
    const plainReplay = cli(['replay', requestFile, '--plain']);
    assert.deepEqual(plainReplay.stdout.split('\n'), [...JSON.parse(original.stdout).result.map(String), '']);
    assert.equal(plainReplay.stderr, '');
  } finally {
    fs.rmSync(dir, {recursive: true, force: true});
  }
});

test('CLI: replay reproduces one fixture record of every kind, written by the other implementation', () => {
  const fixtures = JSON.parse(fs.readFileSync(FIXTURES, 'utf8'));
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dice-fixtures-'));
  try {
    const seen = new Set();
    for (const record of fixtures.records) {
      const kind = record.request.kind;
      if (seen.has(kind)) continue;
      seen.add(kind);
      const file = path.join(dir, kind + '.json');
      fs.writeFileSync(file, JSON.stringify(record));
      const result = cli(['replay', file]);
      assert.equal(result.status, 0, kind + ': ' + result.stderr);
      assertSameJSON(JSON.parse(result.stdout), record, kind, kind === 'normal' ? 1e-9 : 0);
      // Only normals may differ in their last bits between runtimes; everything else is exact, so
      // no note is printed for the other kinds.
      if (kind !== 'normal') assert.equal(result.stderr, '', kind + ' replays without a note');
      // --plain on a replayed suggest fixture: exactly four lines.
      if (kind === 'suggest') {
        const r = record.result;
        assert.equal(cli(['replay', file, '--plain']).stdout, [r.subject, r.partner, r.operation, r.constraint].join('\n') + '\n');
      }
    }
    assert.equal(seen.size, Dice.KINDS.length);
  } finally {
    fs.rmSync(dir, {recursive: true, force: true});
  }
});

test('CLI: suggest with no pool uses the sorted made/ listing without README.md, and a file pool works', () => {
  const result = cli(['suggest', 'c7d70a6 example']);
  assert.equal(result.status, 0, result.stderr);
  const record = JSON.parse(result.stdout);
  const listing = madeListing();
  assert.ok(listing.length >= 2);
  assert.ok(listing.includes('dice.html') && listing.includes('dice.md') && !listing.includes('README.md'));
  assert.deepEqual(record.request.params.pool, listing);
  assert.equal(record.request.stream, 'suggest');
  assert.deepEqual(record, plain(Dice.run(request('suggest', {pool: listing}, 'c7d70a6 example'))));
  assert.ok(listing.includes(record.result.subject) && listing.includes(record.result.partner));
  assert.notEqual(record.result.subject, record.result.partner);
  // --plain on suggest is exactly four lines: subject, partner, operation, constraint.
  const plainOut = cli(['suggest', 'c7d70a6 example', '--plain']);
  assert.equal(plainOut.status, 0);
  const four = plainOut.stdout.split('\n');
  assert.equal(four.length, 5, 'four lines and the final newline');
  assert.deepEqual(four, [record.result.subject, record.result.partner, record.result.operation, record.result.constraint, '']);
  assert.ok(Dice.OPERATIONS.includes(four[2]) && Dice.CONSTRAINTS.includes(four[3]));
  assert.ok(!plainOut.stdout.includes(record.result.invitation), 'the invitation is not among the lines');
  // A pool file: the spec itself, read line by line, trimmed, blanks dropped.
  const spec = path.join(MADE, 'dice.md');
  const lines = fs.readFileSync(spec, 'utf8').split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const fromFile = cli(['pick', 'quiet-hour-15', spec, '3']);
  assert.equal(fromFile.status, 0, fromFile.stderr);
  const picked = JSON.parse(fromFile.stdout);
  assert.deepEqual(picked.request.params.pool, lines);
  assert.deepEqual(picked, plain(Dice.run(request('pick', {pool: lines, count: 3}, 'quiet-hour-15'))));
});

test('CLI: a pool from standard input, for shuffle, sample and weighted', () => {
  const input = 'one\n  two  \n\nthree\r\nfour\n';
  const pool = ['one', 'two', 'three', 'four'];
  const shuffled = cli(['shuffle', 'quiet-hour-15', '-'], input);
  assert.equal(shuffled.status, 0, shuffled.stderr);
  assert.deepEqual(JSON.parse(shuffled.stdout), plain(Dice.run(request('shuffle', {pool}, 'quiet-hour-15'))));
  assert.deepEqual(JSON.parse(shuffled.stdout).result.slice().sort(), pool.slice().sort());
  const sampled = cli(['sample', 'quiet-hour-15', '2', '-'], input);
  assert.equal(sampled.status, 0, sampled.stderr);
  assert.deepEqual(JSON.parse(sampled.stdout), plain(Dice.run(request('sample', {pool, k: 2}, 'quiet-hour-15'))));
  const weighted = cli(['weighted', 'quiet-hour-15', '-', '1,0,2,0.5', '8', '--plain'], input);
  assert.equal(weighted.status, 0, weighted.stderr);
  const lines = weighted.stdout.split('\n');
  assert.equal(lines.length, 9);
  assert.ok(lines.slice(0, 8).every((item) => ['one', 'three', 'four'].includes(item)), 'the zero-weight item never appears');
  assert.deepEqual(lines.slice(0, 8), plain(Dice.run(request('weighted', {pool, weights: [1, 0, 2, 0.5], count: 8}, 'quiet-hour-15')).result));
  const wrongCount = cli(['weighted', 'quiet-hour-15', '-', '1,2'], input);
  assert.notEqual(wrongCount.status, 0);
  assert.equal(wrongCount.stdout, '');
  const badWeight = cli(['weighted', 'quiet-hour-15', '-', '1,x,2,3'], input);
  assert.notEqual(badWeight.status, 0);
  const hexWeight = cli(['weighted', 'quiet-hour-15', '-', '1,0x1,2,3'], input);
  assert.equal(hexWeight.status, 1, 'a hexadecimal weight is not a decimal number');
  assert.equal(hexWeight.stdout, '');
  const spacedWeight = cli(['weighted', 'quiet-hour-15', '-', '1, 2,3,4'], input);
  assert.equal(spacedWeight.status, 1, 'a space inside WEIGHTS is not part of a decimal number');
  const expWeights = cli(['weighted', 'quiet-hour-15', '-', '1e0,.5,2.,+3', '2'], input);
  assert.equal(expWeights.status, 0, expWeights.stderr);
  assert.deepEqual(JSON.parse(expWeights.stdout).request.params.weights, [1, 0.5, 2, 3]);
  const empty = cli(['shuffle', 'quiet-hour-15', '-'], '\n\n');
  assert.notEqual(empty.status, 0, 'an empty pool is an error');
  // The pool loader trims each line with the engine's set and drops the lines that are blank after
  // it: a byte order mark at the start of the input, a line of U+3000, CRLF endings. U+001C and
  // U+0085 are not in the set, so they stay part of their items.
  const odd = '\uFEFFone\r\n\u3000\u00A0\n\u3000two\u3000\r\n\u001Cthree\u0085\n\n';
  const loaded = cli(['shuffle', 'quiet-hour-15', '-'], odd);
  assert.equal(loaded.status, 0, loaded.stderr);
  assert.deepEqual(JSON.parse(loaded.stdout).request.params.pool, ['one', 'two', '\u001Cthree\u0085']);
  assert.deepEqual(JSON.parse(loaded.stdout), plain(Dice.run(request('shuffle', {pool: ['one', 'two', '\u001Cthree\u0085']}, 'quiet-hour-15'))));
  const blankOnly = cli(['shuffle', 'quiet-hour-15', '-'], '\uFEFF\n\u3000\n \t \n');
  assert.equal(blankOnly.status, 1, 'lines that are blank after trimming make an empty pool');
});

test('settled edges: lone surrogates in pool items are refused; pool lines end at CR, LF or CR LF', () => {
  for (const pool of [['\ud800'], ['ok', 'a\udc00b']]) {
    assert.throws(() => Dice.run({version: Dice.VERSION, seed: 's', stream: 'pick', kind: 'pick', params: {pool, count: 1}}), /lone surrogates/);
  }
  const r = cli(['shuffle', 's', '-'], 'a\rb\r\nc\n');
  assert.equal(r.status, 0, r.stderr);
  assert.deepEqual(JSON.parse(r.stdout).request.params.pool, ['a', 'b', 'c']);
  const dash = cli(['name', '-x', '1']);
  assert.equal(dash.status, 0, 'a seed may begin with a dash');
  assert.equal(JSON.parse(dash.stdout).request.seed, '-x');
});
