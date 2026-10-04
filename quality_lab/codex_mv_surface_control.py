"""Preserve raw MV mesh, evaluate native-scale fill and DC remesh separately."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
import trimesh
import cumesh

p = argparse.ArgumentParser()
p.add_argument('--input', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=False)
start = time.time()
stages = []
def record(stage, **kw):
    stages.append(dict(stage=stage, seconds=time.time()-start, **kw))
    (out/'report.json').write_text(json.dumps(stages, indent=2))
    print(stages[-1], flush=True)
def save(name, v, f):
    trimesh.Trimesh(v.cpu().numpy(), f.cpu().numpy(), process=False).export(out/name)
m = trimesh.load(a.input, process=False)
v = torch.tensor(np.asarray(m.vertices), dtype=torch.float32, device='cuda')
f = torch.tensor(np.asarray(m.faces), dtype=torch.int32, device='cuda')
cm = cumesh.CuMesh()
cm.init(v, f)
cm.fill_holes(max_hole_perimeter=.01)
v,f = cm.read()
save('filled.ply', v, f)
record('filled', triangles=len(f), native_perimeter=.01)
v,f = cumesh.remeshing.remesh_narrow_band_dc(
    v, f, center=torch.zeros(3, device='cuda'), scale=1027/1024,
    resolution=1024, band=1, project_back=0, verbose=True)
save('remeshed.ply', v, f)
record('remeshed', triangles=len(f))
cm.init(v,f)
cm.simplify(500000, verbose=True)
cm.compute_vertex_normals()
v,f = cm.read()
n = cm.read_vertex_normals()
# Local raw is Z-up. GLB uses Y-up; preserve outward winding (proper rotation).
v=v.cpu().numpy()[:,[0,2,1]].copy(); v[:,2]*=-1
n=n.cpu().numpy()[:,[0,2,1]].copy(); n[:,2]*=-1
trimesh.Trimesh(v, f.cpu().numpy(), vertex_normals=n, process=False).export(out/'candidate.glb')
record('complete', triangles=len(f), production_accepted=False)
