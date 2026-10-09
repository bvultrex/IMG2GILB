"""Derive an experimental head-height gate from a confirmed render face box.

Audit only: writes no model and never substitutes a guessed face on failure.
The input report must belong to the supplied mesh and baseline render.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import trimesh
from project_hybrid_a3 import ProjectionRender

p = argparse.ArgumentParser()
p.add_argument('--job', type=Path, required=True)
p.add_argument('--projection', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
assert not a.out.exists(), 'Preserve previous audits'
report = json.loads((a.projection/'report.json').read_text())
assert Path(report['job']).resolve() == a.job.resolve()
front = next(v for v in report['views'] if v['name'] == 'front')
steps = front.get('align', {}).get('micro', {}).get('steps', [])
boxes = [s['dst_bbox'] for s in steps if s.get('mode') == 'face_center_translation' and 'dst_bbox' in s]
result = {'accepted': False, 'production_accepted': False}
if not boxes:
    result['reason'] = 'No confirmed destination face; retain generated texture'
else:
    x0,y0,x1,y1 = boxes[0]
    d = np.load(a.job/'controls/uv_mesh.npz')
    v = d['vertices']; h = (v[:,1]-v[:,1].min())/np.ptp(v[:,1])
    mesh = trimesh.Trimesh(vertices=v, faces=d['faces'], process=False,
        visual=trimesh.visual.TextureVisuals(uv=d['uv']))
    r = ProjectionRender(default_resolution=2048, texture_size=2048)
    r.load_mesh(mesh)
    with torch.inference_mode():
        _,clip = r.get_pos_from_mvp(0,0,None,None)
        rast,_ = r.raster_rasterize(clip,r.pos_idx,resolution=[2048,2048])
        field,_ = r.raster_interpolate(torch.tensor(h,device='cuda',dtype=torch.float32)[None,:,None],rast,r.pos_idx)
        field = field[0,:,:,0].cpu().numpy()
        visible = rast[0,:,:,-1].cpu().numpy()>0
    def sample(row):
        row = int(round(row)); left=int(x0+(x1-x0)*.25); right=int(x1-(x1-x0)*.25)
        values=field[max(0,row-2):row+3,left:right][visible[max(0,row-2):row+3,left:right]]
        if len(values)<10: raise ValueError('Insufficient visible face support')
        return float(np.median(values))
    forehead,jaw=sample(y0),sample(y1)
    span=forehead-jaw
    if not 0 < span < .3: raise ValueError('Invalid face scale or coordinate orientation')
    result.update(accepted=True, destination_bbox=boxes[0], forehead_height=forehead,
        jaw_height=jaw, proposed_gate=[jaw-.35*span,jaw-.1*span],
        limitation='Face-derived vertical slab, not semantic head segmentation; inspect hair/collar and second fixture before integration')
result['report_sha256']=hashlib.sha256((a.projection/'report.json').read_bytes()).hexdigest()
result['mesh_sha256']=hashlib.sha256((a.job/'controls/uv_mesh.npz').read_bytes()).hexdigest()
a.out.write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
