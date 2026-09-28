import json
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_download,snapshot_download
root=Path(r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-trellis-runtime\models');root.mkdir(exist_ok=True)
repo='microsoft/TRELLIS.2-4B';revision=HfApi().model_info(repo).sha
hf_hub_download(repo,'pipeline.json',revision=revision,local_dir=root/'trellis2')
cfg=json.loads((root/'trellis2/pipeline.json').read_text())['args']
names=['sparse_structure_flow_model','shape_slat_decoder','shape_slat_flow_model_512','shape_slat_flow_model_1024']
patterns=[cfg['models'][n]+ext for n in names for ext in ['.json','.safetensors']]
print('TRELLIS revision',revision,flush=True)
snapshot_download(repo,revision=revision,allow_patterns=patterns,local_dir=root/'trellis2',max_workers=2)
ssrepo='microsoft/TRELLIS-image-large';ssrev=HfApi().model_info(ssrepo).sha
snapshot_download(ssrepo,revision=ssrev,allow_patterns=['ckpts/ss_dec_conv3d_16l8_fp16.json','ckpts/ss_dec_conv3d_16l8_fp16.safetensors'],local_dir=root/'trellis1',max_workers=2)
(root/'revisions.json').write_text(json.dumps({repo:revision,ssrepo:ssrev},indent=2));print('DONE',flush=True)
