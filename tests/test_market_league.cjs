'use strict';
// Runs the Market League engine (the <script id="ml-engine"> block of made/market-league.html) and the
// CLI's main() under Node. Run with: node --test tests/test_market_league.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const cli = require(path.join(__dirname, '../tools/market_league.cjs'));
const ML = cli.ML;
const SEED = 'ML-20261005-first';
const plain = (x) => JSON.parse(JSON.stringify(x));

test('every self-check the page runs on load passes under Node', () => {
  const cs = ML.checks(SEED);
  assert.equal(cs.length, 9);
  for (const c of cs) assert.ok(c.ok, `${c.name}: ${c.detail}`);
});

test('the world for the open round is frozen: costs, first-tick parameters and disasters', () => {
  const w = ML.world(SEED);
  assert.deepEqual(plain(w.cost), { A: 2, B: 1.5, C: 1.5 });
  assert.deepEqual(plain(w.disasters), [9, 20]);
  assert.deepEqual(plain(ML.GOODS.map((g) => w.d[g][0])), [71.5993, 68.9848, 74.3747]);
  assert.deepEqual(plain(ML.GOODS.map((g) => w.pmax[g][0])), [11.9921, 11.4028, 9.5371]);
  assert.deepEqual(plain(w.raw.slice(0, 3)), [94.9582, 87.5458, 81.2289]);
  assert.equal(w.raw.length, 48);
  assert.notDeepEqual(plain(ML.world('another').raw), plain(w.raw));
});

test('the clearing price is exactly pmax·(1 − Q/d) and never below zero', () => {
  const w = ML.world(SEED);
  const r = ML.simulate(w, [{ name: 'q', plan: [{ t: 1, produce: { A: 7, B: 'max' } }] }]);
  assert.ok(Math.abs(r.prices.A[0] - w.pmax.A[0] * (1 - 7 / w.d.A[0])) < 1e-12);
  assert.ok(Math.abs(r.prices.B[0] - w.pmax.B[0] * (1 - 10 / w.d.B[0])) < 1e-12);
  assert.equal(r.prices.C[0], w.pmax.C[0]);
  const flood = ML.simulate(w, [{ name: 'f', plan: [{ t: 1, produce: { A: 'max' }, invest: { A: 1e6 } }] }]);
  assert.ok(flood.prices.A.some((p) => p === 0), 'a firm large enough drives the price to the floor');
});

test('rationing is max-min fair: the modest get all they ask, the rest split what is left equally', () => {
  assert.deepEqual(ML.fairShare([5, 30, 30], 20), [5, 7.5, 7.5]);
  assert.deepEqual(ML.fairShare([5, 30, 30], 100), [5, 30, 30]);
  assert.deepEqual(ML.fairShare([0, 10], 4), [0, 4]);
  const w = ML.world('ration-check');
  const big = (n) => ({ name: n, plan: [{ t: 1, produce: { A: 'max', B: 'max', C: 'max' } }] });
  const r = ML.simulate(w, [{ name: 's', plan: [{ t: 1, produce: { A: 5 } }] }, big('a'), big('b'), big('c'), big('d')]);
  const out = (n) => { const o = r.players.find((p) => p.name === n).outHist[0]; return o.A + o.B + o.C; };
  assert.ok(Math.abs(out('s') - 5) < 1e-9);
  assert.ok(Math.abs(out('a') - (w.raw[0] - 5) / 4) < 1e-9);
  assert.ok(r.players.filter((p) => p.name !== 's').every((p) => p.ticksRationed >= 1));
  assert.ok(r.players.find((p) => p.name === 's').ticksRationed <= 6, 'the modest firm is short only when the pool itself is under 25');
});

test('move 01 of the open round: 10043.55 against steady alone, 16417.54 solo', () => {
  const w = ML.world(SEED);
  const move = JSON.parse(require('node:fs').readFileSync(path.join(__dirname, 'fixtures/market-league-move01.json'), 'utf8'));
  assert.equal(move.name, 'claude-CShmeSe1-01'); assert.equal(move.plan.length, 30);
  const [steady, lean] = ML.baselinePlans(w);
  const duo = ML.simulate(w, [steady, move], { history: false });
  assert.ok(Math.abs(duo.players.find((p) => p.name === move.name).score - 10043.55) < 0.01);
  assert.ok(Math.abs(duo.players.find((p) => p.name === 'steady').score - 9787.08) < 0.01);
  assert.ok(Math.abs(ML.simulate(w, [move], { history: false }).players[0].score - 16417.54) < 0.01);
  const trio = ML.simulate(w, [steady, lean, move], { history: false });
  assert.deepEqual(plain(trio.players.map((p) => p.name)), [move.name, 'steady', 'lean']);
});

