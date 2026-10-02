"""GPU stages invoked in isolated subprocesses. Does not change installed packages."""
import argparse,json,os,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('stage',choices=['shape','uv','remesh','finalize']);p.add_argument('job');p.add_argument('config');a=p.parse_args()
job=Path(a.job);cfg=json.loads(Path(a.config).read_text(encoding='utf-8-sig'));spec=json.loads((job/'project.json').read_text());s=spec['settings'];lab=Path(cfg['lab'])
os.environ.update(HF_HOME=str(lab/'hf'),HY3DGEN_MODELS=str(lab/'models'),HF_HUB_OFFLINE='1')
sys.path.insert(0,cfg['hunyuan'])
import numpy as np,trimesh
from PIL import Image
if a.stage=='shape':
 import torch,pymeshlab
 from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
 pipe=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(lab/'models/tencent/Hunyuan3D-2mv'),subfolder='hunyuan3d-dit-v2-mv',variant='fp16',use_safetensors=True)
 images={name:Image.open(job/'prepared'/f'{name}.png') for name in spec['views']}
 mesh=pipe(image=images,num_inference_steps=25 if s['quality']=='fast' else 50,guidance_scale=5.,octree_resolution=256 if s['quality']=='fast' else 384,num_chunks=8000,generator=torch.Generator(device='cuda').manual_seed(s['seed']))[0]
 if not np.isfinite(mesh.vertices).all() or not len(mesh.faces):raise ValueError('Invalid generated geometry')
 raw=len(mesh.faces);mesh.export(job/'shape_raw.glb')
 if raw>s['triangles']:
  ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(mesh.vertices,mesh.faces))
  ms.apply_filter('meshing_decimation_quadric_edge_collapse',targetfacenum=s['triangles'],preservenormal=True,preserveboundary=True,autoclean=True)
  m=ms.current_mesh();mesh=trimesh.Trimesh(m.vertex_matrix(),m.face_matrix(),process=False)
 height=mesh.extents[1]
 if height<=1e-8:raise ValueError('Zero model height')
 mesh.apply_scale(s['height_cm']/100/height)
 # Retain centered coordinates; output physical extents are in meters.
 mesh.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[190,195,204,255],metallicFactor=0.,roughnessFactor=.8))
 mesh.export(job/'shape.glb')
 (job/'shape_report.json').write_text(json.dumps({'raw_triangles':raw,'triangles':len(mesh.faces),'vertices':len(mesh.vertices),'height_m':float(mesh.extents[1]),'views':list(images)},indent=2))

