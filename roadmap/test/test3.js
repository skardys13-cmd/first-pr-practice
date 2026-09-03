const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[]; const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const ctx=await b.newContext({viewport:{width:1200,height:1000}});
 const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(500);

 t('card offers a workspace button',(await p.$('[data-ws]'))!==null);
 t('workspace closed by default',(await p.$('.ws'))===null);

 // open via the button
 await p.click('#todayCard .workbtn[data-ws]'); await p.waitForTimeout(300);
 t('workspace opens',(await p.$('.ws'))!==null);
 t('task 1 has written steps',(await p.$$('.steps li')).length>=4);
 t('task 1 offers a work area',(await p.$('[data-add]'))!==null||(await p.$('textarea[data-notes]'))!==null);

 // work area round-trips (list builder or notes, depending on the task)
 const id=await p.evaluate(()=>document.querySelector('.ws').id.replace('ws-',''));
 if(await p.$('#add-'+id)){
   for(const v of ['Roth distribution','ACAT follow-up','? beneficiary change']){
     await p.fill('#add-'+id,v); await p.click('[data-add]'); await p.waitForTimeout(150);
   }
   t('list items add',(await p.$$('.item')).length===3);
   t('items persist',await p.evaluate(i=>JSON.parse(localStorage.getItem('opsladder.v1')).work[i].items.length===3,id));
   await p.click('.item .rm'); await p.waitForTimeout(200);
   t('list items remove',(await p.$$('.item')).length===2);
   await p.fill('#add-'+id,'meeting prep'); await p.press('#add-'+id,'Enter'); await p.waitForTimeout(200);
   t('return key adds an item',(await p.$$('.item')).length===3);
 } else {
   await p.fill('textarea[data-notes]','the publication standard'); await p.waitForTimeout(400);
   t('notes persist',await p.evaluate(i=>JSON.parse(localStorage.getItem('opsladder.v1')).work[i].notes.length>5,id));
 }

 // step ticking
 await p.click('.steps li .sx'); await p.waitForTimeout(200);
 t('steps can be ticked off',(await p.$$('.steps li.on')).length===1);

 // link field
 await p.fill('[data-link]','https://example.com/notes'); await p.waitForTimeout(300);
 t('link saves',await p.evaluate(i=>JSON.parse(localStorage.getItem('opsladder.v1')).work[i].link.includes('example.com'),id));

 // survives reload
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(400);
 t('saved-work hint shows on the card',(await p.textContent('#todayCard')).includes('you have work saved here'));
 await p.click('#todayCard .workbtn[data-ws]'); await p.waitForTimeout(300);
 const kept=await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));
   return Object.values(s.work||{}).some(w=>(w.items&&w.items.length)||(w.notes&&w.notes.length>5));});
 t('work survives reload',kept);

 // notes-type task
 await p.click('[data-budget="240"]'); await p.waitForTimeout(400);
 const n=(await p.$$('#todayCard .daycard')).length;
 let foundNotes=false;
 for(let i=0;i<n;i++){
   const sel='#todayCard .daycard:nth-of-type('+(i+1)+') .workbtn[data-ws]';
   if(!(await p.$(sel))) continue;
   await p.click(sel); await p.waitForTimeout(250);
   if(await p.$('textarea[data-notes]')){foundNotes=true;break;}
   await p.click(sel).catch(()=>{}); await p.waitForTimeout(150);
 }
 t('non-list tasks get a notes area',foundNotes);
 if(foundNotes){
   await p.fill('textarea[data-notes]','drafted the thing'); await p.waitForTimeout(400);
   t('notes save',await p.evaluate(()=>{const s=JSON.parse(localStorage.getItem('opsladder.v1'));return Object.values(s.work).some(w=>w.notes==='drafted the thing');}));
 }

 // mark done from inside the workspace
 const donebtn=await p.$('.ws .workbtn[data-prog$="|100"]');
 if(donebtn){ const before=await p.textContent('#tDay'); await donebtn.click(); await p.waitForTimeout(300);
   t('Mark this done works from the workspace',(await p.textContent('#tDay'))!==before); }

 // backup carries the work
 const bk=await p.evaluate(()=>JSON.parse(localStorage.getItem('opsladder.v1')));
 t('backup includes workspace content',bk.work&&Object.keys(bk.work).length>0);

 t('zero JS errors',errs.length===0,errs[0]);
 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 if(fail.length) console.log('\nFAILURES:\n - '+fail.join('\n - '));
 await b.close();
})();
