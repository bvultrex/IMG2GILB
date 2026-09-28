"""Controlled four-reference paint comparison on the bust's frozen geometry."""
import json,subprocess,time,shutil,uuid,sys
from pathlib import Path
import numpy as np,trimesh
root=Path(r'D:\SF3D_QualityLab\bust_validation');lab=root.parent;desktop=Path(r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop');repo=desktop.parent;record=json.loads((root/'test.json').read_text());base=lab/'app_jobs'/record['job'];out=root/'four_reference';out.mkdir(exist_ok=True);py=lab/'venv/Scripts/python.exe'
while True:
 state=json.loads((base/'state.json').read_text())
 if state['status']=='complete':break
 if state['status'] in ['failed','cancelled','interrupted']:raise RuntimeError('Baseline did not complete')
 time.sleep(2)
def run(args):
 with (out/'run.log').open('a',encoding='utf-8') as log:
  log.write('\nRUN '+json.dumps([str(a) for a in args])+'\n');log.flush();subprocess.run([str(a) for a in args],stdout=log,stderr=subprocess.STDOUT,check=True)
print('Four-reference Paint starting',flush=True)
run([py,repo/'quality_lab/run_paint_multiref.py','--references',*[base/'prepared'/f'{name}.png' for name in ['front','back','left','right']],'--controls',base/'controls','--output',out/'paint','--views','6','--resolution','768'])
print('Baking comparison',flush=True)
run([py,lab/'bake_paint21.py','--input',out/'paint','--uv-cache',base/'controls/uv_mesh.npz','--output-prefix',out/'textured','--views','6','--resolution','768'])
a=next(iter(trimesh.load(base/'output.glb',process=False).geometry.values()));b=next(iter(trimesh.load(out/'textured_pbr.glb',process=False).geometry.values()))
assert np.array_equal(a.faces,b.faces) and np.array_equal(a.vertices,b.vertices);assert np.array_equal(a.visual.uv,b.visual.uv);assert b.visual.material.baseColorTexture.size==(2048,2048)
jid=uuid.uuid4().hex;job=lab/'app_jobs'/jid;job.mkdir();shutil.copytree(base/'inputs',job/'inputs');shutil.copy2(base/'project.json',job/'project.json');shutil.copy2(out/'textured_pbr.glb',job/'output.glb');shutil.copy2(out/'textured_color.glb',job/'preview_color.glb');result=dict(state['result']);result['bytes']=(job/'output.glb').stat().st_size;result['texture_references']=4
now=time.time();state.update(id=jid,label='Büste: 4 Texturreferenzen (Vergleich)',created=now,started=now,finished=now,detail='Gleiche Geometrie und UV; vier statt einer Texturreferenz. Vergleichstest.',result=result)
(job/'result.json').write_text(json.dumps(result,indent=2));(job/'state.json').write_text(json.dumps(state,indent=2));report={'status':'passed','baseline':record['job'],'comparison':jid,'geometry_uv_identical':True,'paint':json.loads((out/'paint/report.json').read_text()),'visual_review':'pending'};(out/'acceptance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
