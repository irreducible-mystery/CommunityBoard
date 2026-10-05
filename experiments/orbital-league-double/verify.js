#!/usr/bin/env node
'use strict';
// verify.js — for a given seed, find the model's minimum-burn full plan, then score
// it in the exact engine with the burn cap raised, to show the model is not just
// counting burns: the plan really captures all seven nodes.
//
//   node experiments/orbital-league-double/verify.js OL-20261005-0000
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

function legs(state, node, R) {
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
    out.push({ td, arrive, thetaDep, thetaArr, burn, dv2, varr, vcirc });
  }
  return out;
}
const vec = (mag, theta) => [mag * -Math.sin(theta), mag * Math.cos(theta)];

const SEED = process.argv[2] || 'OL-20261005-0000';
const fld = OL.field(SEED);
const R = fld.rules;
const nodeById = Object.fromEntries(fld.nodes.map((n) => [n.id, n]));
const ids = fld.nodes.map((n) => n.id);
const start = { r: R.start.r, theta: R.start.phase, vt: Math.sqrt(MU / R.start.r), t: 0, circ: true };

let best = null;
function dfs(state, remaining, burns, fuel, order) {
  if (!remaining.length) {
    if (!best || burns.length < best.burns.length) best = { burns: burns.slice(), fuel, order: order.slice() };
    return;
  }
  for (const id of remaining) {
    const node = nodeById[id];
    const opts = legs(state, node, R);
    const rest = remaining.filter((x) => x !== id);
    for (const L of opts) {
      const freeOK = Math.abs(L.dv2) < R.capSpeed;
      for (const free of freeOK ? [true, false] : [false]) {
        const nFuel = fuel + Math.abs(L.burn) + (free ? 0 : Math.abs(L.dv2));
        if (nFuel > R.budget + 1e-12) continue;
        const nb = burns.concat([[L.td, ...vec(L.burn, L.thetaDep)]]);
        if (!free) nb.push([L.arrive, ...vec(L.dv2, L.thetaArr)]);
        const nstate = free
          ? { r: node.r, theta: L.thetaArr, vt: L.varr, t: L.arrive, circ: false }
          : { r: node.r, theta: L.thetaArr, vt: L.vcirc, t: L.arrive, circ: true };
        dfs(nstate, rest, nb, nFuel, order.concat([id]));
      }
    }
  }
}
dfs(start, ids, [], 0, []);
if (!best) { console.log(`seed ${SEED}: no full plan under the model`); process.exit(0); }
const plan = { name: `seed-search-${SEED}`, burns: best.burns.map((b) => [+b[0].toFixed(9), +b[1].toFixed(9), +b[2].toFixed(9)]) };
console.log(`seed ${SEED}: model order ${best.order.join('')}, ${plan.burns.length} burns, dv ${best.fuel.toFixed(4)}`);
const fldRaised = { ...fld, rules: { ...R, maxBurns: plan.burns.length } };
const res = OL.simulate(fldRaised, [plan], { paths: false });
const p = res.players[0];
console.log(`engine (cap ${plan.burns.length}): score ${p.score} of 18, won ${p.won.join('')}, lost ${p.lost ? p.lost.kind : 'no'}, dv ${p.fuelUsed.toFixed(4)}`);
console.log(`captures: ${p.reached.map((r) => `${r.node}@${r.t}`).join('  ')}`);
console.log(JSON.stringify(plan));
