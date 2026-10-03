"""Independent MeshLab self-intersection selection on frozen candidate meshes."""
import json
from pathlib import Path
import numpy as np
import trimesh,pymeshlab
results=[]
for name in ['headprobe_voxel768_cleanup_normals_verified','headprobe_fan_repair']:
    m=trimesh.load(Path('../quality_runs',name,'candidate.glb'),force='mesh',process=False)
    ms=pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(m.vertices),face_matrix=np.asarray(m.faces)))
    ms.compute_selection_by_self_intersections_per_face()
    selected=ms.current_mesh().face_selection_array()
    results.append(dict(name=name,intersecting_faces=int(selected.sum()),
                        selected_last24=int(selected[-24:].sum()),face_ids=np.flatnonzero(selected).tolist()))
Path('../quality_runs/headprobe_fan_repair/intersections.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print([(r['name'],r['intersecting_faces'],r['selected_last24']) for r in results])
