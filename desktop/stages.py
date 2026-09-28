"""GPU stages invoked in isolated subprocesses. Does not change installed packages."""
import argparse,json,os,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('stage',choices=['shape','uv','finalize']);p.add_argument('job');p.add_argument('config');a=p.parse_args()
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
 source=job/'shape.glb'
 if s['textures']:source=job/'textured_pbr.glb'
 face_status=None
 if s['face']:
  f=json.loads((job/'face/report.json').read_text());face_status=f['status']
  if f['status']=='processed':source=job/'face/Face_1_0.glb'
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
 report={'triangles':len(check.faces),'vertices':len(check.vertices),'height_cm':float(check.extents[1]*100),'bytes':(job/'output.glb').stat().st_size,'texture_size':s['texture_size'] if s['textures'] else None,'rigged':False,'face_status':face_status,'watertight':bool(check.is_watertight)}
 (job/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
