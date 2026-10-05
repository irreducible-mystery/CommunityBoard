#!/usr/bin/env node
'use strict';
// Market League from the command line: the pure engine inside made/market-league.html, loaded from
// that file so there is one copy of the rules. Reads the plan files you name; prints JSON; never
// writes, posts, or reaches the network.
//
//   node tools/market_league.cjs world    --seed ML-20261005-first
//   node tools/market_league.cjs baseline --seed ML-20261005-first
//   node tools/market_league.cjs run      --seed ML-20261005-first plan.json [more.json ...] [--history]
//   node tools/market_league.cjs check    [--seed S]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/market-league.html'), 'utf8');
const match = html.match(/<script id="ml-engine">([\s\S]*?)<\/script>/);
if (!match) throw new Error('Market League engine not found in made/market-league.html');
const context = { module: { exports: {} } };
vm.runInNewContext(match[1], context, { timeout: 60000, filename: 'ml-engine.js' });
const ML = context.module.exports;

const USAGE = `Usage:
  node tools/market_league.cjs world    --seed SEED
  node tools/market_league.cjs baseline --seed SEED
  node tools/market_league.cjs run      --seed SEED PLAN.json [PLAN2.json ...] [--history]
  node tools/market_league.cjs check    [--seed SEED]
JSON to stdout; errors to stderr. Reads only the files named. Never writes or posts.`;

function main(argv, io) {
  const args = argv.slice();
  const cmd = args.shift();
  let seed = 'ML-20261005-first', history = false;
  const files = [];
  while (args.length) {
    const a = args.shift();
    if (a === '--seed') { seed = args.shift(); if (seed === undefined) { io.err('--seed needs a value'); return 1; } }
    else if (a === '--history') history = true;
    else if (a.startsWith('--')) { io.err(`unknown option ${a}\n${USAGE}`); return 1; }
    else files.push(a);
  }
  try {
    if (!cmd || cmd === '--help' || cmd === 'help') { io.out(USAGE); return cmd ? 0 : 1; }
    if (cmd === 'world') { io.out(JSON.stringify(ML.world(seed), null, 1)); return 0; }
    if (cmd === 'baseline') { io.out(JSON.stringify(ML.baselinePlans(ML.world(seed)))); return 0; }
    if (cmd === 'check') {
      const cs = ML.checks(seed);
      for (const c of cs) io.out(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name} — ${c.detail}`);
      return cs.every((c) => c.ok) ? 0 : 1;
    }
    if (cmd === 'run') {
      if (!files.length) { io.err(`run needs at least one plan file\n${USAGE}`); return 1; }
      const plans = [];
      for (const f of files) { const v = JSON.parse(io.readFile(f)); if (Array.isArray(v)) plans.push(...v); else plans.push(v); }
      io.out(JSON.stringify(ML.simulate(ML.world(seed), plans, { history }), null, 1));
      return 0;
    }
    io.err(`unknown command ${cmd}\n${USAGE}`);
    return 1;
  } catch (e) { io.err(String(e && e.message || e)); return 1; }
}

module.exports = { ML, main, USAGE };
if (require.main === module) {
  process.exitCode = main(process.argv.slice(2), { out: (t) => console.log(t), err: (t) => console.error(t), readFile: (f) => fs.readFileSync(f, 'utf8') });
}
