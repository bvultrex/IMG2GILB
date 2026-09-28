"""Face Textures 1.0: explicit local-lab adapter, machine-readable stage progress."""
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh,torch
from core import warp_face,blend_face,feature_mask,Rejected
VERSION='1.0.1'
HERE=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def emit(stage,percent):
    print(json.dumps({'stage':stage,'percent':100 if stage in ['processed','skipped'] else None,'progress_kind':'stage_only'}),flush=True)
def atomic_json(path,value):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2),encoding='utf-8');tmp.replace(path)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=HERE/'anime_project.json');ap.add_argument('--output',type=Path);ap.add_argument('--method',choices=['multiband','feather'],default='multiband');a=ap.parse_args()
 project=json.loads(a.project.read_text(encoding='utf-8-sig'));runtime=json.loads((HERE/'runtime.json').read_text())
 source=Path(project['source']);original=Path(project['mesh']);uv=Path(project['uv']);out=a.output or Path(project['output'])
 out=out.resolve();dest=out/'Face_1_0.glb'
 if dest==original.resolve():raise ValueError('Output must not overwrite original mesh')
 out.mkdir(parents=True,exist_ok=True)
 report={'version':VERSION,'status':'running','method':a.method,'inputs':{str(p):digest(p) for p in [source,original,uv]},'models':runtime['models'],'detector_revision':runtime['detector_revision'],'limitations':['single near-frontal anime face, Y-up unrigged Hunyuan UV cache','landmark scores are heuristic, not calibrated guarantees','target landmarks follow texture, not independently measured 3D anatomy']}
 start=time.monotonic()
 def finish(status,reason=None):
  report.update(status=status,seconds=round(time.monotonic()-start,3))
  if reason:report['reason']=reason
  if dest.exists() and status!='failed':report['output_sha256']=digest(dest)
  atomic_json(out/'report.json',report);emit(status,100 if status!='failed' else None)
 def skip(reason):
  shutil.copyfile(original,dest);report['original_bytes_preserved']=digest(dest)==digest(original);finish('skipped',reason)
 try:
  emit('validate_inputs',5)
  scene=trimesh.load(original,process=False)
  if not isinstance(scene,trimesh.Scene) or len(scene.geometry)!=1:raise ValueError('Expected one unrigged mesh')
  # Reject animations/skins rather than silently dropping them through trimesh export.
  import struct
  raw=original.read_bytes();n,kind=struct.unpack_from('<II',raw,12);gltf=json.loads(raw[20:20+n])
  if gltf.get('skins') or gltf.get('animations'):raise ValueError('Rigged/animated input is not supported by this adapter')
  for node in scene.graph.nodes_geometry:
   transform,_=scene.graph[node]
   if not np.allclose(transform,np.eye(4)):raise ValueError('Nonidentity scene transforms are not supported')
  mesh=next(iter(scene.geometry.values()));data=np.load(uv)
  for key,value in [('vertices',mesh.vertices),('faces',mesh.faces),('uv',mesh.visual.uv),('vertex_normals',mesh.vertex_normals)]:
   if data[key].shape!=value.shape or not np.allclose(data[key],value,atol=1e-6):raise ValueError('UV cache does not match input mesh: '+key)
  material=copy.deepcopy(mesh.visual.material)
  if material.baseColorTexture is None:raise ValueError('Missing base color texture')
  baseline=np.asarray(material.baseColorTexture.convert('RGB'))
  if baseline.shape!=(2048,2048,3):raise ValueError('Version 1.0 adapter requires a 2K base atlas')
  os.environ['IMG2GILB_HUNYUAN_SOURCE']=runtime['hunyuan_source']
  from render_adapter import ProjectionRender
  emit('render_face',15)
  renderer=ProjectionRender(default_resolution=2048,texture_size=2048);renderer.load_mesh(mesh.copy());renderer.set_texture(baseline.astype(np.float32)/255)
  target=(renderer.render(0,0,return_type='np').clip(0,1)*255).round().astype('uint8')
  Image.fromarray(target).save(out/'baseline.png')
  emit('detect_landmarks',30)
  env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['HF_HUB_DISABLE_TELEMETRY']='1'
  result=subprocess.run([runtime['detector_python'],str(HERE/'detect.py'),'--config',str(HERE/'runtime.json'),'--images',str(source),str(out/'baseline.png'),'--output',str(out/'landmarks.json')],capture_output=True,text=True,timeout=180,env=env)
  (out/'detector.log').write_text(result.stdout+result.stderr,encoding='utf-8')
  if result.returncode:raise RuntimeError('Detector subprocess failed; see detector.log')
  lm=json.loads((out/'landmarks.json').read_text())
  emit('align_and_blend',50)
  rgba=np.array(Image.open(source).convert('RGBA'))
  try:warped,mask,alpha,alignment=warp_face(rgba,target,lm[0]['faces'],lm[1]['faces'])
  except Rejected as exc:skip(str(exc));return
  corrected=blend_face(warped,target,mask,alpha,a.method,alignment.get('feature_polygons'))
  report['alignment']=alignment
  emit('project_texture',65)
  protected=feature_mask(alpha.shape,alignment.get('feature_polygons'))*alpha
  premult=np.concatenate([corrected*alpha[:,:,None],alpha[:,:,None],protected[:,:,None]],axis=-1)
  # Full-body baking erodes depth edges by several pixels; at eye scale this
  # removes sclera and brow detail. Keep the depth-edge test without dilation.
  renderer.bake_unreliable_kernel_size=0
  tex,cos,_=renderer.back_project(premult,0,0)
  alpha_uv=tex[:,:,3:4].clamp(0,1)
  protection=(tex[:,:,4:5]/alpha_uv.clamp_min(1e-6)).clamp(0,1)
  angle=((cos-.55)/.3).clamp(0,1)
  feature_angle=((cos-.45)/.15).clamp(0,1)
  weight=alpha_uv*(angle*(1-protection)+feature_angle*protection)
  colours=tex[:,:,:3]/alpha_uv.clamp_min(1e-6)
  mixed=torch.as_tensor(baseline.astype(np.float32)/255,device='cuda')*(1-weight)+colours*weight
  atlas=(mixed.clamp(0,1).cpu().numpy()*255).round().astype('uint8')
  w=weight[:,:,0].cpu().numpy();atlas[w<=1e-6]=baseline[w<=1e-6]
  changed=np.any(atlas!=baseline,axis=2)
  if changed.sum()>baseline.shape[0]*baseline.shape[1]*.12:skip('projection_area_too_large');return
  assert not changed[w<=1e-6].any()
  report['changed_atlas_pixels']=int(changed.sum());report['outside_mask_unchanged']=True
  Image.fromarray(atlas).save(out/'albedo.png');Image.fromarray((w*255).round().astype('uint8')).save(out/'projection_mask.png')
  material.baseColorTexture=Image.fromarray(atlas);mesh.visual.material=material
  mesh.vertex_normals=data['vertex_normals']
  emit('export_and_verify',80)
  temp=out/'Face_1_0.partial.glb';mesh.export(temp)
  check=next(iter(trimesh.load(temp,process=False).geometry.values()))
  for name,old,new in [('positions',mesh.vertices,check.vertices),('normals',mesh.vertex_normals,check.vertex_normals),('UV',mesh.visual.uv,check.visual.uv)]:
   if not np.allclose(old,new,atol=1e-6):raise ValueError('Export changed '+name)
  if not np.array_equal(mesh.faces,check.faces):raise ValueError('Export changed faces')
  # Preserve all PBR texture slots and scalar factors except the new base colour.
  for slot in ['metallicRoughnessTexture','normalTexture','occlusionTexture','emissiveTexture']:
   old=getattr(material,slot,None);new=getattr(check.visual.material,slot,None)
   if (old is None)!=(new is None) or old is not None and not np.array_equal(np.asarray(old),np.asarray(new)):raise ValueError('Export changed '+slot)
  for slot in ['metallicFactor','roughnessFactor','baseColorFactor','emissiveFactor','alphaMode','alphaCutoff','doubleSided']:
   old=getattr(material,slot,None);new=getattr(check.visual.material,slot,None)
   if isinstance(old,np.ndarray):ok=np.allclose(old,new)
   else:ok=old==new
   if not ok:raise ValueError('Export changed '+slot)
  temp.replace(dest);report['export_validation']='passed'
  emit('preview_renders',90)
  renderer.set_texture(atlas.astype(np.float32)/255)
  box=np.asarray(lm[1]['faces'][0]['bbox'][:4]);pad=(box[2:]-box[:2]).max()*.3;box[:2]-=pad;box[2:]+=pad
  box[:2]=np.maximum(box[:2],0);box[2:]=np.minimum(box[2:],2048)
  for label,az in [('front',0),('left',35),('right',-35),('profile',75)]:
   im=renderer.render(0,az,return_type='np')
   if label=='front':Image.fromarray((im.clip(0,1)*255).round().astype('uint8')).save(out/'front_full.png')
   Image.fromarray((im.clip(0,1)*255).round().astype('uint8')).crop(tuple(box.astype(int))).save(out/(label+'.png'))
  emit('verify_face_placement',95)
  result=subprocess.run([runtime['detector_python'],str(HERE/'detect.py'),'--config',str(HERE/'runtime.json'),'--images',str(out/'front_full.png'),'--output',str(out/'final_landmarks.json')],capture_output=True,text=True,timeout=180,env=env)
  (out/'final_detector.log').write_text(result.stdout+result.stderr,encoding='utf-8')
  if result.returncode:raise RuntimeError('Final detector failed')
  from core import checked_face
  final_faces=json.loads((out/'final_landmarks.json').read_text())[0]['faces']
  try:_,centers=checked_face(final_faces,target.shape)
  except Rejected as exc:skip('final_'+str(exc));return
  expected=np.asarray(alignment['target_centers']);errors=np.linalg.norm(centers-expected,axis=1)
  report['final_feature_error_pixels']=errors.tolist()
  if errors.max()>np.linalg.norm(expected[1]-expected[0])*.08:skip('final_feature_alignment_drift');return
  report['head_crop']=box.astype(int).tolist();finish('processed')
 except Exception as exc:
  # Fail closed: never leave a previous successful result mistaken for this run.
  shutil.copyfile(original,dest);report['original_bytes_preserved']=digest(dest)==digest(original)
  finish('failed',str(exc));raise

if __name__=='__main__':main()
