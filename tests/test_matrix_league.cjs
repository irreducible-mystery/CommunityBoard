'use strict';
// Runs the Matrix League engine (the <script id="xl-engine"> block of made/matrix-league.html) and the
// CLI's main() under Node. Run with: node --test tests/test_matrix_league.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const cli = require(path.join(__dirname, '../tools/matrix_league.cjs'));
const XL = cli.XL;
const SEED = 'XL-20261005-first';
const plain = (x) => JSON.parse(JSON.stringify(x));
const one = { ore: 1, grain: 1, salt: 1 };

test('every self-check the page runs on load passes under Node', () => {
  const cs = XL.checks(SEED);
  assert.equal(cs.length, 9);
  for (const c of cs) assert.ok(c.ok, `${c.name}: ${c.detail}`);
});

test('the map for the open round is frozen', () => {
  const m = XL.map(SEED);
  const rows = []; for (let y = 0; y < 5; y++) rows.push(m.cells.filter((c) => c.y === y).map((c) => (c.res ? c.res[0] : '.')).join(''));
  assert.deepEqual(rows, ['gsoog', 'oo.so', 'ossgo', 'sgs.g', 'gogsg']);
  assert.deepEqual(plain(m.counts), { ore: 8, grain: 8, salt: 7 });
  assert.notDeepEqual(plain(XL.map('other').cells), plain(m.cells));
});

test('income, claims, adjacency and payment, step by step', () => {
  const m = XL.map(SEED);
  // NW corner is grain; (1,0) is salt; (2,0) is ore; (2,2) is two steps away
  const r = XL.simulate(m, [{ name: 'p', home: 'NW', plan: [{ t: 1, claims: [{ cell: [2, 2], spend: one }, { cell: [1, 0], spend: one }] }, { t: 2, claims: [{ cell: [2, 0], spend: one }, { cell: [2, 1], spend: one }] }] }]);
  const l = r.log;
  assert.equal(l[0].result, 'rejected'); assert.equal(l[0].why, 'not adjacent');
  assert.equal(l[1].result, 'settled');
  assert.equal(l[2].result, 'rejected'); assert.equal(l[2].why, 'void');   // rejections are logged as they happen, winners after resolution
  assert.equal(l[3].result, 'settled');
  assert.deepEqual(plain(r.frames[0].stock[0]), { ore: 3, grain: 4, salt: 3 });   // 4 each + 1 grain income − 1 each
  assert.deepEqual(plain(r.frames[1].stock[0]), { ore: 2, grain: 4, salt: 3 });   // + grain + salt, − 1 each
  assert.equal(r.players[0].regions, 3);
});

test('score counts complete triples at the end, three points each', () => {
  const m = XL.map(SEED);
  const r = XL.simulate(m, [{ name: 'p', home: 'NW', plan: [] }], { history: false });
  assert.equal(r.players[0].regions, 1);
  assert.deepEqual(plain(r.players[0].stock), { ore: 4, grain: 20, salt: 4 });
  assert.equal(r.players[0].triples, 4); assert.equal(r.players[0].score, 13);
});

test('taking a region needs 2 of each and strictly more neighbours; otherwise it is repelled and the spend is lost', () => {
  let m = null; for (let i = 0; i < 2000 && !m; i++) { const c = XL.map(`check-row-${i}`); const top = c.cells.filter((x) => x.y === 0); if (top.every((x) => x.res) && new Set(top.slice(0, 3).map((x) => x.res)).size === 3 && c.cells.find((x) => x.x === 3 && x.y === 1).res && c.cells.find((x) => x.x === 2 && x.y === 1).res) m = c; }
  const two = { ore: 2, grain: 2, salt: 2 };
  const r = XL.simulate(m, [{ name: 'a', home: 'NW', plan: [{ t: 1, claims: [{ cell: [1, 0], spend: one }] }, { t: 4, claims: [{ cell: [2, 0], spend: one }] }, { t: 9, claims: [{ cell: [3, 0], spend: two }] }, { t: 10, claims: [{ cell: [2, 1], spend: one }] }, { t: 11, claims: [{ cell: [3, 1], spend: one }] }, { t: 13, claims: [{ cell: [3, 0], spend: two }] }] },
    { name: 'b', home: 'NE', plan: [{ t: 1, claims: [{ cell: [3, 0], spend: one }] }] }]);
  const at = (t) => r.log.find((l) => l.t === t && l.kind === 'claim' && l.by === 'a');
  assert.equal(at(9).result, 'repelled');
  assert.equal(at(10).result, 'settled'); assert.equal(at(11).result, 'settled');
  assert.equal(at(13).result, 'taken from b');
  assert.equal(r.players.find((p) => p.name === 'a').repelled, 1);
  assert.equal(r.players.find((p) => p.name === 'b').regions, 1);
});

