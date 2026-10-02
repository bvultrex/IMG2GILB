"""Offline dense feature feasibility audit; no warp or production asset mutation."""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from PIL import Image,ImageDraw
from transformers import AutoModel,AutoImageProcessor

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--model',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
p.add_argument('--size',type=int,default=512)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
processor=AutoImageProcessor.from_pretrained(a.model,local_files_only=True)
model=AutoModel.from_pretrained(a.model,local_files_only=True).eval().to('cuda')
size=a.size;patch=model.config.patch_size;grid=size//patch
if size<=0 or size%patch:raise ValueError('Size must be positive multiple of patch size')
def feature(path):
 im=Image.open(path).convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
 inputs=processor(images=im,do_resize=False,return_tensors='pt').to('cuda')
 with torch.inference_mode():
  tokens=model(**inputs).last_hidden_state[:,1+model.config.num_register_tokens:][0]
 assert len(tokens)==grid*grid
 mask=np.asarray(im).max(2)>15
 mask=mask.reshape(grid,patch,grid,patch).mean((1,3))>.8
 return im,torch.nn.functional.normalize(tokens.float(),dim=-1),torch.tensor(mask.flatten(),device='cuda')
reports=[]
for view in ('left','right'):
 si,s,sm=feature(a.run/(view+'_aligned.png'));di,d,dm=feature(a.run/(view+'_baseline.png'))
 np.savez_compressed(a.out/(view+'_features.npz'),source=s.cpu().numpy(),target=d.cpu().numpy(),source_mask=sm.cpu().numpy(),target_mask=dm.cpu().numpy())
 sim=s@d.T;sim[~sm,:]=-2;sim[:,~dm]=-2
 forward=sim.argmax(1);reverse=sim.argmax(0)
 ids=torch.arange(len(s),device='cuda');valid=sm & dm[forward] & (reverse[forward]==ids)
 pairs=[]
 for i in ids[valid].tolist():
  j=int(forward[i]);pairs.append({'source':[(i%grid+.5)*patch,(i//grid+.5)*patch],'target':[(j%grid+.5)*patch,(j//grid+.5)*patch],'similarity':float(sim[i,j])})
 canvas=Image.new('RGB',(size*2,size));canvas.paste(si);canvas.paste(di,(size,0));draw=ImageDraw.Draw(canvas)
 for q in sorted(pairs,key=lambda x:-x['similarity'])[:40]:
  draw.line([tuple(q['source']),(q['target'][0]+size,q['target'][1])],fill=(0,255,100),width=1)
 canvas.save(a.out/(view+'_matches.png'))
 reports.append({'view':view,'mutual_matches':len(pairs),'pairs':pairs})
 print(view,len(pairs),flush=True)
(a.out/'report.json').write_text(json.dumps({'results':reports,'image_size':size,'patch_size':patch,'production_accepted':False,'limitations':'Mutual feature similarity is not semantic correctness. No warp applied.'},indent=2))
