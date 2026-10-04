'use strict';
// Runs the page's pure engine (the <script id="bh-engine"> block) under Node.
// Run with: node --test tests/test_black_hole.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/black-hole.html'), 'utf8');
const src = html.match(/<script id="bh-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const BH = ctx.module.exports;

test('the shadow edge falls out of the geodesic equation at 3√3 M', () => {
  const bc = BH.criticalB();
  assert.ok(Math.abs(bc - 3 * Math.sqrt(3)) < 0.005, `got ${bc}`);
});

test('a distant ray is deflected by 4M/b plus the second-order term', () => {
  const b = 200, got = BH.deflection(b), want = 4 / b + 15 * Math.PI / (4 * b * b);
  assert.ok(Math.abs(got - want) / want < 0.002, `got ${got}, want ${want}`);
  const b2 = 40, got2 = BH.deflection(b2), want2 = 4 / b2 + 15 * Math.PI / (4 * b2 * b2);
  assert.ok(Math.abs(got2 - want2) / want2 < 0.02, `got ${got2}, want ${want2}`);
});

test('rays inside the critical impact parameter fall in and rays outside escape', () => {
  for (const b of [1, 3, 5, 5.15]) assert.notEqual(BH.fromImpact(b, 200, { maxTurns: 6 }).fate, 'escape', `b=${b}`);
  for (const b of [5.25, 6, 10, 50]) assert.equal(BH.fromImpact(b, 200, { maxTurns: 6 }).fate, 'escape', `b=${b}`);
});

test('the redshift factor is below one face-on and favours the approaching side', () => {
  assert.ok(Math.abs(BH.redshift(6, 0) - Math.sqrt(0.5)) < 1e-9);
  assert.ok(BH.redshift(6, 5) > 1 && BH.redshift(6, -5) < 1);
  assert.ok(BH.redshift(100, 0) > 0.98);  // far out, almost no gravitational redshift
});

test('every self-check the page runs passes', () => {
  const failed = BH.selfCheck().filter(c => !c.ok).map(c => c.name);
  assert.equal(failed.length, 0, failed.join('; '));
});
