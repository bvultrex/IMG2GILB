import trellis_bootstrap
from trellis_bootstrap import runtime
import os,json,time,gc,argparse
os.environ['HF_HUB_OFFLINE']='1'
from pathlib import Path
import torch,numpy as np,trimesh
from PIL import Image
from trellis2 import models
from trellis2.pipelines import Trellis2ImageTo3DPipeline,samplers
from trellis2.modules.image_feature_extractor import DinoV3FeatureExtractor
parser=argparse.ArgumentParser();parser.add_argument('--resolution',type=int,default=512,choices=[512,1024]);parser.add_argument('--direct',action='store_true');parser.add_argument('--full-guidance',action='store_true');parser.add_argument('--head-probe',action='store_true');parser.add_argument('--detail-conditioning',action='store_true');args=parser.parse_args()
if args.detail_conditioning and (not args.direct or args.head_probe):parser.error('detail-conditioning requires direct whole-object mode')
root=runtime/'models';cfg=json.loads((root/'trellis2/pipeline.json').read_text())['args'];loaded={}
names=['sparse_structure_decoder','sparse_structure_flow_model','shape_slat_decoder','shape_slat_flow_model_512']
if args.resolution==1024:names.append('shape_slat_flow_model_1024')
if args.direct:names.remove('shape_slat_flow_model_512')
for name in names:
 path=root/'trellis1/ckpts/ss_dec_conv3d_16l8_fp16' if name=='sparse_structure_decoder' else root/'trellis2'/cfg['models'][name]
 print('LOAD',name,flush=True);loaded[name]=models.from_pretrained(str(path));gc.collect()
params={}
for stage in ['sparse_structure','shape_slat','tex_slat']:
 spec=cfg[stage+'_sampler'];params[stage+'_sampler']=getattr(samplers,spec['name'])(**spec['args']);params[stage+'_sampler_params']=spec['params']
if args.full_guidance:
 for stage in ['sparse_structure','shape_slat']:params[stage+'_sampler_params']['guidance_interval']=[0.,1.]
pipe=Trellis2ImageTo3DPipeline(models=loaded,image_cond_model=DinoV3FeatureExtractor(r'D:\SF3D_QualityLab\models\facebook\dinov3-vitl16-pretrain-lvd1689m'),shape_slat_normalization=cfg['shape_slat_normalization'],tex_slat_normalization=cfg['tex_slat_normalization'],low_vram=True,rembg_model=None,**params);pipe.cuda()
out=Path(r'D:\SF3D_QualityLab\bust_validation\shape_ablation');tag=f'trellis{args.resolution}'+('_direct' if args.direct else '')+('_fullcfg' if args.full_guidance else '')+('_headprobe' if args.head_probe else '')+('_detailcond' if args.detail_conditioning else '')
image=Image.open(r'D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844bc8e15b60509ef308d\prepared\front.png');assert image.mode=='RGBA'
image=pipe.preprocess_image(image)
if args.head_probe:
 # Diagnostic ROI in the normalized front fixture; not an automatic production crop.
 w,h=image.size;image=image.crop((int(.32*w),int(.015*h),int(.675*w),int(.36*h)))
image.save(out/f'{tag}_input.png');torch.manual_seed(42);torch.cuda.reset_peak_memory_stats();start=time.monotonic()
with torch.no_grad():
 cond=pipe.get_cond([image],512);coords=pipe.sample_sparse_structure(cond,64 if args.direct else 32)
 if args.resolution==512:
  slat=pipe.sample_shape_slat(cond,loaded['shape_slat_flow_model_512'],coords);res=512
 elif args.direct:
  cond1024=pipe.get_cond([image],1024)
  if args.detail_conditioning:
   w,h=image.size;detail=image.crop((int(.32*w),int(.015*h),int(.675*w),int(.36*h)));detail.save(out/f'{tag}_detail.png');detailcond=pipe.get_cond([detail],1024)
   cond1024={k:torch.cat([cond1024[k],detailcond[k]],dim=1) for k in cond1024}
  slat=pipe.sample_shape_slat(cond1024,loaded['shape_slat_flow_model_1024'],coords);res=1024
 else:
  cond1024=pipe.get_cond([image],1024);slat,res=pipe.sample_shape_slat_cascade(cond,cond1024,loaded['shape_slat_flow_model_512'],loaded['shape_slat_flow_model_1024'],512,1024,coords)
 torch.save({'feats':slat.feats.cpu(),'coords':slat.coords.cpu(),'resolution':res},out/f'{tag}_latent.pt')
 meshes,subs=pipe.decode_shape_slat(slat,res);m=meshes[0]
 vertices=m.vertices.cpu().numpy();faces=m.faces.cpu().numpy();assert np.isfinite(vertices).all()
 # TRELLIS native Z-up -> glTF Y-up.
 vertices=vertices[:,[0,2,1]];vertices[:,2]*=-1
 mesh=trimesh.Trimesh(vertices,faces,process=False);mesh.apply_scale(.4/mesh.extents[1]);mesh.export(out/f'{tag}.glb')
 report=dict(model='TRELLIS.2-4B',resolution=res,seed=42,full_guidance=args.full_guidance,head_probe=args.head_probe,detail_conditioning=args.detail_conditioning,sampler_parameters={k:v for k,v in params.items() if k.endswith('_params')},triangles=len(faces),seconds=time.monotonic()-start,peak_GiB=torch.cuda.max_memory_allocated()/2**30)
 (out/f'{tag}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
