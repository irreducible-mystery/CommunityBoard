'use strict';
// Exercise the actual page handlers of made/dice.html with a minimal DOM under node:vm, the way
// tests/test_noise_lab_records.cjs does; no browser packages. Every <script> block of the page runs
// in one context, so the second block finds the engine the first one defines, exactly as in a
// browser. Run with: node --test tests/test_dice_page.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// The same engine, loaded the command line's way, as an independent realm to cross-check records.
const Dice = require(path.join(__dirname, '../tools/dice.cjs'));
const plain = (x) => JSON.parse(JSON.stringify(x));
const NOISE_LAB_POOL = ['a flock', 'a maze', 'a word ladder', 'a memory', 'a rhythm', 'an empty space'];

function page() {
  const elements = new Map();
  const initial = {seed: 'quiet-hour-15', stream: '', kind: 'uniform', count: '6', min: '1', max: '6', p: '0.5',
    words: '4', poolcount: '6', k: '3', weights: '2,1,1,1,1,1'};
  const make = (tag) => ({tag, value: initial[tag] || '', textContent: '', className: '', hidden: false, children: [],
    append(...nodes) { this.children.push(...nodes); }, appendChild(node) { this.children.push(node); return node; },
    focus() {}, select() {}, click() {}});
  const get = (id) => { if (!elements.has(id)) elements.set(id, make(id)); return elements.get(id); };
  const context = vm.createContext({document: {getElementById: get, createElement: make},
    crypto: globalThis.crypto || require('node:crypto').webcrypto, URL: globalThis.URL, Blob: globalThis.Blob,
    setTimeout: (fn) => { fn(); return 0; }, navigator: {}});
  const html = fs.readFileSync(path.join(__dirname, '../made/dice.html'), 'utf8');
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) vm.runInContext(match[1], context, {timeout: 5000});
  return {get, record: () => JSON.parse(get('record').value), click: (id) => get(id).onclick()};
}

test('each panel button runs a request through Dice.run whose kind, stream and seed match the controls', () => {
  const {get, record, click} = page();
  assert.equal(get('record').value, '', 'nothing is drawn on load');
  const expected = [['draw', 'uniform', 'uniform'], ['names', 'name', 'name'], ['pick', 'pick', 'pick'],
    ['shuffle', 'shuffle', 'shuffle'], ['sample', 'sample', 'sample'], ['weighted', 'weighted', 'weighted'],
    ['suggest', 'suggest', 'suggest']];
  for (const [button, kind, stream] of expected) {
    click(button);
    const rec = record();
    assert.equal(get('error').textContent, '', button + ' raised no error');
    assert.equal(rec.request.version, 'dice/1');
    assert.equal(rec.request.kind, kind, button + ' draws kind ' + kind);
    assert.equal(rec.request.stream, stream, button + ' draws from stream ' + stream);
    assert.equal(rec.request.seed, 'quiet-hour-15');
    assert.deepEqual(plain(Dice.run(rec.request)), rec, 'the record is what the engine computes for its own request');
  }
  get('stream').value = 'field'; click('draw');
  assert.equal(record().request.stream, 'field', 'a named stream replaces the default');
});

test('the numbers panel draws every kind with only that kind\'s parameters, parsed strictly', () => {
  const {get, record, click} = page();
  const params = {words: ['count'], uniform: ['count'], integer: ['count', 'min', 'max'], normal: ['count'], coin: ['count', 'p'], hex: ['words']};
  for (const kind of Object.keys(params)) {
    get('kind').value = kind; get('kind').onchange(); click('draw');
    assert.equal(get('error').textContent, '');
    assert.equal(record().request.kind, kind);
    assert.deepEqual(Object.keys(record().request.params), params[kind], kind + ' records exactly its parameters');
    assert.match(get('numbersout').textContent, new RegExp('^stream ' + kind + ': '));
  }
  assert.equal(record().result.length, 32, 'hex with 4 words is 32 digits');
  assert.equal(get('fwords').hidden, false); assert.equal(get('fcount').hidden, true);
  get('kind').value = 'integer'; get('kind').onchange();
  assert.equal(get('fmin').hidden, false); assert.equal(get('fp').hidden, true);
  get('count').value = '3'; click('draw');
  const kept = record();
  assert.deepEqual(kept.request.params, {count: 3, min: 1, max: 6});
  for (const [field, value, message] of [['count', '3.0', /Count must be an integer/], ['count', '', /Count must be an integer/],
    ['max', '0', /min must not exceed max/], ['max', '1e3', /Max must be an integer/]]) {
    const before = get(field).value; get(field).value = value; click('draw');
    assert.match(get('error').textContent, message);
    assert.deepEqual(record(), kept, 'a refused draw leaves the record alone');
    get(field).value = before;
  }
  get('kind').value = 'coin'; get('kind').onchange(); get('p').value = '0x1'; click('draw');
  assert.match(get('error').textContent, /p must be a finite decimal number/);
  get('p').value = '1'; click('draw');
  assert.deepEqual(record().result, [true, true, true]);
});

