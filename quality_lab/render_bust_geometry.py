import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path(r'D:\SF3D_QualityLab\bust_validation');job=Path(r'D:\SF3D_QualityLab\app_jobs')/json.loads((root/'test.json').read_text())['job']
for filename,label in [('shape_raw.glb','raw'),('shape.glb','100k')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(job/filename));s=bpy.context.scene;meshes=[o for o in s.objects if o.type=='MESH'];m=meshes[0];bpy.context.view_layer.update();height=m.dimensions.z;m.scale*=.4/height
 
 for poly in m.data.polygons:poly.use_smooth=True
 s.world=bpy.data.worlds.new('World');s.world.color=(.05,.055,.06);s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.46
 for angle in [0,40]:
  a=math.radians(angle);cam.location=(math.sin(a),-math.cos(a),0);cam.rotation_euler=((Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler());s.render.filepath=str(root/f'geometry_{label}_{angle}.png');bpy.ops.render.render(write_still=True)
