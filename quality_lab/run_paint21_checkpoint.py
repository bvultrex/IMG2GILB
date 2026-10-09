import os,sys,json,time,threading,subprocess,argparse,gc,hashlib
from pathlib import Path
r=Path('D:/SF3D_QualityLab');parser=argparse.ArgumentParser();parser.add_argument('--views',type=int,choices=[4,6],default=6);parser.add_argument('--resolution',type=int,default=512)
parser.add_argument('--input',default='input_paint_opaque.png');parser.add_argument('--controls',default='outputs/paint_seed42_front_back_verified');parser.add_argument('--output');parser.add_argument('--checkpoint-only',action='store_true',help='Exit after persisting VAE input; decode in a separate process');parser.add_argument('--ff-chunk',action='store_true',help='Opt-in batch-wise feed-forward chunking; retain all six attention views');parser.add_argument('--references',nargs='+',help='Explicit ordered reference list; replaces --input conditioning');args=parser.parse_args()
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
out=r/args.output if args.output else r/'outputs'/f'paint21_{args.views}v_{args.resolution}';out.mkdir(parents=True,exist_ok=True)
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
 for i,filename in enumerate(references):
  image=Image.open(r/filename).convert('RGBA');box=image.getchannel('A').getbbox()
  if box is None:raise ValueError('Empty reference alpha')
  image=image.crop(box);side=int(max(image.size)*1.4);square=Image.new('RGBA',(side,side),(255,255,255,0));square.paste(image,((side-image.width)//2,(side-image.height)//2));rgb=Image.new('RGB',square.size,'white');rgb.paste(square,mask=square.getchannel('A'));rgb=rgb.resize((args.resolution,args.resolution));rgb.save(out/('reference.png' if i==0 else f'reference_{i}.png'));rgbs.append(rgb)
 print('DINO features',len(rgbs),'references',flush=True)
 with torch.inference_mode():
  dino=Dino_v2(str(r/'models/facebook/dinov2-giant')).half().cuda();features=torch.cat([dino(image) for image in rgbs],dim=1);del dino;gc.collect();torch.cuda.empty_cache()
 print('Load Paint 2.1',flush=True)
 modeldir=r/'models/tencent/Hunyuan3D-2.1/hunyuan3d-paintpbr-v2-1'
 unet=UNet2p5DConditionModel.from_pretrained(str(modeldir/'unet'),torch_dtype=torch.float16)
 pipeline=HunyuanPaintPipeline(unet=unet,vae=AutoencoderKL.from_pretrained(str(modeldir/'vae'),torch_dtype=torch.float16,local_files_only=True),text_encoder=CLIPTextModel.from_pretrained(str(modeldir/'text_encoder'),torch_dtype=torch.float16,local_files_only=True),tokenizer=CLIPTokenizer.from_pretrained(str(modeldir/'tokenizer'),local_files_only=True),scheduler=UniPCMultistepScheduler.from_pretrained(str(modeldir/'scheduler'),local_files_only=True),feature_extractor=CLIPImageProcessor.from_pretrained(str(modeldir/'feature_extractor'),local_files_only=True))
 pipeline.scheduler=UniPCMultistepScheduler.from_config(pipeline.scheduler.config,timestep_spacing='trailing');pipeline.eval()
 if args.ff_chunk:
  chunked=0
  for module in pipeline.unet.modules():
   if hasattr(module,'set_chunk_feed_forward'):
    module.set_chunk_feed_forward(chunk_size=1,dim=0);chunked+=1
  assert chunked>0,'No chunkable feed-forward modules found'
  print('FEED_FORWARD_CHUNKED',chunked,'batch size 1; attention views unchanged',flush=True)
 pipeline.enable_model_cpu_offload();pipeline.enable_vae_slicing();pipeline.enable_vae_tiling()
 # Persist the completed sampler output before native VAE/offload code runs.
 original_decode = pipeline.vae.decode
 def checkpoint_decode(z, *decode_args, **decode_kwargs):
  print('DECODE_CHECKPOINT_START', flush=True)
  checkpoint = out/'vae_decode_input.pt'
  pending = out/'vae_decode_input.pt.pending'
  torch.save(z.detach().cpu(), pending)
  pending.replace(checkpoint)
  print('DECODE_CHECKPOINT_SAVED', flush=True)
  if args.checkpoint_only:
   report = dict(status='sampling_complete_decode_pending',views=args.views,resolution=args.resolution,seed=0,steps=15,guidance=3.,seconds=time.monotonic()-start,source_controls=str(r/args.controls),source_reference=str(r/args.input),source_references=[str(r/f) for f in references],reference_count=len(rgbs),checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest())
   report_path = out/'generation_checkpoint_report.json'
   report_path.with_suffix('.pending').write_text(json.dumps(report,indent=2))
   report_path.with_suffix('.pending').replace(report_path)
   raise SystemExit(0)
  return original_decode(z, *decode_args, **decode_kwargs)
 pipeline.vae.decode = checkpoint_decode
 cache=r/args.controls
 normals=[Image.open(cache/f'render_normal_multiview_{i}.png').resize((args.resolution,args.resolution)) for i in range(args.views)]
 positions=[Image.open(cache/f'render_position_multiview_{i}.png').resize((args.resolution,args.resolution)) for i in range(args.views)]
 torch.cuda.reset_peak_memory_stats();t=time.monotonic();print('GENERATE',args.views,'views',flush=True)
 with torch.inference_mode():
  images=pipeline(rgbs,num_inference_steps=15,prompt='high quality',sync_condition=None,guidance_scale=3.,generator=torch.Generator(device='cuda').manual_seed(0),width=args.resolution,height=args.resolution,num_in_batch=args.views,images_normal=[normals],images_position=[positions],dino_hidden_states=features).images
 assert len(images)==args.views*2,len(images)
 for i,img in enumerate(images):img.save(out/f'{"albedo" if i<args.views else "mr"}_{i%args.views}.png')
 report=dict(status='passed',views=args.views,resolution=args.resolution,total_seconds=time.monotonic()-start,generation_seconds=time.monotonic()-t,peak_torch_allocated_GiB=torch.cuda.max_memory_allocated()/2**30,peak_torch_reserved_GiB=torch.cuda.max_memory_reserved()/2**30,peak_device_used_MiB=max(v for _,v in memory),reference_count=len(rgbs),source_controls=str(cache),source_reference=str(r/args.input),note='Fixed supplied mesh/cameras; raw front reference with opaque alpha and aspect-preserving padding; no delight step; standard 3-branch CFG; CPU offload; DINO released before Paint load')
 (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
finally:
 stop.set();(out/'device_memory.json').write_text(json.dumps(memory))


