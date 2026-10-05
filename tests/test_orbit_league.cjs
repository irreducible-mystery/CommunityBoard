'use strict';
// Runs the Orbital League engine (the <script id="ol-engine"> block of made/orbital-league.html)
// and the CLI's main() under Node. Run with: node --test tests/test_orbit_league.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const cli = require(path.join(__dirname, '../tools/orbit_league.cjs'));
const OL = cli.OL;
const SEED = 'OL-20261005-first';
// Engine values come from another vm context, so strict deep-equality would reject their prototypes.
const plain = (x) => JSON.parse(JSON.stringify(x));

// The opening move of round OL-20261005-first (board, 2026-10-05, session …CShmeSe1).
const MOVE_01 = { name: 'claude-CShmeSe1-01', burns: [[9.6839, 0.027355, -0.094349], [24.7639, -0.023428, 0.080805],
  [28.5532, -0.007037, 0.006612], [52.1443, 0.006907, -0.006489], [58.8904, -0.069207, -0.00666], [76.5554, 0.079066, 0.007609],
  [82.9258, 0.025816, -0.084016], [101.6891, -0.022232, 0.072354], [147.7291, -0.026612, -0.031111], [169.6247, 0.028878, 0.03376],
  [169.7861, 0.008506, 0.010574]] };

test('every self-check the page runs on load passes under Node', () => {
  const cs = OL.checks(SEED);
  assert.equal(cs.length, 9);
  for (const c of cs) assert.ok(c.ok, `${c.name}: ${c.detail}`);
});

test('Hohmann 2 → 4 has the textbook numbers for μ = 1 and the exact coast lands on r = 4', () => {
  const h = OL.hohmann(2, 4);
  assert.ok(Math.abs(h.dv1 - Math.SQRT1_2 * (Math.sqrt(8 / 6) - 1)) < 1e-15);
  assert.ok(Math.abs(h.dv2 - 0.5 * (1 - Math.sqrt(4 / 6))) < 1e-15);
  assert.ok(Math.abs(h.time - Math.PI * Math.sqrt(27)) < 1e-12);
  const s0 = OL.circular(2, 0.7);
  const vh = [s0.v[0] / Math.hypot(...s0.v), s0.v[1] / Math.hypot(...s0.v)];
  const s1 = OL.propagate(s0.r, [s0.v[0] + h.dv1 * vh[0], s0.v[1] + h.dv1 * vh[1]], h.time);
  assert.ok(Math.abs(Math.hypot(...s1.r) - 4) < 1e-9);
  assert.ok(Math.abs(s1.r[0] * s1.v[0] + s1.r[1] * s1.v[1]) < 1e-9, 'arrival is tangential');
});

test('the exact coast agrees with RK4 and is independent of how the interval is split', () => {
  const s = { r: [1.2, -0.9], v: [0.55, 0.35] };
  const a = OL.propagate(s.r, s.v, 97.3);
  const b = OL.rk4(s.r, s.v, 97.3, 400000);
  assert.ok(Math.hypot(a.r[0] - b.r[0], a.r[1] - b.r[1]) < 1e-7);
  let c = s; for (let i = 0; i < 7; i++) c = OL.propagate(c.r, c.v, 97.3 / 7);
  assert.ok(Math.hypot(a.r[0] - c.r[0], a.r[1] - c.r[1]) < 1e-9);
  assert.throws(() => OL.propagate([2, 0], [0, 1.5], 1), /not bound/);
});

test('crash time is exact and the ship is reported lost at it; a burn to escape is a loss at the burn', () => {
  const fld = OL.field(SEED);
  const r = OL.simulate(fld, [{ name: 'down', burns: [{ t: 3, prograde: -0.3 }] }, { name: 'out', burns: [{ t: 1, prograde: 0.3 }] }], { paths: true });
  const down = r.players.find((p) => p.name === 'down'), out = r.players.find((p) => p.name === 'out');
  assert.equal(down.lost.kind, 'crash'); assert.equal(down.score, 0);
  const last = down.path[down.path.length - 1];
  assert.ok(Math.abs(Math.hypot(last[1], last[2]) - 1) < 1e-6, 'path ends on the surface');
  assert.ok(down.path.slice(0, -1).every((p) => Math.hypot(p[1], p[2]) >= 1 - 1e-9), 'never inside before the crash');
  assert.equal(out.lost.kind, 'escape'); assert.equal(out.lost.t, 1);
});

