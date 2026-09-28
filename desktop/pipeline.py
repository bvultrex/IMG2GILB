"""Local job orchestrator with isolated processes, cancellation and verified stage caches."""
import hashlib,json,os,shutil,subprocess,threading,time,urllib.request,urllib.error,uuid
from pathlib import Path
from PIL import Image
from process_guard import ProcessGuard,identity
ROOT=Path(__file__).resolve().parent
class Cancelled(Exception):pass

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,obj):
 # Windows readers/scanners can briefly deny replacement while holding the target.
 # Unique temporary names also prevent unrelated writers from clobbering each other.
 t=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  t.write_text(json.dumps(obj,indent=2),encoding='utf-8')
  for attempt in range(30):
   try:t.replace(p);return
   except PermissionError:
    if attempt==29:raise
    time.sleep(.1)
 finally:
  if t.exists():t.unlink()
def api(url,data=None,timeout=20):
 req=urllib.request.Request(url,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 return json.load(urllib.request.urlopen(req,timeout=timeout))

class Job:
 def __init__(self,path,cfg):
  self.path=path;self.cfg=cfg;self.stop=threading.Event();self.process=None;self.lock=threading.RLock()
  self.state=json.loads((path/'state.json').read_text())
 def update(self,**kw):
  with self.lock:self.state.update(kw);self.state['updated']=time.time();write_json(self.path/'state.json',self.state)
 def snapshot(self):
  with self.lock:return dict(self.state)
 def check(self):
  if self.stop.is_set():raise Cancelled()
 def run_process(self,cmd):
  self.check()
  with (self.path/'job.log').open('a',encoding='utf-8') as log:
   log.write('\nRUN '+json.dumps(cmd)+'\n');log.flush()
   self.process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT,creationflags=(subprocess.CREATE_NO_WINDOW|0x00000004) if os.name=='nt' else 0)
   guard=ProcessGuard(self.process)
   self.update(worker=identity(self.process.pid))
   try:
    while self.process.poll() is None:
     if self.stop.wait(.5):
      if os.name=='nt':subprocess.run(['taskkill','/PID',str(self.process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
      else:self.process.terminate()
      self.process.wait(timeout=20);raise Cancelled()
    if self.process.returncode:raise RuntimeError('Verarbeitung fehlgeschlagen. Details stehen im Diagnoseprotokoll.')
   finally:
    guard.close();self.process=None;self.update(worker=None)
  self.check()
 def comfy_ready(self):
  base=self.cfg['comfy_url']
  try:api(base+'/system_stats',timeout=3)
  except Exception:
   logs=Path(self.cfg['jobs_dir']);logs.mkdir(parents=True,exist_ok=True)
   with (logs/'comfy_service.log').open('ab') as f:
    subprocess.Popen([self.cfg['comfy_python'],'-s',str(Path(self.cfg['comfy'])/'main.py'),'--windows-standalone-build','--listen','127.0.0.1','--port','8188'],cwd=Path(self.cfg['comfy']).parent,stdout=f,stderr=f,creationflags=subprocess.CREATE_NO_WINDOW)
   for _ in range(180):
    self.check()
    try:api(base+'/system_stats',timeout=2);break
    except Exception:self.stop.wait(1)
   else:raise RuntimeError('ComfyUI konnte nicht gestartet werden. comfy_service.log prüfen.')
  info=api(base+'/object_info/BRIA_RMBG_Zho')
  if 'BRIA_RMBG_Zho' not in info:raise RuntimeError('Die konfigurierte ComfyUI-Instanz hat keinen BRIA-Node.')
 def prepare(self,spec):
  self.comfy_ready();out=self.path/'prepared';out.mkdir(exist_ok=True)
  comfy=Path(self.cfg['comfy']);base=self.cfg['comfy_url'];total=len(spec['views'])
  for index,name in enumerate(spec['views']):
   self.check();self.update(detail=f'{name}: Hintergrund entfernen ({index+1}/{total})',stage_fraction=index/total)
   filename=f"img2gilb_{self.path.name}_{name}.png";shutil.copy2(self.path/'inputs'/f'{name}.png',comfy/'input'/filename)
   prompt={'1':{'class_type':'LoadImage','inputs':{'image':filename}},'2':{'class_type':'BRIA_RMBG_ModelLoader_Zho','inputs':{}},'3':{'class_type':'BRIA_RMBG_Zho','inputs':{'image':['1',0],'rmbgmodel':['2',0]}},'4':{'class_type':'SaveImage','inputs':{'images':['3',0],'filename_prefix':f'Img2GLB/app/{self.path.name}/{name}'}}}
   pid=api(base+'/prompt',{'prompt':prompt})['prompt_id'];self.update(comfy_prompt=pid)
   started=time.monotonic()
   while True:
    history=api(base+'/history/'+pid)
    if pid in history:break
    if self.stop.is_set():
     queue=api(base+'/queue')
     if any(item[1]==pid for item in queue.get('queue_pending',[])):
      api(base+'/queue',{'delete':[pid]});raise Cancelled()
     self.update(detail='Abbruch angefordert; laufende Freistellung wird beendet.')
    if time.monotonic()-started>600:raise TimeoutError('BRIA hat nach 10 Minuten kein Ergebnis geliefert.')
    time.sleep(1)
   self.check();entry=history[pid]
   if entry['status']['status_str']!='success':raise RuntimeError('BRIA-Fehler: '+json.dumps(entry['status'])[:1000])
   result=entry['outputs']['4']['images'][0];file=(comfy/'output'/result['subfolder']/result['filename']).resolve()
   if not file.is_relative_to((comfy/'output').resolve()):raise RuntimeError('Invalid ComfyUI output path')
   rgba=Image.open(self.path/'inputs'/f'{name}.png').convert('RGB');alpha=Image.open(file).getchannel('A')
   if rgba.size!=alpha.size:raise RuntimeError('BRIA-Auflösung stimmt nicht mit Eingabe überein.')
   if not alpha.getbbox():raise RuntimeError('Kein Vordergrund erkannt. Anderes Bild verwenden.')
   rgba.putalpha(alpha);rgba.save(out/f'{name}.png')
  self.update(comfy_prompt=None)
 def cached(self,name,outputs,action,fingerprint):
  self.check();file=self.path/'cache.json';cache=json.loads(file.read_text()) if file.exists() else {}
  expected=cache.get(name,{})
  if expected.get('fingerprint')==fingerprint and all(p.exists() and expected.get('files',{}).get(str(p.relative_to(self.path)))==sha(p) for p in outputs):
   self.update(detail='Geprüften Zwischenstand wiederverwenden');return
  action();self.check()
  if not all(p.is_file() for p in outputs):raise RuntimeError('Die Stufe hat nicht alle benötigten Dateien erzeugt.')
  cache[name]={'fingerprint':fingerprint,'files':{str(p.relative_to(self.path)):sha(p) for p in outputs}};write_json(file,cache)
 def run(self):
  try:self._run()
  except Exception as exc:self.update(status='failed',error=str(exc),finished=time.time())
 def _run(self):
  spec=json.loads((self.path/'project.json').read_text());s=spec['settings'];c=self.cfg;lab=Path(c['lab']);py=c['python']
  stages=['prepare','shape']+(['uv','paint','bake'] if s['textures'] else [])+(['face'] if s['face'] else [])+['finalize']+(['rig'] if s.get('rig') else [])
  fingerprint=hashlib.sha256((json.dumps(spec,sort_keys=True)+sha(ROOT/'stages.py')+sha(ROOT/'pipeline.py')+sha(lab/'run_paint21.py')+sha(lab/'bake_paint21.py')+sha(ROOT/'runtime.json')+sha(ROOT/'rig_stage.py')+sha(ROOT/'validate_rig.py')+sha(ROOT/'walk_preview.py')+(sha(c['face_runtime'])+sum_face_code(Path(c['face_runtime']).parent)+sha(Path(c['face_runtime']).parent/'runtime.json') if s['face'] else '')).encode()).hexdigest()
  self.update(status='running',started=time.time(),stages=stages,error=None,completed_stages=0)
  try:
   for i,stage in enumerate(stages):
    self.check();self.update(stage=stage,stage_fraction=None,detail='',completed_stages=i)
    def stage_cmd(name):self.run_process([py,str(ROOT/'stages.py'),name,str(self.path),str(ROOT/'runtime.json')])
    if stage=='prepare':outputs=[self.path/'prepared'/f'{v}.png' for v in spec['views']];action=lambda:self.prepare(spec)
    elif stage=='shape':outputs=[self.path/'shape.glb',self.path/'shape_report.json'];action=lambda:stage_cmd('shape')
    elif stage=='uv':
     outputs=[self.path/'controls/uv_mesh.npz']+[self.path/'controls'/f'render_{kind}_multiview_{n}.png' for kind in ['normal','position'] for n in range(6)];action=lambda:stage_cmd('uv')
    elif stage=='paint':
     outputs=[self.path/'paint'/f'{kind}_{n}.png' for kind in ['albedo','mr'] for n in range(6)]
     action=lambda:self.run_process([py,str(lab/'run_paint21.py'),'--input',str(self.path/'prepared/front.png'),'--controls',str(self.path/'controls'),'--output',str(self.path/'paint'),'--views','6','--resolution','512' if s['quality']=='fast' else '768'])
    elif stage=='bake':
     outputs=[self.path/'textured_pbr.glb',self.path/'textured_color.glb'];action=lambda:self.run_process([py,str(lab/'bake_paint21.py'),'--input',str(self.path/'paint'),'--uv-cache',str(self.path/'controls/uv_mesh.npz'),'--output-prefix',str(self.path/'textured'),'--views','6','--resolution','512' if s['quality']=='fast' else '768'])
    elif stage=='face':
     project={'source':str(self.path/'prepared/front.png'),'mesh':str(self.path/'textured_pbr.glb'),'uv':str(self.path/'controls/uv_mesh.npz'),'output':str(self.path/'face')};write_json(self.path/'face_project.json',project)
     outputs=[self.path/'face/report.json',self.path/'face/Face_1_0.glb'];action=lambda:self.run_process([py,c['face_runtime'],'--project',str(self.path/'face_project.json')])
    elif stage=='rig':
     outputs=[self.path/'output_rigged.glb',self.path/'result_rigged.json',self.path/'rig/verification.json',self.path/'rig/preview.json',self.path/'preview_color.glb'];action=lambda:self.run_process([c['rig_python'],str(ROOT/'rig_stage.py'),str(self.path),str(ROOT/'runtime.json')])
    else:outputs=[self.path/'output.glb',self.path/'result.json']+([] if s.get('rig') else [self.path/'preview_color.glb']);action=lambda:stage_cmd('finalize')
    self.cached(stage,outputs,action,fingerprint)
   result=json.loads((self.path/('result_rigged.json' if s.get('rig') else 'result.json')).read_text());self.update(status='complete',completed_stages=len(stages),result=result,finished=time.time(),detail='Modell bereit')
  except Cancelled:self.update(status='cancelled',finished=time.time(),detail='Abgebrochen. Geprüfte Zwischenstände bleiben erhalten.')
  except Exception as exc:self.update(status='failed',error=str(exc),finished=time.time(),detail='Verarbeitung angehalten')


def sum_face_code(root):
 return "".join(sha(root/name) for name in ("core.py", "detect.py", "detection_policy.py", "render_adapter.py"))
