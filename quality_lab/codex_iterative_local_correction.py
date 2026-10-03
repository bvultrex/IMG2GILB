"""Bounded iterative experiment, rollback on quality or orientation regression."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
import trimesh,pymeshlab
from codex_splice_boundary_audit import audit
src=Path('../quality_runs/headprobe_fan_repair/candidate.glb')
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--freeze-flips',action='store_true');a=p.parse_args()
out=a.out;out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(src.read_bytes()).hexdigest()
m=trimesh.load(src,force='mesh',process=False)
original=np.asarray(m.vertices).copy();faces=np.asarray(m.faces).copy();current=original.copy()
def selected_mesh(v):
    ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(vertex_matrix=v,face_matrix=faces))
    ms.compute_selection_by_self_intersections_per_face()
    return ms,int(ms.current_mesh().face_selection_array().sum())
_,best=selected_mesh(current);history=[]
for step in range(1,9):
    ms,count=selected_mesh(current)
    if count==0:break
    ms.compute_selection_transfer_face_to_vertex(inclusive=False)
    selected=ms.current_mesh().vertex_selection_array().copy()
    assert selected.any()
    ms.apply_coord_laplacian_smoothing(stepsmoothnum=1,boundary=False,cotangentweight=False,selected=True)
    proposal=ms.current_mesh().vertex_matrix()
    assert np.allclose(proposal[~selected],current[~selected],atol=1e-12)
    delta=proposal-original;length=np.linalg.norm(delta,axis=1)
    proposal=original+delta*np.minimum(1,.00025/np.maximum(length,1e-15))[:,None]
    candidate=trimesh.Trimesh(proposal,faces,process=False)
    frozen=set()
    if a.freeze_flips:
        for attempt in range(16):
            bad=np.einsum('ij,ij->i',candidate.face_normals,m.face_normals)<0
            bad|=~candidate.nondegenerate_faces()
            if not bad.any():break
            frozen.update(np.unique(faces[bad]).tolist())
            ids=np.asarray(sorted(frozen));proposal[ids]=current[ids]
            candidate=trimesh.Trimesh(proposal,faces,process=False)
    flips=int((np.einsum('ij,ij->i',candidate.face_normals,m.face_normals)<0).sum())
    degenerate=int((~candidate.nondegenerate_faces()).sum())
    _,after=selected_mesh(proposal)
    accepted=after<best and flips==0 and degenerate==0
    history.append(dict(step=step,flagged_faces=after,flipped_vs_original=flips,degenerate=degenerate,frozen_vertices=len(frozen),accepted=accepted))
    print(history[-1],flush=True)
    if not accepted:break
    current=proposal;best=after
result=trimesh.Trimesh(current,faces,process=False)
changed=np.linalg.norm(current-original,axis=1)>1e-12
affected=np.unique(faces[changed[faces].any(1)])
normals=m.vertex_normals.copy();normals[affected]=result.vertex_normals[affected];result.vertex_normals=normals
result.export(out/'candidate.glb',include_normals=True)
report=dict(source_sha256=sha,history=history,final_flagged_faces=best,moved_vertices=int(changed.sum()),
            max_total_move_mm=float(np.linalg.norm(current-original,axis=1).max()*1000),topology=audit(result),production_accepted=False)
assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
