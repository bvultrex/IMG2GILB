"""Bounded local correction experiment; fixed topology, measured displacement."""
from pathlib import Path
import hashlib,json,argparse
import numpy as np
import trimesh,pymeshlab
from codex_splice_boundary_audit import audit
src=Path('../quality_runs/headprobe_fan_repair/candidate.glb')
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
out=a.out;out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(src.read_bytes()).hexdigest()
m=trimesh.load(src,force='mesh',process=False)
v=np.asarray(m.vertices).copy();f=np.asarray(m.faces).copy()
ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(vertex_matrix=v,face_matrix=f))
ms.compute_selection_by_self_intersections_per_face()
before=int(ms.current_mesh().face_selection_array().sum())
ms.compute_selection_transfer_face_to_vertex(inclusive=False)
selected=ms.current_mesh().vertex_selection_array().copy()
assert selected.any(),'Selection transfer produced no editable vertices'
ms.apply_coord_laplacian_smoothing(stepsmoothnum=1,boundary=False,cotangentweight=False,selected=True)
proposal=ms.current_mesh().vertex_matrix();delta=proposal-v
assert np.max(np.abs(delta[~selected]))<1e-12
length=np.linalg.norm(delta,axis=1)
results=[]
for cap in [.0001,.00025,.0005]:
    moved=delta*np.minimum(1,cap/np.maximum(length,1e-15))[:,None]
    candidate=trimesh.Trimesh(v+moved,f.copy(),process=False)
    changed=np.linalg.norm(moved,axis=1)>1e-12
    affected=np.unique(f[changed[f].any(axis=1)])
    normals=m.vertex_normals.copy();normals[affected]=candidate.vertex_normals[affected]
    candidate.vertex_normals=normals
    check=pymeshlab.MeshSet();check.add_mesh(pymeshlab.Mesh(vertex_matrix=candidate.vertices,face_matrix=f))
    check.compute_selection_by_self_intersections_per_face()
    count=int(check.current_mesh().face_selection_array().sum())
    path=out/f'cap_{round(cap*1e6)}um.glb';candidate.export(path,include_normals=True)
    results.append(dict(path=path.name,cap_mm=cap*1000,moved_vertices=int(changed.sum()),
                        max_move_mm=float(np.linalg.norm(moved,axis=1).max()*1000),
                        flagged_faces=count,topology=audit(candidate),production_accepted=False))
assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
report=dict(source_sha256=sha,before_flagged_faces=before,selected_vertices=int(selected.sum()),candidates=results)
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
