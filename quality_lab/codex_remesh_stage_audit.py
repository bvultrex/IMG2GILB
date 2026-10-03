"""Replay existing cleanup with per-stage indexed topology measurements."""
import trellis_bootstrap
import argparse
import hashlib
import json
from pathlib import Path
import torch
import trimesh
import numpy as np
import cumesh

p = argparse.ArgumentParser()
p.add_argument('--source', required=True, type=Path)
p.add_argument('--out', required=True, type=Path)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
sha = hashlib.sha256(a.source.read_bytes()).hexdigest()
report = dict(source=str(a.source.resolve()), source_sha256=sha, stages=[], production_accepted=False)

def measure(tag, v, f):
    n = len(v)
    e = torch.cat([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]).long()
    lo, hi = e.min(1).values, e.max(1).values
    _, counts = torch.unique(lo*n+hi, return_counts=True)
    r = dict(stage=tag, vertices=n, triangles=len(f), boundary_edges=int((counts==1).sum()),
             nonmanifold_edges=int((counts>2).sum()), degenerate_index_faces=int(((f[:,0]==f[:,1])|(f[:,1]==f[:,2])|(f[:,0]==f[:,2])).sum()))
    report['stages'].append(r)
    (a.out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(r), flush=True)

m = trimesh.load(a.source, force='mesh', process=False)
v = torch.tensor(np.asarray(m.vertices), dtype=torch.float32, device='cuda').contiguous()
f = torch.tensor(np.asarray(m.faces), dtype=torch.int32, device='cuda').contiguous()
del m
measure('raw', v, f)
cm = cumesh.CuMesh(); cm.init(v,f)
del v,f
cm.remove_duplicate_faces(); cm.repair_non_manifold_edges(); cm.unify_face_orientations()
v,f = cm.read(); measure('pre_remesh_repaired',v,f)
lo,hi=v.amin(0),v.amax(0)
v,f=cumesh.remeshing.remesh_narrow_band_dc(v,f,center=(lo+hi)/2,scale=float((hi-lo).max())*515/512,resolution=512,band=1,project_back=0,verbose=False)
measure('remesh512',v,f)
cm.init(v,f); del v,f
cm.simplify(100000,verbose=False)
v,f=cm.read(); measure('simplified100k',v,f)
cm.remove_duplicate_faces(); cm.unify_face_orientations()
v,f=cm.read(); measure('final_cleanup',v,f)
candidate=trimesh.Trimesh(v.cpu().numpy(),f.cpu().numpy(),process=False)
candidate.apply_scale(.4/candidate.extents[1]); candidate.export(a.out/'candidate.glb')
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
report['source_unchanged']=True
(a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
