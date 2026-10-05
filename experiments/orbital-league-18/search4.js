#!/usr/bin/env node
'use strict';
// search4.js — exhaustive check: build every apsis-model prefix plan (any length)
// and score each in the exact engine, looking for ANY plan that reaches 18 within
// the 12-burn cap (including nodes captured as bonuses during a coast).
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

let best = null, e18 = [], count = 0;
const hist = new Map();
function score(burns, order, free) {
  if (!burns.length) return;
  const plan = { name: 'c', burns: burns.map((b) => [+b[0].toFixed(9), +b[1].toFixed(9), +b[2].toFixed(9)]) };
  let res;
  try { res = OL.simulate(fld, [plan], { paths: false }); } catch (e) { return; }
  const p = res.players[0];
  if (p.lost) return;
  count++;
  hist.set(p.score, (hist.get(p.score) || 0) + 1);
  if (p.score >= 18) e18.push({ order: order.join(''), free: [...free].sort().join(''), burns: p.burns.length, fuel: p.fuelUsed, won: p.won.join(''), plan });
  const key = [p.score, -p.burns.length, -p.fuelUsed];
  const better = !best || key[0] > best.key[0] ||
    (key[0] === best.key[0] && key[1] > best.key[1]) ||
    (key[0] === best.key[0] && key[1] === best.key[1] && key[2] > best.key[2]);
  if (better) best = { key, score: p.score, burns: p.burns.length, fuel: p.fuelUsed, won: p.won.join(''), order: order.join(''), free: [...free].sort().join('') };
}
function dfs(state, remaining, burns, fuel, order, freeSet) {
  for (const id of remaining) {
    const node = nodeById[id];
    const opts = legs(state, node);
    const rest = remaining.filter((x) => x !== id);
    for (const L of opts) {
      const freeOK = Math.abs(L.dv2) < R.capSpeed;
      for (const free of (freeOK ? [true, false] : [false])) {
        const nBurns = burns.length + 1 + (free ? 0 : 1);
        if (nBurns > R.maxBurns) continue;
        const nFuel = fuel + Math.abs(L.burn) + (free ? 0 : Math.abs(L.dv2));
        if (nFuel > R.budget + 1e-12) continue;
        const nb = burns.concat([[L.td, ...vec(L.burn, L.thetaDep)]]);
        if (!free) nb.push([L.arrive, ...vec(L.dv2, L.thetaArr)]);
        const nstate = free
          ? { r: node.r, theta: L.thetaArr, vt: L.varr, t: L.arrive, circ: false }
          : { r: node.r, theta: L.thetaArr, vt: L.vcirc, t: L.arrive, circ: true };
        if (free) freeSet.add(id);
        const norder = order.concat([id]);
        score(nb, norder, freeSet);
        dfs(nstate, rest, nb, nFuel, norder, freeSet);
        if (free) freeSet.delete(id);
      }
    }
  }
}
dfs(start, ids, [], 0, [], new Set());
console.log(`seed ${SEED}: scored ${count} legal prefix plans`);
console.log('score histogram:', JSON.stringify([...hist.entries()].sort((a, b) => b[0] - a[0])));
if (best) console.log('BEST within 12 burns:', best.score, 'pts,', best.burns, 'burns, fuel', best.fuel.toFixed(4), 'order', best.order, 'free', best.free || '(none)', 'won', best.won);
console.log('18-point plans within 12 burns:', e18.length);
for (const x of e18.slice(0, 5)) console.log('  18!', x.order, 'free', x.free, x.burns, 'burns', x.fuel.toFixed(4), 'won', x.won);
