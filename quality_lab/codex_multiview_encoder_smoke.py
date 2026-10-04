"""Offline DINO+NAF conditioning smoke; not a reconstruction quality test."""
import argparse
import os
import json
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--runtime', required=True)
p.add_argument('--image', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
os.environ['LOCALMESH_ROOT'] = str(Path(a.runtime).resolve())
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['ATTN_BACKEND'] = 'sdpa'
os.environ['SPARSE_ATTN_BACKEND'] = 'sdpa'
import numpy as np
from PIL import Image
from localmesh_engine import config, patches
from localmesh_engine.multivue import Poids
from localmesh_engine.multivue.traits import encoder

patches._patch_dinov3_layer_lookup()
im = Image.open(a.image).convert('RGB')
# Preserve aspect ratio for this tensor-path smoke. Calibration is a separate gate.
side = max(im.size)
canvas = Image.new('RGB', (side, side), 'white')
canvas.paste(im, ((side-im.width)//2, (side-im.height)//2))
start = time.time()
result = encoder(config, {'front': np.asarray(canvas, dtype=np.float32)/255},
                 Poids.depuis(config.MODELS_ROOT), taille=512)
report = {'passed': True, 'seconds': time.time()-start,
          'image': str(Path(a.image).resolve()),
          'outputs': {k: list(v.shape) for k,v in result['front'].items()},
          'scope': 'DINO and NAF conditioning only; not four-view inference'}
Path(a.out).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
