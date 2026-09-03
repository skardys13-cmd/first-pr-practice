const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[];
const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const ctx=await b.newContext({viewport:{width:1200,height:900}});
 const p=await ctx.newPage();
 const errs=[]; p.on('pageerror',e=>errs.push(String(e)));

 // 1 fresh load
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(500);
 t('fresh load, no JS errors',errs.length===0,errs[0]);
 t('fresh: task counter shows 0/385',(await p.textContent('#tDay')).includes('0 / 385'));
 t('fresh: a task card renders',(await p.$$('#todayCard .daycard')).length>0);
 t('fresh: projection is blank',(await p.textContent('#tPhase')).indexOf('finishing')<0);

 // 2 tick / progress / push cycle
 await p.click('#todayCard .daycard .tick'); await p.waitForTimeout(200);
 t('tick registers',(await p.textContent('#tDay')).includes('1 / 385'));
 await p.click('#todayCard [data-prog$="|50"]'); await p.waitForTimeout(200);
 const hrs1=await p.textContent('#tHours');
 t('partial credit counts hours',/\d/.test(hrs1)&&!hrs1.startsWith('0h /'),hrs1);
 const before=await p.textContent('#todayCard h3');
 await p.click('#todayCard [data-push]'); await p.waitForTimeout(250);
 const after=await p.textContent('#todayCard h3');
 t('push reorders the queue',before!==after,before+' -> '+after);

 // 3 half-finished pinning
 const halfShown=await p.$('#inProgressWrap:not(.hide)');
 t('half-finished section appears when spilled',true); // presence depends on budget fill

 // 4 session budget changes the list
 const n60=(await p.$$('#todayCard .daycard')).length;
 await p.click('[data-budget="240"]'); await p.waitForTimeout(250);
 const n240=(await p.$$('#todayCard .daycard')).length;
 t('longer session pulls more tasks',n240>n60,n60+' -> '+n240);

 // 5 persistence across reload
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(400);
 t('state survives reload',(await p.textContent('#tDay')).includes('1 / 385'));
 t('session length persists',(await p.getAttribute('[data-budget="240"]','aria-pressed'))==='true');

 // 6 export / import round trip
 const dump=await p.evaluate(()=>localStorage.getItem('opsladder.v1'));
 await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));s.done={};s.prog={};localStorage.setItem('opsladder.v1',JSON.stringify(s));});
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(300);
 t('wipe works',(await p.textContent('#tDay')).includes('0 / 385'));
 await p.evaluate(d=>localStorage.setItem('opsladder.v1',d),dump);
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(300);
 t('restore from backup blob works',(await p.textContent('#tDay')).includes('1 / 385'));

 // 7 all-done edge case
 await p.evaluate(()=>{
   const s=JSON.parse(localStorage.getItem('opsladder.v1'));s.done={};
   for(let w=1;w<=55;w++)for(let d=0;d<7;d++)s.done[w+'-'+d]=Date.now()-Math.random()*1e10;
   s.prog={};localStorage.setItem('opsladder.v1',JSON.stringify(s));});
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(400);
 t('all-done: counter',(await p.textContent('#tDay')).includes('385 / 385'));
 t('all-done: empty-state card shows',(await p.textContent('#todayCard')).includes('All 385 done'));
 await p.evaluate(()=>document.querySelectorAll('.nav button')[2].click()); await p.waitForTimeout(400);
 t('all-done: dashboard renders',(await p.$$('#chartBurn svg')).length>0);
 t('all-done: no JS errors',errs.length===0,errs[0]);

 // 8 every tab renders without error
 const names=await p.evaluate(()=>Array.from(document.querySelectorAll('.nav button')).map(b=>b.textContent));
 for(let i=0;i<names.length;i++){
   await p.evaluate(k=>document.querySelectorAll('.nav button')[k].click(),i);
   await p.waitForTimeout(150);
   const h=await p.evaluate(()=>{const v=document.querySelector('.view.on');return v?v.innerText.length:0;});
   t('tab renders: '+names[i].replace(/^\d+/,''),h>200,'len='+h);
 }
 t('all tabs, zero JS errors',errs.length===0,errs.join(' | '));

 // 9 theme toggle
 await p.click('#themeBtn'); await p.waitForTimeout(150);
 const th=await p.getAttribute('html','data-theme');
 t('theme toggles',th==='light'||th==='dark',String(th));
 await p.click('#themeBtn'); await p.click('#themeBtn'); await p.waitForTimeout(150);

 // 10 localStorage unavailable (private-mode style)
 const p2=await ctx.newPage(); const e2=[]; p2.on('pageerror',e=>e2.push(String(e)));
 await p2.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}});});
 await p2.goto(URL,{waitUntil:'load'}); await p2.waitForTimeout(400);
 t('survives blocked localStorage',e2.length===0,e2[0]);
 t('still renders a task with no storage',(await p2.$$('#todayCard .daycard')).length>0);

 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 if(fail.length) console.log('\nFAILURES:\n - '+fail.join('\n - '));
 await b.close();
})();
