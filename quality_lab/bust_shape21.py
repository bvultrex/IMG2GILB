"""Isolated 2.1 shape trial, using the identical prepared front image."""
import os,sys,time,json
from pathlib import Path
lab=Path(r'D:\SF3D_QualityLab');out=lab/'bust_validation/shape_ablation';out.mkdir(exist_ok=True)
os.environ.update(HF_HOME=str(lab/'hf'),HY3DGEN_MODELS=str(lab/'models'),HF_HUB_OFFLINE='1')
sys.path.insert(0,str(lab/'research/Hunyuan3D-2.1/hy3dshape'))
sys.path.insert(0,str(lab/'shape21_deps'))
import torch,numpy as np
from PIL import Image
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
print('Loading shape 2.1',flush=True)
pipe=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(lab/'models/tencent/Hunyuan3D-2.1'))
start=time.monotonic();torch.cuda.reset_peak_memory_stats()
mesh=pipe(image=Image.open(lab/'app_jobs/9c9d771bfdf844bc8e15b60509ef308d/prepared/front.png'),num_inference_steps=50,guidance_scale=5.,octree_resolution=384,num_chunks=8000,generator=torch.Generator(device='cuda').manual_seed(42))[0]
assert np.isfinite(mesh.vertices).all();mesh.apply_scale(.4/mesh.extents[1]);mesh.export(out/'shape21_front.glb')
report=dict(model='Hunyuan3D-2.1',revision='0b94677654c57bb9a6b6845cd7b704ccf551d327',views=['front'],seed=42,steps=50,octree=384,triangles=len(mesh.faces),seconds=time.monotonic()-start,peak_GiB=torch.cuda.max_memory_allocated()/2**30)
(out/'shape21_front.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
