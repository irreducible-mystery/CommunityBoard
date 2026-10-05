#!/usr/bin/env node
'use strict';
// Matrix League from the command line: the pure engine inside made/matrix-league.html, loaded from
// that file so there is one copy of the rules. Reads the plan files you name; prints JSON; never
// writes, posts, or reaches the network.
//
//   node tools/matrix_league.cjs map      --seed XL-20261005-first
//   node tools/matrix_league.cjs baseline --seed XL-20261005-first
//   node tools/matrix_league.cjs run      --seed XL-20261005-first plan.json [more.json ...] [--log]
//   node tools/matrix_league.cjs check    [--seed S]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/matrix-league.html'), 'utf8');
const match = html.match(/<script id="xl-engine">([\s\S]*?)<\/script>/);
if (!match) throw new Error('Matrix League engine not found in made/matrix-league.html');
const context = { module: { exports: {} } };
vm.runInNewContext(match[1], context, { timeout: 60000, filename: 'xl-engine.js' });
const XL = context.module.exports;

const USAGE = `Usage:
  node tools/matrix_league.cjs map      --seed SEED
  node tools/matrix_league.cjs baseline --seed SEED
  node tools/matrix_league.cjs run      --seed SEED PLAN.json [PLAN2.json ...] [--log]
  node tools/matrix_league.cjs check    [--seed SEED]
JSON to stdout; errors to stderr. Reads only the files named. Never writes or posts.`;

function main(argv, io) {
  const args = argv.slice();
  const cmd = args.shift();
  let seed = 'XL-20261005-first', log = false;
  const files = [];
  while (args.length) {
    const a = args.shift();
    if (a === '--seed') { seed = args.shift(); if (seed === undefined) { io.err('--seed needs a value'); return 1; } }
    else if (a === '--log') log = true;
    else if (a.startsWith('--')) { io.err(`unknown option ${a}\n${USAGE}`); return 1; }
    else files.push(a);
  }
  try {
    if (!cmd || cmd === '--help' || cmd === 'help') { io.out(USAGE); return cmd ? 0 : 1; }
    if (cmd === 'map') { io.out(JSON.stringify(XL.map(seed), null, 1)); return 0; }
    if (cmd === 'baseline') { io.out(JSON.stringify(XL.baselinePlans(XL.map(seed)))); return 0; }
    if (cmd === 'check') {
      const cs = XL.checks(seed);
      for (const c of cs) io.out(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name} — ${c.detail}`);
      return cs.every((c) => c.ok) ? 0 : 1;
    }
    if (cmd === 'run') {
      if (!files.length) { io.err(`run needs at least one plan file\n${USAGE}`); return 1; }
      const plans = [];
      for (const f of files) { const v = JSON.parse(io.readFile(f)); if (Array.isArray(v)) plans.push(...v); else plans.push(v); }
      io.out(JSON.stringify(XL.simulate(XL.map(seed), plans, { history: log }), null, 1));
      return 0;
    }
    io.err(`unknown command ${cmd}\n${USAGE}`);
    return 1;
  } catch (e) { io.err(String(e && e.message || e)); return 1; }
}

module.exports = { XL, main, USAGE };
if (require.main === module) {
  process.exitCode = main(process.argv.slice(2), { out: (t) => console.log(t), err: (t) => console.error(t), readFile: (f) => fs.readFileSync(f, 'utf8') });
}
