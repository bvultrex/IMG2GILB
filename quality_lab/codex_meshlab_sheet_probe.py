"""Compare installed MeshLab sheet splitting with no intended geometry displacement."""
from pathlib import Path
import hashlib,json,argparse
import numpy as np
import trimesh,pymeshlab
from scipy.spatial import cKDTree
from codex_splice_boundary_audit import audit

src=Path('../quality_runs/headprobe_voxel768_cleanup_normals_verified/candidate.glb')
p=argparse.ArgumentParser();p.add_argument('--local-repair',action='store_true');p.add_argument('--quad-repair',action='store_true');p.add_argument('--fan-repair',action='store_true');a=p.parse_args()
out=Path('../quality_runs/headprobe_fan_repair' if a.fan_repair else '../quality_runs/headprobe_quad_repair' if a.quad_repair else '../quality_runs/headprobe_meshlab_local_repair' if a.local_repair else '../quality_runs/headprobe_meshlab_sheet_probe');out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(src.read_bytes()).hexdigest()
m=trimesh.load(src,force='mesh',process=False)
ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(m.vertices),face_matrix=np.asarray(m.faces)))
stages=[dict(stage='input',**audit(m))]
operations=[('meshing_repair_non_manifold_edges',dict(method='Split Vertices')),('meshing_repair_non_manifold_vertices',dict(vertdispratio=0.0))]
if a.local_repair:
    operations=[('meshing_repair_non_manifold_edges',dict(method='Remove Faces')),('meshing_close_holes',dict(maxholesize=30,selfintersection=True,refinehole=False))]
if a.quad_repair or a.fan_repair:operations=[('meshing_repair_non_manifold_edges',dict(method='Remove Faces'))]
for name,kwargs in operations:
    ms.apply_filter(name,**kwargs)
    x=ms.current_mesh();candidate=trimesh.Trimesh(x.vertex_matrix(),x.face_matrix(),process=False)
    stages.append(dict(stage=name,**audit(candidate)))
new_centers=[];fan_loops=[]
if a.quad_repair or a.fan_repair:
    edges=candidate.edges; ordered=np.sort(edges,axis=1)
    unique,inverse,counts=np.unique(ordered,axis=0,return_inverse=True,return_counts=True)
    boundary=edges[counts[inverse]==1][:,::-1]
    following={int(x):int(y) for x,y in boundary}
    assert len(following)==len(boundary)
    existing={tuple(e) for e in unique}; added=[]
    while following:
        start=next(iter(following));loop=[start]; nxt=following.pop(start)
        while nxt!=start:loop.append(nxt);nxt=following.pop(nxt)
        assert len(loop)==4,'Only isolated quadrilateral holes supported'
        if a.fan_repair:
            center_id=len(candidate.vertices)+len(new_centers)
            new_centers.append(candidate.vertices[loop].mean(0));fan_loops.append(loop)
            added.extend([[loop[i],loop[(i+1)%4],center_id] for i in range(4)])
            continue
        x,y,z,w=loop
        if tuple(sorted((x,z))) not in existing:added.extend([[x,y,z],[x,z,w]])
        elif tuple(sorted((y,w))) not in existing:added.extend([[y,z,w],[y,w,x]])
        else:raise ValueError('Both diagonals already occupied; reject')
    if new_centers:candidate.vertices=np.vstack([candidate.vertices,new_centers])
    candidate.faces=np.vstack([candidate.faces,np.asarray(added)])
    stages.append(dict(stage='unoccupied_diagonal_quad_fill',**audit(candidate)))
distance,ids=cKDTree(m.vertices).query(candidate.vertices)
candidate.vertex_normals=m.vertex_normals[ids]
if fan_loops:
    n=candidate.vertex_normals.copy()
    for i,loop in enumerate(fan_loops):
        mean=n[loop].mean(0);n[len(n)-len(fan_loops)+i]=mean/max(np.linalg.norm(mean),1e-12)
    candidate.vertex_normals=n
candidate.export(out/'candidate.glb',include_normals=True)
report=dict(source_sha256=sha,stages=stages,max_vertex_to_source_vertex_distance=float(distance.max()),
            new_vertices=len(new_centers),degenerate_faces=int((~candidate.nondegenerate_faces()).sum()),
            winding_consistent=bool(candidate.is_winding_consistent),
            duplicate_faces=len(candidate.faces)-len(np.unique(np.sort(candidate.faces,axis=1),axis=0)),
            faces_before=len(m.faces),faces_after=len(candidate.faces),production_accepted=False,
            scope='Splitting diagnostic; do not conflate indexed manifoldness with spatial separation')
assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
