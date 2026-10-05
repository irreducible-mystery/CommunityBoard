#!/usr/bin/env node
'use strict';
// test.js — validates lambert.js against the Orbital League engine (the truth for coasts).
//   node experiments/orbital-league-lambert/test.js        exits 1 on any failure
const path = require('node:path');
const { OL } = require(path.join(__dirname, '../../tools/orbit_league.cjs'));
const { lambert } = require(path.join(__dirname, 'lambert.js'));
const MU = 1, TAU = 2 * Math.PI;
let failures = 0;
const report = (name, ok, detail) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name} — ${detail}`); if (!ok) failures++; };

// 1. Hohmann 2 -> 4: a 180-degree transfer, so it exercises the degenerate branch.
{
  const h = OL.hohmann(2, 4);
  const r1 = [2, 0], r2 = [-4, 0];
  const sol = lambert(r1, r2, h.time);
  const vc1 = Math.sqrt(MU / 2), vc2 = Math.sqrt(MU / 4);
  const dv1 = Math.hypot(sol.v1[0] - 0, sol.v1[1] - vc1);          // circular velocity at r1 is (0, vc1)
  const dv2 = Math.hypot(0 - sol.v2[0], -vc2 - sol.v2[1]);         // circular velocity at r2 is (0, -vc2)
  const err = Math.max(Math.abs(dv1 - h.dv1), Math.abs(dv2 - h.dv2));
  report('Hohmann 2->4 reproduces the textbook dv1, dv2', err < 1e-9,
    `dv1 ${dv1.toFixed(12)} vs ${h.dv1.toFixed(12)}, dv2 ${dv2.toFixed(12)} vs ${h.dv2.toFixed(12)}, max err ${err.toExponential(2)}`);
  // the transfer really lands on r = 4 (propagate with the engine)
  const end = OL.propagate(r1, sol.v1, h.time);
  report('Hohmann 2->4 Lambert arc lands at r2 (engine propagate)', Math.hypot(end.r[0] - r2[0], end.r[1] - r2[1]) < 1e-9 && Math.hypot(end.v[0] - sol.v2[0], end.v[1] - sol.v2[1]) < 1e-9,
    `position error ${Math.hypot(end.r[0] - r2[0], end.r[1] - r2[1]).toExponential(2)}, v2 error ${Math.hypot(end.v[0] - sol.v2[0], end.v[1] - sol.v2[1]).toExponential(2)}`);
}

// 2. Random bound states: propagate with the engine, then Lambert between the endpoints.
{
  const rnd = OL.rng('lambert-test', 'states');
  let worstV = 0, worstCase = null, n = 0, nulls = 0, nearPi = 0;
  for (let i = 0; i < 2000; i++) {
    const R = 1.2 + 4 * rnd(), th = TAU * rnd();
    const c = OL.circular(R, th);
    const v = [c.v[0] * (0.8 + 0.4 * rnd()) + 0.2 * (rnd() - 0.5), c.v[1] * (0.8 + 0.4 * rnd()) + 0.2 * (rnd() - 0.5)];
    const el = OL.elements(c.r, v);
    if (!el.bound || el.rp < 1.05) continue;
    const dt = el.period * (0.02 + 0.96 * rnd());               // zero revolutions
    const end = OL.propagate(c.r, v, dt);
    const sol = lambert(c.r, end.r, dt);
    if (!sol) { nulls++; continue; }
    n++;
    if (Math.abs(Math.sin(sol.dnu)) < 1e-3) nearPi++;
    const e1 = Math.hypot(sol.v1[0] - v[0], sol.v1[1] - v[1]), e2 = Math.hypot(sol.v2[0] - end.v[0], sol.v2[1] - end.v[1]);
    const e = Math.max(e1, e2);
    if (e > worstV) { worstV = e; worstCase = { R: +R.toFixed(3), e: +el.e.toFixed(3), dt: +dt.toFixed(3), dnu: +sol.dnu.toFixed(4) }; }
  }
  report(`random bound states round-trip (${n} cases, ${nulls} unsolved)`, worstV < 1e-8 && nulls === 0 && n > 1500,
    `worst velocity error ${worstV.toExponential(2)} at ${JSON.stringify(worstCase)}; ${nearPi} within 1e-3 of 180 degrees`);
}

// 3. Transfers at exactly and almost 180 degrees, off-apsis (both branches, same answer).
{
  const r1 = [2.5, 0];
  const c = OL.circular(2.5, 0);
  const v = [0.12, c.v[1] * 1.05];                                  // off-apsis departure
  const el = OL.elements(r1, v);
  // find the time at which the true anomaly has advanced by exactly pi: bisection on angle
  let lo = 0, hi = el.period * 0.9;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2, p = OL.propagate(r1, v, mid);
    const ang = ((Math.atan2(p.r[1], p.r[0]) % TAU) + TAU) % TAU;
    if (ang < Math.PI) lo = mid; else hi = mid;
  }
  const tPi = (lo + hi) / 2, end = OL.propagate(r1, v, tPi);
  const exact = lambert(r1, [-Math.hypot(end.r[0], end.r[1]), 0], tPi);
  const eExact = Math.hypot(exact.v1[0] - v[0], exact.v1[1] - v[1]);
  const end2 = OL.propagate(r1, v, tPi + 0.002), near = lambert(r1, end2.r, tPi + 0.002);
  const eNear = Math.hypot(near.v1[0] - v[0], near.v1[1] - v[1]);
  report('180-degree off-apsis transfer, degenerate branch', eExact < 1e-8, `v1 error ${eExact.toExponential(2)} (sin dnu = ${Math.sin(exact.dnu).toExponential(1)})`);
  report('almost-180-degree transfer, general branch', eNear < 1e-8, `v1 error ${eNear.toExponential(2)} (sin dnu = ${Math.sin(near.dnu).toExponential(1)})`);
}

// 4. Warm start gives the same answer as the cold solve.
{
  const a = lambert([2, 0.3], [-1.5, 2.8], 9.0);
  const b = lambert([2, 0.3], [-1.5, 2.8], 9.2);
  const c = lambert([2, 0.3], [-1.5, 2.8], 9.2, a.z);
  report('warm-started Newton matches cold bisection', Math.hypot(b.v1[0] - c.v1[0], b.v1[1] - c.v1[1]) < 1e-11, `difference ${Math.hypot(b.v1[0] - c.v1[0], b.v1[1] - c.v1[1]).toExponential(2)}`);
}

console.log(failures ? `${failures} failure(s)` : 'all passed');
process.exitCode = failures ? 1 : 0;
