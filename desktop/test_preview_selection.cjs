// Exercise the actual render function with a delayed response from an old job.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'web/app.js'), 'utf8');
const start = source.indexOf('function render(j)');
const end = source.indexOf("$('cancel').onclick", start);
assert(start >= 0 && end > start);
const elements = new Map();
const ctx = {
 current: 'new-job', busy: false, globalBusy: false, submitting: false,
 showColor: false, showWalk: false, loadedModel: null,
 stageNames: {}, stateNames: {complete:'Fertig'},
 $: id => {
  if (!elements.has(id)) elements.set(id, {dataset:{}});
  return elements.get(id);
 }
};
vm.createContext(ctx);
vm.runInContext(source.slice(start, end), ctx);
const result = {triangles:100, vertices:70, height_cm:170, texture_size:2048};
ctx.render({id:'new-job', status:'complete', result});
assert.equal(elements.get('preview').src, '/api/jobs/new-job/model');
assert.equal(elements.get('saveGLB').href, '/api/jobs/new-job/model');
ctx.render({id:'old-job', status:'complete', result});
assert.equal(elements.get('preview').src, '/api/jobs/new-job/model');
assert.equal(elements.get('saveGLB').href, '/api/jobs/new-job/model');
ctx.render({id:'old-job', status:'running'});
assert.equal(ctx.busy, false);
assert.equal(elements.get('downloads').hidden, false);
console.log('PASS: stale job responses cannot replace preview, download or busy state');
