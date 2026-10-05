'use strict';
// Runs the page's engine (the script block with id "ic-engine") under Node.
// Run with: node --test tests/test_infinite_cat.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/infinite-cat.html'), 'utf8');
const src = html.match(/<script id="ic-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const C = ctx.module.exports;

test('every proper part of GHZ_n equals the coin (and GHZ+ equals GHZ-)', () => {
  for (let n = 2; n <= 6; n++) {
    const g = C.pureRho(C.ghz(n)), c = C.coin(n), gm = C.pureRho(C.ghz(n, -1));
    for (let m = 1; m < (1 << n) - 1; m++) {
      assert.ok(C.maxAbsDiff(C.reduce(g, m), C.reduce(c, m)) < 1e-14);
      assert.ok(C.maxAbsDiff(C.reduce(g, m), C.reduce(gm, m)) < 1e-14);
    }
  }
});

test('exactly 2^(n-1) Pauli strings distinguish cat from coin: full-support X/Y with even Y', () => {
  for (let n = 1; n <= 5; n++) {
    const g = C.pureRho(C.ghz(n)), c = C.coin(n); let cnt = 0;
    for (const ps of C.allPaulis(n)) {
      if (Math.abs(C.expect(g, ps) - C.expect(c, ps)) > 1e-9) {
        cnt++;
        assert.ok(ps.every((x) => x === 'X' || x === 'Y'));
        assert.equal(ps.filter((x) => x === 'Y').length % 2, 0);
      }
    }
    assert.equal(cnt, 2 ** (n - 1));
    assert.ok(Math.abs(C.traceDistance(g, c) - 0.5) < 1e-9);
  }
});

test('noisy parity: simulation follows (1-2e)^n for the cat and 0 for the coin', () => {
  for (const n of [1, 10, 40]) {
    assert.ok(Math.abs(C.simulateParity(n, 0.01, 20000, 'test', 'cat') - C.paritySignal(n, 0.01)) < 0.03);
    assert.ok(Math.abs(C.simulateParity(n, 0.01, 20000, 'test', 'coin')) < 0.03);
  }
  assert.ok(C.trialsNeeded(1000, 0.01, 3) > 1e18);
});

test('surface code census: nothing lighter than d flips the answer; all weight-d flippers cross the grid', () => {
  const expected = { 3: [8, 3], 5: [52, 5] };
  for (const d of [3, 5]) {
    const code = C.makeCode(d);
    assert.equal(code.X.length, (d * d - 1) / 2); assert.equal(code.Z.length, (d * d - 1) / 2);
    for (let w = 1; w < d; w++) assert.equal(C.weightCensus(code, w).logical, 0);
    const r = C.weightCensus(code, d);
    assert.equal(r.total, C.choose(d * d, d));
    assert.deepEqual([r.logical, r.straight], expected[d]);
    assert.equal(r.onePerRow, r.logical);
  }
});
