'use strict';
// Runs the page's pure engine (the <script id="ff-engine"> block) under Node.
// Run with: node --test tests/test_fireflies.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/fireflies.html'), 'utf8');
const src = html.match(/<script id="ff-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const FF = ctx.module.exports;

test('the order parameter is 1 for one phase and 0 for evenly spread phases', () => {
  const same = new Float64Array(30).fill(0.7);
  const even = Float64Array.from({ length: 30 }, (_, i) => i * 2 * Math.PI / 30);
  assert.ok(Math.abs(FF.order(same).r - 1) < 1e-12);
  assert.ok(FF.order(even).r < 1e-12);
});

test('the prediction is zero up to K_c = 2γ and rises as √(1 − K_c/K) after it', () => {
  assert.equal(FF.predicted(0.9, 0.5), 0);
  assert.equal(FF.predicted(1.0, 0.5), 0);
  assert.ok(Math.abs(FF.predicted(2.0, 0.5) - Math.sqrt(0.5)) < 1e-12);
  assert.ok(FF.predicted(4, 0.5) > FF.predicted(2, 0.5));
});

test('identical rhythms lock completely under any positive coupling', () => {
  assert.ok(FF.run({ N: 200, K: 0.3, gamma: 0, T: 80 }).rEnd > 1 - 1e-6);
});

test('with a Lorentzian spread, r matches √(1 − 2γ/K) above the threshold and not below', () => {
  const gamma = 0.5, Kc = 1;
  assert.ok(FF.run({ N: 400, K: 0.5 * Kc, gamma }).rMean < 0.15);
  for (const m of [2, 4, 8]) {
    const got = FF.run({ N: 400, K: m * Kc, gamma }).rMean, want = FF.predicted(m * Kc, gamma);
    assert.ok(Math.abs(got - want) < 0.06, `K=${m}Kc: got ${got}, want ${want}`);
  }
});

test('the checker can fail: a threshold of 3γ is rejected by the data', () => {
  const gamma = 0.5;
  const wrongPrediction = (K) => K > 3 * gamma ? Math.sqrt(1 - 3 * gamma / K) : 0;
  const got = FF.run({ N: 400, K: 3 * gamma, gamma }).rMean;   // 1.5 K_c: the flock is partly locked
  assert.ok(got > 0.40, `got ${got}`);
  assert.ok(Math.abs(got - wrongPrediction(3 * gamma)) > 0.3);
});

test('the same seed reproduces the same flock', () => {
  const a = FF.run({ N: 100, K: 1.2, gamma: 0.5, T: 20, seed: 'twice' });
  const b = FF.run({ N: 100, K: 1.2, gamma: 0.5, T: 20, seed: 'twice' });
  assert.equal(a.rMean, b.rMean);
});

test('every self-check the page runs passes', () => {
  const failed = FF.selfCheck().filter(c => !c.ok).map(c => `${c.name}: got ${c.got}, wanted ${c.want}`);
  assert.equal(failed.length, 0, failed.join('\n'));
});
