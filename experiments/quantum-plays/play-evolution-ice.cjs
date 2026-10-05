#!/usr/bin/env node
'use strict';
// Ice-age win search: vary food and mutation (both are world settings, not
// creatures). temp/gradient are locked; mutation is free.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const file = process.argv[2] || path.join(__dirname, 'CommunityBoard/made/evolution.html');
const html = fs.readFileSync(file, 'utf8');
const src = html.match(/<script id="evo-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const E = ctx.module.exports;

function worldCode(w) {
  const rec = { v: 1, seed: w.seed, challenge: w.challenge ? w.challenge.id : null, t: w.t, log: w.log };
  return Buffer.from(JSON.stringify(rec), 'utf8').toString('base64');
}

const foods = [4, 6, 8];
const muts = [0.005, 0.01, 0.02, 0.05];
const seeds = ['quantum-ice', 'ice-b'];
let best = null;

for (const seed of seeds) {
  for (const food of foods) {
    for (const mut of muts) {
      const w = E.createChallenge('ice', seed);
      E.apply(w, { k: 'set', key: 'food', v: food });
      E.apply(w, { k: 'set', key: 'mutation', v: mut });
      E.run(w, 8000);
      const st = E.stats(w);
      const cs = w.challenge || {};
      console.log(`seed ${seed} food ${food} mut ${mut}: pop ${st.pop} fur ${st.mean.fur.toFixed(3)} won ${cs.won} held ${cs.held}`);
      if (cs.won != null && !best) {
        best = { seed, food, mut, code: worldCode(w), won: cs.won, actions: w.log.length };
        console.log('  *** WON *** ' + best.code);
      }
    }
  }
}
console.log('\nbest: ' + JSON.stringify(best));
