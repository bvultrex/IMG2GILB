"""Blender renders for the dry-splice diagnostic."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
MODEL = ROOT / "detail_dry_splice_scene.glb"
REPORT = ROOT / "detail_dry_splice_render.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(MODEL))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
assert len(meshes) == 2, f"Expected two meshes, got {len(meshes)}"

base = next((o for o in meshes if "base" in o.name.lower()), meshes[0])
patch = next((o for o in meshes if o != base), meshes[1])

for obj in meshes:
    for poly in obj.data.polygons:
        poly.use_smooth = True

scene.world = bpy.data.worlds.new("DiagnosticWorld")
scene.world.color = (0.035, 0.035, 0.04)
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.background_type = "WORLD"
scene.display.shading.color_type = "OBJECT"
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

# Strong luminance contrast rather than red/green coding.
base.color = (0.22, 0.22, 0.24, 1.0)
patch.color = (0.92, 0.92, 0.92, 1.0)

bpy.ops.object.camera_add()
cam = bpy.context.object
scene.camera = cam
cam.data.type = "ORTHO"

# Fit camera to imported full bust after glTF axis conversion.
corners = []
for obj in meshes:
    corners.extend([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])
zmin = min(v.z for v in corners)
zmax = max(v.z for v in corners)
height = zmax - zmin
center_z = (zmin + zmax) * 0.5
cam.data.ortho_scale = height * 1.15

outputs = []
for name, angle in [("front", 0), ("three_quarter", 40)]:
    a = math.radians(angle)
    distance = max(height * 3.0, 1.0)
    cam.location = (math.sin(a) * distance, -math.cos(a) * distance, center_z)
    target = Vector((0, 0, center_z))
    cam.rotation_euler = ((target - cam.location).to_track_quat("-Z", "Y").to_euler())
    scene.render.filepath = str(ROOT / f"dry_splice_{name}_contrast.png")
    bpy.ops.render.render(write_still=True)
    outputs.append(scene.render.filepath)

    # Neutral clay version for silhouette/shape reading.
    base.color = (0.58, 0.58, 0.58, 1.0)
    patch.color = (0.58, 0.58, 0.58, 1.0)
    scene.render.filepath = str(ROOT / f"dry_splice_{name}_clay.png")
    bpy.ops.render.render(write_still=True)
    outputs.append(scene.render.filepath)
    base.color = (0.22, 0.22, 0.24, 1.0)
    patch.color = (0.92, 0.92, 0.92, 1.0)

report = {
    "status": "rendered",
    "mesh_count": len(meshes),
    "height_m_blender": float(height),
    "outputs": outputs,
}
REPORT.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
