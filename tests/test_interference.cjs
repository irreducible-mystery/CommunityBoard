'use strict';
// Runs the page's pure engine (the <script id="interference-engine"> block) under Node.
// Run with: node --test tests/test_interference.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/interference.html'), 'utf8');
const src = html.match(/<script id="interference-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const I = ctx.module.exports;

// Far-field geometry used throughout: lambda = 5, separation d = 200, screen at L = 4000.
const K = 2 * Math.PI / 5, L = 4000, d = 200;
const two = I.twoSource(d);

test('every self-check on the page passes', () => {
  const res = I.selfCheck();
  assert.equal(res.length, 10);
  const failed = res.filter(c => !c.ok).map(c => `${c.name}: got ${c.got}, wanted ${c.want}`);
  assert.equal(failed.length, 0, failed.join('\n'));
});

test('for two equal sources the fringe visibility equals the coherence exactly', () => {
  for (const c of [1, 0.9, 0.75, 0.5, 0.25, 0.1, 0]) {
    const v = I.visibility(two, K, c, L, -200, 200, 800);
    assert.ok(Math.abs(v - c) < 1e-6, `c=${c} gave v=${v}`);
  }
});

test('the fringe spacing is lambda L / d (first minimum at half, side maximum at one)', () => {
  const I0 = I.intensityAt(two, L, 0, K, 1);
  const Imin = I.intensityAt(two, L, 50, K, 1);   // lambda L / (2d)
  const Imax = I.intensityAt(two, L, 100, K, 1);  // lambda L / d
  assert.ok(Math.abs(I0 - 4) < 1e-6, `centre ${I0}`);
  assert.ok(Imin < 1e-3, `first minimum ${Imin}`);
  assert.ok(Math.abs(Imax - 4) < 1e-3, `side maximum ${Imax}`);
});

test('the checker can fail: a single source has no fringes, a double slit does', () => {
  const one = [{ x: 0, y: 0, a: 1, phi: 0 }];
  assert.ok(I.visibility(one, K, 1, L, -200, 200, 800) < 1e-9);
  assert.ok(I.visibility(two, K, 1, L, -200, 200, 800) > 0.999);
});

test('energy is conserved: the mean coherent intensity over random phases equals S', () => {
  const rnd = I.mulberry32(7);
  const em = [{ a: 1 }, { a: 0.7 }, { a: 0.4 }];
  const S = I.totalPower(em);
  let acc = 0;
  const N = 50000;
  for (let i = 0; i < N; i++) {
    let re = 0, im = 0;
    for (const e of em) {
      const th = rnd() * 2 * Math.PI;
      re += e.a * Math.cos(th); im += e.a * Math.sin(th);
    }
    acc += re * re + im * im;
  }
  assert.ok(Math.abs(acc / N - S) < 0.01 * S, `mean ${acc / N}, S ${S}`);
});

test('a single source is uniform at every coherence', () => {
  const one = [{ x: 0, y: 0, a: 1, phi: 0 }];
  for (const c of [0, 0.5, 1]) {
    for (const [x, y] of [[0, 0], [37, -12], [-200, 90]]) {
      assert.ok(Math.abs(I.intensityAt(one, x, y, K, c) - 1) < 1e-12);
    }
  }
});

test('a fixed seed reproduces the layout, a new seed changes it', () => {
  assert.deepEqual(I.makeEmitters('art'), I.makeEmitters('art'));
  assert.notDeepEqual(I.makeEmitters('art'), I.makeEmitters('art-2'));
});
