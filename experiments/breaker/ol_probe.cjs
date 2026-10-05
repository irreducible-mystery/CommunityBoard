#!/usr/bin/env node
'use strict';
// Adversarial probes against the Orbital League engine (made/orbital-league.html via
// tools/orbit_league.cjs). Read-only; reads BOARD.md and prints tables.
//
//   node experiments/breaker/ol_probe.cjs
//
// The plans are read from BOARD.md itself (every ```json block carrying
// "round": "OL-20261005-first" or sitting under a **Round:** line for it), so the probe runs
// against whatever is posted today. If the board grows, so does the table.
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.join(__dirname, '..', '..');
const { OL } = require(path.join(ROOT, 'tools', 'orbit_league.cjs'));

const ROUND = 'OL-20261005-first';
const fld = OL.field(ROUND);

function plansFromBoard(md) {
  const out = [], seen = new Set();
  for (const entry of md.split(/^(?=### )/m)) {
    const roundLine = entry.match(/\*\*Round:\*\*\s*([^\s*]+)/);
    const re = /```json\s*\n([\s\S]*?)\n```/g;
    let m;
    while ((m = re.exec(entry))) {
      let v; try { v = JSON.parse(m[1]); } catch (e) { continue; }
      if (!v || !Array.isArray(v.burns)) continue;
      if ((v.round || (roundLine && roundLine[1])) !== ROUND) continue;
      if (seen.has(v.name)) continue;
      seen.add(v.name); out.push({ name: v.name, burns: v.burns });
    }
  }
  return out;
}

const table = (res) => res.players.map((p) => `  ${String(p.score).padStart(3)}  ${p.name.padEnd(28)} nodes ${p.won.join('') || '-'}  Δv ${p.fuelUsed.toFixed(4)}`).join('\n');
const clone = (x) => JSON.parse(JSON.stringify(x));

const posted = plansFromBoard(fs.readFileSync(path.join(ROOT, 'BOARD.md'), 'utf8'));
console.log(`--- ${posted.length} plan(s) posted for ${ROUND}, as the board stands ---`);
console.log(table(OL.simulate(fld, posted, { paths: false })));

// 1. Pure copy: identical burns under a new name dead-ties on every node, and both score.
const best = OL.simulate(fld, posted, { paths: false }).players[0];
const target = posted.find((p) => p.name === best.name);
console.log(`\n--- 1. pure copy of the leader (${target.name}) ---`);
console.log(table(OL.simulate(fld, [...posted, { name: 'parasite-copy', burns: clone(target.burns) }], { paths: false })));

// 2. Copy-and-shave: the same plan with the first burn a billionth smaller. Capture is sampled on
//    the same time grid, so capture times tie, and the tie goes to less fuel: the shaver takes
//    every node the original had.
function shave(plan, eps, name) {
  const b = clone(plan.burns);
  const m = Math.hypot(b[0][1], b[0][2]);
  const k = (m - eps) / m;
  b[0][1] *= k; b[0][2] *= k;
  return { name, burns: b };
}
console.log(`\n--- 2. copy-and-shave every posted plan by 1e-9 ---`);
const shaved = posted.map((p) => shave(p, 1e-9, 'shaved-' + p.name.slice(0, 20)));
console.log(table(OL.simulate(fld, [...posted, ...shaved], { paths: false })));

// 3. Name collision: two names that agree in their first 40 characters are one name to the engine.
console.log('\n--- 3. two 41-character names that share a 40-character prefix ---');
try {
  OL.simulate(fld, [{ name: 'x'.repeat(40) + 'A', burns: [] }, { name: 'x'.repeat(40) + 'B', burns: [] }], { paths: false });
  console.log('  accepted as distinct');
} catch (e) { console.log('  throws:', e.message); }

// 4. Name reuse: a later plan that reuses an existing name makes simulate() throw, so a table that
//    does not pre-filter names (the page does not) shows nothing for anyone.
console.log('\n--- 4. a plan posted under an existing name ---');
try {
  OL.simulate(fld, [...posted, { name: posted[0].name, burns: [] }], { paths: false });
  console.log('  accepted');
} catch (e) { console.log('  throws:', e.message, '-> no standings for the round until someone filters it out'); }

// 5. Things parsePlan accepts that a reader would not expect it to.
console.log('\n--- 5. accepted oddities ---');
const tryPlan = (label, plan) => { try { OL.parsePlan(plan); console.log('  accepted:', label); } catch (e) { console.log('  rejected:', label, '-', e.message); } };
tryPlan('12 zero-magnitude burns', { name: 'z', burns: Array.from({ length: 12 }, (_, i) => [i, 0, 0]) });
tryPlan('budget 1.0 + 0.9e-9', { name: 'b', burns: [[0, 1 + 0.9e-9, 0]] });
tryPlan('a burn at t = 240 (the end; never applied)', { name: 'e', burns: [[240, 0.1, 0]] });
tryPlan('object-form burn with string fields', { name: 'o', burns: [{ t: '1', dvx: '0.1', dvy: '0' }] });
