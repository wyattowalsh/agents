/* Optional rendered acceptance; requires an existing Playwright/Chromium runtime. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {spawnSync}=require('node:child_process');
const {chromium}=require(process.env.FILES_BUDDY_PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const output=process.argv[2]||fs.mkdtempSync(path.join(os.tmpdir(),'files-buddy-browser-'));
fs.mkdirSync(output,{recursive:true});
(async()=>{
  const html=path.join(output,'report-'+Date.now()+'.html');
  const render=spawnSync(process.env.FILES_BUDDY_TEST_PYTHON||'python3.13',[path.join(root,'scripts/dashboard-renderer.py'),'--data',path.join(__dirname,'fixtures/reports/storage-audit.json'),'--output',html],{encoding:'utf8'});
  assert.equal(render.status,0,render.stdout+render.stderr);
  let browser;
  const executablePath=process.env.FILES_BUDDY_BROWSER_PATH||undefined;
  try{browser=await chromium.launch({headless:true,executablePath});}
  catch(error){console.log(JSON.stringify({status:'blocked',phase:'browser-launch',error:error.message,screenshots:[],native_browser_verified:false}));process.exitCode=2;return;}
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(pathToFileURL(html).href);
    assert.equal(await page.getByRole('heading',{name:'Verified reclaimed',exact:true}).count(),1);
    assert.equal(await page.locator('#error').isVisible(),false);
    assert.equal(await page.getByRole('heading',{name:'Verified reclaimed',exact:true}).locator('..').locator('.stat-value').innerText(),'0 B');
    const reducedMotion=await page.evaluate(()=>({
      requested:matchMedia('(prefers-reduced-motion: reduce)').matches,
      allStatic:[...document.querySelectorAll('*')].every(element=>{
        const style=getComputedStyle(element);
        return style.animationName==='none'&&style.transitionDuration.split(',').every(value=>parseFloat(value)===0)&&style.scrollBehavior==='auto';
      })
    }));
    assert.deepEqual(reducedMotion,{requested:true,allStatic:true});
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip').evaluate(el=>el===document.activeElement),true);
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#report-content').evaluate(el=>el===document.activeElement),true);
    await page.getByRole('searchbox').fill('not-a-known-path');
    assert.ok(await page.getByText('No matching rows supplied.').count()>0);
    await page.getByRole('searchbox').fill('');
    const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/reports/storage-audit.json'),'utf8'));
    assert.equal(await page.getByText(fixture.files[1].path,{exact:true}).count(),1);
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
    const invalid=path.join(output,'invalid.json');fs.writeFileSync(invalid,'null');
    await page.locator('#file-input').setInputFiles(invalid);
    await page.waitForFunction(()=>!document.getElementById('error').hidden);
    assert.equal(await page.locator('#error').isVisible(),true);
    assert.ok(await page.getByRole('heading',{name:'Storage accounting',exact:true}).count());
    const refreshed=path.join(output,'refreshed.json');fixture.run_id='browser-refreshed';
    fs.writeFileSync(refreshed,JSON.stringify(fixture));
    await page.locator('#file-input').setInputFiles(refreshed);
    await page.getByText('browser-refreshed',{exact:true}).waitFor();
    assert.equal(await page.locator('#error').isVisible(),false);
    assert.match(await page.locator('#refresh-status').innerText(),/Imported refreshed\.json/);
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({status:'passed',checks:['desktop','mobile','long-content','keyboard-skip-focus','filter-empty','zero-preserved','invalid-import-keeps-valid-report','valid-import-refresh','reduced-motion-computed-styles','console-errors'],screenshots:[path.join(output,'desktop.png'),path.join(output,'mobile.png')]}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
