'use strict';
// Runs the page's pure engine (the <script id="qw-engine"> block) under Node.
// Run with: node --test tests/test_quantum_walk.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/quantum-walk.html'), 'utf8');
const src = html.match(/<script id="qw-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const QW = ctx.module.exports;

test('every self-check on the page passes', () => {
  const res = QW.selfCheck();
  assert.equal(res.length, 10);
  const failed = res.filter(c => !c.ok).map(c => `${c.name}: got ${c.got}, wanted ${c.want}`);
  assert.equal(failed.length, 0, failed.join('\n'));
});

test('the classical walk has variance exactly t and mean 0', () => {
  for (const t of [1, 5, 20, 60]) {
    const s = QW.stats(QW.classicalDist(t, t + 3), t + 3);
    assert.ok(Math.abs(s.v - t) < 1e-9, `var ${s.v} at t=${t}`);
    assert.ok(Math.abs(s.m) < 1e-9);
    assert.ok(Math.abs(s.s - 1) < 1e-12);
  }
});

test('the quantum walk spreads ballistically: variance / t^2 -> 1 - 1/sqrt2', () => {
  const coefs = [40, 80, 160, 320].map(t => QW.stats(QW.quantumDist(t, t + 5, 0), t + 5).v / (t * t));
  for (const c of coefs) assert.ok(Math.abs(c - QW.QVAR) < 0.01, `coef ${c}`);
  // and it really is growing like t^2, not t: the ratio to the classical variance grows
  const r40 = QW.stats(QW.quantumDist(40, 45, 0), 45).v / 40;
  const r160 = QW.stats(QW.quantumDist(160, 165, 0), 165).v / 160;
  assert.ok(r160 > 3 * r40, `${r40} -> ${r160}`);
});

test('the checker can fail: a walk with a biased coin is not the quantum walk', () => {
  // a "quantum walk" whose coin is measured every step is classical, so its variance is t, not t^2
  const s = QW.stats(QW.quantumDist(60, 65, 1, 'bias', 800), 65);
  assert.ok(Math.abs(s.v - 60) / 60 < 0.15, `got ${s.v}`);
  assert.ok(Math.abs(s.v - QW.QVAR * 3600) > 500);
});

test('decoherence interpolates monotonically between quantum and classical', () => {
  const vs = [0, 0.25, 0.5, 0.75, 1].map(p => QW.stats(QW.quantumDist(50, 55, p, 'mono', 600), 55).v);
  for (let i = 1; i < vs.length; i++) assert.ok(vs[i] < vs[i - 1] + 1e-6, `${vs[i - 1]} -> ${vs[i]}`);
  assert.ok(Math.abs(vs[vs.length - 1] - 50) / 50 < 0.15);
});

test('the quantum walk keeps the parity of the step count', () => {
  for (const t of [10, 21, 40]) {
    const d = QW.quantumDist(t, t + 4, 0), T = t + 4, par = t % 2;
    for (let i = 0; i < d.length; i++) {
      if (Math.abs(i - T) % 2 !== par) assert.ok(d[i] < 1e-12, `wrong-parity cell ${i - T} at t=${t}`);
    }
  }
});

test('a fixed seed reproduces the same ensemble exactly', () => {
  const a = QW.quantumDist(30, 34, 0.4, 'twice', 200);
  const b = QW.quantumDist(30, 34, 0.4, 'twice', 200);
  assert.deepEqual(Array.from(a), Array.from(b));
});
