"""Blender clay views for ranger TRELLIS baseline."""
import bpy, json, math, sys, argparse
from pathlib import Path
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = args.output
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.model))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
assert len(meshes) == 1
scene.world = bpy.data.worlds.new('QualityWorld')
scene.world.color = (0.05, 0.055, 0.06)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.55, 0.55, 0.55)
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.background_type = 'WORLD'
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
bpy.ops.object.camera_add()
cam = bpy.context.object
scene.camera = cam
cam.data.type = 'ORTHO'
# Full-body needs larger ortho scale than bust 0.46
bb = [meshes[0].matrix_world @ v.co for v in meshes[0].data.vertices]
xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
cam.data.ortho_scale = float(extent * 1.25)
center = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
for name, angle in [('front', 0), ('three_quarter', 40), ('side', 90), ('back', 180)]:
    a = math.radians(angle)
    dist = extent * 1.6
    cam.location = (center.x + math.sin(a) * dist, center.y - math.cos(a) * dist, center.z)
    cam.rotation_euler = ((center - cam.location).to_track_quat('-Z', 'Y').to_euler())
    scene.render.filepath = str(out / f'{name}_clay.png')
    bpy.ops.render.render(write_still=True)
report = {
    'blender_import': 'passed',
    'mesh_count': len(meshes),
    'height_m': float(max(zs) - min(zs)),
    'render_views': 4,
    'model': str(args.model),
}
(out / 'blender_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