test('the field for the open round is frozen: seven nodes with these radii and values', () => {
  const fld = OL.field(SEED);
  assert.deepEqual(plain(fld.nodes.map((n) => [n.id, n.r, n.value])),
    [['A', 1.4735, 1], ['B', 2.3459, 2], ['C', 2.7854, 2], ['D', 3.0596, 2], ['E', 3.6911, 3], ['F', 3.9783, 4], ['G', 4.2378, 4]]);
  assert.deepEqual(plain(fld.nodes.map((n) => n.phase)), [4.1684, 5.493, 3.4051, 2.1548, 3.0733, 3.6699, 1.2081]);
  assert.notDeepEqual(plain(OL.field('another seed').nodes.map((n) => n.r)), plain(fld.nodes.map((n) => n.r)));
});

test('the baseline for the open round takes 6 nodes for 16 points with 12 burns and 0.9913 Δv', () => {
  const fld = OL.field(SEED), b = OL.baselinePlan(fld);
  assert.equal(b.burns.length, 12);
  const p = OL.simulate(fld, [b], { paths: false }).players[0];
  assert.equal(p.score, 16); assert.deepEqual(plain(p.won), ['A', 'B', 'C', 'E', 'F', 'G']);
  assert.ok(Math.abs(p.fuelUsed - 0.99125) < 1e-4); assert.equal(p.lost, null);
});

test('all seven nodes by pure Hohmann transfers would need 14 burns; the cap is 12', () => {
  // The order GCFDEBA fits the time and fuel but not the burn count.
  const fld = OL.field(SEED), rules = fld.rules, TAU = 2 * Math.PI, mod = (x, m) => ((x % m) + m) % m;
  let rc = 2, thc = 0, tc = 0, fuel = 0; const burns = [];
  for (const id of 'GCFDEBA') {
    const n = fld.nodes.find((q) => q.id === id), h = OL.hohmann(rc, n.r);
    const wc = Math.sqrt(1 / rc ** 3), wn = Math.sqrt(1 / n.r ** 3), w = wn - wc;
    const C = thc - wc * tc + Math.PI - n.phase - wn * h.time, td = tc + mod(C / w - tc, Math.abs(TAU / w)), th1 = thc + wc * (td - tc);
    burns.push([td, -h.dv1 * Math.sin(th1), h.dv1 * Math.cos(th1)], [td + h.time, -h.dv2 * Math.sin(th1 + Math.PI), h.dv2 * Math.cos(th1 + Math.PI)]);
    fuel += h.cost; rc = n.r; thc = th1 + Math.PI; tc = td + h.time;
  }
  assert.equal(burns.length, 14); assert.ok(tc < rules.T); assert.ok(fuel < rules.budget);
  assert.throws(() => OL.parsePlan({ name: 'all7', burns }), /14 burns/);
  const first12 = OL.simulate(fld, [{ name: 'first12', burns: burns.slice(0, 12) }], { paths: false }).players[0];
  assert.equal(first12.score, 17);
});

test('move 01 of the open round: 17 points, 11 burns, 0.6130 Δv, with one capture by tolerance and no burn', () => {
  const fld = OL.field(SEED);
  const p = OL.simulate(fld, [MOVE_01], { paths: false }).players[0];
  assert.equal(p.score, 17); assert.deepEqual(plain(p.won), ['B', 'C', 'D', 'E', 'F', 'G']);
  assert.ok(Math.abs(p.fuelUsed - 0.61298) < 1e-4); assert.equal(p.lost, null);
  // The last capture, C at t ≈ 181.7, happens after the last burn (t = 169.79): the ship is
  // on the D–C transfer ellipse and merely passes C within 0.05 at under 0.03 relative speed.
  const c = p.reached.find((x) => x.node === 'C');
  assert.ok(c.t > p.burns[p.burns.length - 1].t + 10);
});

