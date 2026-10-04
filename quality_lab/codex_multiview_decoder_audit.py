"""Verify existing decoder checkpoint keys/shapes against the MV implementation."""
import os
import json
import argparse
from pathlib import Path
import torch
from safetensors.torch import load_file

p = argparse.ArgumentParser()
p.add_argument('--runtime', required=True)
p.add_argument('--existing', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
os.environ['LOCALMESH_ROOT'] = str(Path(a.runtime).resolve())
os.environ['ATTN_BACKEND'] = 'sdpa'
os.environ['SPARSE_ATTN_BACKEND'] = 'sdpa'
from localmesh_engine import config
models = config.trellis('models')
results = []
for rel in ('trellis1/ckpts/ss_dec_conv3d_16l8_fp16',
            'trellis2/ckpts/shape_dec_next_dc_f16c32_fp16'):
    base = Path(a.existing) / rel
    desc = json.loads(base.with_suffix('.json').read_text())
    with torch.device('meta'):
        model = getattr(models, desc['name'])(**desc['args'])
    state = load_file(str(base.with_suffix('.safetensors')))
    model.load_state_dict(state, strict=True, assign=True)
    results.append({'checkpoint': str(base), 'strict_load': True,
                    'parameters': len(state),
                    'meta_remaining': [n for n,t in list(model.named_parameters())
                                       + list(model.named_buffers()) if t.is_meta]})
    del state, model
Path(a.out).write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
