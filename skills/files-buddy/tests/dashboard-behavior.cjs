/* Exercise the packaged browser script and its real event handlers without a browser. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const skill = path.resolve(__dirname, '..');
const template = fs.readFileSync(path.join(skill, 'templates/dashboard.html'), 'utf8');
const sample = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/reports/storage-audit.json'), 'utf8'));
const schema = JSON.parse(fs.readFileSync(path.join(skill, 'assets/report.schema.json'), 'utf8'));
const source = [...template.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
class Element {
  constructor() { this.textContent='';this.innerHTML='';this.value='';this.disabled=false;this.hidden=false;this.handlers={};this.attributes={};this.clicked=false; }
  addEventListener(name, fn) { this.handlers[name]=fn; }
  setAttribute(name,value) { this.attributes[name]=value; }
  click() { this.clicked=true; }
}
function harness(data) {
  const elements=new Map();
  const get=id=>{ if(!elements.has(id))elements.set(id,new Element());return elements.get(id); };
  get('data').textContent=JSON.stringify(data);get('report-schema').textContent=JSON.stringify(schema);get('progress-config').textContent='{}';get('sort').value='path';
  const document={getElementById:get,hidden:false,handlers:{},addEventListener(name,fn){this.handlers[name]=fn;}};
  const intervals=new Map();let serial=0;
  const window={handlers:{},addEventListener(name,fn){this.handlers[name]=fn;},setInterval(fn){intervals.set(++serial,fn);return serial;},clearInterval(id){intervals.delete(id);}};
  vm.runInNewContext(source,{document,window,console,Date,JSON,Number,Object,Array,String,Error,RegExp,Math});
  return {get,window,document,intervals};
}
function file(data,name='snapshot.json') { const raw=typeof data==='string'?data:JSON.stringify(data);return {name,size:Buffer.byteLength(raw),async text(){return raw;}}; }
(async()=>{
  const h=harness(sample);
  assert.equal(h.get('error').hidden,true);
  let html=h.get('report-content').innerHTML;
  assert.match(html,/Verified reclaimed<\/h2><p class="stat-value">0 B<\/p>/);
  assert.match(html,/Bytes acted on<\/td><td class="">1.0 GiB/);
  assert.match(html,/Cloud offload[\s\S]*Supplied local estimate: 64.0 MiB/);
  assert.match(html,/Cloud impact: Unknown/);
  assert.match(html,/manifests\/run.json/);
  assert.doesNotMatch(html,/\[object Object\]/);
  assert.doesNotMatch(html,/risk-low">Low<\/span><\/td><td class="">[1-9]/);
  assert.match(html,/kind|Exact and perceptual/);
  h.get('filter').value='missing-file-name';h.get('filter').handlers.input();
  assert.match(h.get('report-content').innerHTML,/No matching rows supplied/);
  h.get('filter').value='';h.get('filter').handlers.input();
  assert.equal(h.get('filter').value,'');
  await h.get('choose-file').handlers.click();assert.equal(h.get('file-input').clicked,true);
  const next=structuredClone(sample);next.run_id='fresh-import';next.files[0].path='<img src=x onerror=alert(1)>';
  await h.get('file-input').handlers.change({target:{files:[file(next)]}});
  html=h.get('report-content').innerHTML;
  assert.match(html,/fresh-import/);assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);assert.doesNotMatch(html,/<img src=x/);
  const good=html;
  await h.get('file-input').handlers.change({target:{files:[file({schema_version:'2.0',files:{}})]}});
  assert.equal(h.get('report-content').innerHTML,good);assert.equal(h.get('error').hidden,false);
  assert.match(h.get('error').textContent,/Snapshot was not replaced/);
  let active=structuredClone(sample);active.run_id='selected-file';
  h.window.showOpenFilePicker=async()=>[{getFile:async()=>file(active)}];
  await h.get('choose-file').handlers.click();assert.equal(h.get('refresh-file').disabled,false);
  active.run_id='changed-on-disk';await h.get('refresh-file').handlers.click();
  assert.match(h.get('report-content').innerHTML,/changed-on-disk/);
  h.get('auto-refresh').handlers.click();assert.equal(h.intervals.size,1);assert.equal(h.get('auto-refresh').attributes['aria-pressed'],'true');
  active.run_id='auto-refreshed';await [...h.intervals.values()][0]();await new Promise(resolve=>setImmediate(resolve));
  assert.match(h.get('report-content').innerHTML,/auto-refreshed/);
  h.document.hidden=true;h.document.handlers.visibilitychange();assert.equal(h.intervals.size,0);
  assert.equal(h.get('auto-refresh').attributes['aria-pressed'],'false');
  for (const run_id of ['.','..','.hidden','../outside','a/b']) { const invalid=harness({...sample,run_id});assert.equal(invalid.get('error').hidden,false);assert.match(invalid.get('error').textContent,/run_id/); }
  for (const updated_at of ['2026-11-20 18:00:00+00:00','20261120T180000+0000']) { const invalid=harness({...sample,updated_at});assert.equal(invalid.get('error').hidden,false);assert.match(invalid.get('error').textContent,/updated_at/); }
  const invalid=harness({...sample,savings:{candidate_bytes:-1}});assert.equal(invalid.get('error').hidden,false);
  assert.match(template,/id="filter"/);assert.match(template,/<label for="sort">/);assert.match(template,/:focus-visible/);assert.match(template,/prefers-reduced-motion/);
  console.log(JSON.stringify({status:'passed',checks:['zero-verified','acted-bytes','cloud-unknown','offload-consistency','manifest-object','unknown-risk','filtered-empty','file-import','escaped-path','invalid-import-retention','file-handle-refresh','auto-refresh','hidden-tab-pause','invalid-embedded-data','run-id-boundary','accessible-controls'],kind:'Node VM markup and event handlers',browser_layout_verified:false}));
})().catch(error=>{console.error(error);process.exitCode=1;});
