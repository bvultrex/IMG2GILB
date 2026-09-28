"""Independent geometry benchmark using official TripoSG and existing BRIA mask."""
import os,sys,json,time
from pathlib import Path
runtime=Path(r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-triposg-runtime')
sys.path[:0]=[str(runtime/'deps'),str(runtime/'source'),str(runtime/'source/scripts')]
os.environ['HF_HUB_OFFLINE']='1'
import torch,numpy as np,trimesh
from triposg.pipelines.pipeline_triposg import TripoSGPipeline
from image_process import prepare_image
out=Path(r'D:\SF3D_QualityLab\bust_validation\shape_ablation')
image=prepare_image(r'D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844bc8e15b60509ef308d\prepared\front.png',bg_color=np.ones(3),rmbg_net=None)
image.save(out/'triposg_front_input.png')
pipe=TripoSGPipeline.from_pretrained(str(runtime/'models'),torch_dtype=torch.float16).to('cuda')
def checkpoint(pipeline,step,timestep,kwargs):
 if step==49:torch.save(kwargs['latents'].cpu(),out/'triposg_front_latent.pt')
 return kwargs
torch.cuda.reset_peak_memory_stats();start=time.monotonic()
with torch.no_grad():
 result=pipe(image=image,generator=torch.Generator(device='cuda').manual_seed(42),num_inference_steps=50,guidance_scale=7.,use_flash_decoder=False,dense_octree_depth=7,hierarchical_octree_depth=9,callback_on_step_end=checkpoint)
v,f=result.samples[0];assert np.isfinite(v).all()
m=trimesh.Trimesh(v,f,process=False);m.apply_scale(.4/m.extents[1]);m.export(out/'triposg_front.glb')
report=dict(model='TripoSG',seed=42,steps=50,guidance=7.,dense_octree_depth=7,hierarchical_octree_depth=9,flash_decoder=False,triangles=len(m.faces),seconds=time.monotonic()-start,peak_GiB=torch.cuda.max_memory_allocated()/2**30)
(out/'triposg_front.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
