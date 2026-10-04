'use strict';
// Runs the page's pure engine (the <script id="cr-engine"> block) under Node.
// Run with: node --test tests/test_crossing.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/crossing.html'), 'utf8');
const src = html.match(/<script id="cr-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(src, ctx, { timeout: 20000 });
const CR = ctx.module.exports;

test('every self-check on the page passes', () => {
  const res = CR.selfCheck();
  assert.equal(res.length, 7);
  for (const r of res) assert.ok(r.ok, r.msg);
});

test('both swaps work at (1,1) and at no other integer point in a wider window', () => {
  const hits = [];
  for (let b = -20; b <= 20; b++) for (let c = -20; c <= 20; c++) {
    if (c === 0) continue;
    if (CR.swaps(CR.S, b, c) && CR.swaps(CR.P, b, c)) hits.push([b, c]);
  }
  assert.deepEqual(hits.map(String), ['1,1']);
});

test('the checker can fail: a wrong swap is not accepted anywhere', () => {
  const notASwap = (z) => [z[0] + 0.5, z[1]];
  for (const [b, c] of [[1, 1], [1, 2], [2, 1], [0, 1]]) assert.equal(CR.swaps(notASwap, b, c), false);
});

test('Cassini on the orange line is (-1)^k for every n; on the blue line it scales with Gamma', () => {
  for (const n of [0, 1, 2, 5, 9]) assert.deepEqual(Array.from(CR.cassini(n, 1, 6)), [-1, 1, -1, 1, -1, 1]);
  assert.deepEqual(Array.from(CR.cassini(1, 3, 4)), [-1, 3, -9, 27]);  // (-1)^k * 3^(k-1), not (-3)^k
});

test('the blue flow ends at 2, not at the golden ratio', () => {
  assert.ok(Math.abs(CR.flowSum(1, 300) - 2) < 1e-12);
  assert.ok(Math.abs(CR.flowSum(1, 300) - CR.PHI) > 0.3);
});
