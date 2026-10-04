#!/usr/bin/env node
'use strict';
// Runs the same pure engine embedded in the self-contained HTML. No npm packages.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../made/noise-lab.html'), 'utf8');
const match = html.match(/<script id="noise-engine">([\s\S]*?)<\/script>/);
if (!match) throw new Error('Noise Lab engine not found.');
const context = {module:{exports:{}}};
vm.runInNewContext(match[1], context, {timeout:1000, filename:'noise-engine.js'});
const engine = context.module.exports;
module.exports = engine;
if (require.main === module) {
  try {
    const args = process.argv.slice(2);
    if (args[0] === '--help' || args.length === 0) {
      console.log('Usage: node tools/noise_lab.cjs invitation SEED [INDEX] [POOL_FILE]\n       node tools/noise_lab.cjs numbers SEED [INDEX] [COUNT]\n       node tools/noise_lab.cjs simulation SEED [NOISE] [R]\n       node tools/noise_lab.cjs replay RECORD.json\nJSON to stdout; diagnostics to stderr. Never writes files or posts to the board.\nFor integer/normal draws or other parameters, edit a record request and replay it.');
    } else {
      const [kind, seed, a, b] = args;
      let request;
      if (kind === 'replay') {
        if (args.length !== 2) throw new Error('Replay requires one JSON filename.');
        request = JSON.parse(fs.readFileSync(seed, 'utf8')).request;
      } else {
        if (args.length > 4) throw new Error('Too many arguments. See --help.');
        let params;
        if (kind === 'invitation') params={index:a===undefined?0:Number(a),pool:b===undefined?engine.DEFAULT_POOL:fs.readFileSync(b,'utf8').split(/\r?\n/).map(s=>s.trim()).filter(Boolean)};
        else if (kind === 'numbers') params={index:a===undefined?0:Number(a),count:b===undefined?6:Number(b),distribution:'uniform'};
        else if (kind === 'simulation') params={noise:a===undefined?0.002:Number(a),r:b===undefined?3.9:Number(b),steps:240};
        else throw new Error('Unknown command. See --help.');
        request={version:engine.VERSION,seed,kind,params};
      }
      console.log(JSON.stringify(engine.run(request),null,2));
    }
  } catch (error) { console.error(error.message); process.exitCode=1; }
}
