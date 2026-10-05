'use strict';
// Runs the page's engine (the script block with id "ti-engine") under Node.
// Run with: node --test tests/test_tetralemma_infinity.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/tetralemma-infinity.html'), 'utf8');
const src = html.match(/<script id="ti-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const T = ctx.module.exports;

test('cat coherence (1-2q)^n matches the exact sum over error patterns; half-life ~ ln2/(2n)', () => {
  for (const q of [0.001, 0.05, 0.2]) for (let n = 1; n <= 12; n++) assert.ok(Math.abs(T.catCoherence(n, q) - T.catCoherenceExact(n, q)) < 1e-12);
  for (const n of [1, 10, 1000, 1e6]) assert.ok(Math.abs(T.catCoherence(n, T.oneHalfLifeQ(n)) - 0.5) < 1e-9);
  assert.ok(Math.abs(T.oneHalfLifeQ(1e6) * 2e6 / Math.LN2 - 1) < 1e-5);
});

test('Page gap: fast formula equals the direct sum; half cut rises to 1/(2 ln 2)', () => {
  for (let n = 2; n <= 22; n += 2) assert.ok(Math.abs(T.pageGap(n / 2, n) - T.pageGapDirect(n / 2, n)) < 1e-9);
  for (let n = 3; n <= 20; n++) assert.ok(Math.abs(T.pageGap(1, n) - T.pageGapDirect(1, n)) < 1e-9);
  assert.ok(Math.abs(T.pageGap(10, 20) - 0.72135) < 1e-4);
  let prev = 0;
  for (const n of [2, 4, 8, 16, 32]) { const g = T.pageGap(n / 2, n); assert.ok(g > prev && g < T.LIMIT_GAP); prev = g; }
  assert.ok(Math.abs(T.pageGap(500, 1000) - 1 / (2 * Math.LN2)) < 1e-12);
  for (const k of [1, 2, 3]) { const a = 2 ** (2 * k - 40) * (1 - 4 ** -k) / (2 * Math.LN2); assert.ok(Math.abs(T.pageGap(k, 40) / a - 1) < 1e-3); }
});

test('sampled random states match Lubkin mean purity', () => {
  for (const n of [6, 8, 10]) {
    let t = 0; for (let i = 0; i < 30; i++) t += T.purityLow(T.randomState(n, 'test', 'l' + i), n / 2);
    assert.ok(Math.abs(t / 30 / T.lubkin(n / 2, n) - 1) < 0.06, `n=${n}`);
  }
});

test('Dicke pair concurrence: closed form = state vector; best is W with 2/n', () => {
  for (const n of [3, 4, 6, 9]) for (let k = 0; k <= n; k++) assert.ok(Math.abs(T.xConcurrence(T.pairReduced(T.dickeState(n, k), n)) - T.dickeConcurrence(n, k)) < 1e-12);
  for (const n of [2, 3, 10, 100, 1000]) { const b = T.bestDicke(n); assert.equal(b.k, 1); assert.ok(Math.abs(b.c - 2 / n) < 1e-12); assert.ok(b.c <= 1 / Math.sqrt(n - 1) + 1e-12); }
});

test('repetition code: exact binomial agreement and a step at p = 1/2', () => {
  for (const d of [1, 3, 11, 51]) for (const p of [0.05, 0.3, 0.5, 0.7]) assert.ok(Math.abs(T.repFail(d, p) - T.repFailExact(d, p)) < 1e-12);
  const ds = [1, 3, 11, 101, 1001];
  for (let i = 1; i < ds.length; i++) { assert.ok(T.repFail(ds[i], 0.3) < T.repFail(ds[i - 1], 0.3)); assert.ok(T.repFail(ds[i], 0.7) > T.repFail(ds[i - 1], 0.7)); }
  for (const d of ds) assert.ok(Math.abs(T.repFail(d, 0.5) - 0.5) < 1e-9);
  assert.ok(T.repFail(1001, 0.3) < 1e-39);
});
