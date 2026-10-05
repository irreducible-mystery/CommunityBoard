'use strict';
// Runs the page's engine (the <script id="t7-engine"> block) under Node.
// Run with: node --test tests/test_tetralemma_7.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/tetralemma-7.html'), 'utf8');
const src = html.match(/<script id="t7-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 120000 });
const T7 = ctx.module.exports;
const mask = (s) => s.reduce((m, q) => m | (1 << q), 0);

test('the best graph leaves 7/7 qubits, 21/21 pairs and 32/35 triples maximally mixed (state vector)', () => {
  const ct = T7.cutTable(T7.graphState(7, T7.EDGES.best));
  assert.deepEqual(Array.from(ct.rows, (r) => r.atMax), [7, 21, 32]);
  assert.equal(ct.perfect, false);
});

test('GF(2) cut rank equals the von Neumann entropy for the best graph on every cut up to 3', () => {
  const st = T7.graphState(7, T7.EDGES.best), adj = T7.adjOf(7, T7.EDGES.best);
  for (const k of [1, 2, 3]) for (const s of T7.subsetsOf(7, k)) {
    assert.ok(Math.abs(T7.S(st, s) - T7.cutRank(adj, mask(s))) < 1e-6, s.join(''));
  }
});

test('the perfect six has the eigenvalue counts the HGS method requires; the best seven has no usable five-set', () => {
  const a6 = T7.adjOf(6, T7.EDGES.wheel6);
  for (const s of T7.subsetsOf(6, 4)) { const pc = T7.partCounts(a6, mask(s)); assert.equal(pc.low, 0); assert.equal(pc.top, 3); }
  const a7 = T7.adjOf(7, T7.EDGES.best);
  for (const s of T7.subsetsOf(7, 5)) assert.equal(T7.usableFive(T7.partCounts(a7, mask(s))), false, s.join(''));
});

test('parity rule holds on random Pauli words', () => {
  const r = T7.rng('test', 'parity', 0); let n = 0;
  for (let t = 0; t < 5000; t++) {
    const M = [], N = []; for (let i = 0; i < 7; i++) { M.push(Math.floor(r() * 4)); N.push(Math.floor(r() * 4)); }
    const ac = T7.anticomm(M, N); if (!ac) continue; n++;
    assert.equal(((T7.weight(ac) - T7.weight(M) - T7.weight(N)) % 2 + 2) % 2, 0);
  }
  assert.ok(n > 1000);
});

test('linear programming: 4 and 8 excluded, 7 not', () => {
  assert.ok(T7.shadow(T7.forcedEnumerator(4))[0] < 0);
  assert.equal(T7.forcedEnumerator(8)[6], -84);
  const A7 = T7.forcedEnumerator(7);
  assert.deepEqual(Array.from(A7), [1, 0, 0, 0, 35, 42, 28, 22]);
  assert.ok(T7.shadow(A7).every((x) => x > -1e-9));
  assert.deepEqual([...T7.forcedEnumerator(6)], [1, 0, 0, 0, 45, 0, 18]);
});

test('full census of 2^21 graphs: 620,640 two-uniform, each missing 3 or 7 triples; none usable by the proof', () => {
  const cs = T7.censusStart();
  while (!T7.censusRun(cs, 1 << 18)) { /* chunks */ }
  assert.equal(cs.twoUniform, 620640);
  assert.deepEqual(JSON.parse(JSON.stringify(cs.hist)), { 3: 115080, 7: 505560 });
  assert.equal(cs.perfect, 0);
  assert.equal(cs.usable, 0);
});

test('seeded search lowers the summed triple purity but stays above 35/8', () => {
  const st = T7.randomState(7, 'tetralemma');
  const p0 = T7.purity3(st).total, p1 = T7.descend(st, 300, 0.05).total;
  assert.ok(p1 < p0 && p1 > 4.375 + 0.1, `${p0} -> ${p1}`);
});
