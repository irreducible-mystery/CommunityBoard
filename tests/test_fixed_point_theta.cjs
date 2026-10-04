'use strict';
// Turing's fixed-point combinator, run on fixed-point.html's own engine (unchanged).
// Answers the 09:34 board note: "Turing's Θ gives the one-way version if anyone wants it."
// Y f and f (Y f) are only beta-convertible (they meet in a common reduct).
// Θ f reduces to f (Θ f) itself, in two normal-order steps.
// Run with: node --test tests/test_fixed_point_theta.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/fixed-point.html'), 'utf8');
const src = html.match(/<script id="fp-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const FP = ctx.module.exports;
const { V, L, A } = FP;

// U = λx.λy. y (x x y);  Θ = U U
const U = L('x', L('y', A(V('y'), A(A(V('x'), V('x')), V('y')))));
const THETA = A(U, U);

test('Θ f reduces to exactly f (Θ f) in two normal-order steps (one-way, not just =β)', () => {
  const target = A(V('f'), A(THETA, V('f')));
  const r1 = FP.reduce(A(THETA, V('f')), 'normal', 1).result;
  const r2 = FP.reduce(A(THETA, V('f')), 'normal', 2).result;
  assert.ok(!FP.eq(r1, target), 'one step is not enough');
  assert.ok(FP.eq(r2, target), 'got ' + FP.show(r2));
});

test('contrast: Y f never reduces to f (Y f) itself within 50 normal-order steps', () => {
  const target = A(V('f'), A(FP.Y, V('f')));
  for (let n = 0; n <= 50; n++) {
    const r = FP.reduce(A(FP.Y, V('f')), 'normal', n).result;
    assert.ok(!FP.eq(r, target), 'reached f (Y f) at step ' + n);
  }
});

test('Θ computes the same factorials as Y under normal order (n = 0..6)', () => {
  const FACT_T = A(THETA, FP.FACT_STEP);
  for (let n = 0; n <= 6; n++) {
    const r = FP.reduce(A(FACT_T, FP.N(n)), 'normal', 20000);
    assert.ok(r.done && r.result.t === 'num', 'n=' + n + ' did not reach a numeral');
    assert.equal(r.result.v, FP.factorial(n), 'n=' + n);
  }
});

test('the Liar is no better behaved under Θ: Θ NOT has no normal form within 400 steps', () => {
  assert.equal(FP.reduce(A(THETA, FP.NOT), 'normal', 400).done, false);
});
