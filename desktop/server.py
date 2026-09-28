"""Loopback-only desktop API. Standard-library server; no installation at startup."""
import base64,io,json,math,mimetypes,os,re,secrets,sys,threading,time,uuid,zipfile
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageOps
from pipeline import Job,write_json,sha
from process_guard import identity
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'runtime.json').read_text(encoding='utf-8-sig'))
JOBS=Path(CFG['jobs_dir']);JOBS.mkdir(parents=True,exist_ok=True)
def rig_available():
 return bool(CFG.get('rig_enabled') and Path(CFG.get('rig_python','')).is_file() and (Path(CFG.get('rig_source',''))/'demo.py').is_file())

TOKEN=secrets.token_urlsafe(32);LOCK=threading.RLock();ACTIVE=None;THREAD=None
# This application never adopts work from an earlier server instance.
for p in JOBS.glob('*/state.json'):
 try:
  state=json.loads(p.read_text())
  if state['status'] in ['running','queued'] and state.get('worker') and identity(state['worker']['pid'])==state['worker']:
   raise RuntimeError('A previous worker is still alive; wait for it before restarting the app.')
  if state['status'] in ['running','queued']:state.update(status='interrupted',error='Die App wurde während der Verarbeitung beendet. Diagnose prüfen und erneut starten.');write_json(p,state)
 except (ValueError,KeyError):pass

