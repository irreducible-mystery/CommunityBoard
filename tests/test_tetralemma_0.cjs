'use strict';
// Runs the page's engine (the script block with id "t0-engine") under Node.
// Run with: node --test tests/test_tetralemma_0.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/tetralemma-0.html'), 'utf8');
const src = html.match(/<script id="t0-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const T = ctx.module.exports;

test('zero and one qubit pass the perfect test by checking only the empty part', () => {
  const z = T.perfectReport(T.state(0, [1]));
  assert.equal(z.partsChecked, 1); assert.equal(z.perfect, true);
  for (let i = 0; i < 10; i++) {
    const r = T.perfectReport(T.randomState(1, 'test', 'one-' + i));
    assert.equal(r.partsChecked, 1); assert.equal(r.perfect, true);
  }
});

test('the test has teeth from two qubits: Bell and GHZ3 pass, W3 and random states fail', () => {
  assert.equal(T.perfectReport(T.named('bell', 2)).perfect, true);
  assert.equal(T.perfectReport(T.named('ghz', 3)).perfect, true);
  assert.equal(T.perfectReport(T.named('w', 3)).perfect, false);
  for (let n = 2; n <= 5; n++) assert.equal(T.perfectReport(T.randomState(n, 'test')).perfect, false);
  assert.deepEqual([0, 1, 2, 3, 4, 5].map(T.cutCount), [0, 0, 1, 3, 7, 15]);
});

test('asking every qubit leaves one amplitude whose square is the Born probability', () => {
  for (let n = 1; n <= 6; n++) {
    const s = T.randomState(n, 'test'); let tot = 0;
    for (let i = 0; i < (1 << n); i++) {
      const b = []; for (let k = 0; k < n; k++) b.push(i >> k & 1);
      const r = T.peel(s, b);
      assert.equal(r.steps.at(-1).qubits, 0); assert.equal(r.steps.at(-1).amplitudes, 1);
      assert.ok(Math.abs(r.prob - (s.re[i] ** 2 + s.im[i] ** 2)) < 1e-15);
      tot += r.prob;
    }
    assert.ok(Math.abs(tot - 1) < 1e-12);
  }
});

test('one-qubit pure states lie on the Bloch sphere with purity 1', () => {
  const r = T.rng('test', 'bloch', 0);
  for (let i = 0; i < 100; i++) {
    const q = T.qubit(Math.PI * r(), 2 * Math.PI * r()), b = T.bloch(q);
    assert.ok(Math.abs(b.x * b.x + b.y * b.y + b.z * b.z - 1) < 1e-12);
    assert.ok(Math.abs(T.purity(T.state(1, [q.a[0], q.b[0]], [q.a[1], q.b[1]]), 1) - 1) < 1e-12);
  }
});

test('entanglement of sqrt(1-p)|00> + sqrt(p)|11> is H(p), with infinite slope at 0', () => {
  for (const p of [0.5, 0.2, 0.01, 1e-3, 1e-6, 1e-9]) assert.ok(Math.abs(T.entropyQubit0(T.pair(p)) - T.H2(p)) < 1e-9);
  assert.ok(Math.abs(T.H2(0.01) - 0.080793) < 1e-6);
  assert.ok(Math.abs(T.H2(0.001) - 0.011408) < 1e-6);
  let prev = 0;
  for (const p of [1e-2, 1e-4, 1e-6, 1e-8, 1e-10, 1e-12]) { const ratio = T.H2(p) / p; assert.ok(ratio > prev); prev = ratio; }
  for (const p of [1e-3, 1e-6, 1e-9]) assert.ok(Math.abs(T.H2(p) / (p * Math.log(Math.E / p) / Math.LN2) - 1) < 0.01);
});