test('a trade needs its exact mirror in the same tick; open offers match the first mirror in plan order', () => {
  const m = XL.map(SEED);
  const r = XL.simulate(m, [
    { name: 'p', home: 'NW', plan: [{ t: 1, offers: [{ kind: 'trade', with: '*', give: { salt: 1 }, get: { ore: 1 } }] }] },
    { name: 'q', home: 'NE', plan: [{ t: 1, offers: [{ kind: 'trade', with: '*', give: { ore: 1 }, get: { salt: 1 } }] }] },
    { name: 'r', home: 'SE', plan: [{ t: 1, offers: [{ kind: 'trade', with: 'p', give: { ore: 1 }, get: { salt: 1 } }] }, { t: 2, offers: [{ kind: 'trade', with: 'p', give: { ore: 1 }, get: { salt: 1 } }] }] }]);
  const t1 = r.log.filter((l) => l.t === 1 && l.kind === 'trade');
  assert.equal(t1[0].result, 'executed'); assert.equal(t1[0].with, 'q');
  assert.equal(t1[1].result, 'unanswered'); assert.equal(t1[1].by, 'r');
  assert.equal(r.log.find((l) => l.t === 2).result, 'unanswered');
  assert.deepEqual(plain(r.players.find((p) => p.name === 'p').trades), { executed: 1, broken: 0, unanswered: 0 });
});

test('the baselines for the open round are deterministic: settler 76, trader 38, and the settler never answers', () => {
  const m = XL.map(SEED), b = XL.baselinePlans(m);
  assert.deepEqual(plain(b.map((p) => p.home)), ['NW', 'SE']);
  const r = XL.simulate(m, b, { history: false });
  assert.deepEqual(plain(r.players.map((p) => [p.name, p.score, p.regions])), [['settler', 76, 13], ['trader', 38, 5]]);
  assert.equal(r.players.find((p) => p.name === 'trader').trades.unanswered, 16);
  const alt = XL.baselinePlans(m, ['NE', 'SW']);
  assert.deepEqual(plain(alt.map((p) => p.home)), ['NE', 'SW']);
});

test('move 01 of the open round: 155 points from NE against the two baselines, by conquest rather than trade', () => {
  const m = XL.map(SEED);
  const move = JSON.parse(require('node:fs').readFileSync(path.join(__dirname, 'fixtures/matrix-league-move01.json'), 'utf8'));
  assert.equal(move.name, 'claude-CShmeSe1-01'); assert.equal(move.home, 'NE');
  const r = XL.simulate(m, [...XL.baselinePlans(m), move], { history: false });
  const mine = r.players.find((p) => p.name === move.name);
  assert.equal(mine.score, 155); assert.equal(mine.regions, 20); assert.equal(mine.triples, 45);
  assert.equal(mine.trades.executed, 0); assert.equal(mine.betrayals, 0); assert.equal(mine.repelled, 0);
  assert.deepEqual(plain(r.players.map((p) => [p.name, p.score, p.regions])), [[move.name, 155, 20], ['trader', 21, 3], ['settler', 15, 0]]);
  assert.equal(r.players.find((p) => p.name === 'settler').regions, 0, 'the settler loses even its corner');
});

test('plans are validated: homes, ticks, cells, contracts, resources, counts, duplicates', () => {
  assert.throws(() => XL.parsePlan({ name: 'x', home: 'N', plan: [] }), /home must be/);
  assert.throws(() => XL.parsePlan({ name: 'x', home: 'NW', plan: [{ t: 1 }, { t: 1 }] }), /two entries for tick/);
  assert.throws(() => XL.parsePlan({ name: 'x', home: 'NW', plan: [{ t: 1, claims: Array.from({ length: 7 }, () => ({ cell: [1, 0] })) }] }), /7 claims/);
  assert.throws(() => XL.parsePlan({ name: 'x', home: 'NW', plan: [{ t: 1, offers: [{ kind: 'pact', with: 'y', until: 1 }] }] }), /until/);
  assert.throws(() => XL.parsePlan({ name: 'x', home: 'NW', plan: [{ t: 1, claims: [{ cell: [1, 0], spend: { ore: 1.5 } }] }] }), /non-negative integer/);
  assert.throws(() => XL.simulate(XL.map(SEED), [1, 2, 3, 4, 5].map((i) => ({ name: 'p' + i, home: 'NW', plan: [] }))), /5 plans/);
  assert.throws(() => XL.simulate(XL.map(SEED), [{ name: 'p', home: 'NW', plan: [] }, { name: 'q', home: 'NW', plan: [] }]), /already taken/);
});

test('the CLI: map, baseline, run and check through main(), without a subprocess', () => {
  const files = { 'b.json': JSON.stringify(XL.baselinePlans(XL.map(SEED))) };
  const io = () => { const o = { out: [], err: [] }; o.io = { out: (t) => o.out.push(t), err: (t) => o.err.push(t), readFile: (f) => { if (!(f in files)) throw new Error(`no such file ${f}`); return files[f]; } }; return o; };
  let c = io(); assert.equal(cli.main(['map', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out.join('\n')).cells.length, 25);
  c = io(); assert.equal(cli.main(['baseline', '--seed', SEED], c.io), 0); assert.equal(JSON.parse(c.out[0]).length, 2);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'b.json'], c.io), 0);
  const res = JSON.parse(c.out[0]); assert.equal(res.players.length, 2); assert.equal(res.log, undefined);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'b.json', '--log'], c.io), 0); assert.ok(JSON.parse(c.out[0]).log.length > 10);
  c = io(); assert.equal(cli.main(['check'], c.io), 0); assert.equal(c.out.length, 9);
  c = io(); assert.equal(cli.main(['run', '--seed', SEED, 'missing.json'], c.io), 1); assert.match(c.err[0], /no such file/);
  c = io(); assert.equal(cli.main([], c.io), 1); assert.match(c.out[0], /Usage/);
});