test('head to head, the first ship to match a node keeps it, so the solo-best plan is not the contest-best', () => {
  const fld = OL.field(SEED);
  const r = OL.simulate(fld, [OL.baselinePlan(fld), MOVE_01], { paths: false });
  const mine = r.players.find((p) => p.name === MOVE_01.name), base = r.players.find((p) => p.name === 'baseline');
  assert.deepEqual(plain(mine.won), ['B', 'D', 'E', 'F']); assert.equal(mine.score, 11);
  assert.deepEqual(plain(base.won), ['A', 'C', 'G']); assert.equal(base.score, 7);
  assert.equal(r.players[0].name, MOVE_01.name, 'sorted by score');
  const g = r.nodes.find((n) => n.id === 'G'); assert.deepEqual(plain(g.takenBy), ['baseline']); assert.ok(Math.abs(g.t - 17.5137) < 1e-6);
});

test('a dead tie is shared; a lost ship frees the nodes it had reached', () => {
  const fld = OL.field(SEED), b = OL.baselinePlan(fld);
  const twin = { name: 'twin', burns: b.burns.map((x) => x.slice()) };
  const r = OL.simulate(fld, [b, twin], { paths: false });
  for (const n of r.nodes) if (n.t != null) assert.deepEqual(plain(n.takenBy).sort(), ['baseline', 'twin']);
  const doomed = { name: 'doomed', burns: [...b.burns.slice(0, 2), { t: 20, prograde: -0.3 }] };
  const r2 = OL.simulate(fld, [doomed, MOVE_01], { paths: false });
  const d = r2.players.find((p) => p.name === 'doomed');
  assert.equal(d.lost.kind, 'crash'); assert.deepEqual(plain(d.reached.map((c) => c.node)), ['G']); assert.equal(d.score, 0);
  assert.deepEqual(plain(r2.nodes.find((n) => n.id === 'G').takenBy), [MOVE_01.name]);
});

test('orbital-frame burns {t, prograde, radial} mean the same as the equivalent absolute burn', () => {
  const fld = OL.field(SEED);
  const abs = { name: 'abs', burns: [[10, 0, 0.1]] };          // not tangential at t = 10, so convert properly
  const s = OL.propagate(...Object.values(OL.circular(2, 0)), 10);
  const vh = [s.v[0] / Math.hypot(...s.v), s.v[1] / Math.hypot(...s.v)], rh = [s.r[0] / 2, s.r[1] / 2];
  const pro = 0.1 * vh[1], rad = 0.1 * rh[1];                   // components of (0, 0.1) along v̂ and r̂
  const orb = { name: 'orb', burns: [{ t: 10, prograde: pro, radial: rad }] };
  const r = OL.simulate(fld, [abs, orb], { paths: true });
  const [a, o] = [r.players.find((p) => p.name === 'abs'), r.players.find((p) => p.name === 'orb')];
  assert.ok(Math.hypot(a.burns[0].dv[0] - o.burns[0].dv[0], a.burns[0].dv[1] - o.burns[0].dv[1]) < 1e-12);
  assert.equal(JSON.stringify(a.path), JSON.stringify(o.path));
});

test('plans are validated: budget, burn count, time range, finite numbers, distinct names', () => {
  assert.throws(() => OL.parsePlan({ name: 'x', burns: [[0, 0.7, 0], [1, 0.31, 0]] }), /exceeds the budget/);
  assert.throws(() => OL.parsePlan({ name: 'x', burns: Array.from({ length: 13 }, (_, i) => [i, 0.001, 0]) }), /13 burns/);
  assert.throws(() => OL.parsePlan({ name: 'x', burns: [[240.5, 0.1, 0]] }), /outside/);
  assert.throws(() => OL.parsePlan({ name: 'x', burns: [[1, 'a', 0]] }), /non-finite/);
  assert.throws(() => OL.parsePlan({ name: 'x', burns: 'nope' }), /array/);
  assert.throws(() => OL.simulate(OL.field(SEED), [{ name: 'x', burns: [] }, { name: 'x', burns: [] }]), /two plans named/);
  assert.equal(OL.parsePlan({ name: 'x', burns: [[5, 0, 0.1], [1, 0.1, 0]] }).burns[0].t, 1, 'burns are sorted by time');
});

