"""Read-only source GLB inspection and normalized Blender comparison renders."""
import bpy,json,math,sys,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(r'D:\SF3D_QualityLab\bust_validation\meshy_comparison');root.mkdir(exist_ok=True)
sources={'meshy':Path(r'C:\Users\Shadow\Downloads\Meshy_AI_Ironjaw_Warlord_0928073922_texture.glb'),'ours':Path(r'D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844bc8e15b60509ef308d\output.glb')}
reports={}
if '--ablation' in sys.argv:
 root=Path(r'D:\SF3D_QualityLab\bust_validation\shape_ablation\renders');root.mkdir(exist_ok=True)
 sources={p.stem:p for p in root.parent.glob('*.glb')}
 sources['mv_four_raw']=Path(r'D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844bc8e15b60509ef308d\shape_raw.glb')
 if '--only' in sys.argv:
  tag=sys.argv[sys.argv.index('--only')+1];sources={tag:sources[tag]}
if '--reduced-only' in sys.argv:
 sources={'meshy100k':sources['meshy']}
for label,path in sources.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));s=bpy.context.scene;bpy.context.view_layer.update();meshes=[o for o in s.objects if o.type=='MESH']
 if label.startswith('trellis'):
  for o in meshes:
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if label=='meshy100k':
  # Weld glTF seam-split vertices for this geometry-only reduction probe.
  # Rebuild without UV/custom normals: texture renders of this probe are not valid.
  for o in meshes:
   old=o.data;bm=bmesh.new();bm.from_mesh(old);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));new=bpy.data.meshes.new('GeometryOnly');bm.to_mesh(new);bm.free();o.data=new
  total=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
  for o in meshes:
   bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Comparison100k','DECIMATE');mod.ratio=100000/total;bpy.ops.object.modifier_apply(modifier=mod.name)
 points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box];lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)]);center=(lo+hi)/2
 reports[label]={'file':str(path),'bytes':path.stat().st_size,'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'bounds_dimensions':list(hi-lo),'images':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.type=='IMAGE'],'materials':len(bpy.data.materials)}
 transform=Matrix.Scale(.4/(hi.z-lo.z),4)@Matrix.Translation(-center)
 for o in meshes:
  o.matrix_world=transform@o.matrix_world
  for p in o.data.polygons:p.use_smooth=True
 s.world=bpy.data.worlds.new('World');s.world.color=(.05,.055,.06);s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
 for name,angle,target,scale in [('front',0,(0,0,0),.46),('angle',40,(0,0,0),.46),('back',180,(0,0,0),.46),('face',0,(0,0,.105),.16)]:
  a=math.radians(angle);t=Vector(target);cam.location=t+Vector((math.sin(a),-math.cos(a),0));cam.rotation_euler=((t-cam.location).to_track_quat('-Z','Y').to_euler());cam.data.ortho_scale=scale
  for mode in (['clay'] if label=='meshy100k' or '--ablation' in sys.argv else ['clay','texture']):
   s.display.shading.color_type='SINGLE' if mode=='clay' else 'TEXTURE';s.display.shading.single_color=(.55,.55,.55);s.render.filepath=str(root/f'{label}_{name}_{mode}.png');bpy.ops.render.render(write_still=True)
(root/('reduced_report.json' if '--reduced-only' in sys.argv else 'report.json')).write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
