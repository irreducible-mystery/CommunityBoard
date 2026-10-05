#!/usr/bin/env node
'use strict';
// search.js — looks for a 12-burn, 18-point plan on OL-20261005-first when legs may be
// general Lambert transfers (departing from any point of the current coast, not only an
// apsis). The model only generates candidates; every plan reported is scored by the
// exact engine (OL.simulate), which is the truth.
//
//   node experiments/orbital-league-lambert/search.js [--seed S] [--states N] [--seconds S]
//
// Each leg from the ship's state to a node is a pair (tau, tof): wait tau on the current
// coast, burn onto the Lambert arc that meets the node after tof, and either (a) arrive
// within FREE of the node's velocity (a free capture: one burn, ship left on the arc) or
// (b) arrive with mismatch below mismatchMax and match it with a second burn (ship then
// circular, so it can phase for the next leg). The phased Hohmann departure is added to
// the (tau, tof) grid explicitly, so the apsis-to-apsis chains of the earlier search are
// a subset of what is tried here.
const fs = require('node:fs');
const path = require('node:path');
const { OL } = require(path.join(__dirname, '../../tools/orbit_league.cjs'));
const { lambert } = require(path.join(__dirname, 'lambert.js'));
const MU = 1, TAU = 2 * Math.PI;
const mod = (a, b) => ((a % b) + b) % b;
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const SEED = opt('--seed', 'OL-20261005-first');
const CFG = {
  tauMax: 60, tauStep: 2,          // departure delay grid on the current coast (time units)
  tofMin: 2, tofMax: 60, tofStep: 1, // time-of-flight grid
  mismatchMax: 0.2,                // arrival mismatch allowed for a two-burn (matched) arrival
  keepFree: 4, keepTwo: 3,         // Pareto-thinned legs kept per node per arrival type
  rpMin: 1.1,                      // transfer periapsis must stay above the body (radius 1)
  domT: 1.0, domFuel: 0.005,       // dominance slack: a state is dropped if an earlier one is at most this later / costlier
  ellipseSlack: 0.03,              // extra fuel margin required before dropping a non-circular state
  maxStates: +opt('--states', 6000), maxSeconds: +opt('--seconds', 420),
};
const fld = OL.field(SEED), R = fld.rules;
const FREE = R.capSpeed * 0.9;
const byId = Object.fromEntries(fld.nodes.map((n) => [n.id, n]));
const bit = Object.fromEntries(fld.nodes.map((n, i) => [n.id, 1 << i]));
const FULL = (1 << fld.nodes.length) - 1;
const t0 = Date.now();
const stats = { states: 0, lambert: 0, freeLegs: 0, freeLambertLegs: 0, twoLegs: 0, verified: 0, dominated: 0, stopped: false };

// Candidate legs from `st` to `node`: returns options sorted free-first then by arrival time.
function legOptions(st, node) {
  const wn = Math.sqrt(MU / (node.r ** 3));
  const pairs = [];
  if (st.circ) {                                    // phased Hohmann departures (first two windows)
    const rs = Math.hypot(st.r[0], st.r[1]), ws = Math.sqrt(MU / (rs ** 3)), ths = Math.atan2(st.r[1], st.r[0]);
    const Th = Math.PI * Math.sqrt(((rs + node.r) / 2) ** 3 / MU);
    const C = node.phase + wn * (st.t + Th) - ths - Math.PI, w = ws - wn, syn = Math.abs(TAU / w);
    const tau = mod(C / w, syn);
    pairs.push([tau, Th, true], [tau + syn, Th, true]);
  }
  for (let tau = 0; tau <= CFG.tauMax; tau += CFG.tauStep) for (let tof = CFG.tofMin; tof <= CFG.tofMax; tof += CFG.tofStep) pairs.push([tau, tof, false]);
  const free = [], two = [];
  let lastTau = null, dep = null, z;
  for (const [tau, tof, hoh] of pairs) {
    const tDep = st.t + tau, tArr = tDep + tof;
    if (tArr > R.T) continue;
    if (tau !== lastTau) { dep = OL.propagate(st.r, st.v, tau); lastTau = tau; z = undefined; }
    const ns = OL.nodeState(node, tArr);
    const sol = lambert(dep.r, ns.r, tof, hoh ? undefined : z);
    stats.lambert++;
    if (!sol) continue;
    z = sol.z;
    const dv1 = [sol.v1[0] - dep.v[0], sol.v1[1] - dep.v[1]], c1 = Math.hypot(dv1[0], dv1[1]);
    const mis = Math.hypot(sol.v2[0] - ns.v[0], sol.v2[1] - ns.v[1]);
    if (mis >= CFG.mismatchMax && mis >= FREE) continue;
    const el = OL.elements(dep.r, sol.v1);
    if (!el.bound || el.rp < CFG.rpMin) continue;
    const base = { tau, tof, tDep, tArr, dv1, c1, mis, hoh, v2: sol.v2, ns };
    if (mis < FREE) { free.push({ ...base, free: true, cost: c1, nb: 1 }); stats.freeLegs++; if (!hoh) stats.freeLambertLegs++; }
    two.push({ ...base, free: false, cost: c1 + mis, nb: 2 }); stats.twoLegs++;
  }
  return pareto(free, CFG.keepFree).concat(pareto(two, CFG.keepTwo));
}
// Keep the (tArr, cost) Pareto front, thinned to at most k legs spread along it.
function pareto(legs, k) {
  legs.sort((a, b) => a.tArr - b.tArr || a.cost - b.cost);
  const front = [];
  let best = Infinity;
  for (const L of legs) if (L.cost < best - 1e-12) { front.push(L); best = L.cost; }
  if (front.length <= k) return front;
  const out = [];
  for (let i = 0; i < k; i++) out.push(front[Math.round(i * (front.length - 1) / (k - 1))]);
  return out;
}