class API(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def response(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def file(self,p,mime=None,download=None):
  if not p.is_file():return self.response(404,{'error':'Datei nicht vorhanden'})
  self.send_response(200);self.send_header('Content-Type',mime or mimetypes.guess_type(p.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(p.stat().st_size));self.send_header('Cache-Control','no-cache')
  if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
  self.end_headers()
  with p.open('rb') as f:
   while chunk:=f.read(1024*1024):self.wfile.write(chunk)
 def host_ok(self):return self.headers.get('Host') in [f'127.0.0.1:{CFG["port"]}',f'localhost:{CFG["port"]}']
 def do_GET(self):
  if not self.host_ok():return self.response(403,{'error':'Host nicht erlaubt'})
  path=urlsplit(self.path).path
  if path=='/health':return self.response(200,{'app':'IMG2GILB','version':'0.1.0'})
  if path=='/':
   html=(ROOT/'web/index.html').read_text(encoding='utf-8').replace('__APP_TOKEN__',TOKEN).encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(html)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(html);return
  if path in ['/app.js','/style.css','/model-viewer.min.js']:return self.file(ROOT/'web'/path[1:])
  if path=='/api/config':return self.response(200,{'rigging':rig_available(),'rigging_reason':'Automatisches Rigging wird noch getestet.' if not rig_available() else 'Lokales automatisches Rigging','face':Path(CFG['face_runtime']).is_file(),'local':True})
  if path=='/api/jobs':
   states=[]
   for p in JOBS.glob('*/state.json'):
    try:states.append(json.loads(p.read_text()))
    except Exception:pass
   return self.response(200,sorted(states,key=lambda x:x.get('created',0),reverse=True)[:30])
  match=re.fullmatch(r'/api/jobs/([a-f0-9]{32})(?:/(model|color|project|log))?',path)
  if match:
   jid,kind=match.groups();job=JOBS/jid
   if not (job/'state.json').exists():return self.response(404,{'error':'Projekt nicht gefunden'})
   state=json.loads((job/'state.json').read_text())
   if kind is None:return self.response(200,state)
   if kind=='log':return self.file(job/'job.log','text/plain; charset=utf-8','diagnose.txt')
   if state['status']!='complete':return self.response(409,{'error':'Ergebnis ist noch nicht bereit'})
   if kind in ['model','color']:return self.file(job/(('output_rigged.glb' if state.get('result',{}).get('rigged') else 'output.glb') if kind=='model' else 'preview_color.glb'),'model/gltf-binary','IMG2GILB.glb')
   if kind=='project':
    dest=job/'project.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
     for f in [job/'project.json',job/('result_rigged.json' if state.get('result',{}).get('rigged') else 'result.json'),job/('output_rigged.glb' if state.get('result',{}).get('rigged') else 'output.glb'),*list((job/'inputs').glob('*.png'))]:
      archive_name={'result_rigged.json':'result.json','output_rigged.glb':'output.glb'}.get(f.name,str(f.relative_to(job)));z.write(f,archive_name)
    return self.file(dest,'application/zip','IMG2GILB-Projekt.zip')
  return self.response(404,{'error':'Nicht gefunden'})
 def do_POST(self):
  global ACTIVE,THREAD
  if not self.host_ok() or self.headers.get('X-App-Token')!=TOKEN:return self.response(403,{'error':'Ungültige Sitzung. Seite neu laden.'})
  origin=self.headers.get('Origin')
  if origin and origin not in [f'http://127.0.0.1:{CFG["port"]}',f'http://localhost:{CFG["port"]}']:return self.response(403,{'error':'Ursprung nicht erlaubt'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=48*1024*1024:raise ValueError('Upload ist leer oder größer als 48 MB.')
   data=json.loads(self.rfile.read(size));path=urlsplit(self.path).path
   with LOCK:
    busy=THREAD is not None and THREAD.is_alive()
    if path=='/api/jobs':
     if busy:return self.response(409,{'error':'Ein Modell wird bereits verarbeitet.'})
     settings=data.get('settings',{});views=data.get('views',{})
     if 'front' not in views or not set(views)<=set(['front','back','left','right']) or len(views)>4:raise ValueError('Ein Frontbild ist erforderlich; maximal vier benannte Ansichten.')
     quality=settings.get('quality','standard');triangles=int(settings.get('triangles',100000));height=float(settings.get('height_cm',170));res=int(settings.get('texture_size',2048))
     if quality not in ['fast','standard'] or not 5000<=triangles<=400000 or not math.isfinite(height) or not .1<=height<=10000 or res not in [1024,2048]:raise ValueError('Einstellungen liegen außerhalb des erlaubten Bereichs.')
     for key in ['textures','face','rig']:
      if key in settings and not isinstance(settings[key],bool):raise ValueError('Ungültiger Schalter: '+key)
     if settings.get('rig',False) and not rig_available():raise ValueError('Automatisches Rigging ist noch nicht verfügbar.')
     s={'quality':quality,'triangles':triangles,'height_cm':height,'texture_size':res,'textures':settings.get('textures',True),'face':settings.get('face',False),'rig':settings.get('rig',False),'seed':42}
     if s['face'] and not s['textures']:raise ValueError('Gesichtsdetails erfordern Texturen.')
     decoded={}
     Image.MAX_IMAGE_PIXELS=30_000_000
     for name,url in views.items():
      if not isinstance(url,str) or not url.startswith('data:image/'):raise ValueError('Ungültiges Bildformat')
      raw=base64.b64decode(url.split(',',1)[1],validate=True)
      if len(raw)>12*1024*1024:raise ValueError('Ein Bild darf höchstens 12 MB groß sein.')
      im=Image.open(io.BytesIO(raw));im.load();im=ImageOps.exif_transpose(im)
      if min(im.size)<64 or max(im.size)>8192:raise ValueError('Bild muss 64–8192 Pixel groß sein.')
      decoded[name]=im.convert('RGBA')
     jid=uuid.uuid4().hex;job=JOBS/jid;(job/'inputs').mkdir(parents=True)
     for name,im in decoded.items():im.save(job/'inputs'/f'{name}.png')
     spec={'schema':1,'views':list(decoded),'settings':s,'input_hashes':{name:sha(job/'inputs'/f'{name}.png') for name in decoded}}
     write_json(job/'project.json',spec);write_json(job/'state.json',{'id':jid,'status':'queued','created':time.time(),'settings':s,'views':list(decoded),'stage':None,'completed_stages':0,'stages':[]})
     ACTIVE=Job(job,CFG);THREAD=threading.Thread(target=ACTIVE.run,daemon=True);THREAD.start();return self.response(202,ACTIVE.snapshot())
    m=re.fullmatch(r'/api/jobs/([a-f0-9]{32})/(cancel|retry)',path)
    if m:
     jid,action=m.groups();job=JOBS/jid
     if action=='cancel':
      if not busy or ACTIVE.path.name!=jid:return self.response(409,{'error':'Dieses Projekt läuft nicht.'})
      ACTIVE.stop.set();ACTIVE.update(detail='Abbruch angefordert');return self.response(202,ACTIVE.snapshot())
     if busy:return self.response(409,{'error':'Noch ein laufendes Projekt'})
     if not (job/'state.json').is_file():return self.response(404,{'error':'Projekt nicht gefunden'})
     state=json.loads((job/'state.json').read_text())
     if state['status'] not in ['cancelled','failed','interrupted']:return self.response(409,{'error':'Projekt benötigt keinen Neustart.'})
     ACTIVE=Job(job,CFG);THREAD=threading.Thread(target=ACTIVE.run,daemon=True);THREAD.start();return self.response(202,ACTIVE.snapshot())
    return self.response(404,{'error':'Nicht gefunden'})
  except (ValueError,TypeError,KeyError,IndexError,Image.DecompressionBombError) as exc:return self.response(400,{'error':str(exc)})
  except Exception as exc:return self.response(500,{'error':str(exc)})

if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',CFG['port']),API);print('IMG2GILB ready',flush=True)
 try:server.serve_forever()
 finally:
  if ACTIVE:ACTIVE.stop.set()
  server.server_close()
