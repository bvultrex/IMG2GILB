"""Audit embedded glTF MR packing and sampled values without modifying assets."""
import argparse
import json
import struct
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('model', type=Path)
p.add_argument('--raw-mr', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
raw = a.model.read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+size])
scene = trimesh.load(a.model, force='scene', process=False)
mesh = next(iter(scene.geometry.values()))
mat = mesh.visual.material
mr = np.asarray(mat.metallicRoughnessTexture.convert('RGB'))
original = np.asarray(Image.open(a.raw_mr).convert('RGB'))
uv = mesh.visual.uv[mesh.faces].mean(axis=1)
x = np.clip(np.rint(uv[:,0]*(mr.shape[1]-1)).astype(int),0,mr.shape[1]-1)
y = np.clip(np.rint((1-uv[:,1])*(mr.shape[0]-1)).astype(int),0,mr.shape[0]-1)
samples = mr[y,x]/255.
def stats(v):
    return dict(min=float(v.min()), max=float(v.max()),
                percentiles=dict(zip(['p05','p50','p95'],np.percentile(v,[5,50,95]).tolist())),
                mean=float(v.mean()), std=float(v.std()))
report = dict(materials=doc['materials'], images=doc['images'],
    packing_matches_generated=dict(metallic_B_from_R=bool(np.array_equal(mr[:,:,2],original[:,:,0])),
        roughness_G_from_G=bool(np.array_equal(mr[:,:,1],original[:,:,1]))),
    triangle_centroid_samples=dict(metallic=stats(samples[:,2]),roughness=stats(samples[:,1])),
    limitations='Triangle-centroid UV samples, not area-weighted or semantic material classification; no claim that generated values are physically correct')
a.out.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
