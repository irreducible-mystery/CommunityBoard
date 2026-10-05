'use strict';
// lambert.js — a 2D Lambert solver for mu = 1 (Bate–Mueller–White universal variables,
// Vallado algorithm 58). Prograde (counter-clockwise) transfers only, zero revolutions:
// the transfer angle is taken in [0, 2pi) counter-clockwise from r1 to r2, so both the
// short way (< pi) and the long way (> pi) are covered, as long as the ship does not
// complete a full lap. Standard library only.
//
//   lambert(r1, r2, tof, z0?)  ->  { v1, v2, z } or null
//
// z is the universal variable (z = dE^2 on an ellipse); passing the z of a nearby solved
// problem as z0 warm-starts a Newton iteration, and the bisection below is the fallback.
const MU = 1;
const TAU = 2 * Math.PI;
const Z_LO = -100, Z_HI = TAU * TAU - 1e-9;   // z -> 4pi^2 is tof -> infinity (one lap)

function stumpff(z) {
  if (z > 1e-6) { const s = Math.sqrt(z); return { C: (1 - Math.cos(s)) / z, S: (s - Math.sin(s)) / (s * s * s) }; }
  if (z < -1e-6) { const s = Math.sqrt(-z); return { C: (1 - Math.cosh(s)) / z, S: (Math.sinh(s) - s) / (s * s * s) }; }
  return { C: 0.5 - z / 24 + z * z / 720, S: 1 / 6 - z / 120 + z * z / 5040 };
}

// Time of flight as a function of z for fixed geometry; NaN where y < 0 (z too small).
function tofOf(z, r1n, r2n, A) {
  const { C, S } = stumpff(z);
  const y = r1n + r2n + A * (z * S - 1) / Math.sqrt(C);
  if (!(y > 0)) return { t: NaN, y, C, S };
  const x = Math.sqrt(y / C);
  return { t: (x * x * x * S + A * Math.sqrt(y)) / Math.sqrt(MU), y, C, S };
}

function solveZ(tof, r1n, r2n, A, z0) {
  const tol = 1e-13 * tof;
  // Newton from a warm start (numerical derivative), inside the bracket.
  if (Number.isFinite(z0) && z0 > Z_LO && z0 < Z_HI) {
    let z = z0;
    for (let i = 0; i < 12; i++) {
      const f = tofOf(z, r1n, r2n, A).t;
      if (!Number.isFinite(f)) break;
      if (Math.abs(f - tof) < tol) return z;
      const h = 1e-7 * Math.max(1, Math.abs(z));
      const f2 = tofOf(z + h, r1n, r2n, A).t;
      if (!Number.isFinite(f2) || f2 === f) break;
      const zn = z - (f - tof) * h / (f2 - f);
      if (!(zn > Z_LO && zn < Z_HI)) break;
      if (Math.abs(zn - z) < 1e-15 * Math.max(1, Math.abs(z))) { z = zn; break; }
      z = zn;
    }
    const f = tofOf(z, r1n, r2n, A).t;
    if (Number.isFinite(f) && Math.abs(f - tof) < 1e-11 * tof) return z;
  }
  // Bisection: tof(z) is monotone increasing on the zero-revolution branch.
  let lo = Z_LO, hi = Z_HI;
  if (tofOf(hi, r1n, r2n, A).t < tof) return NaN;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (mid === lo || mid === hi) return mid;
    const f = tofOf(mid, r1n, r2n, A).t;
    if (!Number.isFinite(f) || f < tof) lo = mid; else hi = mid;
    if (Number.isFinite(f) && Math.abs(f - tof) < tol) return mid;
  }
  return (lo + hi) / 2;
}

function lambert(r1, r2, tof, z0) {
  if (!(tof > 0)) return null;
  const r1n = Math.hypot(r1[0], r1[1]), r2n = Math.hypot(r2[0], r2[1]);
  const cross = r1[0] * r2[1] - r1[1] * r2[0], dotp = r1[0] * r2[0] + r1[1] * r2[1];
  const dnu = ((Math.atan2(cross, dotp) % TAU) + TAU) % TAU;         // prograde transfer angle
  const cosd = dotp / (r1n * r2n), sind = cross / (r1n * r2n);
  if (1 - cosd < 1e-12) return null;                                   // r1 and r2 on the same ray
  const A = sind * Math.sqrt(r1n * r2n / (1 - cosd));
  const z = solveZ(tof, r1n, r2n, A, z0);
  if (!Number.isFinite(z)) return null;
  const { y } = tofOf(z, r1n, r2n, A);
  if (!(y > 0)) return null;
  let v1, v2;
  if (Math.abs(sind) < 1e-8) {
    // 180-degree transfer: the f and g form divides by g -> 0. In two dimensions the prograde
    // solution is still unique; build it from the eccentric anomalies. With d = dE/2:
    //   r1 + r2 = 2a sin^2 d,   e sin m = (r2 - r1)/(2a sin d),   e cos m = cos d,
    // where m = (E1 + E2)/2 (the last identity is A = 0 in the universal tof equation).
    if (!(z > 0)) return null;
    const d = Math.sqrt(z) / 2, sd = Math.sin(d);
    const a = (r1n + r2n) / (2 * sd * sd);
    const esm = (r2n - r1n) / (2 * a * sd), ecm = Math.cos(d);
    const e = Math.hypot(esm, ecm), m = Math.atan2(esm, ecm);
    const E1 = m - d, E2 = m + d;
    const h = Math.sqrt(MU * a * Math.max(0, 1 - e * e)), sma = Math.sqrt(MU * a);
    const comp = (rv, rn, E) => {
      const vr = sma * e * Math.sin(E) / rn, vt = h / rn;
      const ux = rv[0] / rn, uy = rv[1] / rn;
      return [vr * ux - vt * uy, vr * uy + vt * ux];
    };
    v1 = comp(r1, r1n, E1); v2 = comp(r2, r2n, E2);
  } else {
    const f = 1 - y / r1n, g = A * Math.sqrt(y / MU), gd = 1 - y / r2n;
    v1 = [(r2[0] - f * r1[0]) / g, (r2[1] - f * r1[1]) / g];
    v2 = [(gd * r2[0] - r1[0]) / g, (gd * r2[1] - r1[1]) / g];
  }
  if (![v1[0], v1[1], v2[0], v2[1]].every(Number.isFinite)) return null;
  return { v1, v2, z, dnu };
}

module.exports = { lambert, stumpff, tofOf, MU };
