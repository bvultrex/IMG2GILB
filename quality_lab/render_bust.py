"""Blender visual QA: textured and clay views of the completed bust test."""
import bpy,json,math,sys,argparse
from pathlib import Path
from mathutils import Vector
root=Path(r'D:\SF3D_QualityLab\bust_validation');record=json.loads((root/'test.json').read_text());job=Path(r'D:\SF3D_QualityLab\app_jobs')/record['job'];state=json.loads((job/'state.json').read_text());assert state['status']=='complete'
parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=job/'output.glb');parser.add_argument('--output',type=Path,default=root)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);root=args.output;root.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(args.model));scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH'];assert len(meshes)==1
scene.world=bpy.data.worlds.new('QualityWorld');scene.world.color=(.05,.055,.06);scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True;scene.display.shading.background_type='WORLD';scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.46
for name,angle in [('front',0),('three_quarter',40),('side',90),('back',180)]:
 a=math.radians(angle);cam.location=(math.sin(a),-math.cos(a),0);cam.rotation_euler=((Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler())
 for mode in ['texture','clay']:
  scene.display.shading.color_type='TEXTURE' if mode=='texture' else 'SINGLE';scene.display.shading.single_color=(.55,.55,.55);scene.render.filepath=str(root/f'{name}_{mode}.png');bpy.ops.render.render(write_still=True)
points=[meshes[0].matrix_world@v.co for v in meshes[0].data.vertices];report={'blender_import':'passed','height_cm':100*(max(v.z for v in points)-min(v.z for v in points)),'mesh_count':len(meshes),'armatures':sum(o.type=='ARMATURE' for o in scene.objects),'render_views':4,'review':'pending'};assert abs(report['height_cm']-40)<.001;assert report['armatures']==0;(root/'blender_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
