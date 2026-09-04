const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const URL='file:///home/user/first-pr-practice/roadmap/index.html';
const pass=[],fail=[]; const t=(n,c,d='')=>c?pass.push(n):fail.push(n+(d?' :: '+d:''));
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const ctx=await b.newContext({viewport:{width:1280,height:1000}});
 const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(URL,{waitUntil:'load'}); await p.waitForTimeout(500);

 /* ---- 1. the vanishing-panel bug ---- */
 // simulate what the sample capability does: stream, then finish
 await p.click('#todayCard .workbtn[data-ws]'); await p.waitForTimeout(250);
 const id=await p.evaluate(()=>document.querySelector('.ws').id.replace('ws-',''));
 t('a task with written steps shows them',(await p.$$('.ws .steps li')).length>=4);
 await p.evaluate(async i=>{
   SAMPLE=async(prompt,opts)=>{ opts.onText({text:'1. first\n2. second'}); await new Promise(r=>setTimeout(r,20));
     opts.onText({text:'1. first\n2. second\n3. third'}); return {text:'1. first\n2. second\n3. third'}; };
   await genSteps(i);
 },id);
 await p.waitForTimeout(400);
 t('generated detail survives the re-render',(await p.$$('.detail .steps li')).length===3);
 t('generated detail persisted to storage',
   await p.evaluate(i=>(JSON.parse(localStorage.getItem('opsladder.v1')).work[i].detail||'').includes('third'),id));
 await p.reload({waitUntil:'load'}); await p.waitForTimeout(400);
 await p.click('#todayCard .workbtn[data-ws]'); await p.waitForTimeout(250);
 t('detail is still there after a reload',(await p.$$('.detail .steps li')).length===3);
 t('built-in steps and generated detail both show',(await p.$$('.ws .steps li')).length>=7);
 await p.click('.detail .steps li .sx'); await p.waitForTimeout(200);
 t('detail steps tick off',(await p.$$('.detail .steps li.on')).length===1);
 await p.click('[data-clrdet]'); await p.waitForTimeout(250);
 t('clear removes the generated detail',(await p.$('.detail'))===null);

 /* ---- 2. destinations ---- */
 const dest=await p.evaluate(()=>{
   const bad=[];
   Object.keys(LINKS).forEach(k=>{ if(!ALLDAYS.find(d=>d.id===k))bad.push('unknown task '+k);
     LINKS[k].forEach(r=>{if(!REFS[r])bad.push(k+' bad ref '+r);}); });
   Object.keys(REFS).forEach(k=>{ if(!/^https:\/\//.test(REFS[k][1]))bad.push('non-https '+k); });
   const withSteps=ALLDAYS.filter(d=>STEPS[d.id]);
   return {bad, nSteps:withSteps.length,
     noLinks:withSteps.filter(d=>linksFor(d).length===0).map(d=>d.id),
     everyTaskHasTools:ALLDAYS.every(d=>toolsFor(d).length>0),
     everyTaskHasSends:ALLDAYS.every(d=>sendsFor(d).length>0),
     xrefNeverSelf:ALLDAYS.every(d=>xref(d).every(x=>x.id!==d.id)),
     xrefAlwaysEarlier:ALLDAYS.every(d=>xref(d).every(x=>ALLDAYS.find(y=>y.id===x.id).idx<d.idx))};
 });
 t('link registry is clean',dest.bad.length===0,dest.bad.join('; '));
 t('no duplicate reference labels',await p.evaluate(()=>{
   const seen=new Set();return Object.keys(REFS).every(k=>{const u=REFS[k][1];if(seen.has(u))return false;seen.add(u);return true;});}));
 t('106 tasks have written walkthroughs',dest.nSteps===106,'got '+dest.nSteps);
 t('every walkthrough task but the two policy ones links somewhere',dest.noLinks.length<=2,dest.noLinks.join(','));
 t('every task offers at least one tool',dest.everyTaskHasTools);
 t('every task offers a send-to-section',dest.everyTaskHasSends);
 t('cross-task links never point at themselves',dest.xrefNeverSelf);
 t('cross-task links only point backwards',dest.xrefAlwaysEarlier);

 /* ---- 3. saved tools ---- */
 await p.evaluate(()=>go('systems')); await p.waitForTimeout(250);
 t('tool boxes render',(await p.$$('#toolBox input[data-tool]')).length===8);
 await p.fill('input[data-tool="tableau"]','https://public.tableau.com/app/profile/seth'); await p.waitForTimeout(300);
 t('tool url persists',await p.evaluate(()=>JSON.parse(localStorage.getItem('opsladder.v1')).tools.tableau.includes('seth')));
 await p.evaluate(()=>openTask('3-1')); await p.waitForTimeout(400);
 const hrefs=await p.$$eval('#ws-3-1 .goes a',as=>as.map(a=>a.href));
 t('a saved tool becomes a link on a task',hrefs.some(h=>h.includes('profile/seth')),hrefs.join(' '));
 t('external refs render as links too',hrefs.some(h=>h.includes('tableau.com/products/public/download')));
 t('links open in a new tab',await p.$$eval('#ws-3-1 .goes a',as=>as.every(a=>a.target==='_blank'&&a.rel.includes('noopener'))));

 /* ---- 4. cross-task jump ---- */
 await p.click('#ws-3-1 .goes [data-jump]'); await p.waitForTimeout(600);
 t('jumping to a prerequisite opens that task',await p.evaluate(()=>focusTask==='1-1'||focusTask==='2-2'));
 t('the prerequisite workspace is open',await p.evaluate(()=>!!document.getElementById('ws-'+focusTask)));
 t('a focus note explains why it is at the top',(await p.$('.focusnote'))!==null);
 await p.click('[data-unfocus]'); await p.waitForTimeout(300);
 t('clearing focus restores the queue',(await p.$('.focusnote'))===null);

 /* ---- 5. ledgers ---- */
 await p.evaluate(()=>openTask('3-1')); await p.waitForTimeout(400);
 await p.click('#ws-3-1 [data-send^="builds"]'); await p.waitForTimeout(400);
 t('send-to-section lands on the right view',await p.$eval('.view.on',v=>v.id)==='v-builds');
 t('the row is created and prefilled',
   await p.evaluate(()=>{const r=S.builds[S.builds.length-1];return r&&r.name&&r.kind==='Dashboard'&&r.comp==='Reporting and firm KPIs';}));
 t('build row renders',(await p.$$('#ledBuilds tbody tr')).length===1);
 await p.fill('#ledBuilds input[data-led$="|saves"]','40 min'); await p.waitForTimeout(300);
 t('ledger edits persist',await p.evaluate(()=>JSON.parse(localStorage.getItem('opsladder.v1')).builds[0].saves==='40 min'));
 await p.click('[data-ledadd="builds"]'); await p.waitForTimeout(300);
 t('add row works',(await p.$$('#ledBuilds tbody tr')).length===2);
 await p.click('#ledBuilds tbody tr:nth-child(2) .del'); await p.waitForTimeout(300);
 t('delete row works',(await p.$$('#ledBuilds tbody tr')).length===1);
 t('delete removes the right row',await p.evaluate(()=>S.builds.length===1&&S.builds[0].comp==='Reporting and firm KPIs'));

 /* ---- 6. SOP library ---- */
 await p.evaluate(()=>go('sops')); await p.waitForTimeout(300);
 t('all 40 SOPs listed',(await p.$$('#sopLib tbody tr')).length===40);
 await p.selectOption('#sopLib select[data-sopf="1|status"]','Firm-approved'); await p.waitForTimeout(300);
 t('SOP status persists',await p.evaluate(()=>JSON.parse(localStorage.getItem('opsladder.v1')).soplib['1'].status==='Firm-approved'));
 t('SOP status still drives the portfolio count',await p.evaluate(()=>S.sops['1']===true));
 await p.check('#sopLib input[data-sopf="1|pub"]'); await p.waitForTimeout(300);
 t('public-version flag persists',await p.evaluate(()=>JSON.parse(localStorage.getItem('opsladder.v1')).soplib['1'].pub===true));

 /* ---- 7. state of play ---- */
 await p.evaluate(()=>go('state')); await p.waitForTimeout(300);
 t('clocks render',(await p.$$('#stClocks > div')).length===4);
 t('section counts render',(await p.$$('#stCounts > div')).length===6);
 t('evidence map has all nine COO areas',(await p.$$('#stCov tbody tr')).length===9);
 t('evidence map counts the tagged build',
   await p.evaluate(()=>evidenceFor('Reporting and firm KPIs')>=1));
 t('recent list shows what was logged',(await p.$$('#stRecent tbody tr')).length>=1);

 /* ---- 8. nothing broken elsewhere ---- */
 for(const v of ['today','plan','dash','portfolio','skills','coo','certs','targets','money','move','delegate','systems']){
   await p.evaluate(x=>go(x),v); await p.waitForTimeout(120);
 }
 t('no page errors across every view',errs.length===0,errs.slice(0,3).join(' | '));
 t('old state upgrades cleanly',await p.evaluate(()=>{
   const old={v:3,done:{'1-0':1},work:{'1-0':{notes:'hi'}},sops:{}};
   const m=MERGE(old);
   return Array.isArray(m.wins)&&Array.isArray(m.qlog)&&m.done['1-0']===1&&m.work['1-0'].notes==='hi'&&m.v===4;
 }));

 console.log('PASS '+pass.length+'   FAIL '+fail.length);
 fail.forEach(f=>console.log('  ✗ '+f));
 await b.close(); process.exit(fail.length?1:0);
})();
