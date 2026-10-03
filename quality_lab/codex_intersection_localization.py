"""Compare flagged surfaces by geometry rather than unstable face indices."""
import hashlib,json
from pathlib import Path
import numpy as np
import trimesh

lab=Path('../quality_runs')
results=json.loads((lab/'headprobe_fan_repair/intersections.json').read_text())
root=Path('D:/SF3D_QualityLab/bust_validation/shape_ablation')
before=trimesh.load(root/'trellis1024_direct_headprobe_100000_remesh512.glb',force='mesh',process=False)
registered=trimesh.load(root/'detail_registered_v5_autoroiv3.glb',force='mesh',process=False)
assert np.array_equal(before.faces,registered.faces)
A=np.linalg.lstsq(np.c_[before.vertices,np.ones(len(before.vertices))],registered.vertices,rcond=None)[0]
assert np.max(np.abs(np.c_[before.vertices,np.ones(len(before.vertices))]@A-registered.vertices))<1e-7
sets=[];details=[]
for item in results:
    path=lab/item['name']/'candidate.glb'
    m=trimesh.load(path,force='mesh',process=False)
    ids=np.array(item['face_ids'],dtype=int)
    triangles=m.triangles[ids]
    signatures={tuple(sorted(tuple(v) for v in tri)) for tri in triangles}
    sets.append(signatures)
    points=np.c_[triangles.reshape(-1,3),np.ones(len(triangles)*3)]@A
    points=points.reshape(-1,3,3)
    inside=(abs(points[:,:,0])<.066)&(points[:,:,1]>.09)&(points[:,:,1]<.183)&(points[:,:,2]>-.01)
    protected=(abs(points[:,:,0])<.048)&(points[:,:,1]>.100)&(points[:,:,1]<.172)&(points[:,:,2]>0)
    details.append(dict(name=item['name'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        flagged_faces=len(ids),crop_any_vertex=int(inside.any(1).sum()),
                        crop_all_vertices=int(inside.all(1).sum()),protected_any_vertex=int(protected.any(1).sum())))
report=dict(candidates=details,new_flagged_surfaces=len(sets[1]-sets[0]),removed_flagged_surfaces=len(sets[0]-sets[1]),
            exact_flagged_surface_set_unchanged=sets[0]==sets[1],
            scope='MeshLab-selected triangles, historical box only; not unique intersection-pair count or generic ROI')
(lab/'headprobe_fan_repair/intersection_localization.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
