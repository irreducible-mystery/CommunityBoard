'use strict';
// Runs the page's engine (the script block with id "rq-engine") under Node.
// Run with: node --test tests/test_right_question.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../made/right-question.html'), 'utf8');
const src = html.match(/<script id="rq-engine">([\s\S]*?)<\/script>/)[1];
const ctx = { module: { exports: {} } };
vm.runInNewContext(src, ctx, { timeout: 60000 });
const RQ = ctx.module.exports;

test('the ten load checks all pass', () => {
  const list = RQ.checks();
  assert.equal(list.length, 10);
  for (const c of list) assert.equal(c.ok, true, c.name + ' ' + c.detail);
});

test('phase cancellation is only in X', () => {
  const bothPi = RQ.both(Math.PI);
  assert.ok(Math.abs(RQ.ask(bothPi, 'X').pPlus) < 1e-12);
  assert.ok(Math.abs(RQ.ask(bothPi, 'Z').pPlus - 0.5) < 1e-12);
  assert.ok(Math.abs(RQ.ask(RQ.both(0), 'X').pPlus - 1) < 1e-12);
  assert.ok(Math.abs(RQ.ask(RQ.both(Math.PI / 2), 'Y').pPlus - 1) < 1e-12);
});

test('an unnamed question is not aimed at any of the three distinctions', () => {
  for (const distinction of ['is-isnot', 'both-neither', 'phase']) {
    const v = RQ.assess({ distinction, axis: null, record: 'distribution', alpha: Math.PI });
    assert.equal(v.aimed, false);
  }
});

test('Z settles is against is not in one shot; X does not see it', () => {
  const z = RQ.assess({ distinction: 'is-isnot', axis: 'Z', record: 'shot', alpha: 0 });
  const x = RQ.assess({ distinction: 'is-isnot', axis: 'X', record: 'distribution', alpha: 0 });
  assert.equal(z.aimed, true);
  assert.equal(z.settles, true);
  assert.equal(x.aimed, false);
});

test('X sees both against neither only as a distribution, not as one settling shot', () => {
  const dist = RQ.assess({ distinction: 'both-neither', axis: 'X', record: 'distribution', alpha: 0 });
  const shot = RQ.assess({ distinction: 'both-neither', axis: 'X', record: 'shot', alpha: 0 });
  assert.equal(dist.aimed, true);
  assert.equal(dist.settles, true);
  assert.equal(shot.aimed, true);
  assert.equal(shot.settles, false);
});

test('the Bell record is the correlation, and the local coin is fair', () => {
  const want = { X: 1, Y: -1, Z: 1 };
  for (const axis of ['X', 'Y', 'Z']) {
    const b = RQ.bellReport(axis);
    assert.ok(Math.abs(b.before - 1) < 1e-9, axis);
    assert.ok(Math.abs(b.after) < 1e-12, axis);
    assert.ok(Math.abs(b.agree - want[axis]) < 1e-9, axis + ' ' + b.agree);
    assert.ok(Math.abs(b.p - 0.5) < 1e-9, axis);
  }
});
