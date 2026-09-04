/* Guards against the class of bug where a task is retargeted and its
   walkthrough silently stays attached to the new task. */
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs'),crypto=require('crypto');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[]; const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
const FP=JSON.parse(fs.readFileSync(__dirname+'/steps-fingerprints.json','utf8'));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const p=await (await b.newContext({viewport:{width:1280,height:1000}})).newPage();
 const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(400);

 const data=await p.evaluate(()=>{
   const out={};
   Object.keys(STEPS).forEach(k=>{
     const d=ALLDAYS.find(x=>x.id===k);
     out[k]=d?{boundTo:STEPS[k].t,title:d.t,do_:d.d,output:d.o,n:STEPS[k].s.length,
               shown:!!stepList(d),stale:stepsStale(d)}:null;
   });
   return out;
 });

 // 1. every walkthrough points at a task that exists
 const orphans=Object.keys(data).filter(k=>!data[k]);
 t('no walkthrough points at a task that does not exist',orphans.length===0,orphans.join(','));

 // 2. THE BUG: the title a walkthrough was written for must still be the task's title
 const drifted=Object.keys(data).filter(k=>data[k]&&data[k].boundTo!==data[k].title)
   .map(k=>k+' written for "'+data[k].boundTo+'" but task is now "'+data[k].title+'"');
 t('every walkthrough is still bound to its own task',drifted.length===0,drifted.join(' | '));

 // 3. and none is being withheld at runtime
 const withheld=Object.keys(data).filter(k=>data[k]&&data[k].stale);
 t('no walkthrough is withheld as stale',withheld.length===0,withheld.join(','));
 const notShown=Object.keys(data).filter(k=>data[k]&&!data[k].shown);
 t('every walkthrough actually renders',notShown.length===0,notShown.join(','));

 // 4. the task text itself has not changed since the walkthrough was reviewed
 const changed=[];
 Object.keys(FP).forEach(k=>{
   const d=data[k]; if(!d)return;
   const h=crypto.createHash('sha256').update(d.title+' '+d.do_+' '+d.output).digest('hex').slice(0,16);
   if(h!==FP[k].h)changed.push(k+' ("'+d.title+'")');
 });
 t('no task with a walkthrough has been reworded since it was audited',changed.length===0,
   changed.join(' | ')+'  -- re-read those walkthroughs, then run: python3 test/fingerprint.py from the roadmap directory');
 t('every walkthrough has a fingerprint on file',
   Object.keys(data).every(k=>FP[k]),Object.keys(data).filter(k=>!FP[k]).join(','));

 // 5. shape
 const short=Object.keys(data).filter(k=>data[k]&&data[k].n<4);
 t('every walkthrough has at least four steps',short.length===0,short.join(','));

 // 6. the withholding guard actually works when a title does drift
 const guard=await p.evaluate(()=>{
   const d=ALLDAYS.find(x=>x.id==='1-3');
   const real=d.t; d.t='Something else entirely';
   const r={shown:stepList(d),stale:stepsStale(d)};
   d.t=real; return r;
 });
 t('a drifted task has its old steps withheld, not shown',guard.shown===null&&guard.stale===true);
 await p.evaluate(()=>{const d=ALLDAYS.find(x=>x.id==='1-3');d.t='Drifted';openTask('1-3');});
 await p.waitForTimeout(300);
 const body=await p.textContent('#todayCard');
 t('and the user is told why, in the workspace',body.includes('Withheld'));

 // 7. the specific bug that started this: 1-3 is the ADV task, not the exam-date one
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(300);
 const adv=await p.evaluate(()=>{
   const d=ALLDAYS.find(x=>x.id==='1-3');
   return {title:d.t,steps:stepList(d).join(' ')};
 });
 t('1-3 is the Form ADV task',/Form ADV/i.test(adv.title));
 t('1-3 steps are about the ADV brochure',/brochure|Item 5|Item 15/i.test(adv.steps));
 t('1-3 steps no longer mention the exam date',!/Series 65|exam date|practice exam/i.test(adv.steps));

 t('no page errors',errs.length===0,errs[0]||'');
 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 fail.forEach(f=>console.log('  x '+f));
 await b.close(); process.exit(fail.length?1:0);
})();
