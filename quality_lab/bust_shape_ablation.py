"""Same prepared bust inputs/seed, controlled MV conditioning experiment."""
import os,sys,json,time
from pathlib import Path
lab=Path(r'D:\SF3D_QualityLab');out=lab/'bust_validation/shape_ablation';out.mkdir(exist_ok=True)
os.environ.update(HF_HOME=str(lab/'hf'),HY3DGEN_MODELS=str(lab/'models'),HF_HUB_OFFLINE='1')
sys.path.insert(0,r'C:\Users\Shadow\Documents\ComfyUI\Hunyuan3D-2-Lab')
import torch,numpy as np
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
base=lab/'app_jobs/9c9d771bfdf844bc8e15b60509ef308d'
pipe=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(lab/'models/tencent/Hunyuan3D-2mv'),subfolder='hunyuan3d-dit-v2-mv',variant='fp16',use_safetensors=True)
for tag,keys in [('mv_front',['front']),('mv_front_back',['front','back'])]:
 print('START',tag,flush=True);start=time.monotonic();torch.cuda.reset_peak_memory_stats()
 mesh=pipe(image={k:Image.open(base/'prepared'/f'{k}.png') for k in keys},num_inference_steps=50,guidance_scale=5.,octree_resolution=384,num_chunks=8000,generator=torch.Generator(device='cuda').manual_seed(42))[0]
 assert np.isfinite(mesh.vertices).all();mesh.apply_scale(.4/mesh.extents[1]);mesh.export(out/f'{tag}.glb')
 report=dict(tag=tag,views=keys,seed=42,steps=50,octree=384,triangles=len(mesh.faces),seconds=time.monotonic()-start,peak_GiB=torch.cuda.max_memory_allocated()/2**30)
 (out/f'{tag}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
