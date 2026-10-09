"""Ranger-only spatial ablation, not automatic garment segmentation."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch,trimesh
from PIL import Image
from scipy.ndimage import distance_transform_edt
from project_hybrid_a3 import ProjectionRender
from replace_glb_albedo_exact import replace

p=argparse.ArgumentParser()
for name in ('job','base','side','source','out'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
d=np.load(a.job/'controls/uv_mesh.npz');v=d['vertices']
h=(v[:,1]-v[:,1].min())/np.ptp(v[:,1])
n=d['vertex_normals']; side=np.abs(n[:,0])/(np.abs(n[:,0])+np.abs(n[:,2])+1e-6)
# A deliberately bounded hypothesis: side-facing torso/skirt only. Do not
# silently advertise these fixture heights as a semantic clothing detector.
def smooth(x,lo,hi):
 t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
gate=smooth(side,.55,.85)*smooth(h,.43,.47)*(1-smooth(h,.75,.79))
gate*=1-smooth(h,.59,.61)*(1-smooth(h,.65,.67))
m=trimesh.Trimesh(vertices=v,faces=d['faces'],process=False,visual=trimesh.visual.TextureVisuals(uv=d['uv']))
m.vertex_normals=n
r=ProjectionRender(default_resolution=2048,texture_size=2048);r.load_mesh(m)
with torch.inference_mode():
 mask=r.uv_feature_map(torch.tensor(gate[:,None],device='cuda',dtype=torch.float32),bg=0).cpu().numpy()[:,:,0]
 covered=r.uv_feature_map(torch.ones((len(v),1),device='cuda'),bg=0).cpu().numpy()[:,:,0]>.5
ix=distance_transform_edt(~covered,return_distances=False,return_indices=True);mask=mask[ix[0],ix[1]]
base=np.array(Image.open(a.base).convert('RGB'));new=np.array(Image.open(a.side).convert('RGB'))
assert base.shape==new.shape==(2048,2048,3)
result=np.rint(base*(1-mask[...,None])+new*mask[...,None]).clip(0,255).astype('uint8')
assert np.array_equal(result[mask==0],base[mask==0])
Image.fromarray(result).save(a.out/'albedo.png');Image.fromarray((mask*255).astype('uint8')).save(a.out/'mask.png')
report=replace(a.source,a.out/'albedo.png',a.out/'candidate.glb')
report.update(scope='Ranger fixture mask; not semantic segmentation',production_accepted=False,outside_mask_exact=True,changed_texels=int(np.any(base!=result,axis=2).sum()),inputs={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (a.base,a.side,a.source,a.job/'controls/uv_mesh.npz')})
(a.out/'report.json').write_text(json.dumps(report,indent=2))