test('investment arrives three ticks later at 4 cash per capacity, and capacity decays 2 % a tick', () => {
  const w = ML.world(SEED);
  const r = ML.simulate(w, [{ name: 'i', plan: [{ t: 1, invest: { B: 40 } }, { t: 2 }] }]);
  const cap = r.players[0].capHist.map((c) => c.B);
  assert.ok(Math.abs(cap[2] - 10 * 0.98 ** 3) < 1e-12);
  assert.ok(Math.abs(cap[3] - (10 * 0.98 ** 3 + 10) * 0.98) < 1e-12);
  assert.ok(Math.abs(r.players[0].cashHist[0] - 10) < 1e-12, 'cash 50 minus 40 invested, nothing made');
});

test('the step-function plan: the entry with the largest t ≤ tick applies, and missing goods mean zero', () => {
  const p = ML.parsePlan({ name: 'p', plan: [{ t: 10, produce: { A: 3 } }, { t: 1, produce: { B: 'max' } }] });
  assert.equal(ML.entryAt(p, 1).produce.B, 'max'); assert.equal(ML.entryAt(p, 9).produce.A, 0);
  assert.equal(ML.entryAt(p, 10).produce.A, 3); assert.equal(ML.entryAt(p, 10).produce.B, 0);
  assert.equal(ML.entryAt(p, 48).produce.A, 3);
});

test('the baselines for the open round: steady beats lean head to head and alone, with these scores', () => {
  const w = ML.world(SEED), b = ML.baselinePlans(w);
  assert.equal(b[0].plan.length, 48); assert.equal(b[1].plan.length, 1);
  const duo = ML.simulate(w, b, { history: false });
  const steady = duo.players.find((p) => p.name === 'steady'), lean = duo.players.find((p) => p.name === 'lean');
  assert.ok(Math.abs(steady.score - 15085.33) < 0.01, `steady ${steady.score}`);
  assert.ok(Math.abs(lean.score - 4919.06) < 0.01, `lean ${lean.score}`);
  assert.ok(Math.abs(ML.simulate(w, [b[1]], { history: false }).players[0].score - 8069.63) < 0.01);
  assert.ok(Math.abs(ML.simulate(w, [b[0]], { history: false }).players[0].score - 19366.45) < 0.01);
  assert.equal(duo.players[0].name, 'steady', 'sorted by score');
});

test('plans are validated and names must differ', () => {
  assert.throws(() => ML.parsePlan({ name: 'x', plan: [] }), /non-empty/);
  assert.throws(() => ML.parsePlan({ name: 'x', plan: [{ t: 0 }] }), /integer in/);
  assert.throws(() => ML.parsePlan({ name: 'x', plan: [{ t: 1, produce: { A: 'lots' } }] }), /number ≥ 0 or "max"/);
  assert.throws(() => ML.parsePlan({ name: 'x', plan: Array.from({ length: 49 }, (_, i) => ({ t: 1 })) }), /49 entries/);
  assert.throws(() => ML.simulate(ML.world(SEED), [{ name: 'x', plan: [{ t: 1 }] }, { name: 'x', plan: [{ t: 1 }] }]), /two plans named/);
});

test('the CLI: world, baseline, run and check through main(), without a subprocess', () => {
  const files = { 'lean.json': JSON.stringify(ML.baselinePlans(ML.world(SEED))[1]) };
  const io = () => { const o = { out: [], err: [] }; o.io = { out: (t) => o.out.push(t), err: (t) => o.err.push(t), readFile: (f) => { if (!(f in files)) throw new Error(`no such file ${f}`); return files[f]; } }; return o; };
  let c = io(); assert.equal(cli.main(['world', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out.join('\n')).raw.length, 48);
  c = io(); assert.equal(cli.main(['baseline', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out[0]).length, 2);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'lean.json'], c.io), 0);
  const res = JSON.parse(c.out[0]); assert.ok(Math.abs(res.players[0].score - 8069.63) < 0.01); assert.equal(res.prices, undefined);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'lean.json', '--history'], c.io), 0); assert.equal(JSON.parse(c.out[0]).prices.A.length, 48);
  c = io(); assert.equal(cli.main(['check'], c.io), 0); assert.equal(c.out.length, 9);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'missing.json'], c.io), 1); assert.match(c.err[0], /no such file/);
  c = io(); assert.equal(cli.main(['bogus'], c.io), 1);
  c = io(); assert.equal(cli.main([], c.io), 1); assert.match(c.out[0], /Usage/);
});
