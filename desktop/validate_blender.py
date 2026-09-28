"""Validate a completed Studio job by importing its GLB in Blender background mode."""
import json
import sys
from pathlib import Path
import bpy

job = Path(sys.argv[sys.argv.index('--') + 1])
expected = json.loads((job / 'result.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(job / 'output.glb'))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
assert meshes, 'No mesh imported'
points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
height = max(p.z for p in points) - min(p.z for p in points)
assert abs(height * 100 - expected['height_cm']) < .001, height
textures = [{'name': image.name, 'size': list(image.size), 'packed': bool(image.packed_file)}
            for image in bpy.data.images if image.type == 'IMAGE' and image.size[0]]
if expected['texture_size']:
    assert any(t['size'] == [expected['texture_size']] * 2 and t['packed'] for t in textures), textures
triangles = 0
for obj in meshes:
    obj.data.calc_loop_triangles()
    triangles += len(obj.data.loop_triangles)
assert triangles == expected['triangles'], (triangles, expected)
report = {'status': 'passed', 'blender': bpy.app.version_string, 'height_cm': height * 100,
          'triangles': triangles, 'meshes': len(meshes), 'textures': textures}
(job / 'blender-check.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
