'use strict';
// Runs the page's engine (the script block with id "limits-engine") under Node.
// Run with: node --test tests/test_limits.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/limits.html'), 'utf8');
const src = html.match(/<script id="limits-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const Limits = ctx.module.exports;

test('every load check passes', () => {
  const list = Limits.checks();
  assert.equal(list.length, 13);
  for (const c of list) assert.equal(c.ok, true, c.name + ' ' + c.detail);
});

test('Belnap–Dunn distributes and the qubit lattice does not', () => {
  const d = Limits.compute();
  assert.equal(d.bd4Fail, 0);
  assert.equal(d.meetNB, 'f');
  assert.equal(d.joinNB, 't');
  assert.equal(d.dim1Fail, 0);
  assert.equal(d.parallel, false);
  assert.equal(d.spanFull, true);
});

test('dephasing leaves a shared bit, not independence', () => {
  const bell = Limits.compute().bell;
  const at = t => bell.find(b => b.t === t);
  assert.ok(Math.abs(at(0).I - 2) < 1e-12);
  assert.ok(Math.abs(at(4).I - 1) < 1e-4);
  assert.ok(at(4).c < 1e-3);
  assert.ok(Math.abs(at(1).c - Math.exp(-2)) < 1e-12);
});

test('asking rarely splits the two records; asking often freezes the flip', () => {
  const z = Limits.compute().zeno;
  const at = N => z.find(row => row.N === N);
  assert.ok(at(1).sel < 1e-12 && at(1).non < 1e-12);
  assert.ok(Math.abs(at(2).sel - 0.25) < 1e-12);
  assert.ok(Math.abs(at(2).non - 0.5) < 1e-12);
  assert.ok(at(256).sel > 0.99 && at(256).non > 0.99);
});

test('a sum of three cubes can be 29 and cannot be 4 mod 9', () => {
  const d = Limits.compute();
  assert.equal(d.twentyNine, 29);
  assert.equal(d.sumHas4, false);
  assert.equal(d.sumHas5, false);
});
