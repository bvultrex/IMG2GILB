import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(r'D:\SF3D_QualityLab\male_anime_validation\walk_v2');root.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'D:\SF3D_QualityLab\app_jobs\8532227aa14949dc97de45503b6ce6da\preview_color.glb')
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o!=mesh:o.hide_render=True
s=bpy.context.scene;s.world=bpy.data.worlds.new('World');s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=False;s.display.shading.background_type='WORLD';s.world.color=(.045,.055,.05);s.render.resolution_x=600;s.render.resolution_y=800;s.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(3,-4,.1));cam=bpy.context.object;cam.rotation_euler=((Vector((0,0,-.02))-cam.location).to_track_quat('-Z','Y').to_euler());cam.data.type='ORTHO';cam.data.ortho_scale=1.95;s.camera=cam
report={'actions':[{ 'name':a.name,'range':list(a.frame_range)} for a in bpy.data.actions],'frames':[]}
for frame in [1,9,16,24,31]:
 s.frame_set(frame);bpy.context.view_layer.update();row={'frame':frame,'ankles':{name:list(arm.matrix_world@arm.pose.bones[name].head) for name in ['bone_16','bone_20']}};report['frames'].append(row)
 if frame!=31:s.render.filepath=str(root/f'frame_{frame}.png');bpy.ops.render.render(write_still=True)
samples=[]
for k in range(81):
 f=k*30/80;s.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
 samples.append({name:list(arm.matrix_world@arm.pose.bones[name].head) for name in ['bone_16','bone_20']})
report['stance_height_range_m']={name:max(samples[k][name][2] for k in range(80) if (k/80+offset)%1<.6)-min(samples[k][name][2] for k in range(80) if (k/80+offset)%1<.6) for name,offset in [('bone_20',0),('bone_16',.5)]}
report['loop_ankle_error_m']=max((Vector(samples[0][name])-Vector(samples[-1][name])).length for name in samples[0])
assert max(report['stance_height_range_m'].values())<.001
assert report['loop_ankle_error_m']<1e-5
(root/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
