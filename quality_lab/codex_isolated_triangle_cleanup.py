"""Experimental removal of faces whose three edges have no other incident face."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from codex_splice_boundary_audit import audit

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
m=trimesh.load(a.source,force='mesh',process=False)
faces=m.faces.copy(); vertices=m.vertices.copy()
normals=m.vertex_normals.copy()
edges=np.sort(m.edges,axis=1)
_,inverse,counts=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
isolated=(counts[inverse].reshape(-1,3)==1).all(axis=1)
before=audit(m)
removed_area=float(m.area_faces[isolated].sum())
removed_bounds=m.triangles[isolated].reshape(-1,3)
np.save(a.out/'removed_face_ids.npy',np.flatnonzero(isolated))
m.update_faces(~isolated)
assert np.array_equal(m.vertices,vertices)
assert np.array_equal(m.faces,faces[~isolated])
m.vertex_normals=normals
m.export(a.out/'candidate.glb',include_normals=True)
reloaded=trimesh.load(a.out/'candidate.glb',force='mesh',process=False)
assert np.array_equal(reloaded.faces,m.faces)
used=np.unique(m.faces)
assert np.allclose(reloaded.vertex_normals[used],normals[used],atol=1e-6)
report=dict(source_sha256=sha,before=before,after=audit(m),removed_faces=int(isolated.sum()),
            removed_area_m2=removed_area,retained_geometry_exact=True,normals_reload_verified=True,
            removed_bounds=[removed_bounds.min(0).tolist(),removed_bounds.max(0).tolist()] if len(removed_bounds) else None,
            production_accepted=False)
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
(a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
