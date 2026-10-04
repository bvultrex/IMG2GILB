"""Isolated trained MV geometry trial, with explicit nominal-camera limitations."""
import argparse
import os
import json
import time
import traceback
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--runtime', required=True)
p.add_argument('--existing', required=True)
p.add_argument('--inputs', required=True)
p.add_argument('--out', required=True)
p.add_argument('--untiled', action='store_true', help='Control only: use non-tiled surface extraction')
a = p.parse_args()
root = Path(a.runtime).resolve()
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=False)
os.environ.update(LOCALMESH_ROOT=str(root), HF_HUB_OFFLINE='1',
                  ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='sdpa')
import numpy as np
import torch
import trimesh
from PIL import Image
from localmesh_engine import config, patches
from localmesh_engine.multivue.chemin import generer

report = {'status': 'running', 'seed': 42, 'inputs': {},
          'tiled_surface_extraction': not a.untiled,
          'camera': 'nominal yaw 0/90/180/270, FOV20, distance3.1192; NOT calibrated',
          'limitations': ['Reference backgrounds retained; framing padded without cropping',
                          'Generated reference views are not guaranteed consistent',
                          'Isolated geometry trial, not fresh end-to-end product acceptance'],
          'decoder_substitutions': []}
def save():
    (out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
def progress(stage, fraction):
    report.update(stage=stage, fraction=fraction, seconds=time.time()-start)
    save()
    print(stage, fraction, flush=True)

start = time.time()
save()
try:
    patches._patch_dinov3_layer_lookup()
    models = config.trellis('models')
    config.trellis('modules.sparse.config').set_attn_backend('sdpa')
    config.trellis('modules.attention.config').set_backend('sdpa')
    original_loader = models.from_pretrained
    mapping = {
        'shape_dec_next_dc_f16c32_fp8': 'trellis2/ckpts/shape_dec_next_dc_f16c32_fp16',
        'ss_dec_conv3d_16l8_fp16': 'trellis1/ckpts/ss_dec_conv3d_16l8_fp16'}
    def load_decoder(path, **kwargs):
        key = Path(path).name
        if key in mapping:
            path = str(Path(a.existing).resolve()/mapping[key])
            report['decoder_substitutions'].append(path)
            save()
        model = original_loader(path, **kwargs)
        if key == 'shape_dec_next_dc_f16c32_fp8':
            forward = model.forward
            def recorded_forward(x, **forward_kwargs):
                torch.save({'coords': x.coords.cpu(), 'feats': x.feats.cpu(),
                            'resolution': model.resolution}, out/'shape_latent.pt')
                if a.untiled:
                    forward_kwargs['useTiled'] = False
                return forward(x, **forward_kwargs)
            model.forward = recorded_forward
        return model
    models.from_pretrained = load_decoder
    images = {}
    for role in ('front', 'right', 'back', 'left'):
        path = Path(a.inputs)/f'{role}.png'
        im = Image.open(path).convert('RGB')
        side = max(im.size)
        canvas = Image.new('RGB', (side, side), 'white')
        canvas.paste(im, ((side-im.width)//2, (side-im.height)//2))
        canvas.save(out/f'input_{role}.png')
        images[role] = np.asarray(canvas, dtype=np.float32)/255
        report['inputs'][role] = {'path': str(path.resolve()),
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    save()
    mesh, info = generer(config, images, 42, lateralite='normale',
                         force_imposee=0.0, jalon=progress)
    vertices = mesh.vertices.detach().cpu().numpy()
    faces = mesh.faces.detach().cpu().numpy()
    assert len(faces) and np.isfinite(vertices).all()
    trimesh.Trimesh(vertices, faces, process=False).export(out/'raw.ply')
    report.update(status='complete', vertices=len(vertices), triangles=len(faces),
                  info=info, seconds=time.time()-start)
    save()
except Exception:
    report.update(status='failed', error=traceback.format_exc(), seconds=time.time()-start)
    save()
    raise
