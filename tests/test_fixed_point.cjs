'use strict';
// Runs the page's pure engine (the <script id="fp-engine"> block) under Node.
// Run with: node --test tests/test_fixed_point.cjs
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

test('Y f unfolds to f (Y f): the argument is Y f one step earlier', () => {
  const r1 = FP.reduce(FP.A(FP.Y, FP.V('f')), 'normal', 1).result;
  const r2 = FP.reduce(FP.A(FP.Y, FP.V('f')), 'normal', 2).result;
  const u = FP.unApp(r2);
  assert.equal(u.head.t, 'v');
  assert.equal(u.head.n, 'f');
  assert.equal(u.args.length, 1);
  assert.ok(FP.eq(u.args[0], r1), 'the two-step reduct is f applied to the one-step reduct');
});

test('FACT n = n! for n = 0..6 under normal order', () => {
  for (let n = 0; n <= 6; n++) {
    const r = FP.reduce(FP.A(FP.FACT, FP.N(n)), 'normal', 20000);
    assert.ok(r.done && r.result.t === 'num', `n=${n} did not reach a numeral`);
    assert.equal(r.result.v, FP.factorial(n), `n=${n}`);
  }
});

test('the Liar has a fixed point that diverges: Y NOT has no normal form', () => {
  assert.equal(FP.reduce(FP.LIAR, 'normal', 400).done, false);
});

test('evaluation order decides convergence: Y K reaches a WHNF under normal order, not applicative', () => {
  assert.equal(FP.reduceWHNF(FP.A(FP.Y, FP.K), 'normal', 400).done, true);
  assert.equal(FP.reduceWHNF(FP.A(FP.Y, FP.K), 'applicative', 400).done, false);
});

test('FACT 5 = 120 under normal order and diverges under applicative order', () => {
  const n = FP.reduce(FP.A(FP.FACT, FP.N(5)), 'normal', 20000);
  assert.ok(n.done && n.result.t === 'num' && n.result.v === 120, `got ${n.result.v}`);
  assert.equal(FP.reduce(FP.A(FP.FACT, FP.N(5)), 'applicative', 400).done, false);
});

test('over {0,1} NOT has no fixed point (the fold.html fact)', () => {
  const not = (b) => (b === 0 ? 1 : 0);
  assert.notEqual(not(0), 0);
  assert.notEqual(not(1), 1);
});

test('every self-check the page runs passes', () => {
  const failed = FP.selfCheck().filter((c) => !c.ok).map((c) => c.name);
  assert.equal(failed.length, 0, failed.join('; '));
});
