#!/usr/bin/env node
'use strict';
// search3.js — a rigorous apsis-to-apsis search for "18 points in 12 burns" on
// OL-20261005-first. Every leg departs from an apsis with a purely tangential
// burn, coasts half an ellipse and arrives at the other apsis, so the whole plan
// is a chain of (r, theta, vt, t, circular?) states. A circular orbit may wait to
// phase; an elliptical one (left by a free capture) may only depart at once or a
// whole period later. A capture is "free" when the arrival speed is within 0.03 of
// the node's circular speed, so the circularisation burn can be skipped.
//
// The model only *generates* candidate burn lists; every complete 7-node candidate
// is scored by the exact engine (OL.simulate), and only engine scores are reported.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../../made/orbital-league.html'), 'utf8');
const m = html.match(/<script id="ol-engine">([\s\S]*?)<\/script>/);
const ctx = { module: { exports: {} } };
vm.runInNewContext(m[1], ctx, { timeout: 60000 });
const OL = ctx.module.exports;
const MU = OL.MU, TAU = 2 * Math.PI;
const mod = (a, b) => ((a % b) + b) % b;

const SEED = process.argv[2] || 'OL-20261005-first';
const fld = OL.field(SEED);
const R = fld.rules;
const nodeById = Object.fromEntries(fld.nodes.map((n) => [n.id, n]));

function legs(state, node) {
  const wn = Math.sqrt(MU / (node.r * node.r * node.r));
  const a = (state.r + node.r) / 2;
  const vdep = Math.sqrt(MU * (2 / state.r - 1 / a));
  const Th = Math.PI * Math.sqrt(a * a * a / MU);
  const burn = vdep - state.vt;
  const varr = Math.sqrt(MU * (2 / node.r - 1 / a));
  const vcirc = Math.sqrt(MU / node.r);
  const dv2 = vcirc - varr;
  const tds = [];
  if (state.circ) {
    const w = Math.sqrt(MU / (state.r * state.r * state.r));
    const denom = w - wn;
    const rhs = node.phase + wn * Th - state.theta - Math.PI + w * state.t;
    tds.push(state.t + mod(rhs / denom - state.t, Math.abs(TAU / denom)));
  } else {
    const aCur = 1 / (2 / state.r - state.vt * state.vt / MU);
    const P = TAU * Math.sqrt(aCur * aCur * aCur / MU);
    for (let k = 0; k <= 8; k++) {
      const cand = state.t + k * P;
      if (cand > R.T + 1e-9) break;
      const lhs = state.theta + Math.PI;
      const rhs2 = node.phase + wn * (cand + Th);
      if (Math.abs(mod(lhs - rhs2 + Math.PI, TAU) - Math.PI) <= 1e-6) tds.push(cand);
    }
  }
  const out = [];
  for (const td of tds) {
    const thetaDep = state.theta + (state.circ ? Math.sqrt(MU / (state.r * state.r * state.r)) * (td - state.t) : 0);
    const thetaArr = thetaDep + Math.PI;
    const arrive = td + Th;
    if (arrive > R.T + 1e-9) continue;
    out.push({ td, arrive, thetaDep, thetaArr, burn, dv2, varr, vcirc, a, Th });
  }
  return out;
}
const vec = (mag, theta) => [mag * -Math.sin(theta), mag * Math.cos(theta)];

const ids = fld.nodes.map((n) => n.id);
const start = { r: R.start.r, theta: R.start.phase, vt: Math.sqrt(MU / R.start.r), t: 0, circ: true };

const cands = [];
const stats = { legNull: 0, overFuel: 0, overBurns: 0, overTime: 0, leaves: 0, freeUse: 0 };
function dfs(state, remaining, burns, fuel, order, freeSet) {
  if (!remaining.length) {
    stats.leaves++;
    cands.push({ order: order.slice(), free: [...freeSet].sort().join(''), burns: burns.slice(), fuel });
    return;
  }
  for (const id of remaining) {
    const node = nodeById[id];
    const opts = legs(state, node);
    if (!opts.length) { stats.legNull++; continue; }
    const rest = remaining.filter((x) => x !== id);
    for (const L of opts) {
      const freeOK = Math.abs(L.dv2) < R.capSpeed;
      const choices = freeOK ? [true, false] : [false];
      for (const free of choices) {
        const nBurns = burns.length + 1 + (free ? 0 : 1);
        if (nBurns > R.maxBurns) { stats.overBurns++; continue; }
        const nFuel = fuel + Math.abs(L.burn) + (free ? 0 : Math.abs(L.dv2));
        if (nFuel > R.budget + 1e-12) { stats.overFuel++; continue; }
        const b1 = [L.td, ...vec(L.burn, L.thetaDep)];
        const nb = burns.concat([b1]);
        if (!free) nb.push([L.arrive, ...vec(L.dv2, L.thetaArr)]);
        const nstate = free
          ? { r: node.r, theta: L.thetaArr, vt: L.varr, t: L.arrive, circ: false }
          : { r: node.r, theta: L.thetaArr, vt: L.vcirc, t: L.arrive, circ: true };
        if (free) { freeSet.add(id); stats.freeUse++; }
        dfs(nstate, rest, nb, nFuel, order.concat([id]), freeSet);
        if (free) freeSet.delete(id);
      }
    }
  }
}
dfs(start, ids, [], 0, [], new Set());
console.log(`seed ${SEED}: candidates ${cands.length}  stats ${JSON.stringify(stats)}`);

// Score every candidate in the exact engine; keep the best.
let best = null;
const byScore = new Map();
let e18 = [];
for (const c of cands) {
  const plan = { name: 'cand', burns: c.burns.map((b) => [+b[0].toFixed(9), +b[1].toFixed(9), +b[2].toFixed(9)]) };
  let res;
  try { res = OL.simulate(fld, [plan], { paths: false }); } catch (e) { continue; }
  const p = res.players[0];
  if (p.lost) continue;
  byScore.set(p.score, (byScore.get(p.score) || 0) + 1);
  if (p.score >= 18) e18.push({ order: c.order.join(''), free: c.free, burns: p.burns.length, fuel: p.fuelUsed, won: p.won.join(''), plan });
  const key = [p.score, -p.burns.length, -p.fuelUsed];
  const better = !best || key[0] > best.key[0] ||
    (key[0] === best.key[0] && key[1] > best.key[1]) ||
    (key[0] === best.key[0] && key[1] === best.key[1] && key[2] > best.key[2]);
  if (better) best = { key, score: p.score, burns: p.burns.length, fuel: p.fuelUsed, won: p.won.join(''), order: c.order.join(''), free: c.free, plan };
}
console.log('engine score histogram:', JSON.stringify([...byScore.entries()].sort((a, b) => b[0] - a[0])));
if (best) {
  console.log('BEST:', best.score, 'pts,', best.burns, 'burns, fuel', best.fuel.toFixed(4), 'order', best.order, 'free', best.free || '(none)', 'won', best.won);
  console.log(JSON.stringify(best.plan));
} else console.log('no legal plan found');
console.log('18-point plans found:', e18.length);
for (const x of e18.slice(0, 5)) console.log('  18!', x.order, 'free', x.free, x.burns, 'burns', x.fuel.toFixed(4), 'won', x.won);
