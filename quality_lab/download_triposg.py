"""Pinned official TripoSG weights; experimental runtime only."""
from huggingface_hub import snapshot_download
from pathlib import Path
import json
root=Path(r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-triposg-runtime')
revision='2c1c516d22d58db486a058d98d31bb6177344e06'
snapshot_download('VAST-AI/TripoSG',revision=revision,local_dir=str(root/'models'),allow_patterns=['*.json','*.safetensors'])
(root/'revision.json').write_text(json.dumps({'repo':'VAST-AI/TripoSG','revision':revision},indent=2))
print('DOWNLOAD_COMPLETE',flush=True)
