'use strict';
// Runs the page's engine (the script block with id "sc-engine") under Node.
// Run with: node --test tests/test_surface_code.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/surface-code.html'), 'utf8');
const src = html.match(/<script id="sc-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const SC = ctx.module.exports;
const blank = (n) => ({ x: new Uint8Array(n), z: new Uint8Array(n) });

test('d = 3..15: X and Z checks commute; (d^2-1)/2 independent checks of each type', () => {
  for (let d = 3; d <= 15; d += 2) {
    const c = SC.makeCode(d);
    for (const a of c.checks.X) for (const b of c.checks.Z) {
      const o = a.qubits.filter((q) => b.qubits.includes(q)).length;
      assert.equal(o % 2, 0, `d=${d}`);
    }
    assert.equal(SC.rank2rows(SC.checkMatrix(c, 'X')), (d * d - 1) / 2);
    assert.equal(SC.rank2rows(SC.checkMatrix(c, 'Z')), (d * d - 1) / 2);
  }
});

test('every single accident and every pair (d = 5) is repaired cleanly', () => {
  for (const d of [5, 7, 9]) {
    const c = SC.makeCode(d);
    for (let q = 0; q < c.n; q++) for (const k of ['x', 'z']) {
      const f = blank(c.n); f[k][q] = 1;
      const r = SC.correctFrame(c, f);
      assert.ok(r[k].clean && !r[k].logical, `d=${d} q=${q} ${k}`);
    }
  }
  const c5 = SC.makeCode(5);
  for (let a = 0; a < 25; a++) for (let b = a + 1; b < 25; b++) for (const k of ['x', 'z']) {
    const f = blank(25); f[k][a] = f[k][b] = 1;
    const r = SC.correctFrame(c5, f);
    assert.ok(r[k].clean && !r[k].logical, `pair ${a},${b} ${k}`);
  }
});

test('a column line of (d-1)/2 X accidents is repaired; (d+1)/2 fool the decoder', () => {
  for (const d of [3, 5, 7, 9, 11]) {
    const c = SC.makeCode(d), h = (d + 1) / 2;
    for (const len of [h - 1, h]) {
      const f = blank(c.n); for (let r = 0; r < len; r++) f.x[r * d] = 1;
      assert.equal(SC.correctFrame(c, f).x.logical, len === h, `d=${d} len=${len}`);
    }
  }
});

test('a row of Z is silent and logical; one X check is silent and not logical', () => {
  const c = SC.makeCode(9), row = new Uint8Array(81);
  for (let q = 0; q < 9; q++) row[q] = 1;
  assert.ok(SC.syndrome(c, 'X', row).every((s) => !s));
  assert.ok(SC.isLogical(c, 'X', row));
  for (const chk of c.checks.X) {
    const st = new Uint8Array(81); chk.qubits.forEach((q) => { st[q] = 1; });
    assert.ok(SC.syndrome(c, 'Z', st).every((s) => !s));
    assert.ok(!SC.isLogical(c, 'Z', st));
  }
});

test('repairs always clear the syndrome; d = 7 beats d = 3 at 3% and loses at 15%', () => {
  const c3 = SC.makeCode(3), c7 = SC.makeCode(7), r = SC.rng('test', 'clean', 0);
  for (let t = 0; t < 300; t++) {
    const res = SC.correctFrame(c7, SC.randomFrame(c7, 0.12, r));
    assert.ok(res.x.clean && res.z.clean);
  }
  const s = 'tetralemma-check';
  assert.ok(SC.failureRate(c7, 0.03, 1000, s) < SC.failureRate(c3, 0.03, 1000, s));
  assert.ok(SC.failureRate(c7, 0.15, 1000, s) > SC.failureRate(c3, 0.15, 1000, s));
});
