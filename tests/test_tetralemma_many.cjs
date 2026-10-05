'use strict';
// Runs the page's engine (the <script id="tm-engine"> block) under Node.
// Run with: node --test tests/test_tetralemma_many.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/tetralemma-many.html'), 'utf8');
const src = html.match(/<script id="tm-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const TM = ctx.module.exports;

test('Hermitian eigensolver reproduces trace, tr(A^2) and tr(A^3) of random matrices', () => {
  const r = TM.rng('test', 'herm', 0);
  for (const d of [2, 5, 16, 40]) {
    const re = new Float64Array(d * d), im = new Float64Array(d * d);
    for (let i = 0; i < d; i++) for (let j = i; j < d; j++) { const a = r() - 0.5, b = i === j ? 0 : r() - 0.5; re[i * d + j] = re[j * d + i] = a; im[i * d + j] = b; im[j * d + i] = -b; }
    for (let i = 0; i < d; i++) re[i * d + i] += d;
    const ev = TM.hermEig({ d, re, im });
    let t1 = 0, t2 = 0, t3 = 0;
    for (let i = 0; i < d; i++) t1 += re[i * d + i];
    for (let k = 0; k < d * d; k++) t2 += re[k] ** 2 + im[k] ** 2;
    for (let i = 0; i < d; i++) for (let j = 0; j < d; j++) for (let k = 0; k < d; k++) {
      const ar = re[i * d + j], ai = im[i * d + j], br = re[j * d + k], bi = im[j * d + k], cr = re[k * d + i], ci = im[k * d + i];
      const xr = ar * br - ai * bi, xi = ar * bi + ai * br; t3 += xr * cr - xi * ci;
    }
    const s = (p) => ev.reduce((a, x) => a + x ** p, 0);
    assert.ok(Math.abs(s(1) - t1) < 1e-9 * d, `d=${d} trace`);
    assert.ok(Math.abs(s(2) - t2) < 1e-8 * d * d, `d=${d} tr A^2`);
    assert.ok(Math.abs(s(3) / t3 - 1) < 1e-10, `d=${d} tr A^3`);
  }
});

test('Page: closed forms and the 1/(2 ln 2) limit', () => {
  assert.ok(Math.abs(TM.pageMean(2, 2) - 1 / (3 * Math.LN2)) < 1e-12);
  const lim = 1 / (2 * Math.LN2);
  assert.ok(Math.abs(TM.pageGap(40, 20) - lim) < 1e-6);
  for (const [n, k] of [[8, 2], [10, 3], [12, 5], [14, 6], [16, 8]]) {
    const a = Math.min(k, n - k);
    assert.ok(Math.abs(TM.pageGap(n, k) - (a - TM.pageMean(2 ** a, 2 ** (n - a)))) < 1e-9, `${n},${k}`);
  }
  for (let k = 1; k <= 10; k++) assert.ok(Math.abs(TM.pageGap(20, k) / (2 ** (2 * k - 20) * (1 - 4 ** -k) * lim) - 1) < 1e-3, `k=${k}`);
});

test('a random 16-qubit state tracks Page within 0.02 bits at every k, and quadruples toward half', () => {
  const st = TM.randomState(16, 'tetralemma');
  let prev = null;
  for (let k = 1; k <= 8; k++) {
    const gap = k - TM.entropyFirst(st, k), pg = TM.pageGap(16, k);
    assert.ok(Math.abs(gap - pg) < 0.02, `k=${k}: ${gap} vs ${pg}`);
    if (k >= 6) assert.ok(gap / prev > 3.5 && gap / prev < 4.5, `ratio at k=${k}`);
    prev = gap;
  }
});

test('either side of a cut gives the same entropy; subset and block reductions agree', () => {
  const st = TM.randomState(11, 'sides');
  for (let k = 1; k <= 10; k++) {
    const last = []; for (let q = k; q < 11; q++) last.push(q);
    if (last.length <= 5) assert.ok(Math.abs(TM.entropyFirst(st, k) - TM.entropyBits(TM.hermEig(TM.reducedSubset(st, last)))) < 1e-9, `k=${k}`);
  }
});

test('GHZ loses everything on one answer; a random state loses about half a bit', () => {
  for (let t = 0; t < 10; t++) {
    const m = TM.measureDrop(TM.ghz(12), t % 12, TM.rng('test', 'ghz', t));
    for (let k = 1; k <= 5; k++) assert.ok(TM.entropyFirst(m.state, k) < 1e-9);
  }
  const s = TM.randomState(14, 'crowd'), before = TM.entropyFirst(s, 7);
  const m = TM.measureDrop(s, 0, TM.rng('test', 'crowd', 0)), after = TM.entropyFirst(m.state, 6);
  assert.ok(before - after > 0.2 && before - after < 1.0, `${before} -> ${after}`);
  assert.ok(Math.abs(TM.norm2(m.state) - 1) < 1e-12);
});