test('the pool panel starts with the Noise Lab ingredients and reads count, k and weights from its fields', () => {
  const {get, record, click} = page();
  assert.equal(get('pool').value, NOISE_LAB_POOL.join('\n'));
  click('shuffle');
  assert.deepEqual(record().request.params.pool, NOISE_LAB_POOL);
  assert.deepEqual(record().result.slice().sort(), NOISE_LAB_POOL.slice().sort(), 'a shuffle is a permutation');
  get('poolcount').value = '2'; click('pick');
  assert.equal(record().result.length, 2);
  get('k').value = '4'; click('sample');
  assert.equal(record().request.params.k, 4); assert.equal(new Set(record().result).size, 4);
  get('weights').value = '0, 0, 0, 0, 0, 5'; click('weighted');
  assert.deepEqual(record().request.params.weights, [0, 0, 0, 0, 0, 5]);
  assert.deepEqual(record().result, ['an empty space', 'an empty space']);
  const kept = record();
  get('weights').value = '1,2'; click('weighted');
  assert.match(get('error').textContent, /one number per pool item/); assert.deepEqual(record(), kept);
  get('pool').value = ' \n\n'; click('shuffle');
  assert.match(get('error').textContent, /pool must have 1 to 1000 items/); assert.deepEqual(record(), kept);
  get('pool').value = '  one \r\n\r\ntwo\n'; click('shuffle');
  assert.deepEqual(record().request.params.pool, ['one', 'two'], 'lines are trimmed and blank lines dropped, as the command lines do');
});

test('suggest counts its stream up per seed (suggest, suggest/1, ...) and offers the pasted made/ listing as its pool', () => {
  const {get, record, click} = page();
  const pool = get('suggestpool').value.split('\n');
  assert.ok(pool.length >= 2 && pool.includes('dice.html') && pool.includes('noise-lab.html') && !pool.includes('README.md'));
  assert.deepEqual(pool, pool.slice().sort(), 'in code point order, as the command lines sort');
  // Nothing is ever deleted from made/ (RULES.md), so every pasted name should still be there.
  const made = new Set(fs.readdirSync(path.join(__dirname, '../made')));
  for (const name of pool) assert.ok(made.has(name), name + ' is still in made/');
  click('suggest'); assert.equal(record().request.stream, 'suggest', 'the first suggestion is the command lines\' default stream');
  click('suggest'); assert.equal(record().request.stream, 'suggest/1');
  assert.deepEqual(record().request.params.pool, pool);
  const r = record().result;
  assert.notEqual(r.subject, r.partner);
  assert.ok(Dice.OPERATIONS.includes(r.operation) && Dice.CONSTRAINTS.includes(r.constraint));
  assert.deepEqual(r.choices, ['accept', 'reinterpret', 'decline']);
  assert.match(get('suggestout').textContent, /^stream suggest\/1\nSubject: .+\nPartner: .+\nOperation: .+\nConstraint: .+\n\n.+\n\nChoices: accept \/ reinterpret \/ decline\./);
  get('seed').value = 'another seed'; click('suggest'); assert.equal(record().request.stream, 'suggest', 'a new seed starts again at the bare kind');
  get('seed').value = 'quiet-hour-15'; click('suggest'); assert.equal(record().request.stream, 'suggest/2', 'the first seed resumes');
  get('stream').value = 'field'; click('suggest'); assert.equal(record().request.stream, 'field');
  get('stream').value = ''; click('suggest'); assert.equal(record().request.stream, 'suggest/3', 'a named stream does not count');
  get('suggestpool').value = 'only one'; click('suggest');
  assert.match(get('error').textContent, /2 to 1000 items/);
});

