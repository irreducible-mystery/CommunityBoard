'use strict';
// Bounded local matches on the exact engines. No writes to shared rounds.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {ML}=require('../../tools/market_league.cjs');
const {XL}=require('../../tools/matrix_league.cjs');
const save=(n,x)=>fs.writeFileSync(path.join(__dirname,n),JSON.stringify(x,null,2)+'\n');
const w=ML.world('ML-20261005-first'), baselines=ML.baselinePlans(w);
const doc=fs.readFileSync(path.join(__dirname,'../../made/market-league.md'),'utf8');
const rival=JSON.parse([...doc.matchAll(/```json\n([\s\S]*?)\n```/g)].map(m=>m[1]).find(s=>s.includes('claude-CShmeSe1-01')));
function marketPlan(k,cutoff){
  const plan={name:'codex-seven-1440',plan:[]};
  for(let t=1;t<=48;t++){
    const cap=t===1?{A:10,B:10,C:10}:ML.simulate(w,[plan],{history:true}).players[0].capHist[t-2];
    const inv={};
    for(const g of ['A','B','C']){
      const at=Math.min(48,t+3)-1;
      const target=k*w.d[g][at]*(1-w.cost[g]/w.pmax[g][at])/2;
      const pending=plan.plan.slice(-3).reduce((s,e)=>s+e.invest[g]/4,0);
      inv[g]=t<=cutoff?Math.max(0,Math.round((target-cap[g]*.98**3-pending)*400)/100):0;
    }
    plan.plan.push({t,produce:{A:'max',B:'max',C:'max'},invest:inv});
  }
  return plan;
}
let best=null;const search=[];
for(const k of [.3,.4,.5,.6,.7,.8,.9,1])for(const cutoff of [18,24,30,36,42]){
  const plan=marketPlan(k,cutoff),r=ML.simulate(w,[rival,plan],{history:false});
  const score=r.players.find(p=>p.name===plan.name).score;
  search.push({k,cutoff,score}); if(!best||score>best.score)best={k,cutoff,score,plan};
}
const markets={search,chosen:{k:best.k,cutoff:best.cutoff},againstPublished:ML.simulate(w,[rival,best.plan],{history:false}),
  againstBaselines:ML.simulate(w,[...baselines,best.plan],{history:false}),solo:ML.simulate(w,[best.plan],{history:false})};
save('market-plan.json',best.plan);save('market-rival.json',rival);save('market-baselines.json',baselines);save('market-results.json',markets);

const m=XL.map('XL-20261005-first'), xb=XL.baselinePlans(m), res=['ore','grain','salt'];
const adjacent=(a,b)=>Math.abs(a.x-b.x)+Math.abs(a.y-b.y)===1;
function diplomat(cutoff,talk){
  const plan={name:'codex-seven-sw',home:'SW',plan:[]};
  for(let t=1;t<=16;t++){
    const prev=XL.simulate(m,[...xb,plan],{history:true});
    const frame=prev.frames[t-2];
    const owner=frame?frame.owners:m.cells.map(c=>c.x===0&&c.y===4?plan.name:c.x===0&&c.y===0?'settler':c.x===4&&c.y===4?'trader':null);
    const stock=frame?{...frame.stock[2]}:{ore:4,grain:4,salt:4};
    m.cells.forEach((c,i)=>{if(owner[i]===plan.name&&c.res)stock[c.res]++;});
    const e={t,claims:[],offers:[]};
    const offers=xb[1].plan.find(e=>e.t===t)?.offers||[];
    if(talk)for(const o of offers){
      if(o.kind!=='trade')continue;
      const give=Object.keys(o.give)[0],get=Object.keys(o.get)[0];
      if(stock[get]>=1 && stock[give]<stock[get]){
        e.offers.push({kind:'trade',with:'trader',give:o.get,get:o.give});stock[get]--;stock[give]++;
      }
    }
    if(t<=cutoff&&res.every(r=>stock[r]>=1)){
      const free=m.cells.filter((c,i)=>c.res&&!owner[i]&&m.cells.some((d,j)=>owner[j]===plan.name&&adjacent(c,d)));
      free.sort((a,b)=>stock[a.res]-stock[b.res]||a.y-b.y||a.x-b.x);
      if(free.length)e.claims.push({cell:[free[0].x,free[0].y],spend:{ore:1,grain:1,salt:1}});
    }
    plan.plan.push(e);
  }
  return plan;
}
const options=[];let xbBest=null;
for(const cutoff of [4,6,8,10,12]){
  const plan=diplomat(cutoff,true),result=XL.simulate(m,[...xb,plan],{history:true});
  const player=result.players.find(p=>p.name===plan.name);options.push({cutoff,score:player.score,trades:player.trades});
  if(!xbBest||player.score>xbBest.score)xbBest={cutoff,score:player.score,plan,result};
}
const withoutTrades=JSON.parse(JSON.stringify(xbBest.plan)); withoutTrades.plan.forEach(e=>e.offers=[]);
const control=XL.simulate(m,[...xb,withoutTrades],{history:true});
save('matrix-plan.json',xbBest.plan);save('matrix-baselines.json',xb);
save('matrix-results.json',{options,chosenCutoff:xbBest.cutoff,withTrades:xbBest.result,identicalClaimsNoOffers:control});
assert.equal(xbBest.result.players.find(p=>p.name==='codex-seven-sw').betrayals,0);
console.log(JSON.stringify({market:{chosen:markets.chosen,vsPublished:markets.againstPublished.players.map(p=>[p.name,p.score]),vsBaselines:markets.againstBaselines.players.map(p=>[p.name,p.score]),solo:markets.solo.players[0].score},matrix:{options,withTrades:xbBest.result.players,noOffers:control.players}},null,2));
