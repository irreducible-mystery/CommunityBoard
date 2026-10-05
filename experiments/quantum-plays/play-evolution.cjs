#!/usr/bin/env node
'use strict';
// play-evolution.cjs — a headless play of the Evolution game from PR #85.
// Loads the page's pure engine and tries to win two challenges by changing the
// world (never the creatures), then prints a world code for each win.
//
//   node experiments/quantum-plays/play-evolution.cjs [path/to/evolution.html]
//
// The engine lives on the superninja/evolution branch, not on main, so pass the
// path to that branch's made/evolution.html (default: made/evolution.html).
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const file = process.argv[2] || path.join(__dirname, '../../made/evolution.html');
const html = fs.readFileSync(file, 'utf8');
const engineSrc = html.match(/<script id="evo-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(engineSrc, ctx, { timeout: 20000 });
const E = ctx.module.exports;

function worldCode(w) {
  const rec = { v: 1, seed: w.seed, challenge: w.challenge ? w.challenge.id : null, t: w.t, log: w.log };
  return Buffer.from(JSON.stringify(rec), 'utf8').toString('base64');
}
function report(name, w) {
  const st = E.stats(w);
  const cs = w.challenge || {};
  console.log(`\n== ${name} ==`);
  console.log(`  tick ${w.t}  pop ${st.pop}  won ${cs.won}  lost ${cs.lost}  held ${cs.held}`);
  console.log(`  mean genes: size ${st.mean.size.toFixed(3)} speed ${st.mean.speed.toFixed(3)} sense ${st.mean.sense.toFixed(3)} colour ${st.mean.color.toFixed(3)} fur ${st.mean.fur.toFixed(3)}`);
  console.log(`  fingerprint ${E.fingerprint(w)}`);
  if (cs.won != null) {
    const code = worldCode(w);
    console.log(`  WON at tick ${cs.won}; world code (${w.log.length} actions, ${code.length} chars):`);
    console.log(`  ${code}`);
    // Prove the code replays to the same world.
    const rec = JSON.parse(Buffer.from(code, 'base64').toString('utf8'));
    const r = E.replay(rec, rec.t);
    console.log(`  replay check: ${E.fingerprint(r) === E.fingerprint(w) ? 'OK, same fingerprint' : 'MISMATCH'}`);
  } else {
    console.log('  not won');
  }
  return cs.won != null;
}

// --- First bloom: grow 20 founders into 250, held 300 ticks. Food is the limit. ---
{
  const w = E.createChallenge('bloom', 'quantum-bloom');
  E.apply(w, { k: 'set', key: 'food', v: 4.0 });
  E.run(w, 40);
  for (const [x, y] of [[200, 200], [400, 300], [600, 400], [300, 500], [500, 150]]) E.apply(w, { k: 'sow', x, y });
  E.run(w, 1400);
  report('First bloom (food raised to 4.0, five hand-sown patches)', w);
}

// --- Ice age: temp -1, keep 60 alive with mean fur above 0.85, held 600 ticks. ---
{
  const w = E.createChallenge('ice', 'quantum-ice');
  E.apply(w, { k: 'set', key: 'food', v: 3.0 });   // more food buys time for fur to grow
  E.run(w, 3000);
  report('Ice age (food raised to 3.0; temperature and gradient are locked)', w);
}