test('replaying the record box reproduces it without touching the controls; a bad replay changes nothing', () => {
  const {get, record, click} = page();
  get('kind').value = 'normal'; get('kind').onchange(); get('count').value = '4'; click('draw');
  const drawn = record();
  get('count').value = '9'; get('seed').value = 'edited later';
  get('replayinput').value = get('record').value; click('replay');
  assert.deepEqual(record(), drawn);
  assert.match(get("status").textContent, /matches the recomputed one, value for value/);
  assert.equal(get('count').value, '9'); assert.equal(get('seed').value, 'edited later');
  get('replayinput').value = JSON.stringify(drawn.request); click('replay');
  assert.deepEqual(record(), drawn, 'a bare request replays too');
  assert.match(get('status').textContent, /Recomputed the request/);
  get('replayinput').value = JSON.stringify({...drawn, result: drawn.result.map((x) => x + 1)}); click('replay');
  assert.deepEqual(record(), drawn, 'the saved result is recomputed, not trusted');
  assert.match(get('status').textContent, /differs/);
  const bad = ['', 'not json', '[1]', 'null',
    '{"version":"dice/2","seed":"x","stream":"y","kind":"words","params":{"count":1}}',
    JSON.stringify({request: {...drawn.request, extra: 1}}),
    JSON.stringify({request: {...drawn.request, params: {count: 0}}})];
  for (const text of bad) {
    get('replayinput').value = text; click('replay');
    assert.notEqual(get('error').textContent, '', JSON.stringify(text) + ' is refused');
    assert.equal(get('status').textContent, '');
    assert.deepEqual(record(), drawn, 'the record is unchanged after ' + JSON.stringify(text));
  }
  click('names');
  assert.equal(get('error').textContent, '', 'the next good draw clears the error');
});

test('new seed draws a name through Dice.run from fresh entropy, and later draws use it', () => {
  const {get, record, click} = page();
  click('newseed');
  assert.equal(get('error').textContent, '');
  const seed = get('seed').value;
  assert.match(seed, /^[a-z]+-[a-z]+-[1-9][0-9]?$/);
  const [adjective, noun] = seed.split('-');
  assert.ok(Dice.ADJECTIVES.includes(adjective) && Dice.NOUNS.includes(noun));
  const entropy = get('status').textContent.match(/temporary seed ([0-9a-f]{32}) /)[1];
  assert.equal(Dice.run({version: 'dice/1', seed: entropy, stream: 'name', kind: 'name', params: {count: 1}}).result[0], seed,
    'the status names the temporary seed that gives the new one');
  assert.equal(get('record').value, '', 'the temporary draw is not the record');
  click('names');
  assert.equal(record().request.seed, seed);
  assert.equal(record().result.length, 6);
});

test('copy and download act on the latest record and refuse an empty one', () => {
  const {get, click} = page();
  click('copy'); assert.match(get('error').textContent, /draw something first/);
  click('download'); assert.match(get('error').textContent, /draw something first/);
  click('draw'); click('copy');
  assert.equal(get('error').textContent, ''); assert.match(get('status').textContent, /Selected the record/);
  click('download');
  assert.equal(get('error').textContent, ''); assert.match(get('status').textContent, /Downloaded dice-uniform-uniform\.json\./);
});

test('the checks list is filled from Dice.checks() with no FAIL, and the summary says so', () => {
  const {get} = page();
  const items = get('checks').children;
  assert.equal(items.length, Dice.checks().length);
  assert.ok(items.length >= 13, 'the spec lists at least thirteen checks');
  for (const item of items) {
    assert.equal(item.className, 'ok', item.children[1].textContent + item.children[2].textContent);
    assert.equal(item.children[0].textContent, 'ok');
  }
  assert.equal(get('checksummary').textContent, items.length + ' checks, all ok.');
});
