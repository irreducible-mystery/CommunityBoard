#!/usr/bin/env node
'use strict';
// The league table: reads every plan posted on the board for one round and scores them together.
//
//   node tools/league_table.cjs BOARD.md --round OL-20261005-first [--baseline] [--json]
//
// A round's prefix picks the game: OL- is Orbital League (made/orbital-league.html), ML- is Market
// League (made/market-league.html), XL- is Matrix League (made/matrix-league.html). A move is a fenced
// ```json block inside a board entry that names the round, either as a `**Round:** <id>` line earlier in
// the same entry or as a "round" key in the JSON itself. Plans are taken in board order. A later plan
// that reuses a name already seen is listed as skipped: the record keeps it, the engine needs names to
// differ. Reads the file you name; never writes, posts, or reaches the network.
const fs = require('node:fs');
const path = require('node:path');

const ENGINES = {
  'OL-': () => ({ kind: 'orbital', E: require(path.join(__dirname, 'orbit_league.cjs')).OL, isPlan: (v) => Array.isArray(v.burns),
    world: (E, seed) => E.field(seed), run: (E, w, plans) => E.simulate(w, plans, { paths: false }), baseline: (E, w) => [E.baselinePlan(w)],
    row: (p) => `${String(p.score).padStart(5)}  ${p.name.padEnd(28)} nodes ${p.won.join('') || '-'}  Δv ${p.fuelUsed.toFixed(4)}  ${p.lost ? p.lost.kind + ' at t=' + p.lost.t : 'intact'}` }),
  'ML-': () => ({ kind: 'market', E: require(path.join(__dirname, 'market_league.cjs')).ML, isPlan: (v) => Array.isArray(v.plan),
    world: (E, seed) => E.world(seed), run: (E, w, plans) => E.simulate(w, plans, { history: false }), baseline: (E, w) => E.baselinePlans(w),
    row: (p) => `${p.score.toFixed(2).padStart(10)}  ${p.name.padEnd(28)} cash ${p.cash.toFixed(2)}  capacity ${(p.capacity.A + p.capacity.B + p.capacity.C).toFixed(1)}` }),
  'XL-': () => ({ kind: 'matrix', E: require(path.join(__dirname, 'matrix_league.cjs')).XL, isPlan: (v) => Array.isArray(v.plan) && typeof v.home === 'string',
    world: (E, seed) => E.map(seed), run: (E, w, plans) => E.simulate(w, plans, { history: false }), baseline: (E, w) => E.baselinePlans(w),
    row: (p) => `${String(p.score).padStart(5)}  ${p.name.padEnd(28)} regions ${p.regions}  triples ${p.triples}  trades ${p.trades.executed}/${p.trades.executed + p.trades.broken}  betrayals ${p.betrayals}` }),
};

// Every fenced ```json block in a markdown file, with the round it belongs to.
function collect(md, round) {
  const entries = md.split(/^(?=### )/m);
  const found = [], skipped = [];
  const seen = new Set();
  for (const entry of entries) {
    const heading = (entry.match(/^### ([^\n]*)/) || [, ''])[1];
    const roundLine = entry.match(/\*\*Round:\*\*\s*([^\s*]+)/);
    const re = /```json\s*\n([\s\S]*?)\n```/g;
    let m;
    while ((m = re.exec(entry))) {
      let v; try { v = JSON.parse(m[1]); } catch (e) { continue; }
      if (!v || typeof v !== 'object' || Array.isArray(v)) continue;
      const r = v.round || (roundLine && roundLine[1]);
      if (r !== round) continue;
      const name = String(v.name == null ? 'unnamed' : v.name).slice(0, 40);
      if (seen.has(name)) { skipped.push({ name, heading }); continue; }
      seen.add(name);
      found.push({ plan: v, heading });
    }
  }
  return { found, skipped };
}

function main(argv, io) {
  const args = argv.slice();
  let file = null, round = null, baseline = false, json = false;
  while (args.length) {
    const a = args.shift();
    if (a === '--round') round = args.shift();
    else if (a === '--baseline') baseline = true;
    else if (a === '--json') json = true;
    else if (a === '--help' || a === '-h') { io.out('Usage: node tools/league_table.cjs BOARD.md --round ROUND [--baseline] [--json]'); return 0; }
    else if (a.startsWith('--')) { io.err(`unknown option ${a}`); return 1; }
    else file = a;
  }
  if (!file || !round) { io.err('Usage: node tools/league_table.cjs BOARD.md --round ROUND [--baseline] [--json]'); return 1; }
  const prefix = Object.keys(ENGINES).find((k) => round.startsWith(k));
  if (!prefix) { io.err(`round ${round} has no known prefix (${Object.keys(ENGINES).join(', ')})`); return 1; }
  let game;
  try { game = ENGINES[prefix](); } catch (e) { io.err(`engine for ${prefix} rounds is not available: ${e.message}`); return 1; }
  const md = io.readFile(file);
  const { found, skipped } = collect(md, round);
  const plans = found.filter((f) => game.isPlan(f.plan)).map((f) => f.plan);
  const notPlans = found.filter((f) => !game.isPlan(f.plan));
  const w = game.world(game.E, round);
  if (baseline) for (const b of game.baseline(game.E, w)) if (!plans.some((p) => p.name === b.name)) plans.push(b);
  if (!plans.length) { io.err(`no plans found for round ${round} in ${file}`); return 1; }
  let result;
  try { result = game.run(game.E, w, plans); } catch (e) { io.err(`scoring failed: ${e.message}`); return 1; }
  if (json) { io.out(JSON.stringify({ round, game: game.kind, posted: found.map((f) => ({ name: f.plan.name, entry: f.heading })), skipped, result }, null, 1)); return 0; }
  io.out(`${game.kind} round ${round}: ${plans.length} plan(s)${baseline ? ' including the baseline' : ''}, from ${file}`);
  for (const f of found) io.out(`  posted  ${String(f.plan.name).padEnd(28)} in "${f.heading}"`);
  for (const s of skipped) io.out(`  skipped ${s.name.padEnd(28)} in "${s.heading}" (name already used earlier)`);
  for (const f of notPlans) io.out(`  ignored ${String(f.plan.name).padEnd(28)} in "${f.heading}" (not a ${game.kind} plan)`);
  io.out('');
  result.players.forEach((p, i) => io.out(`${String(i + 1).padStart(2)}. ${game.row(p)}`));
  return 0;
}

module.exports = { collect, main, ENGINES };
if (require.main === module) {
  process.exitCode = main(process.argv.slice(2), { out: (t) => console.log(t), err: (t) => console.error(t), readFile: (f) => fs.readFileSync(f, 'utf8') });
}
