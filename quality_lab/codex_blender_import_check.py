"""Independent Blender GLB import and CPU unlit render; preserves source assets."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--model', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.out.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(a.model.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.model))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
assert meshes, 'No imported mesh'
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
center = (lo + hi) / 2
extent = max(hi-lo)
images = [{'name': i.name, 'size': list(i.size)} for i in bpy.data.images if i.type == 'IMAGE']
assert any(i['size'][0] > 0 for i in images), 'No decoded texture'
report = {'source_sha256': source_hash, 'blender': bpy.app.version_string,
          'mesh_count': len(meshes), 'vertices': sum(len(o.data.vertices) for o in meshes),
          'triangles': sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),
          'extents_m': list(hi-lo), 'images': images,
          'scope': 'Independent GLB import and base-color emission render; PBR lighting and Studio UI not covered'}
# Link imported base-color input to emission, only in this transient Blender scene.
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if principled and output:
        emission = nodes.new('ShaderNodeEmission')
        base = principled.inputs['Base Color']
        if base.is_linked:
            links.new(base.links[0].from_socket, emission.inputs['Color'])
        else:
            emission.inputs['Color'].default_value = base.default_value
        links.new(emission.outputs[0], output.inputs['Surface'])
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add(location=center + Vector((0, -extent*3, 0)))
camera = bpy.context.object
camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = extent*1.12
scene.camera = camera
scene.render.filepath = str(a.out/'front_unlit.png')
bpy.ops.render.render(write_still=True)
report['source_unchanged'] = hashlib.sha256(a.model.read_bytes()).hexdigest() == source_hash
assert report['source_unchanged']
(a.out/'import_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('IMPORT_CHECK_PASS', json.dumps(report), flush=True)
