"""Read-only output acceptance for the bust fixture; run after its Studio job finishes."""
import json,sys,time,subprocess
from pathlib import Path
import numpy as np,trimesh
sys.path.insert(0,r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop')
from validate_rig import load_glb
root=Path(r'D:\SF3D_QualityLab\bust_validation');record=json.loads((root/'test.json').read_text());job=Path(r'D:\SF3D_QualityLab\app_jobs')/record['job'];last=None
for _ in range(1800):
 state=json.loads((job/'state.json').read_text())
 marker=(state['status'],state.get('stage'))
 if marker!=last:print(marker,flush=True);last=marker
 if state['status'] in ('complete','failed','cancelled','interrupted'):break
 time.sleep(2)
else:raise TimeoutError('Bust job did not finish within one hour')
if state['status']!='complete':raise RuntimeError(state.get('error') or state['status'])
d,b=load_glb(job/'output.glb');assert not d.get('skins');assert not d.get('animations')
scene=trimesh.load(job/'output.glb',process=False);mesh=next(iter(scene.geometry.values()))
assert np.isfinite(mesh.vertices).all();assert abs(mesh.extents[1]-.4)<1e-5;assert mesh.visual.material.baseColorTexture.size==(2048,2048)
report={'status':'structural_checks_passed','job':record['job'],'triangles':len(mesh.faces),'vertices':len(mesh.vertices),'height_cm':float(mesh.extents[1]*100),'texture_size':list(mesh.visual.material.baseColorTexture.size),'rigged':False,'face_refinement':False,'watertight':bool(mesh.is_watertight),'elapsed_seconds':state['finished']-state['started'],'visual_review':'pending','limitations':['Side pedestal projections are inconsistent with torso rotation','Structural checks do not measure fine detail fidelity']}
(root/'acceptance.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
