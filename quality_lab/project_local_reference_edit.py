"""Isolated masked reference-edit projection; never a production segmentation rule.

The explicit fixture ROI is a diagnostic constraint, not an automatic material detector.
Only edit colors are projected. Existing atlas pixels outside projected mask stay exact.
"""
import argparse
import json
import hashlib
from pathlib import Path
import cv2
import numpy as np
import torch
import trimesh
from PIL import Image
from project_hybrid_a3 import ProjectionRender
from replace_glb_albedo_exact import replace

p = argparse.ArgumentParser()
p.add_argument('--job', type=Path, required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--atlas', type=Path, required=True)
p.add_argument('--original', type=Path, required=True)
p.add_argument('--edited', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--roi', type=Path, required=True)
p.add_argument('--azimuth', type=float, required=True)
p.add_argument('--local-flow', action='store_true', help='Diagnostic bidirectionally checked image-to-current-render registration')
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
spec = json.loads(a.roi.read_text())
original = np.asarray(Image.open(a.original).convert('RGB'))
edited = np.asarray(Image.open(a.edited).convert('RGB'))
assert original.shape == edited.shape
h,w = original.shape[:2]
roi = np.zeros((h,w), np.uint8)
cv2.fillPoly(roi, [np.rint(np.array(spec['polygon'])*[w,h]).astype(np.int32)], 1)
hsv = cv2.cvtColor(original, cv2.COLOR_RGB2HSV)
# Restrict to the original pale garment; preserve belts/straps and all non-target regions.
target = ((roi > 0) & (hsv[:,:,1] < spec['max_saturation']) &
          (hsv[:,:,2] > spec['min_value'])).astype(np.uint8)
alpha = np.clip(cv2.distanceTransform(target, cv2.DIST_L2, 5)/3.,0,1)
Image.fromarray((alpha*255).astype(np.uint8)).save(a.out/'reference_edit_mask.png')
assert alpha.sum() > 100, 'Empty target mask'
data = np.load(a.job/'controls/uv_mesh.npz')
mesh = trimesh.Trimesh(vertices=data['vertices'], faces=data['faces'], process=False,
    visual=trimesh.visual.TextureVisuals(uv=data['uv']))
mesh.vertex_normals = data['vertex_normals']
base_u8 = np.asarray(Image.open(a.atlas).convert('RGB'))
size = base_u8.shape[0]
assert base_u8.shape == (2048,2048,3), 'Fixed 2K atlas required'
renderer = ProjectionRender(default_resolution=size, texture_size=size)
renderer.load_mesh(mesh)
renderer.set_texture(base_u8.astype(np.float32)/255.)
alignment = {'mode':'existing_alignment'}
if a.local_flow:
    rendered = renderer.render(0,a.azimuth,return_type='np')
    render_rgb = cv2.resize(np.rint(rendered[:,:,:3].clip(0,1)*255).astype(np.uint8),(w,h))
    Image.fromarray(render_rgb).save(a.out/'registration_target.png')
    clahe = cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8))
    gray_target = clahe.apply(cv2.cvtColor(render_rgb,cv2.COLOR_RGB2GRAY))
    gray_source = clahe.apply(cv2.cvtColor(edited,cv2.COLOR_RGB2GRAY))
    flow_engine = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    forward = flow_engine.calc(gray_target,gray_source,None)
    backward = flow_engine.calc(gray_source,gray_target,None)
    yy,xx = np.mgrid[:h,:w].astype(np.float32)
    mx,my = xx+forward[:,:,0],yy+forward[:,:,1]
    reverse = cv2.remap(backward,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    cycle = np.linalg.norm(forward+reverse,axis=2)
    magnitude = np.linalg.norm(forward,axis=2)
    warped_alpha = cv2.remap(alpha,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    # Reject unreliable correspondence; never clamp a large displacement into a false match.
    reliable = (cycle <= 2.) & (magnitude <= 24.)
    region = warped_alpha > .5
    alignment = {'mode':'DIS_bidirectional', 'cycle_limit_pixels':2., 'displacement_limit_pixels':24.,
        'target_pixels':int(region.sum()),'reliable_pixels':int((region&reliable).sum()),
        'median_displacement':float(np.median(magnitude[region])),
        'median_cycle_error':float(np.median(cycle[region])),
        'limitation':'Photometric flow is not semantic correspondence; visual gate required.'}
    alpha = warped_alpha*np.clip(cv2.distanceTransform(reliable.astype(np.uint8),cv2.DIST_L2,5)/3.,0,1)
    edited = cv2.remap(edited,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    Image.fromarray(edited).save(a.out/'registered_edit.png')
    Image.fromarray(np.rint(alpha*255).astype(np.uint8)).save(a.out/'registered_mask.png')
    np.savez_compressed(a.out/'registration.npz',flow=forward,cycle_error=cycle)
premult = np.concatenate([edited.astype(np.float32)/255.*alpha[:,:,None],alpha[:,:,None]],-1)
premult = cv2.resize(premult,(size,size),interpolation=cv2.INTER_LINEAR)
with torch.inference_mode():
    tex,cos,_ = renderer.back_project(premult,0,a.azimuth)
    opacity = tex[:,:,3:4].clamp(0,1)
    color = tex[:,:,:3]/opacity.clamp_min(1e-6)
    incidence = ((cos-.3)/.5).clamp(0,1)
    weight = opacity*incidence
    weights = weight.detach().cpu().numpy()
    result = base_u8/255.*(1-weights)+color.detach().cpu().numpy()*weights
result_u8 = np.rint(result.clip(0,1)*255).astype(np.uint8)
outside = weights[:,:,0] == 0
assert np.array_equal(result_u8[outside],base_u8[outside])
atlas = a.out/'albedo.png'
Image.fromarray(result_u8).save(atlas)
Image.fromarray(np.rint(weights[:,:,0]*255).astype(np.uint8)).save(a.out/'atlas_edit_mask.png')
report = replace(a.source,atlas,a.out/'candidate.glb')
report.update(changed_texels=int(np.any(result_u8 != base_u8,axis=2).sum()), alignment=alignment,
    outside_mask_exact=True, production_accepted=False, azimuth=a.azimuth,
    limitation='Fixture-specific diagnostic ROI/color gate, not automatic semantic segmentation. Existing registration retained; inspect oblique seams.',
    inputs={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in
        [a.source,a.atlas,a.original,a.edited,a.roi]})
(a.out/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
