"""Independent Blender BVH overlap diagnostic; no geometry changes."""
import bpy,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[2]/'quality_runs/headprobe_fan_repair'
path=root/'candidate.glb';sha=hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(path))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
m=obj.data;m.calc_loop_triangles()
faces=[tuple(t.vertices) for t in m.loop_triangles]
points=[v.co.copy() for v in m.vertices]
tree=BVHTree.FromPolygons(points,faces,all_triangles=True,epsilon=0.0)
pairs=sorted({tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b})
disjoint=[];shared=[]
for a,b in pairs:
    (shared if set(faces[a])&set(faces[b]) else disjoint).append([a,b])
report=dict(source_sha256=sha,triangles=len(faces),overlap_pairs=len(pairs),
            shared_vertex_pairs=len(shared),no_shared_vertex_pairs=len(disjoint),
            disjoint_pairs=disjoint,
            scope='Blender BVH overlapping triangles; shared-vertex exclusions may omit adjacent foldovers; not a complete collision-free certificate')
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
(root/'blender_intersection_pairs.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='disjoint_pairs'}),flush=True)
