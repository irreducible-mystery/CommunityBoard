#!/usr/bin/env node
'use strict';
// verify.js — run superninja-18-in-13.json through the exact engine with the burn
// cap raised to 13, to show it captures all seven nodes. The game itself caps at
// 12 burns, so this plan is a note about the open question, not a legal move.
//
//   node experiments/orbital-league-18/verify.js
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../../made/orbital-league.html'), 'utf8');
const m = html.match(/<script id="ol-engine">([\s\S]*?)<\/script>/);
const ctx = { module: { exports: {} } };
vm.runInNewContext(m[1], ctx, { timeout: 60000 });
const OL = ctx.module.exports;
const SEED = 'OL-20261005-first';
const fld = OL.field(SEED);
const fld13 = { ...fld, rules: { ...fld.rules, maxBurns: 13 } };
const plan = JSON.parse(fs.readFileSync(path.join(__dirname, 'superninja-18-in-13.json'), 'utf8'));
const res = OL.simulate(fld13, [plan], { paths: false });
const p = res.players[0];
console.log(`plan ${plan.name}: ${plan.burns.length} burns`);
console.log(`engine (cap 13): score ${p.score} of 18, won ${p.won.join('')}, lost ${p.lost ? p.lost.kind : 'no'}, dv ${p.fuelUsed.toFixed(4)}`);
console.log(`captures: ${p.reached.map((r) => `${r.node}@${r.t}`).join('  ')}`);
console.log(p.score === 18 ? 'OK: 18 points, but in 13 burns (one over the cap).' : 'unexpected result');
