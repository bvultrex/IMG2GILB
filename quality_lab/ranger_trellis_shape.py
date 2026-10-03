"""Ranger ortho_v1 front-only TRELLIS shape baseline.

Experimental fixture runner. Reuses IMG2GILB-trellis-runtime; does not touch
bust seam/Auto-ROI scripts. Input is pre-matted RGBA (simple border-BG matte;
BRIA weights not available offline here).
"""
import trellis_bootstrap
from trellis_bootstrap import runtime
import os, json, time, gc, argparse
os.environ['HF_HUB_OFFLINE'] = '1'
from pathlib import Path
import torch, numpy as np, trimesh
from PIL import Image
from trellis2 import models
from trellis2.pipelines import Trellis2ImageTo3DPipeline, samplers
from trellis2.modules.image_feature_extractor import DinoV3FeatureExtractor

parser = argparse.ArgumentParser()
parser.add_argument('--resolution', type=int, default=512, choices=[512, 1024])
parser.add_argument('--direct', action='store_true')
args = parser.parse_args()

root = runtime / 'models'
cfg = json.loads((root / 'trellis2/pipeline.json').read_text())['args']
loaded = {}
names = ['sparse_structure_decoder', 'sparse_structure_flow_model', 'shape_slat_decoder', 'shape_slat_flow_model_512']
if args.resolution == 1024:
    names.append('shape_slat_flow_model_1024')
if args.direct:
    names.remove('shape_slat_flow_model_512')
for name in names:
    path = root / 'trellis1/ckpts/ss_dec_conv3d_16l8_fp16' if name == 'sparse_structure_decoder' else root / 'trellis2' / cfg['models'][name]
    print('LOAD', name, flush=True)
    loaded[name] = models.from_pretrained(str(path))
    gc.collect()

params = {}
for stage in ['sparse_structure', 'shape_slat', 'tex_slat']:
    spec = cfg[stage + '_sampler']
    params[stage + '_sampler'] = getattr(samplers, spec['name'])(**spec['args'])
    params[stage + '_sampler_params'] = spec['params']

pipe = Trellis2ImageTo3DPipeline(
    models=loaded,
    image_cond_model=DinoV3FeatureExtractor(r'D:\SF3D_QualityLab\models\facebook\dinov3-vitl16-pretrain-lvd1689m'),
    shape_slat_normalization=cfg['shape_slat_normalization'],
    tex_slat_normalization=cfg['tex_slat_normalization'],
    low_vram=True,
    rembg_model=None,
    **params,
)
pipe.cuda()

out = Path(r'D:\SF3D_QualityLab\ranger_validation\ortho_v1')
tag = f'trellis{args.resolution}' + ('_direct' if args.direct else '')
image = Image.open(out / 'front_rgba.png')
assert image.mode == 'RGBA'
image = pipe.preprocess_image(image)
image.save(out / f'{tag}_input.png')
torch.manual_seed(42)
torch.cuda.reset_peak_memory_stats()
start = time.monotonic()
with torch.no_grad():
    cond = pipe.get_cond([image], 512)
    coords = pipe.sample_sparse_structure(cond, 64 if args.direct else 32)
    if args.resolution == 512:
        slat = pipe.sample_shape_slat(cond, loaded['shape_slat_flow_model_512'], coords)
        res = 512
    elif args.direct:
        cond1024 = pipe.get_cond([image], 1024)
        slat = pipe.sample_shape_slat(cond1024, loaded['shape_slat_flow_model_1024'], coords)
        res = 1024
    else:
        cond1024 = pipe.get_cond([image], 1024)
        slat, res = pipe.sample_shape_slat_cascade(
            cond, cond1024, loaded['shape_slat_flow_model_512'], loaded['shape_slat_flow_model_1024'], 512, 1024, coords
        )
    torch.save({'feats': slat.feats.cpu(), 'coords': slat.coords.cpu(), 'resolution': res}, out / f'{tag}_latent.pt')
    meshes, subs = pipe.decode_shape_slat(slat, res)
    m = meshes[0]
    vertices = m.vertices.cpu().numpy()
    faces = m.faces.cpu().numpy()
    assert np.isfinite(vertices).all()
    # TRELLIS native Z-up -> glTF Y-up.
    vertices = vertices[:, [0, 2, 1]]
    vertices[:, 2] *= -1
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.apply_scale(0.4 / mesh.extents[1])
    mesh.export(out / f'{tag}.glb')
    report = dict(
        model='TRELLIS.2-4B',
        fixture='ranger_ortho_v1',
        view='front_only',
        alpha_source='border_bg_distance_matte',
        resolution=res,
        seed=42,
        direct=bool(args.direct),
        triangles=len(faces),
        seconds=time.monotonic() - start,
        peak_GiB=torch.cuda.max_memory_allocated() / 2**30,
        input=str(out / 'front_rgba.png'),
        output=str(out / f'{tag}.glb'),
    )
    (out / f'{tag}.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
