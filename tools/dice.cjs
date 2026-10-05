#!/usr/bin/env node
'use strict';
// Dice from the command line: the same engine that made/dice.html runs in the browser, loaded
// from that file so there is exactly one JavaScript implementation. Node.js 18+, no npm packages.
// Prints one JSON record {request, result} to stdout; errors go to stderr with exit status 1.
// Reads only the files named on the line (and stdin when a pool is "-"); never writes, posts, or
// reaches the network. The specification, with every anchor value, is made/dice.md.
//
//   node tools/dice.cjs name quiet-hour-15
//   node tools/dice.cjs integer quiet-hour-15 1 6 10 --plain
//   node tools/dice.cjs suggest "c7d70a6 example"
//   node tools/dice.cjs check
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/dice.html'), 'utf8');
const match = html.match(/<script id="dice-engine">([\s\S]*?)<\/script>/);
if (!match) throw new Error('The Dice engine was not found in made/dice.html.');
const context = {module: {exports: {}}};
vm.runInNewContext(match[1], context, {timeout: 10000, filename: 'dice-engine.js'});
const Dice = context.module.exports;
module.exports = Dice;

const USAGE = `Usage: node tools/dice.cjs KIND SEED [ARGS] [--stream NAME] [--plain]

  words     SEED [COUNT]                 raw 32-bit words
  uniform   SEED [COUNT]
  integer   SEED MIN MAX [COUNT]
  normal    SEED [COUNT]
  coin      SEED [COUNT] [P]
  hex       SEED [WORDS]
  name      SEED [COUNT]
  pick      SEED POOL [COUNT]            with replacement
  shuffle   SEED POOL
  sample    SEED K POOL                  without replacement
  weighted  SEED POOL WEIGHTS [COUNT]    WEIGHTS comma-separated, one per pool line
  suggest   SEED [POOL]                  POOL default: files in made/ except README.md, sorted
  replay    RECORD.json                  recompute the request inside a saved record (or a bare request)
  check                                  built-in checks; exit 1 if any fails

Defaults: COUNT 6, P 0.5, WORDS 4, --stream the kind. A POOL is a file name or - for standard
input: one item per line, trimmed, blank lines dropped. The two flags may appear anywhere.
JSON record to stdout; with --plain only the values, one per line (for suggest: the subject, the
partner, the operation and the constraint). replay takes no --stream, since the record names its
own stream; check takes no flags. Errors to stderr, exit 1.
Reads only what it is given; writes nothing; never reaches the network.`;

