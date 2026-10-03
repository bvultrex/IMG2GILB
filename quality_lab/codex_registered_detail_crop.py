"""Transfer verified historical registration; inspect box crop without surface-distance holes."""
import json, hashlib
from pathlib import Path
import numpy as np
import trimesh
from codex_splice_boundary_audit import audit

root=Path('D:/SF3D_QualityLab/bust_validation/shape_ablation')
out=Path('../quality_runs/headprobe_coherent_crop');out.mkdir(parents=True,exist_ok=False)
src=root/'trellis1024_direct_headprobe_100000_remesh512.glb'
dst=root/'detail_registered_v5_autoroiv3.glb'
new=Path('../quality_runs/headprobe_voxel768_cleanup_normals_verified/candidate.glb')
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [src,dst,new]}
s=trimesh.load(src,force='mesh',process=False); d=trimesh.load(dst,force='mesh',process=False)
assert np.array_equal(s.faces,d.faces)
affine=np.linalg.lstsq(np.c_[s.vertices,np.ones(len(s.vertices))],d.vertices,rcond=None)[0]
error=np.linalg.norm(np.c_[s.vertices,np.ones(len(s.vertices))]@affine-d.vertices,axis=1).max()
assert error<1e-7
m=trimesh.load(new,force='mesh',process=False)
matrix=np.eye(4);matrix[:3,:]=affine.T;m.apply_transform(matrix)
v=m.vertices
inside=(abs(v[:,0])<.066)&(v[:,1]>.090)&(v[:,1]<.183)&(v[:,2]>-.010)
keep=inside[m.faces].all(axis=1)
patch=m.submesh([keep],append=True,repair=False)
patch.export(out/'patch.glb',include_normals=True)
m.export(out/'registered.glb',include_normals=True)
e=np.sort(m.edges,axis=1);u,c=np.unique(e,axis=0,return_counts=True)
bad=u[c>2]; centers=v[bad].mean(1)
report=dict(registration_transfer_max_error_m=float(error),source_hashes=hashes,
            full=audit(m),patch=audit(patch),
            contact_centers_m=centers.tolist(),contacts_fully_in_crop=int(inside[bad].all(axis=1).sum()),
            production_accepted=False,scope='Historical fixture box; no fusion or general ROI claim')
for p,h in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
