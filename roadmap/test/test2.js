const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[]; const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const ctx=await b.newContext({viewport:{width:1200,height:900}});
 const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(500);

 // FIX 1: push now moves a half-finished task
 await p.click('#todayCard [data-prog$="|50"]'); await p.waitForTimeout(200);
 const before=await p.textContent('#todayCard h3');
 await p.click('#todayCard [data-push]'); await p.waitForTimeout(250);
 const after=await p.textContent('#todayCard h3');
 t('push moves a half-finished task',before!==after,before+' -> '+after);
 t('pushed task still tracked as half finished',
   await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));return Object.keys(s.prog||{}).length>0;}));

 // FIX 2: no blank Why lines anywhere
 const blanks=await p.evaluate(()=>{
   let n=0; for(const w of PLAN) for(const d of w.days) if(!d.k||!d.k.trim()) n++;
   return n;});
 t('zero blank Why fields',blanks===0,'blank='+blanks);

 // FIX 3: no stale "week N" wording in task text
 const stale=await p.evaluate(()=>{
   let n=0; for(const w of PLAN) for(const d of w.days)
     if(/\bweeks? \d+/i.test(d.t+' '+d.d+' '+d.o+' '+d.k)) n++;
   return n;});
 t('no stale week-N references',stale===0,'found='+stale);

 // FIX 4: all 40 SOPs produced
 const sops=await p.evaluate(()=>{
   const set=new Set();
   for(const w of PLAN) for(const d of w.days)
     for(const m of (d.o+' '+d.t).matchAll(/SOPs? (\d+)(?:-(\d+))?/g)){
       const a=+m[1],bb=m[2]?+m[2]:+m[1]; for(let i=a;i<=bb;i++) set.add(i);}
   return [...Array(40)].map((_,i)=>i+1).filter(n=>!set.has(n));});
 t('all 40 SOPs are produced by a task',sops.length===0,'missing='+sops);

 // storage indicator
 t('storage status renders',(await p.textContent('#syncNote')).includes('This browser only'));
 t('storage status names the risk',(await p.textContent('#syncNote')).includes('Clearing site data'));
 t('no backup nudge on a new install',(await p.textContent('#backupNudge')).trim()==='');

 // nudge appears after 30+ days of use, dismisses for 14
 await p.evaluate(()=>{
   const s=JSON.parse(localStorage.getItem('opsladder.v1'));
   const iso=x=>x.getFullYear()+"-"+String(x.getMonth()+1).padStart(2,"0")+"-"+String(x.getDate()).padStart(2,"0");
   s.log={}; for(let i=0;i<60;i+=3){const d=new Date();d.setDate(d.getDate()-i);s.log[iso(d)]=60;}
   s.lastExport=0; localStorage.setItem('opsladder.v1',JSON.stringify(s));});
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(400);
 t('nudge fires after 30 days with no backup',(await p.textContent('#backupNudge')).includes('never exported'));
 await p.click('[data-nudge]'); await p.waitForTimeout(200);
 t('nudge dismisses',(await p.textContent('#backupNudge')).trim()==='');
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(300);
 t('nudge stays dismissed across reload',(await p.textContent('#backupNudge')).trim()==='');

 // export stamps lastExport
 await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));s.nudgeSeen=0;localStorage.setItem('opsladder.v1',JSON.stringify(s));});
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(300);
 await ctx.grantPermissions(['clipboard-write','clipboard-read']).catch(()=>{});
 await p.click('#exportBtn'); await p.waitForTimeout(600);
 const stamped=await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));return !!s.lastExport;});
 t('export stamps the backup date',stamped);
 t('nudge clears after exporting',(await p.textContent('#backupNudge')).trim()===''); 
 t('storage note shows backup age',(await p.textContent('#syncNote')).includes('Backup exported'));

 // regression sweep: all tabs still render
 const names=await p.evaluate(()=>Array.from(document.querySelectorAll('.nav button')).map(b=>b.textContent));
 for(let i=0;i<names.length;i++){
   await p.evaluate(k=>document.querySelectorAll('.nav button')[k].click(),i); await p.waitForTimeout(120);
   const h=await p.evaluate(()=>{const v=document.querySelector('.view.on');return v?v.innerText.length:0;});
   if(h<200) fail.push('tab blank: '+names[i]);
 }
 t('all 12 tabs still render',!fail.some(f=>f.startsWith('tab blank')));
 t('zero JS errors throughout',errs.length===0,errs[0]);

 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 if(fail.length) console.log('\nFAILURES:\n - '+fail.join('\n - '));
 await b.close();
})();
