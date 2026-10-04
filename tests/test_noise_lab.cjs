'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const path = require('node:path');
const lab = require('../tools/noise_lab.cjs');
const request = (kind,params,seed='room-for-chance') => ({version:lab.VERSION,seed,kind,params});
const run = (...args) => JSON.parse(JSON.stringify(lab.run(request(...args))));

test('versioned invitation fixture and replay remain stable',()=>{
  const record=run('invitation',{index:0,pool:lab.DEFAULT_POOL});
  assert.deepEqual(record.result.ingredients,['a flock','a memory']);
  assert.equal(record.result.constraint,'Make something that works without a network.');
  assert.equal(JSON.stringify(lab.run(record.request)),JSON.stringify(record));
});
test('draw streams are independent of calls and simulation parameters',()=>{
  const params={index:2,count:20,distribution:'uniform'};
  const before=run('numbers',params);
  run('simulation',{r:3.9,noise:.03,steps:100});run('invitation',{index:6,pool:lab.DEFAULT_POOL});
  assert.deepEqual(run('numbers',params),before);
  assert.notDeepEqual(run('numbers',{...params,index:3}).result,before.result);
  assert.notDeepEqual(run('numbers',params,'another-seed').result,before.result);
});
test('zero noise exactly preserves baseline; chaotic and settling regimes differ',()=>{
  const chaotic=run('simulation',{r:3.9,noise:0,steps:240}).result;
  assert.deepEqual(chaotic.baseline,chaotic.disturbed);
  assert.ok(Math.max(...chaotic.baseline.map((v,i)=>Math.abs(v-chaotic.nearby[i])))>.1);
  const settled=run('simulation',{r:2.8,noise:0,steps:240}).result;
  assert.ok(Math.abs(settled.baseline[240]-(1-1/2.8))<1e-12);
  assert.ok(Math.abs(settled.baseline[240]-settled.nearby[240])<1e-12);
});
test('noise stays bounded across seeds and extreme permitted amplitude',()=>{
  for(let i=0;i<20;i++){
    const result=run('simulation',{r:3.9,noise:.03,steps:2000},String(i)).result;
    for(const key of ['baseline','nearby','disturbed'])assert.ok(result[key].every(v=>Number.isFinite(v)&&v>=0&&v<=1));
  }
});
test('numeric distributions honor ranges and do not produce nonfinite values',()=>{
  const ints=run('numbers',{index:0,count:1000,distribution:'integer',min:-2,max:2}).result;
  assert.deepEqual([...new Set(ints)].sort((a,b)=>a-b),[-2,-1,0,1,2]);
  assert.ok(ints.every(v=>Number.isInteger(v)&&v>=-2&&v<=2));
  assert.deepEqual(run('numbers',{index:0,count:5,distribution:'integer',min:4,max:4}).result,[4,4,4,4,4]);
  assert.ok(run('numbers',{index:0,count:1000,distribution:'normal'}).result.every(Number.isFinite));
  assert.ok(run('numbers',{index:0,count:1000,distribution:'uniform'}).result.every(v=>v>=0&&v<1));
});
test('invitations always use two distinct pool members',()=>{
  for(let index=0;index<100;index++){
    const result=run('invitation',{index,pool:['one','two']}).result;
    assert.deepEqual([...result.ingredients].sort(),['one','two']);
  }
});
test('invalid inputs fail instead of silently changing experiments',()=>{
  const good=request('numbers',{index:0,count:6,distribution:'uniform'});
  for(const bad of [{...good,seed:''},{...good,version:'noise-lab/999'},{...good,params:{...good.params,count:1e9}},{...good,params:{...good.params,index:-1}},{...good,params:{...good.params,count:NaN}}])assert.throws(()=>lab.run(bad));
  assert.throws(()=>run('invitation',{index:0,pool:['a',' a ']}));
  assert.throws(()=>run('invitation',{index:0,pool:['one']}));
  assert.throws(()=>run('numbers',{index:0,count:1,distribution:'integer',min:2,max:1}));
  assert.throws(()=>run('simulation',{r:3.9,noise:Infinity,steps:10}));
});
test('CLI produces the same record and exits nonzero for bad arguments',()=>{
  const cli=path.join(__dirname,'../tools/noise_lab.cjs');
  const result=spawnSync(process.execPath,[cli,'invitation','room-for-chance'],{encoding:'utf8'});
  assert.equal(result.status,0);
  assert.deepEqual(JSON.parse(result.stdout),run('invitation',{index:0,pool:lab.DEFAULT_POOL}));
  assert.notEqual(spawnSync(process.execPath,[cli,'numbers','seed','0','NaN']).status,0);
});
