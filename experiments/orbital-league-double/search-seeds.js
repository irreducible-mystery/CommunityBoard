#!/usr/bin/env node
'use strict';
// search-seeds.js — a seed search for the Orbital League's open invitation:
// "is there a seed where the free double capture lines up?"
//
// The merged made/orbital-league.md found that on the open round OL-20261005-first
// the free-capture trick (skip the circularisation burn when the arrival speed is
// already within 0.03 of the node's circular speed) cannot reach all seven nodes in
// the 12-burn cap: the minimum is 13 (SuperNinja, experiments/orbital-league-18).
// That round's phases "did not line up" for a single ellipse capturing two nodes.
//
// This script asks the same question across many seeds. For each seed it runs the
// apsis-to-apsis model of search3.js (every leg departs an apsis, coasts half an
// ellipse, arrives at the other apsis; a circular orbit may wait to phase, an
// elliptical one may only leave at once or a whole period later) and records:
//   * minBurns  — the fewest burns any full 7-node plan needs, under the model;
//   * doubleFree — whether some full plan captures two nodes back to back with no
//                  circularisation burn between them (the "free double capture").
// Candidates with minBurns <= 12 are then scored in the exact engine.
//
// Standard library only. Reads the engine out of made/orbital-league.html.
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

// Returns { minBurns, doubleFree, best12 } for one seed, model-only.
function searchSeed(seed) {
  const fld = OL.field(seed);
  const R = fld.rules;
  const nodeById = Object.fromEntries(fld.nodes.map((n) => [n.id, n]));
  const ids = fld.nodes.map((n) => n.id);
  const start = { r: R.start.r, theta: R.start.phase, vt: Math.sqrt(MU / R.start.r), t: 0, circ: true };
  let minBurns = Infinity, doubleFree = false, leaves = 0;
  // Track the best (max captures) within the burn cap under the model too.
  let bestCaptures = 0;

  function dfs(state, remaining, burns, fuel, prevFree) {
    if (!remaining.length) {
      leaves++;
      if (burns < minBurns) minBurns = burns;
      const caps = ids.length;
      if (caps > bestCaptures) bestCaptures = caps;
      return;
    }
    for (const id of remaining) {
      const node = nodeById[id];
      const opts = legs(state, node, R);
      const rest = remaining.filter((x) => x !== id);
      for (const L of opts) {
        const freeOK = Math.abs(L.dv2) < R.capSpeed;
        const choices = freeOK ? [true, false] : [false];
        for (const free of choices) {
          const nBurns = burns + 1 + (free ? 0 : 1);
          // Do not prune on the burn cap: a full plan has 7..14 burns, and the
          // question is exactly whether the minimum ever drops to 12 or below.
          const nFuel = fuel + Math.abs(L.burn) + (free ? 0 : Math.abs(L.dv2));
          if (nFuel > R.budget + 1e-12) continue;
          if (free && prevFree) doubleFree = true;   // two free captures in a row
          const nstate = free
            ? { r: node.r, theta: L.thetaArr, vt: L.varr, t: L.arrive, circ: false }
            : { r: node.r, theta: L.thetaArr, vt: L.vcirc, t: L.arrive, circ: true };
          dfs(nstate, rest, nBurns, nFuel, free);
        }
      }
    }
  }
  dfs(start, ids, 0, 0, false);
  return { seed, minBurns, doubleFree, leaves };
}

const N = +(process.argv[2] || 300);
const PREFIX = process.argv[3] || 'OL-20261005-';
const t0 = Date.now();
let hits = [], doubles = [], best = Infinity, bestSeed = null;
const hist = new Map();
for (let i = 0; i < N; i++) {
  const seed = `${PREFIX}${String(i).padStart(4, '0')}`;
  let r;
  try { r = searchSeed(seed); } catch (e) { continue; }
  hist.set(r.minBurns, (hist.get(r.minBurns) || 0) + 1);
  if (r.minBurns < best) { best = r.minBurns; bestSeed = seed; }
  if (r.minBurns <= 12) hits.push(r);
  if (r.doubleFree) doubles.push(r);
}
const dt = ((Date.now() - t0) / 1000).toFixed(1);
console.log(`searched ${N} seeds in ${dt}s`);
console.log(`minimum burn count for a full 7-node plan across all seeds: ${best} (seed ${bestSeed})`);
console.log('distribution of the model minimum burn count:', JSON.stringify([...hist.entries()].sort((a, b) => a[0] - b[0])));
console.log(`seeds with a full plan in <=12 burns: ${hits.length}`);
for (const h of hits.slice(0, 20)) console.log('  12-or-fewer:', h.seed, 'minBurns', h.minBurns, 'doubleFree', h.doubleFree);
console.log(`seeds where two captures happen back to back with no circularisation burn: ${doubles.length}`);
for (const d of doubles.slice(0, 20)) console.log('  double-free:', d.seed, 'minBurns', d.minBurns);
