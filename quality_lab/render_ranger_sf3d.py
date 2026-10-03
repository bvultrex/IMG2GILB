import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

argv = sys.argv[sys.argv.index("--")+1:]
model = Path(argv[argv.index("--model")+1])
out = Path(argv[argv.index("--output")+1])
prefix = argv[argv.index("--prefix")+1] if "--prefix" in argv else "view"
mode = argv[argv.index("--mode")+1] if "--mode" in argv else "clay"
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(model))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
assert meshes
scene.world = bpy.data.worlds.new("W"); scene.world.color=(0.05,0.055,0.06)
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True
scene.display.shading.background_type="WORLD"
scene.render.resolution_x=720; scene.render.resolution_y=960; scene.render.resolution_percentage=100
if mode=="clay":
  scene.display.shading.color_type="SINGLE"
  scene.display.shading.single_color=(0.55,0.55,0.55)
else:
  scene.display.shading.color_type="TEXTURE"
bpy.ops.object.camera_add(); cam=bpy.context.object; scene.camera=cam; cam.data.type="ORTHO"
pts=[]
for m in meshes:
  pts.extend([m.matrix_world@v.co for v in m.data.vertices])
xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
extent=max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
cam.data.ortho_scale=float(extent*1.25)
center=Vector(((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2))
outputs=[]
for name,angle in [("front",0),("three_quarter",40),("side",90),("back",180)]:
  a=math.radians(angle); dist=extent*1.6
  cam.location=(center.x+math.sin(a)*dist, center.y-math.cos(a)*dist, center.z)
  cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y").to_euler())
  scene.render.filepath=str(out/f"{prefix}_{name}.png")
  bpy.ops.render.render(write_still=True)
  outputs.append(scene.render.filepath)
(out/f"{prefix}_report.json").write_text(json.dumps({"model":str(model),"mode":mode,"outputs":outputs,"height_m":float(max(zs)-min(zs))},indent=2))
print(json.dumps({"ok":True,"n":len(outputs)}))