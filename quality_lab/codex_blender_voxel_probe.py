"""Isolated voxel remesh / decimate experiment. Run with Blender Python."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import bpy

p = argparse.ArgumentParser()
p.add_argument('--source', required=True, type=Path)
p.add_argument('--out', required=True, type=Path)
p.add_argument('--resolution', type=int, default=384)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out = a.out.resolve(); a.out.mkdir(parents=True, exist_ok=False)
sha = hashlib.sha256(a.source.read_bytes()).hexdigest()
started = time.monotonic()
def checkpoint(stage, **details):
    state = dict(stage=stage, elapsed_seconds=time.monotonic()-started,
                 source_sha256=sha, **details)
    (a.out/'progress.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(state),flush=True)
checkpoint('importing')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
objects = [o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objects)==1
obj=objects[0]; bpy.context.view_layer.objects.active=obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
voxel=max(obj.dimensions)/a.resolution
checkpoint('remeshing', voxel_size=voxel)
mod=obj.modifiers.new('VoxelProbe','REMESH'); mod.mode='VOXEL'
mod.voxel_size=voxel; mod.adaptivity=0.0
bpy.ops.object.modifier_apply(modifier=mod.name)
obj.data.calc_loop_triangles()
pre=len(obj.data.loop_triangles)
bpy.ops.export_scene.gltf(filepath=str(a.out/'remeshed.glb'),export_format='GLB',use_selection=True)
checkpoint('decimating', input_triangles=pre, target_triangles=100000)
if pre>100000:
    mod=obj.modifiers.new('Budget','DECIMATE'); mod.ratio=100000/pre
    bpy.ops.object.modifier_apply(modifier=mod.name)
for poly in obj.data.polygons: poly.use_smooth=True
obj.data.calc_loop_triangles()
bpy.ops.export_scene.gltf(filepath=str(a.out/'candidate.glb'),export_format='GLB',use_selection=True)
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
report=dict(source=str(a.source.resolve()),source_sha256=sha,blender=bpy.app.version_string,
            voxel_size=voxel,resolution=a.resolution,remeshed_triangles=pre,
            reduced_triangles=len(obj.data.loop_triangles),source_unchanged=True,production_accepted=False)
(a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
checkpoint('completed', reduced_triangles=report['reduced_triangles'])
print(json.dumps(report),flush=True)
