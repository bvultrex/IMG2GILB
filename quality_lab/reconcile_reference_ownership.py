"""Conservative side-reference experiment with front/back as the canonical design.

Requires previously computed, same-mesh projection components; no new inference.
Only admit a side winner where an overlapping front/back observation agrees.
This is not a semantic material classifier or a registration repair.
"""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from replace_glb_albedo_exact import replace

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
all_views = np.load(a.root/'ownership/projection/projection_components.npz')
anchor = np.load(a.root/'ownership_front_back/projection/projection_components.npz')
assert np.array_equal(all_views['base'], anchor['base']), 'Different base atlases'
aw, fw = anchor['strongest_weight'], all_views['strongest_weight']
side = fw[..., 0] > aw[..., 0] + 1e-5
delta = np.linalg.norm(
    cv2.cvtColor(all_views['selected'].clip(0, 1), cv2.COLOR_RGB2LAB)
    - cv2.cvtColor(anchor['selected'].clip(0, 1), cv2.COLOR_RGB2LAB), axis=-1)
# A deliberately conservative experimental gate, not a production threshold.
# Reject unsupported side regions rather than silently changing the costume.
admit = side & (aw[..., 0] >= .05) & (delta <= 20.)
selected = np.where(admit[..., None], all_views['selected'], anchor['selected'])
weight = np.where(admit[..., None], fw, aw)
t = np.clip(weight/.5, 0, 1)
alpha = t*t*(3-2*t)
color = anchor['base']*(1-alpha)+selected*alpha
atlas = a.out/'albedo.png'
Image.fromarray((color.clip(0, 1)*255).round().astype('uint8')).save(atlas)
Image.fromarray(admit.astype('uint8')*255).save(a.out/'accepted_side_texels.png')
report = replace(a.source, atlas, a.out/'candidate.glb')
report.update(method='anchor_agreement_only', side_winner_texels=int(side.sum()),
              admitted_side_texels=int(admit.sum()), minimum_anchor_weight=.05,
              maximum_lab_distance=20., production_accepted=False,
              limitation='Unsupported side regions retain front/back+Paint. Color agreement is not semantic correctness.')
(a.out/'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
