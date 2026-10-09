"""Controlled ablation: preserve generated clothing, reuse improved hybrid head only.

Normalized height gate is a Ranger diagnostic, not production head segmentation.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch,trimesh
from scipy.ndimage import distance_transform_edt
from PIL import Image
from project_hybrid_a3 import ProjectionRender
from replace_glb_albedo_exact import replace
p=argparse.ArgumentParser()
p.add_argument('--job',type=Path,required=True)
p.add_argument('--paint',type=Path,required=True)
p.add_argument('--hybrid',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--gate-audit',type=Path,help='Experimental face-derived gate, bound to this UV mesh')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
gate=[.825,.85]
if a.gate_audit:
    audit=json.loads(a.gate_audit.read_text())
    assert audit['mesh_sha256']==hashlib.sha256((a.job/'controls/uv_mesh.npz').read_bytes()).hexdigest(), 'Gate belongs to another mesh'
    assert audit.get('accepted') is True, 'No confirmed face: do not apply head refinement'
    gate=audit['proposed_gate']
    assert len(gate)==2 and 0<=gate[0]<gate[1]<=1, 'Invalid gate'
d=np.load(a.job/'controls/uv_mesh.npz')
vertices=d['vertices'];height=vertices[:,1]
height=(height-height.min())/(height.max()-height.min())
mesh=trimesh.Trimesh(vertices=vertices,faces=d['faces'],process=False,
    visual=trimesh.visual.TextureVisuals(uv=d['uv']))
mesh.vertex_normals=d['vertex_normals']
r=ProjectionRender(default_resolution=2048,texture_size=2048);r.load_mesh(mesh)
with torch.inference_mode():
    uvheight=r.uv_feature_map(torch.tensor(height[:,None],device='cuda',dtype=torch.float32),bg=0).cpu().numpy()
    covered=r.uv_feature_map(torch.ones((len(vertices),1),device='cuda'),bg=0).cpu().numpy()[:,:,0]>.5
# Bilinear/mipmap sampling reaches outside rasterized UV triangles. A zero mask
# there reintroduces the old atlas as thin cracks, even when the face is fully
# selected. Extend the selection field to nearest covered UV texel; never blur
# colors or interpolate across disconnected UV islands.
nearest=distance_transform_edt(~covered,return_distances=False,return_indices=True)
uvheight=uvheight[nearest[0],nearest[1]]
# Include the entire jaw. The initial .86-.895 transition crossed the chin,
# mixing generated chin marks back into the corrected face.
t=np.clip((uvheight-gate[0])/(gate[1]-gate[0]),0,1);alpha=t*t*(3-2*t)
paint=np.array(Image.open(a.paint).convert('RGB'))
hybrid=np.array(Image.open(a.hybrid).convert('RGB'))
assert paint.shape==hybrid.shape==(2048,2048,3)
result=np.rint(paint*(1-alpha)+hybrid*alpha).clip(0,255).astype('uint8')
outside=alpha[:,:,0]==0
assert np.array_equal(result[outside],paint[outside])
atlas=a.out/'albedo.png';Image.fromarray(result).save(atlas)
Image.fromarray(np.rint(alpha[:,:,0]*255).astype('uint8')).save(a.out/'head_mask.png')
report=replace(a.job/'textured_pbr.glb',atlas,a.out/'candidate.glb')
report.update(head_height_gate=gate,body_exact=True,production_accepted=False,
    gate_audit_sha256=hashlib.sha256(a.gate_audit.read_bytes()).hexdigest() if a.gate_audit else None,
    input_sha256={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in {'paint':a.paint,'hybrid':a.hybrid,'uv_mesh':a.job/'controls/uv_mesh.npz'}.items()},
    mask_padding='nearest_covered_uv_texel',padded_texels=int((~covered).sum()),
    limitation='Fixture height gate; validates source-scope hypothesis, not general automatic head segmentation.',
    changed_texels=int(np.any(result!=paint,axis=2).sum()))
(a.out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