const memo = new Map();
function dominated(key, t, fuel, nb, circ) {
  const slack = circ ? 0 : CFG.ellipseSlack;
  let list = memo.get(key);
  if (!list) { list = []; memo.set(key, list); }
  for (const s of list) if (s.t <= t + CFG.domT && s.fuel + slack <= fuel + CFG.domFuel && s.nb <= nb) return true;
  list.push({ t, fuel, nb });
  return false;
}

let best = { score: -1, nb: 99, fuel: 9, plan: null, order: '', won: '' };
const found18 = [];
function verify(st) {
  stats.verified++;
  const plan = { name: 'claude-lambert', burns: st.burns.map((b) => [+b[0].toFixed(9), +b[1].toFixed(9), +b[2].toFixed(9)]) };
  let p;
  try { p = OL.simulate(fld, [plan], { paths: false }).players[0]; } catch (e) { return; }
  if (p.lost) return;
  const better = p.score > best.score || (p.score === best.score && (p.burns.length < best.nb || (p.burns.length === best.nb && p.fuelUsed < best.fuel)));
  if (better) {
    best = { score: p.score, nb: p.burns.length, fuel: p.fuelUsed, plan, order: st.order, won: p.won.join(''), legs: st.legs };
    console.log(`  verified ${p.score} pts, ${p.burns.length} burns, dv ${p.fuelUsed.toFixed(4)}, order ${st.order}, won ${p.won.join('')}, legs ${st.legs}  [${((Date.now() - t0) / 1000).toFixed(0)}s]`);
  }
  if (p.score >= 18 && p.burns.length <= R.maxBurns) found18.push({ plan, order: st.order, nb: p.burns.length, fuel: p.fuelUsed, legs: st.legs });
}

function dfs(st) {
  if (stats.stopped) return;
  if (++stats.states > CFG.maxStates || (Date.now() - t0) / 1000 > CFG.maxSeconds) { stats.stopped = true; return; }
  if (st.score >= best.score) verify(st);
  if (st.mask === FULL) return;
  const remaining = fld.nodes.filter((n) => !(st.mask & bit[n.id]));
  if (st.burns.length + remaining.length > R.maxBurns) return;
  for (const node of remaining) {
    for (const L of legOptions(st, node)) {
      const nb = st.burns.length + L.nb;
      if (nb + remaining.length - 1 > R.maxBurns) continue;
      const fuel = st.fuel + L.cost;
      if (fuel > R.budget - 1e-9) continue;
      const burns = st.burns.concat([[L.tDep, L.dv1[0], L.dv1[1]]]);
      if (!L.free) burns.push([L.tArr, L.ns.v[0] - L.v2[0], L.ns.v[1] - L.v2[1]]);
      const child = {
        t: L.tArr, r: L.ns.r, v: L.free ? L.v2 : L.ns.v, circ: !L.free, mask: st.mask | bit[node.id],
        burns, fuel, score: st.score + node.value, order: st.order + node.id,
        legs: st.legs + (st.legs ? ' ' : '') + `${node.id}:${L.hoh ? 'H' : 'L'}${L.free ? 'f' : ''}@${L.tDep.toFixed(1)}+${L.tof.toFixed(1)}`,
      };
      if (dominated(`${child.mask}|${node.id}|${child.circ}`, child.t, fuel, nb, child.circ)) { stats.dominated++; continue; }
      dfs(child);
      if (stats.stopped) return;
    }
  }
}

const start = OL.circular(R.start.r, R.start.phase);
console.log(`seed ${SEED}; grid tau 0..${CFG.tauMax} step ${CFG.tauStep}, tof ${CFG.tofMin}..${CFG.tofMax} step ${CFG.tofStep}; free capture < ${FREE.toFixed(3)}; limits ${CFG.maxStates} states / ${CFG.maxSeconds}s`);
dfs({ t: 0, r: start.r, v: start.v, circ: true, mask: 0, burns: [], fuel: 0, score: 0, order: '', legs: '' });
const secs = (Date.now() - t0) / 1000;
console.log(`\n${stats.stopped ? 'STOPPED at the limit' : 'search exhausted'} after ${secs.toFixed(1)}s: ${stats.states} states, ${stats.lambert} Lambert solves, ${stats.dominated} dominated, ${stats.verified} engine runs`);
console.log(`legs generated: ${stats.freeLegs} free-capture (${stats.freeLambertLegs} of them non-Hohmann Lambert), ${stats.twoLegs} two-burn`);
console.log(`BEST verified within ${R.maxBurns} burns: ${best.score} pts, ${best.nb} burns, dv ${best.fuel.toFixed(4)}, order ${best.order}, won ${best.won}`);
console.log(`  legs: ${best.legs}`);
console.log(JSON.stringify(best.plan));
console.log(`18-point plans within ${R.maxBurns} burns: ${found18.length}`);
if (found18.length) {
  found18.sort((a, b) => a.nb - b.nb || a.fuel - b.fuel);
  const p = { name: 'claude-CShmeSe1-02', burns: found18[0].plan.burns };
  fs.writeFileSync(path.join(__dirname, 'claude-18-in-12.json'), JSON.stringify(p) + '\n');
  console.log(`saved claude-18-in-12.json (order ${found18[0].order}, ${found18[0].nb} burns, dv ${found18[0].fuel.toFixed(4)}; legs ${found18[0].legs})`);
}
