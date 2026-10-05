'use strict';
// Runs the pure engine embedded in made/emergence.html (<script id="emergence-engine">) under Node.
// Run with: node --test tests/test_emergence.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/emergence.html'), 'utf8');
const src = html.match(/<script id="emergence-engine">([\s\S]*?)<\/script>/)[1];
const ctx = {module: {exports: {}}, TextEncoder, TextDecoder, Buffer};
vm.runInNewContext(src, ctx, {timeout: 60000});
const E = ctx.module.exports;
const preset = (id) => E.PRESETS.find((p) => p.id === id).text;
const run = (text, steps, seed) => { const w = new E.World(E.parse(text), seed); for (let i = 0; i < steps; i++) w.step(); return w; };

test('every self-check on the page passes', () => {
  const res = E.runChecks();
  assert.equal(res.length, 10);
  for (const r of res) assert.ok(r.ok, `${r.name}: ${r.detail}`);
});

test('the page has no remote scripts, links or eval', () => {
  assert.doesNotMatch(html, /<script[^>]+src=/i);
  assert.doesNotMatch(html, /https?:\/\//);
  assert.doesNotMatch(src, /\beval\s*\(|new Function|import\(/);
});

test('every preset parses and runs, and swap-only presets conserve counts', () => {
  assert.equal(E.PRESETS.length, 9);
  for (const p of E.PRESETS) {
    const w = run(p.text, 30);
    assert.equal(w.t, 30, p.id);
    const swapOnly = w.spec.rules.every((r) => r.kind === 'swap') && w.spec.noise === 0;
    if (swapOnly) assert.ok(w.conserved(), p.id);
  }
});

test('changing one number changes what emerges: Schelling tolerance', () => {
  const clump = (tol) => run(preset('schelling').replace(/0\.3\b/g, String(tol)), 200).measure().clumping;
  const low = clump(0.1), mid = clump(0.3), high = clump(0.6);
  assert.ok(low < 0.1, `0.1 -> ${low}`);
  assert.ok(mid > 0.3, `0.3 -> ${mid}`);
  assert.ok(high > mid, `0.6 -> ${high}`);
});

test('changing the update order changes Life: sync Life thins to ash, async Life stays crowded', () => {
  const sync = run(preset('life'), 600, 'x').measure();
  const async = run(preset('life-async'), 600, 'x').measure();
  const n = 96 * 72;
  assert.ok(sync.counts[1] / n < 0.12, `sync alive ${sync.counts[1] / n}`);
  assert.ok(async.counts[1] / n > 0.3, `async alive ${async.counts[1] / n}`);
});

test('runs are reproducible from rule text plus seed', () => {
  assert.equal(run(preset('forest'), 80, 's').hash(), run(preset('forest'), 80, 's').hash());
  assert.notEqual(run(preset('forest'), 80, 's').hash(), run(preset('forest'), 80, 't').hash());
});

test('parser errors carry line numbers and stay inside the language', () => {
  const bad = [
    ['states a\na -> a', 1, /at least two states/],
    ['states a b\na -> c', 2, /unknown state 'c'|unknown name 'c'|'c'/],
    ['states a b\nsize 3 3\na -> b', 2, /size/],
    ['states a b\na -> b if (a > 1', 2, /\)/],
    ['states a b\nconstructor -> a', 2, /./],
    ['states a b\na -> b if alert(1)', 2, /./],
    ['states a b\nfrobnicate', 2, /not a rule or setting/],
    ['states a b\na -> b if toString > 0', 2, /unknown name 'toString'/],
    ['states a b\na -> b if __proto__ > 0', 2, /unknown name '__proto__'/],
  ];
  for (const [text, line, re] of bad) {
    assert.throws(() => E.parse(text), (e) => e instanceof E.RuleError && e.line === line && re.test(e.message), text);
  }
});

test('conditions: arithmetic, directions, division by zero', () => {
  const spec = E.parse('states a b\nedges wall\nsize 4 4\nstart a 1\na -> b if N is wall and 1 / 0 == 0 and 7 % 3 == 1\n');
  const w = new E.World(spec); w.step();
  assert.deepEqual([...w.stateCounts()], [12, 4]);
});

test('share codes round-trip unicode rule text', () => {
  const t = '# Ünïcode → rules\nstates a b\na -> b\n';
  assert.equal(E.decode(E.encode(t)), t);
  assert.match(E.encode(t), /^[A-Za-z0-9_-]+$/);
});
