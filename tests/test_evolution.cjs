'use strict';
// Runs the page's pure engine (<script id="evo-engine">) and its self-checks under Node.
// Run with: node --test tests/test_evolution.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/evolution.html'), 'utf8');
const engineSrc = html.match(/<script id="evo-engine">([\s\S]*?)<\/script>/)[1];
const checksSrc = html.match(/<script id="evo-checks">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} }, Math };
vm.runInNewContext(engineSrc, ctx, { timeout: 20000 });
const E = ctx.module.exports;
vm.runInNewContext(checksSrc, ctx, { timeout: 60000 });
const evoSelfCheck = ctx.module.exports.evoSelfCheck;

function mean(w, k) { return E.stats(w).mean[k]; }

test('every self-check on the page passes', () => {
  const res = evoSelfCheck(E);
  assert.equal(res.length, 10);
  for (const r of res) assert.ok(r.ok, r.msg);
});

test('the page loads nothing: no external script, link or src', () => {
  assert.doesNotMatch(html, /<script[^>]+src=/i);
  assert.doesNotMatch(html, /<link[^>]+href=/i);
  assert.doesNotMatch(html, /https?:\/\//i);
});

test('a replay with every kind of action matches the live world', () => {
  const w = E.create({ seed: 'all-actions' });
  E.run(w, 120);
  E.apply(w, { k: 'set', key: 'food', v: 3.2 });
  E.apply(w, { k: 'paint', x: 400, y: 300, v: 0.9, r: 3 });
  E.run(w, 60);
  E.apply(w, { k: 'release', x: 200, y: 200 });
  E.apply(w, { k: 'set', key: 'hawks', v: 5 });
  E.run(w, 200);
  E.apply(w, { k: 'meteor', x: 600, y: 300 });
  E.apply(w, { k: 'sow', x: 100, y: 500 });
  E.apply(w, { k: 'set', key: 'hawks', v: 1 });
  E.run(w, 300);
  const r = E.replay({ seed: 'all-actions', log: w.log }, w.t);
  assert.equal(E.fingerprint(r), E.fingerprint(w));
  assert.equal(r.creatures.length, w.creatures.length);
  assert.deepEqual({ ...r.deaths }, { ...w.deaths });
});

test('challenge replays rebuild the challenge world, not a sandbox', () => {
  const w = E.createChallenge('hide', 'x');
  E.run(w, 50); E.apply(w, { k: 'set', key: 'mutation', v: 0.1 }); E.run(w, 150);
  const r = E.replay({ seed: 'x', challenge: 'hide', log: w.log }, w.t);
  assert.equal(E.fingerprint(r), E.fingerprint(w));
  assert.equal(r.hawks.length, 6);
});

test('cold selects for fur and heat selects against it (same seed, 6000 ticks)', () => {
  const cold = E.run(E.create({ seed: 'climate', settings: { temp: -1 } }), 6000);
  const hot = E.run(E.create({ seed: 'climate', settings: { temp: 1 } }), 6000);
  const mild = E.run(E.create({ seed: 'climate' }), 6000);
  assert.ok(mean(cold, 'fur') > 0.7, 'cold fur ' + mean(cold, 'fur'));
  assert.ok(mean(hot, 'fur') < 0.3, 'hot fur ' + mean(hot, 'fur'));
  assert.ok(Math.abs(mean(mild, 'fur') - 0.5) < 0.12, 'mild fur ' + mean(mild, 'fur'));
});

test('without hawks colour only drifts; with hawks on pale ground it is selected', () => {
  const free = E.run(E.create({ seed: 'colour', ground: 0.86, genes: { color: 0.14 }, settings: { mutation: 0.12 } }), 12000);
  const hunted = E.run(E.create({ seed: 'colour', ground: 0.86, genes: { color: 0.14 }, settings: { mutation: 0.12, hawks: 6 } }), 12000);
  assert.ok(mean(hunted, 'color') > 0.6, 'hunted colour ' + mean(hunted, 'color'));
  assert.ok(mean(hunted, 'color') - mean(free, 'color') > 0.25, 'free ' + mean(free, 'color') + ' vs hunted ' + mean(hunted, 'color'));
});

test('mutation zero means children are exact copies', () => {
  const w = E.create({ seed: 'clones', founders: 5, settings: { mutation: 0, food: 4 } });
  const founderGenes = new Set(w.creatures.map((c) => JSON.stringify(c.g)));
  E.run(w, 1500);
  assert.ok(w.births > 10);
  for (const c of w.creatures) assert.ok(founderGenes.has(JSON.stringify(c.g)), 'a new genome appeared without mutation');
});

test('a meteor kills exactly the creatures inside its radius', () => {
  const w = E.run(E.create({ seed: 'meteor' }), 300);
  const inside = w.creatures.filter((c) => (c.x - 450) ** 2 + (c.y - 280) ** 2 < 75 * 75).length;
  const before = w.creatures.length;
  E.apply(w, { k: 'meteor', x: 450, y: 280 });
  assert.ok(inside > 0);
  assert.equal(before - w.creatures.length, inside);
  assert.equal(w.deaths.meteor, inside);
});

test('genes stay in [0,1] and population stays under its cap at extreme settings', () => {
  const w = E.create({ seed: 'extreme', settings: { food: 6, mutation: 0.2 } });
  for (let i = 0; i < 40; i++) { E.run(w, 100); assert.ok(w.creatures.length <= 700); }
  for (const c of w.creatures) for (const g of E.GENES) assert.ok(c.g[g] >= 0 && c.g[g] <= 1);
});

test('First bloom is won by sowing, and a frozen world with no food goes extinct and is marked lost', () => {
  const w = E.createChallenge('bloom', 'b');
  E.apply(w, { k: 'set', key: 'food', v: 4 });
  E.run(w, 3000);
  assert.ok(w.challenge.won != null && w.challenge.won < 3000, 'won ' + w.challenge.won);
  const d = E.createChallenge('ice', 'd');
  E.apply(w, { k: 'set', key: 'food', v: 0 });
  E.apply(d, { k: 'set', key: 'food', v: 0 });
  E.run(d, 4000);
  assert.equal(d.creatures.length, 0);
  assert.ok(d.challenge.lost != null);
  assert.equal(d.challenge.won, null);
});

test('Ice age can be won by changing the world (more food, more mutation)', () => {
  const w = E.createChallenge('ice', 'ice-test');
  E.apply(w, { k: 'set', key: 'food', v: 3.5 });
  E.apply(w, { k: 'set', key: 'mutation', v: 0.1 });
  E.run(w, 15000);
  assert.ok(w.challenge.won != null, 'fur ' + mean(w, 'fur'));
});
