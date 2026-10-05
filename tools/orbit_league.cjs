#!/usr/bin/env node
'use strict';
// Orbital League from the command line: the same pure engine that made/orbital-league.html
// runs in the browser, loaded from that file so there is exactly one copy of the rules.
// Reads plan files you name; prints JSON to stdout; never writes, posts, or reaches the network.
//
//   node tools/orbit_league.cjs field    --seed OL-20261005-first
//   node tools/orbit_league.cjs baseline --seed OL-20261005-first
//   node tools/orbit_league.cjs run      --seed OL-20261005-first plan.json [more.json ...] [--paths]
//   node tools/orbit_league.cjs check    [--seed S]
//
// A plan file holds one plan {name, burns} or an array of them. `run` prints the scored result;
// `check` runs the page's self-checks and exits 1 if any fails.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/orbital-league.html'), 'utf8');
const match = html.match(/<script id="ol-engine">([\s\S]*?)<\/script>/);
if (!match) throw new Error('Orbital League engine not found in made/orbital-league.html');
const context = { module: { exports: {} } };
vm.runInNewContext(match[1], context, { timeout: 60000, filename: 'ol-engine.js' });
const OL = context.module.exports;

const USAGE = `Usage:
  node tools/orbit_league.cjs field    --seed SEED
  node tools/orbit_league.cjs baseline --seed SEED
  node tools/orbit_league.cjs run      --seed SEED PLAN.json [PLAN2.json ...] [--paths]
  node tools/orbit_league.cjs check    [--seed SEED]
JSON to stdout; errors to stderr. Reads only the files named. Never writes or posts.`;

// main(argv, io) so tests can call it without starting a process.
// io = { out(text), err(text), readFile(name) }. Returns the exit code.
function main(argv, io) {
  const args = argv.slice();
  const cmd = args.shift();
  let seed = 'OL-20261005-first', paths = false;
  const files = [];
  while (args.length) {
    const a = args.shift();
    if (a === '--seed') { seed = args.shift(); if (seed === undefined) { io.err('--seed needs a value'); return 1; } }
    else if (a === '--paths') paths = true;
    else if (a.startsWith('--')) { io.err(`unknown option ${a}\n${USAGE}`); return 1; }
    else files.push(a);
  }
  try {
    if (!cmd || cmd === '--help' || cmd === 'help') { io.out(USAGE); return cmd ? 0 : 1; }
    if (cmd === 'field') { io.out(JSON.stringify(OL.field(seed), null, 1)); return 0; }
    if (cmd === 'baseline') { io.out(JSON.stringify(OL.baselinePlan(OL.field(seed)))); return 0; }
    if (cmd === 'check') {
      const cs = OL.checks(seed);
      for (const c of cs) io.out(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name} — ${c.detail}`);
      return cs.every((c) => c.ok) ? 0 : 1;
    }
    if (cmd === 'run') {
      if (!files.length) { io.err(`run needs at least one plan file\n${USAGE}`); return 1; }
      const plans = [];
      for (const f of files) {
        const v = JSON.parse(io.readFile(f));
        if (Array.isArray(v)) plans.push(...v); else plans.push(v);
      }
      io.out(JSON.stringify(OL.simulate(OL.field(seed), plans, { paths }), null, 1));
      return 0;
    }
    io.err(`unknown command ${cmd}\n${USAGE}`);
    return 1;
  } catch (e) { io.err(String(e && e.message || e)); return 1; }
}

module.exports = { OL, main, USAGE };
if (require.main === module) {
  process.exitCode = main(process.argv.slice(2), {
    out: (t) => console.log(t), err: (t) => console.error(t), readFile: (f) => fs.readFileSync(f, 'utf8') });
}
