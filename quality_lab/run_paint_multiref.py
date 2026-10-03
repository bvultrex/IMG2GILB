import os,sys,json,time,threading,subprocess,argparse,gc
from pathlib import Path
r=Path('D:/SF3D_QualityLab');parser=argparse.ArgumentParser();parser.add_argument('--views',type=int,choices=[4,6],default=6);parser.add_argument('--resolution',type=int,default=512)
parser.add_argument('--references',nargs='+');parser.add_argument('--input',default='input_paint_opaque.png');parser.add_argument('--controls',default='outputs/paint_seed42_front_back_verified');parser.add_argument('--output');args=parser.parse_args()
os.environ.update(HF_HOME=str(r/'hf'),HF_HUB_OFFLINE='1')
sys.path.insert(0,str(r/'research/Hunyuan3D-2.1/hy3dpaint'))
import torch,numpy as np
from PIL import Image
from hunyuanpaintpbr.pipeline import HunyuanPaintPipeline
from hunyuanpaintpbr.unet.modules import Dino_v2,UNet2p5DConditionModel
import hunyuanpaintpbr.unet.modules as paint_modules
sys.modules["modules"]=paint_modules
from diffusers import UniPCMultistepScheduler,AutoencoderKL
from transformers import CLIPTextModel,CLIPTokenizer,CLIPImageProcessor
out=(Path(args.output) if (args.output and Path(args.output).is_absolute()) else (r/args.output if args.output else r/'outputs'/f'paint21_{args.views}v_{args.resolution}'));out.mkdir(parents=True,exist_ok=True)
start=time.monotonic();memory=[];stop=threading.Event()
def monitor():
 while not stop.is_set():
  try:
   s=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],creationflags=subprocess.CREATE_NO_WINDOW,text=True);memory.append([time.monotonic()-start,int(s.strip().splitlines()[0])])
  except Exception:pass
  stop.wait(1)
threading.Thread(target=monitor,daemon=True).start()
try:
 references=args.references or [args.input]
 rgbs=[]
 for n,filename in enumerate(references):
  image=Image.open(filename if Path(filename).is_absolute() else r/filename).convert('RGBA');box=image.getchannel('A').getbbox()
  if not box:raise ValueError('Empty reference alpha')
  image=image.crop(box);side=int(max(image.size)*1.4);square=Image.new('RGBA',(side,side),(255,255,255,0));square.paste(image,((side-image.width)//2,(side-image.height)//2));rgb=Image.new('RGB',square.size,'white');rgb.paste(square,mask=square.getchannel('A'));rgb=rgb.resize((args.resolution,args.resolution));rgb.save(out/f'reference_{n}.png');rgbs.append(rgb)
 print('DINO features',flush=True)
 with torch.inference_mode():
  dino=Dino_v2(str(r/'models/facebook/dinov2-giant')).half().cuda();features=torch.cat([dino(image) for image in rgbs],dim=1);del dino;gc.collect();torch.cuda.empty_cache()
 print('Load Paint 2.1',flush=True)
 modeldir=r/'models/tencent/Hunyuan3D-2.1/hunyuan3d-paintpbr-v2-1'
 unet=UNet2p5DConditionModel.from_pretrained(str(modeldir/'unet'),torch_dtype=torch.float16)
 pipeline=HunyuanPaintPipeline(unet=unet,vae=AutoencoderKL.from_pretrained(str(modeldir/'vae'),torch_dtype=torch.float16,local_files_only=True),text_encoder=CLIPTextModel.from_pretrained(str(modeldir/'text_encoder'),torch_dtype=torch.float16,local_files_only=True),tokenizer=CLIPTokenizer.from_pretrained(str(modeldir/'tokenizer'),local_files_only=True),scheduler=UniPCMultistepScheduler.from_pretrained(str(modeldir/'scheduler'),local_files_only=True),feature_extractor=CLIPImageProcessor.from_pretrained(str(modeldir/'feature_extractor'),local_files_only=True))
 pipeline.scheduler=UniPCMultistepScheduler.from_config(pipeline.scheduler.config,timestep_spacing='trailing');pipeline.eval()
 pipeline.enable_model_cpu_offload();pipeline.enable_vae_slicing();pipeline.enable_vae_tiling()
 cache=Path(args.controls) if Path(args.controls).is_absolute() else r/args.controls
 normals=[Image.open(cache/f'render_normal_multiview_{i}.png').resize((args.resolution,args.resolution)) for i in range(args.views)]
 positions=[Image.open(cache/f'render_position_multiview_{i}.png').resize((args.resolution,args.resolution)) for i in range(args.views)]
 torch.cuda.reset_peak_memory_stats();t=time.monotonic();print('GENERATE',args.views,'views',flush=True)
 with torch.inference_mode():
  images=pipeline(rgbs,num_inference_steps=15,prompt='high quality',sync_condition=None,guidance_scale=3.,generator=torch.Generator(device='cuda').manual_seed(0),width=args.resolution,height=args.resolution,num_in_batch=args.views,images_normal=[normals],images_position=[positions],dino_hidden_states=features).images
 assert len(images)==args.views*2,len(images)
 for i,img in enumerate(images):img.save(out/f'{"albedo" if i<args.views else "mr"}_{i%args.views}.png')
 report=dict(status='passed',views=args.views,resolution=args.resolution,total_seconds=time.monotonic()-start,generation_seconds=time.monotonic()-t,peak_torch_allocated_GiB=torch.cuda.max_memory_allocated()/2**30,peak_torch_reserved_GiB=torch.cuda.max_memory_reserved()/2**30,peak_device_used_MiB=max(v for _,v in memory),reference_count=len(rgbs),source_controls=str(cache),source_references=[str(Path(filename) if Path(filename).is_absolute() else r/filename) for filename in references],note='Fixed supplied mesh/cameras; multiple RGBA references and aspect-preserving padding; no delight step; standard 3-branch CFG; CPU offload; DINO released before Paint load')
 (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
finally:
 stop.set();(out/'device_memory.json').write_text(json.dumps(memory))

