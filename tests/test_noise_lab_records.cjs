'use strict';
// Exercise the actual page handlers with a minimal DOM; no browser packages.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function page() {
  const elements = new Map();
  const initial = {seed:'room-for-chance',regime:'3.9',noise:'0.002',count:'6',distribution:'uniform',minimum:'1',maximum:'6'};
  const canvas = new Proxy({}, {get: () => () => {}});
  const get = id => {
    if (!elements.has(id)) elements.set(id, {value:initial[id] || '',textContent:'',
      setAttribute() {},getBoundingClientRect:() => ({width:600}),getContext:() => canvas});
    return elements.get(id);
  };
  const context = vm.createContext({document:{getElementById:get},
    window:{devicePixelRatio:1,addEventListener() {}},setInterval:() => 1,clearInterval() {}});
  const html = fs.readFileSync(path.join(__dirname,'../made/noise-lab.html'),'utf8');
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))
    vm.runInContext(match[1],context,{timeout:1000});
  return {get, record:() => JSON.parse(get('record').value)};
}

test('simulation controls preserve an invitation until explicitly recorded',() => {
  const {get,record} = page();
  get('invite').onclick();
  const invitation = record();
  assert.equal(invitation.request.kind,'invitation');
  get('noise').value = '0.017'; get('noise').oninput();
  get('regime').value = '2.8'; get('regime').onchange();
  get('step').onclick(); get('finish').onclick();
  assert.deepEqual(record(),invitation);
  get('simrecord').onclick();
  assert.equal(record().request.kind,'simulation');
  assert.equal(record().request.params.noise,0.017);
  assert.equal(record().request.params.r,2.8);
  get('invite').onclick();
  assert.equal(record().request.params.index,1);
  assert.equal(get('error').textContent,'');
});

test('number and replay records survive parameter edits; reset deliberately replaces them',() => {
  const {get,record} = page();
  get('numbers').onclick();
  const numbers = record();
  get('noise').value = '0.01'; get('noise').oninput();
  assert.deepEqual(record(),numbers);
  get('replayinput').value = JSON.stringify(numbers); get('replay').onclick();
  const replay = record();
  get('regime').value = '2.8'; get('regime').onchange();
  assert.deepEqual(record(),replay);
  get('seed').value = 'a new seed'; get('reset').onclick();
  assert.equal(record().request.kind,'simulation');
  assert.equal(record().request.seed,'a new seed');
  get('numbers').onclick();
  assert.equal(record().request.params.index,0);
});