// Integers on the command line are plain decimal digits with an optional sign. Anything else
// (a decimal point, an exponent, hexadecimal, an empty string) is an error, not a guess.
function parseInteger(text, what) {
  if (!/^[+-]?[0-9]+$/.test(text)) throw new Error(what + ' must be an integer, not "' + text + '".');
  return Number(text);
}
// Real numbers (P and WEIGHTS) are finite decimal numbers: an optional sign, digits with an
// optional fraction (or a bare fraction), and an optional exponent. Number() alone would also
// read hexadecimal ("0x1") and surrounding spaces, which are not decimal numbers.
const DECIMAL = /^[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;
function parseNumber(text, what) {
  if (!DECIMAL.test(text)) throw new Error(what + ' must be a decimal number, not "' + text + '".');
  const value = Number(text);
  if (!Number.isFinite(value)) throw new Error(what + ' must be a finite number, not "' + text + '".');
  return value;
}
// A pool: one item per line from a file, or from standard input when the name is "-". A line ends
// at LF, CR LF or a lone CR (the same three as made/dice.py), nothing else. Each line
// is trimmed with String.prototype.trim(), which is exactly the engine's trimming set (the spec's
// "Text rules"); a line that is empty after that trim is blank and dropped, so a line of U+3000
// or a leading U+FEFF byte order mark goes, while U+001C or U+0085 stays part of its item.
function readPool(name) {
  const text = name === '-' ? fs.readFileSync(0, 'utf8') : fs.readFileSync(name, 'utf8');
  return text.split(/\r\n|\r|\n/).map((line) => line.trim()).filter((line) => line.length > 0);
}
// Plain string comparison in the spec's sense: code point order (Python's sorted()). The default
// Array sort compares UTF-16 units, which differs only when an astral character meets one from
// U+E000 to U+FFFF; the names here are ASCII, so both orders agree, and this one is the spec's.
function compareCodePoints(a, b) {
  const x = Array.from(a, (c) => c.codePointAt(0)), y = Array.from(b, (c) => c.codePointAt(0));
  for (let i = 0; i < x.length && i < y.length; i++) if (x[i] !== y[i]) return x[i] - y[i];
  return x.length - y.length;
}
// The default pool for suggest: the regular files (following symbolic links, which statSync does)
// in made/ beside this tool, except README.md and names beginning with a dot, sorted as above.
function madeListing() {
  const made = path.join(__dirname, '../made');
  return fs.readdirSync(made)
    .filter((name) => name !== 'README.md' && !name.startsWith('.'))
    .filter((name) => fs.statSync(path.join(made, name)).isFile())
    .sort(compareCodePoints);
}
// With --plain: one value per line. Strings print as themselves; numbers and booleans print as
// this language's JSON writes them (0.00001, true). An array is one line per item, a string (hex)
// one line, and a suggestion exactly four lines: subject, partner, operation, constraint.
function plainValue(value) { return typeof value === 'string' ? value : JSON.stringify(value); }
// Equality of two JSON values: arrays by position, objects by key set, everything else by ===, so
// 1.0 and 1 are the same, text and key order do not matter, and a value from the engine's vm realm
// compares like a parsed one.
function sameValue(a, b) {
  if (Array.isArray(a) || Array.isArray(b)) {
    return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((item, i) => sameValue(item, b[i]));
  }
  if ((a !== null && typeof a === 'object') || (b !== null && typeof b === 'object')) {
    if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length && keys.every((key) => Object.prototype.hasOwnProperty.call(b, key) && sameValue(a[key], b[key]));
  }
  return a === b;
}
function plainLines(result) {
  if (Array.isArray(result)) return result.map(plainValue);
  if (result !== null && typeof result === 'object') {
    return [result.subject, result.partner, result.operation, result.constraint].map(plainValue);
  }
  return [plainValue(result)];
}

function buildRequest(kind, positional, streamName) {
  const seed = positional[0];
  if (seed === undefined) throw new Error('A seed is required after the kind. See --help.');
  const rest = positional.slice(1);
  const most = (n) => { if (rest.length > n) throw new Error('Too many arguments for ' + kind + '. See --help.'); };
  let params;
  if (kind === 'words' || kind === 'uniform' || kind === 'normal' || kind === 'name') {
    most(1);
    params = {count: rest[0] === undefined ? 6 : parseInteger(rest[0], 'COUNT')};
  } else if (kind === 'integer') {
    most(3);
    if (rest.length < 2) throw new Error('integer needs MIN and MAX. See --help.');
    params = {count: rest[2] === undefined ? 6 : parseInteger(rest[2], 'COUNT'),
      min: parseInteger(rest[0], 'MIN'), max: parseInteger(rest[1], 'MAX')};
  } else if (kind === 'coin') {
    most(2);
    params = {count: rest[0] === undefined ? 6 : parseInteger(rest[0], 'COUNT'),
      p: rest[1] === undefined ? 0.5 : parseNumber(rest[1], 'P')};
  } else if (kind === 'hex') {
    most(1);
    params = {words: rest[0] === undefined ? 4 : parseInteger(rest[0], 'WORDS')};
  } else if (kind === 'pick') {
    most(2);
    if (rest.length < 1) throw new Error('pick needs a POOL. See --help.');
    params = {pool: readPool(rest[0]), count: rest[1] === undefined ? 6 : parseInteger(rest[1], 'COUNT')};
  } else if (kind === 'shuffle') {
    most(1);
    if (rest.length < 1) throw new Error('shuffle needs a POOL. See --help.');
    params = {pool: readPool(rest[0])};
  } else if (kind === 'sample') {
    most(2);
    if (rest.length < 2) throw new Error('sample needs K and a POOL. See --help.');
    params = {pool: readPool(rest[1]), k: parseInteger(rest[0], 'K')};
  } else if (kind === 'weighted') {
    most(3);
    if (rest.length < 2) throw new Error('weighted needs a POOL and WEIGHTS. See --help.');
    params = {pool: readPool(rest[0]),
      weights: rest[1].split(',').map((piece, i) => parseNumber(piece, 'Weight ' + (i + 1))),
      count: rest[2] === undefined ? 6 : parseInteger(rest[2], 'COUNT')};
  } else if (kind === 'suggest') {
    most(1);
    params = {pool: rest[0] === undefined ? madeListing() : readPool(rest[0])};
  } else {
    throw new Error('Unknown kind "' + kind + '". See --help.');
  }
  return {version: Dice.VERSION, seed, stream: streamName === undefined ? kind : streamName, kind, params};
}

// main(argv) returns the exit status and prints on the way, so the one process-level side effect
// (process.exitCode) stays in the block at the bottom.
function main(argv) {
  const positional = [];
  let streamName, plain = false;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--stream') {
      if (i + 1 >= argv.length) { console.error('--stream needs a name.'); return 1; }
      streamName = argv[++i];
    } else if (arg === '--plain') {
      plain = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(USAGE); return 0;
    } else if (arg.startsWith('--')) {
      console.error('Unknown option "' + arg + '". See --help.'); return 1;
    } else {
      positional.push(arg);
    }
  }
  // --help went to stdout with exit 0 above; no arguments at all is a mistake, so the usage goes
  // to stderr with exit 1 and stdout stays empty.
  if (positional.length === 0) { console.error(USAGE); return 1; }
  const kind = positional[0];
  try {
    if (kind === 'check') {
      if (positional.length > 1) throw new Error('check takes no arguments.');
      if (streamName !== undefined || plain) throw new Error('check takes no flags.');
      const results = Dice.checks();
      for (const c of results) console.log((c.ok ? 'ok   ' : 'FAIL ') + c.name + ': ' + c.detail);
      const failed = results.filter((c) => !c.ok).length;
      console.log(results.length + ' checks, ' + (failed === 0 ? 'all ok.' : failed + ' failed.'));
      return failed === 0 ? 0 : 1;
    }
    let request, saved;
    if (kind === 'replay') {
      if (streamName !== undefined) throw new Error('replay takes no --stream: the record names its own stream.');
      if (positional.length !== 2) throw new Error('replay needs exactly one RECORD.json file name.');
      saved = JSON.parse(fs.readFileSync(positional[1], 'utf8'));
      request = saved !== null && typeof saved === 'object' && saved.request !== undefined ? saved.request : saved;
    } else {
      request = buildRequest(kind, positional.slice(1), streamName);
    }
    const record = Dice.run(request);
    if (plain) { for (const line of plainLines(record.result)) console.log(line); }
    else console.log(JSON.stringify(record, null, 2));
    // A replayed record is recomputed, never trusted: when the saved result differs from the
    // recomputed one, say so on stderr, but still exit 0, since normals may differ in their last
    // bits between runtimes. The comparison is by value (the same doubles), not by JSON text.
    if (kind === 'replay' && saved !== null && typeof saved === 'object' && 'result' in saved && saved.request !== undefined
        && !sameValue(saved.result, record.result)) {
      console.error('Note: the saved result differs from the recomputed one printed above.');
    }
    return 0;
  } catch (error) {
    console.error(error instanceof SyntaxError ? 'The file is not valid JSON: ' + error.message : String(error && error.message || error));
    return 1;
  }
}

if (require.main === module) process.exitCode = main(process.argv.slice(2));