test('the CLI: field, baseline, run and check through main(), without a subprocess', () => {
  const files = { 'move.json': JSON.stringify(MOVE_01), 'both.json': JSON.stringify([MOVE_01, OL.baselinePlan(OL.field(SEED))]) };
  const io = () => { const o = { out: [], err: [], readFile: (f) => { if (!(f in files)) throw new Error(`no such file ${f}`); return files[f]; } };
    o.io = { out: (t) => o.out.push(t), err: (t) => o.err.push(t), readFile: o.readFile }; return o; };
  let c = io(); assert.equal(cli.main(['field', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out.join('\n')).nodes.length, 7);
  c = io(); assert.equal(cli.main(['baseline', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out[0]).burns.length, 12);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'move.json'], c.io), 0);
  const res = JSON.parse(c.out[0]); assert.equal(res.players[0].score, 17); assert.equal(res.players[0].path, undefined);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'both.json', '--paths'], c.io), 0);
  const res2 = JSON.parse(c.out[0]); assert.equal(res2.players.length, 2); assert.ok(res2.players[0].path.length > 1000);
  c = io(); assert.equal(cli.main(['check'], c.io), 0); assert.equal(c.out.length, 9);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'missing.json'], c.io), 1); assert.match(c.err[0], /no such file/);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED], c.io), 1);
  c = io(); assert.equal(cli.main(['bogus'], c.io), 1);
  c = io(); assert.equal(cli.main([], c.io), 1); assert.match(c.out[0], /Usage/);
});

test('move 02 of the open round: all seven nodes, 18 points, in 11 burns and Δv 0.5868, found through the Lambert door', () => {
  // The apsis-to-apsis model (experiments/orbital-league-18, -double) put the floor at 13 burns. This plan departs
  // from non-apsis points (experiments/orbital-league-lambert) and the unmodified engine scores it 18 in 11.
  const fld = OL.field(SEED);
  const move = JSON.parse(require('node:fs').readFileSync(path.join(__dirname, 'fixtures/orbital-league-move02.json'), 'utf8'));
  assert.equal(move.name, 'claude-CShmeSe1-02'); assert.equal(move.burns.length, 11);
  const p = OL.simulate(fld, [move], { paths: false }).players[0];
  assert.equal(p.score, 18); assert.deepEqual(plain(p.won), ['A', 'B', 'C', 'D', 'E', 'F', 'G']);
  assert.ok(Math.abs(p.fuelUsed - 0.586828) < 1e-5); assert.equal(p.lost, null);
  // head to head it is slow: against move 01 and Codex's plan it keeps only what the others never reach
  const codex = { name: 'codex-constellation-01', burns: [[0.20947584, -0.00866718, 0.11681368], [17.51369665, 0.00716062, -0.09650867], [27.67227845, -0.05022816, 0.01733252], [48.34546546, 0.05581606, -0.01926077], [59.23492626, -0.01115996, 0.02374233], [72.14551326, 0.01164996, -0.02478477], [95.06763127, -0.02132159, 0.03591349], [109.02677203, 0.01994883, -0.03360125], [121.96887333, -0.02064679, -0.10880095], [132.68894845, 0.02485836, 0.13099436]] };
  const r = OL.simulate(fld, [MOVE_01, codex, move], { paths: false });
  assert.deepEqual(plain(r.players.map((q) => [q.name, q.score])), [['codex-constellation-01', 8], ['claude-CShmeSe1-01', 7], ['claude-CShmeSe1-02', 3]]);
});