elif a.stage=='remesh':
 # Optional topology cleanup before UV. Export hygiene only ? does not invent missing forms.
 import pymeshlab
 mesh=trimesh.load(job/'shape.glb',force='mesh',process=False)
 before=dict(faces=int(len(mesh.faces)),vertices=int(len(mesh.vertices)),watertight=bool(mesh.is_watertight))
 ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(mesh.vertices,mesh.faces))
 # Mild cleanup; keep face count near target. No aggressive remesh that destroys detail.
 try:ms.apply_filter('meshing_remove_unreferenced_vertices')
 except Exception:pass
 try:ms.apply_filter('meshing_remove_duplicate_faces')
 except Exception:pass
 try:ms.apply_filter('meshing_remove_duplicate_vertices')
 except Exception:pass
 try:ms.apply_filter('meshing_repair_non_manifold_edges',method=0)
 except Exception:pass
 try:ms.apply_filter('meshing_repair_non_manifold_vertices',vertdispratio=0)
 except Exception:pass
 # Optional isotropic remesh only when settings.remesh_isotropic true (off by default)
 if s.get('remesh_isotropic'):
  target=int(s.get('triangles',100000))
  try:ms.apply_filter('meshing_isotropic_explicit_remeshing',targetlen=pymeshlab.PercentageValue(1.2),iterations=3)
  except Exception:
   try:ms.apply_filter('meshing_decimation_quadric_edge_collapse',targetfacenum=target,preservenormal=True,preserveboundary=True,autoclean=True)
   except Exception:pass
 m=ms.current_mesh();mesh=trimesh.Trimesh(m.vertex_matrix(),m.face_matrix(),process=False)
 # Preserve height from prior shape stage
 height=mesh.extents[1]
 if height>1e-8 and abs(height-s['height_cm']/100)>1e-3:
  mesh.apply_scale((s['height_cm']/100)/height)
 mesh.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[190,195,204,255],metallicFactor=0.,roughnessFactor=.8))
 mesh.export(job/'shape.glb')
 report={'before':before,'after':{'faces':int(len(mesh.faces)),'vertices':int(len(mesh.vertices)),'watertight':bool(mesh.is_watertight)},'note':'topology cleanup only; no form invention; UV must re-run after','production_accepted':False}
 (job/'remesh_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

elif a.stage=='uv':
 from hy3dgen.texgen.utils.uv_warp_utils import mesh_uv_wrap
 from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
 from hy3dgen.texgen.pipelines import Hunyuan3DTexGenConfig
 out=job/'controls';out.mkdir(exist_ok=True)
 mesh=trimesh.load(job/'shape.glb',force='mesh',process=False);mesh.visual=trimesh.visual.TextureVisuals();mesh=mesh_uv_wrap(mesh)
 np.savez_compressed(out/'uv_mesh.npz',vertices=mesh.vertices,faces=mesh.faces,uv=mesh.visual.uv,vertex_normals=mesh.vertex_normals)
 render=MeshRender(default_resolution=2048,texture_size=2048);render.load_mesh(mesh);conf=Hunyuan3DTexGenConfig('unused','unused','hunyuan3d-paint-v2-0')
 for i,(e,az) in enumerate(zip(conf.candidate_camera_elevs,conf.candidate_camera_azims)):
  render.render_normal(e,az,use_abs_coor=True,return_type='pl').save(out/f'render_normal_multiview_{i}.png')
  render.render_position(e,az,return_type='pl').save(out/f'render_position_multiview_{i}.png')
else:
 # Default finalize lineage: shape -> textured_pbr -> face/Face_1_0 when face processed.
 # Opt-in finalize_candidate (job-relative path, default OFF) overrides source for output.glb.
 source=job/'shape.glb';face_source='shape';finalize_candidate=None
 if s['textures']:source=job/'textured_pbr.glb';face_source='textured_pbr'
 face_status=None
 if s['face']:
  f=json.loads((job/'face/report.json').read_text());face_status=f['status']
  if f['status']=='processed':source=job/'face/Face_1_0.glb';face_source='face_processed'
  else:face_source='face_skipped_keep_pbr' if s['textures'] else 'face_skipped_keep_shape'
 cand_raw=s.get('finalize_candidate')
 if cand_raw:
  if not isinstance(cand_raw,str) or not cand_raw.strip():raise ValueError('finalize_candidate must be a non-empty job-relative path when set')
  rel=cand_raw.replace('\\','/').lstrip('/')
  if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('finalize_candidate must stay inside the job directory')
  cand=(job/rel).resolve();job_root=job.resolve()
  if job_root not in cand.parents and cand!=job_root:raise ValueError('finalize_candidate escapes job directory')
  if not cand.is_file():raise ValueError('finalize_candidate missing: '+rel)
  source=cand;finalize_candidate=rel.replace('\\','/')
  face_source=s.get('face_source') or ('finalize_candidate:'+finalize_candidate)
 elif s.get('face_source'):
  # Allow explicit face_source label without changing default mesh lineage.
  if isinstance(s.get('face_source'),str) and s.get('face_source').strip():face_source=s['face_source'].strip()
 scene=trimesh.load(source,process=False);mesh=next(iter(scene.geometry.values()))
 if s['textures'] and s['texture_size']!=2048:
  for slot in ['baseColorTexture','metallicRoughnessTexture','normalTexture','occlusionTexture']:
   texture=getattr(mesh.visual.material,slot,None)
   if texture is not None:setattr(mesh.visual.material,slot,texture.resize((s['texture_size'],s['texture_size']),Image.Resampling.LANCZOS))
 mesh.export(job/'output.glb')
 import copy
 mat=copy.deepcopy(mesh.visual.material);mat.metallicFactor=0.;mat.roughnessFactor=.8;mat.metallicRoughnessTexture=None;mesh.visual.material=mat;mesh.export(job/'preview_color.glb')
 scene=trimesh.load(job/'output.glb',process=False);check=next(iter(scene.geometry.values()))
 if abs(check.extents[1]-s['height_cm']/100)>1e-5:raise ValueError('Export height mismatch')
 if not np.isfinite(check.vertices).all():raise ValueError('Invalid exported positions')
 if s['textures'] and check.visual.material.baseColorTexture.size!=(s['texture_size'],s['texture_size']):raise ValueError('Texture resolution mismatch')
 report={'triangles':len(check.faces),'vertices':len(check.vertices),'height_cm':float(check.extents[1]*100),'bytes':(job/'output.glb').stat().st_size,'texture_size':s['texture_size'] if s['textures'] else None,'rigged':False,'face_status':face_status,'watertight':bool(check.is_watertight),'face_source':face_source,'finalize_candidate':finalize_candidate,'finalize_source':str(Path(source).resolve()),'production_accepted':False}
 (job/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
