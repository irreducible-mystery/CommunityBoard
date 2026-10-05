'use strict';
// Runs the page's pure engine (the <script id="chsh-engine"> block) under Node.
// Run with: node --test tests/test_chsh.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/chsh.html'), 'utf8');
const src = html.match(/<script id="chsh-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const C = ctx.module.exports;

test('every self-check on the page passes', () => {
  const res = C.selfCheck();
  assert.equal(res.length, 10);
  const failed = res.filter(c => !c.ok).map(c => `${c.name}: got ${c.got}, wanted ${c.want}`);
  assert.equal(failed.length, 0, failed.join('\n'));
});

test('no classical strategy beats 3/4, by enumeration over all four functions each side', () => {
  assert.equal(C.classicalBest(), 0.75);
});

test('the quantum optimum wins cos^2(pi/8) and reaches S = 2 sqrt 2', () => {
  const d = C.OPT.map(x => x * C.D2R);
  assert.ok(Math.abs(C.winProb(...d) - C.TS) < 1e-12);
  assert.ok(Math.abs(C.chshS(...d) - 2 * Math.SQRT2) < 1e-12);
  assert.ok(Math.abs(C.TS - 0.8535533905932737) < 1e-12);
});

test('the checker can fail: a product-like strategy cannot pass the wall', () => {
  // directions that make two of the four correlators equal the other two give S = 2, P = 3/4
  const wall = C.WALL.map(x => x * C.D2R);
  assert.ok(Math.abs(C.chshS(...wall) - 2) < 1e-12);
  assert.ok(Math.abs(C.winProb(...wall) - 0.75) < 1e-12);
  // and no grid point exceeds the Tsirelson bound
  assert.ok(C.gridMax() <= C.TS + 1e-6);
});

test('the singlet correlator is -cos of the angle', () => {
  for (const [a, b] of [[0, 0], [0, Math.PI], [0.4, 1.9], [2.2, 2.2]]) {
    assert.ok(Math.abs(C.corr(a, b) + Math.cos(a - b)) < 1e-12);
  }
  assert.ok(Math.abs(C.corr(1.1, 1.1) + 1) < 1e-12);
  assert.ok(Math.abs(C.corr(1.1, 1.1 + Math.PI) - 1) < 1e-12);
});

test('played rounds agree with the predicted win rate at the optimum', () => {
  const d = C.OPT.map(x => x * C.D2R);
  const r = C.playRounds(...d, 'agree', 40000);
  assert.ok(Math.abs(r.rate - C.TS) < 0.01, `rate ${r.rate}`);
  assert.ok(Math.abs(r.xRate - 0.5) < 0.02 && Math.abs(r.yRate - 0.5) < 0.02);
});

test('a fixed seed reproduces the same tally', () => {
  const d = C.OPT.map(x => x * C.D2R);
  const a = C.playRounds(...d, 'twice', 5000), b = C.playRounds(...d, 'twice', 5000);
  assert.deepEqual(a, b);
});
