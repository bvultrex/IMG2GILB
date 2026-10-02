"""Compare camera hypotheses using frozen DINOv3 features, without applying poses."""
import argparse,json
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from transformers import AutoModel,AutoImageProcessor
p=argparse.ArgumentParser();p.add_argument('--candidates',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
processor=AutoImageProcessor.from_pretrained(a.model,local_files_only=True)
model=AutoModel.from_pretrained(a.model,local_files_only=True).eval().cuda()
def features(path):
 im=Image.open(path).convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
 mask=np.asarray(im)[:,:,3]>127
 inputs=processor(images=im.convert('RGB'),do_resize=False,return_tensors='pt').to('cuda')
 with torch.inference_mode():f=model(**inputs).last_hidden_state[0,1+model.config.num_register_tokens:]
 return torch.nn.functional.normalize(f.float(),dim=-1),torch.tensor(mask.reshape(32,16,32,16).mean((1,3)).flatten()>.8,device='cuda')
rows=[]
for c in json.loads((a.candidates/'manifest.json').read_text())['candidates']:
 folder=a.candidates/c['key'];s,sm=features(folder/'source.png');t,tm=features(folder/'target.png');valid=sm&tm
 scores=(s*t).sum(1)[valid]
 row={**c,'same_position_cosine_median':float(scores.median()),'foreground_overlap_patches':int(valid.sum())}
 rows.append(row);print(c['key'],row['same_position_cosine_median'],flush=True)
with a.out.open('x') as f:json.dump({'candidates':rows,'production_accepted':False,'limitations':'Same-position semantic agreement is diagnostic; generated texture and incorrect geometry bias ranking.'},f,indent=2)
