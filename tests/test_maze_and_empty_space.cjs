'use strict';
// Runs the page's own script under Node with a stub DOM, then checks the counts.
// Run with: node --test tests/test_maze_and_empty_space.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function page(seed) {
  const html = fs.readFileSync(path.join(__dirname, '../made/maze-and-empty-space.html'), 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const els = new Map(), noop = () => {};
  const ctx = new Proxy({}, { get: () => noop });
  const el = id => { if (!els.has(id)) els.set(id, { value: id === 'seed' ? seed : '0', textContent: '',
    addEventListener: noop, getContext: () => ctx, width: 744, height: 504 }); return els.get(id); };
  const sandbox = { document: { getElementById: el, documentElement: {} },
    getComputedStyle: () => ({ getPropertyValue: () => '#000' }), crypto: { getRandomValues: noop },
    Number, Math, JSON, Object, Uint8Array, Int32Array, Float64Array, Uint32Array };
  sandbox.window = sandbox;
  vm.runInNewContext(script, sandbox, { timeout: 20000 });
  return sandbox.MAZE;
}

test('a perfect maze has exactly one shortest route', () => {
  const rows = page('claude-session-01BaeJNnZ').sweep();
  assert.equal(rows[0].result.routes, 1);
  assert.equal(rows[0].result.cells_on_shortest_routes, rows[0].result.length + 1);
});

test('the published sweep for the session seed is reproduced', () => {
  const rows = page('claude-session-01BaeJNnZ').sweep();
  const got = rows.map(r => [r.request.params.room, r.result.length, r.result.routes]);
  assert.deepEqual(got.slice(0, 7), [[0, 200, 1], [1, 200, 1], [2, 186, 1], [3, 186, 3], [4, 184, 1], [5, 174, 3], [6, 92, 56]]);
  assert.deepEqual(got[9], [9, 76, 12870]);
  assert.deepEqual(got[15], [15, 76, 4457400]);
});

test('a bigger room never lengthens the shortest route', () => {
  for (const seed of ['claude-session-01BaeJNnZ', 'room-for-chance', 'tetralemma']) {
    const rows = page(seed).sweep();
    for (let i = 1; i < rows.length; i++) assert.ok(rows[i].result.length <= rows[i - 1].result.length, seed + ' room ' + i);
  }
});
