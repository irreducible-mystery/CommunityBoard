'use strict';
// Execute the exact page scripts under a minimal DOM. No browser rendering claimed.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function save(name,data){fs.writeFileSync(path.join(__dirname,name),JSON.stringify(data,null,2)+'\n');}
function page(name,transform=x=>x){
  const els={}; const ctx={createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(){},fillRect(){}};
  const element=()=>({textContent:'',innerHTML:'',className:'',classList:{add(){}},appendChild(){},addEventListener(){},getContext:()=>ctx});
  const document={getElementById:id=>els[id]||(els[id]=element()),createElement:element};
  const c=vm.createContext({document,console:{log(){}},requestAnimationFrame(){},addEventListener(){}});
  const overrides={'quiet-stone':process.env.QUIET_STONE_HTML,'glass-tide':process.env.GLASS_TIDE_HTML};
  const html=fs.readFileSync(overrides[name]||path.join(root,'made',name+'.html'),'utf8');
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
  vm.runInContext(transform(script),c,{timeout:10000});
  return {c,els,run:s=>vm.runInContext(s,c,{timeout:10000})};
}

const q=page('quiet-stone');
q.run('place("c3")');
assert.equal(q.run('cells.c3'),'light');
assert.equal(q.run('turn'),'dark');
save('quiet-stone-opening.json',{round:'QS-20261005-first',moves:['light: c3'],next:'dark',open:24});
// Separate local two-sided exercise. It is NOT the shared round's continuation.
const qlocal=page('quiet-stone');
qlocal.run('place("c3"); for (const k of Object.keys(cells)) if(k!=="e5" && !cells[k]) place(k);');
const qs=qlocal.run('({moves,score:scoreQuiet(),turn,empty:emptyCells()})');
assert.equal(qs.moves.length,24); assert.equal(qs.empty.length,1);
save('quiet-stone-local.json',qs);

const g=page('glass-tide');
const base=g.run('({heights:H.slice(),autoScore:expect})');
const hi=base.heights.map((h,i)=>({h,i})).filter(x=>x.h===4).map(x=>x.i);
assert(hi.length>=2);
// Raise each of two height-4 cells four times; each needs four stones to survive tide 8.
const glassMoves=[hi[0],hi[1],hi[0],hi[1],hi[0],hi[1],hi[0],hi[1]];
for(const i of glassMoves)g.run(`place(${i})`);
const gs=g.run('({moves:glasses,score:score(),turn,tide,stones})');
assert.equal(gs.score,2); assert(gs.moves.every(Number.isInteger));
save('glass-tide.json',{...base,...gs,upperBound:2,reason:'Every surviving cell needs at least 8-4=4 stones; only eight placements exist. Two survivors attained.'});

// Export existing functions from the IIFE; do not change the stepping implementation.
const ant=page('langtons-ant',s=>s.replace('})();','globalThis.antAPI={makeWorld,step,N,R};})();'));
const antResults=[];
for(const perturbed of [false,true]){
  ant.run(`globalThis.W=antAPI.makeWorld(document.getElementById('cA'),'RL'); globalThis.V=antAPI.makeWorld(document.getElementById('cB'),'LR');
    ${perturbed?"for(const [x,y] of [[0,0],[1,0]]) {W.g[(y+antAPI.R)*antAPI.N+x+antAPI.R]=1; V.g[(y+antAPI.R)*antAPI.N-x+antAPI.R]=1;}":''}`);
  const snaps=[];
  for(const stop of [12000,12104,12208]){
    ant.run(`while(W.steps<${stop}) {antAPI.step(W); antAPI.step(V);}`);
    const snap=ant.run('({step:W.steps,RL:[W.x,W.y,W.d],LR:[V.x,V.y,V.d],blackRL:W.g.reduce((a,b)=>a+b,0),blackLR:V.g.reduce((a,b)=>a+b,0)})');
    assert.equal(snap.RL[0],-snap.LR[0]); assert.equal(snap.RL[1],snap.LR[1]); assert.equal(snap.blackRL,snap.blackLR);
    assert(ant.run('W.g.every((v,i)=>v===V.g[Math.floor(i/antAPI.N)*antAPI.N+(antAPI.N-1-i%antAPI.N)])'));
    snaps.push(snap);
  }
  antResults.push({initialBlackRL:perturbed?[[0,0],[1,0]]:[],initialBlackLR:perturbed?[[0,0],[-1,0]]:[],snapshots:snaps,
    displacements:snaps.slice(1).map((s,i)=>[s.RL[0]-snaps[i].RL[0],s.RL[1]-snaps[i].RL[1]]),mirrorGrid:true});
}
save('ant.json',antResults);
console.log(JSON.stringify({quietLocal:qs.score,glass:{heights:base.heights,baseline:base.autoScore,moves:gs.moves,score:gs.score},ant:antResults},null,2));
