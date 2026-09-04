/* The plan is 426 hours run at 3-4 evening hours a week. These assert that the
   date-bound tasks land before the date they are written for, and that the
   re-sequence did not lose anyone's saved progress. */
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[]; const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const p=await (await b.newContext({viewport:{width:1280,height:1000}})).newPage();
 const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(400);

 // week each task is reached at 4 evening hours a week
 const wk=await p.evaluate(()=>{
   let run=0,out={};
   ALLDAYS.forEach(d=>{run+=d.m;out[d.id]=run/240;});
   return out;
 });
 const at=title=>p.evaluate(x=>{const d=ALLDAYS.find(y=>y.t===x);return d?d.id:null;},title);

 // 1. structure survived
 const shape=await p.evaluate(()=>{
   const per={};ALLDAYS.forEach(d=>per[d.w]=(per[d.w]||0)+1);
   return {n:ALLDAYS.length,blocks:Object.keys(per).length,
           allSeven:Object.values(per).every(v=>v===7),
           mins:ALLDAYS.reduce((a,d)=>a+d.m,0),
           dupTitles:ALLDAYS.length-new Set(ALLDAYS.map(d=>d.t)).size};
 });
 t('still 385 tasks in 55 blocks of 7',shape.n===385&&shape.blocks===55&&shape.allSeven);
 t('total workload unchanged at 426 hours',Math.round(shape.mins/60)===426,String(shape.mins/60));
 t('no duplicate titles after the swaps',shape.dupTitles===0);

 // 2. the December kit lands before the decision (~week 21)
 const DEC=['Decision criteria, before the December fork',
            'Hold the call before the December fork',
            'Check the licence clock before December',
            'Build the three-column compensation model',
            'Model the internal role like an outside offer',
            'Two negotiation scripts, internal and external',
            'Florida breakeven, both move dates'];
 for(const title of DEC){
   const id=await at(title);
   t('lands before December: '+title,id!==null&&wk[id]<=23.5,id?('week '+wk[id].toFixed(1)):'TASK NOT FOUND');
 }
 // and the two that consume the kit sit right after it
 for(const title of ['Runway for both move dates','Price both forks before December']){
   const id=await at(title);
   t('sits with the December kit: '+title,id!==null&&wk[id]<=25.5,id?('week '+wk[id].toFixed(1)):'NOT FOUND');
 }

 // 3. the credential pair straddles the exam (~week 9)
 const stage=await at('Stage the credential announcement');
 const send=await at('When it lands: hold the send');
 t('credential announcement is staged before the exam result',wk[stage]<=9,'week '+wk[stage].toFixed(1));
 t('the send is held for just after the result',wk[send]>wk[stage]&&wk[send]<=13,'week '+wk[send].toFixed(1));

 // 4. dependencies still point backwards
 const dep=[['Generate your synthetic dataset','Load your synthetic book into Tableau'],
            ['Install DuckDB and write your first SELECT','Answer ten questions with SQL'],
            ['Set the rule for what leaves the building','Read the whole site, then go live'],
            ['Read the market in data','Build the three-column compensation model'],
            ['Build the three-column compensation model','Two negotiation scripts, internal and external'],
            ['Florida breakeven, both move dates','Runway for both move dates'],
            ['Decision criteria, before the December fork','Price both forks before December'],
            ['Stage the credential announcement','When it lands: hold the send'],
            ['Read the market in data','Close the gaps the postings named']];
 for(const [first,then] of dep){
   const a=await at(first), c=await at(then);
   t('"'+first+'" comes before "'+then+'"',a&&c&&wk[a]<wk[c],
     a&&c?('weeks '+wk[a].toFixed(1)+' vs '+wk[c].toFixed(1)):'missing');
 }

 // 5. every walkthrough and link followed its task to the new id
 const bound=await p.evaluate(()=>{
   const bad=[];
   Object.keys(STEPS).forEach(k=>{const d=ALLDAYS.find(x=>x.id===k);
     if(!d)bad.push('STEPS '+k+' has no task');
     else if(STEPS[k].t!==d.t)bad.push('STEPS '+k+' bound to "'+STEPS[k].t+'" not "'+d.t+'"');});
   Object.keys(LINKS).forEach(k=>{if(!ALLDAYS.find(x=>x.id===k))bad.push('LINKS '+k+' has no task');});
   return bad;
 });
 t('every walkthrough and link followed its task',bound.length===0,bound.slice(0,3).join(' | '));

 // 6. saved progress survives the id changes
 const mig=await p.evaluate(()=>{
   // a save from before the re-sequence: these ids meant these tasks
   const old={v:4,done:{"34-0":111,"12-0":222,"5-2":333},
              prog:{"42-5":50},work:{"34-0":{notes:"my comp model notes"}}};
   const m=MERGE(JSON.parse(JSON.stringify(old)));
   const idOf=t=>(ALLDAYS.find(d=>d.t===t)||{}).id;
   return {comp:m.done[idOf('Build the three-column compensation model')],
           suit:m.done[idOf('Suitability in operational terms')],
           duck:m.done[idOf('Install DuckDB and write your first SELECT')],
           crit:m.prog[idOf('Decision criteria, before the December fork')],
           notes:(m.work[idOf('Build the three-column compensation model')]||{}).notes,
           kept:Object.keys(m.done).length};
 });
 t('a completed task stays completed after the move',mig.comp===111,JSON.stringify(mig));
 t('the task it swapped with also keeps its tick',mig.suit===222);
 t('an untouched task is unaffected',mig.duck===333);
 t('partial progress follows too',mig.crit===50);
 t('per-task work follows the task, not the slot',mig.notes==='my comp model notes');
 t('nothing was dropped in migration',mig.kept===3);
 const twice=await p.evaluate(()=>{
   const o={v:4,done:{"34-0":111}};
   const once=MERGE(JSON.parse(JSON.stringify(o)));
   const again=MERGE(JSON.parse(JSON.stringify(once)));
   const id=(ALLDAYS.find(d=>d.t==='Build the three-column compensation model')||{}).id;
   return again.done[id]===111&&Object.keys(again.done).length===1;
 });
 t('migrating an already-migrated save is a no-op',twice);

 // 7. phases now say how long they really take
 await p.evaluate(()=>go('plan')); await p.waitForTimeout(250);
 const ph=await p.textContent('#phaseCards');
 t('phase cards state the real month, not just the block',/month 6/.test(ph)&&/month 25/.test(ph),ph.slice(0,120));

 t('no page errors',errs.length===0,errs[0]||'');
 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 fail.forEach(f=>console.log('  x '+f));
 await b.close(); process.exit(fail.length?1:0);
})();
