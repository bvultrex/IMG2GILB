"""Isolated Ranger control: one reference owns strongly supported texels."""
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from project_hybrid_a3 import run
import project_hybrid_a3 as projection
from replace_glb_albedo_exact import replace

p = argparse.ArgumentParser()
p.add_argument('--job', type=Path, required=True)
p.add_argument('--atlas', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--front-back-only', action='store_true')
p.add_argument('--export-source-components', action='store_true', help='Save separate per-reference UV colors/weights for ownership diagnostics')
p.add_argument('--no-depth-margin', action='store_true', help='Isolated audit: keep depth rejection but disable its spatial dilation')
a = p.parse_args()
assert not a.out.exists(), 'Never overwrite an earlier experiment'
a.out.mkdir(parents=True)
source = a.job/'textured_pbr.glb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
provenance = {'runner': sha(Path(__file__)), 'projection_code': sha(Path(__file__).with_name('project_hybrid_a3.py')),
              'input_atlas': sha(a.atlas), 'source_glb': sha(source)}
provenance['no_depth_margin'] = a.no_depth_margin
provenance['export_source_components'] = a.export_source_components
(a.out/'provenance.json').write_text(json.dumps(provenance, indent=2))
# Experimental guard only: never invent a face ROI on a non-face object.
original_micro_align = projection.micro_align_front
def guarded_micro_align(warped, rendered, matrix, **kwargs):
    src_bgr = projection.cv2.cvtColor(warped[:, :, :3], projection.cv2.COLOR_RGB2BGR)
    dst_rgb = (rendered[:, :, :3].clip(0, 1)*255).astype(np.uint8)
    dst_bgr = projection.cv2.cvtColor(dst_rgb, projection.cv2.COLOR_RGB2BGR)
    _, src_face = projection._try_anime_face_keypoints(src_bgr)
    _, dst_face = projection._try_anime_face_keypoints(dst_bgr)
    if src_face is None or dst_face is None:
        iou = projection.silhouette_iou(warped[:, :, 3] > 127, rendered[:, :, 3] > .5)
        return warped, matrix, float(iou), {
            'chosen': 'skip_face_alignment_unconfirmed', 'accepted': False,
            'source_face_detected': src_face is not None,
            'render_face_detected': dst_face is not None,
            'weight_map': 'none'}, None
    return original_micro_align(warped, rendered, matrix, **kwargs)
projection.micro_align_front = guarded_micro_align
if a.no_depth_margin or a.export_source_components:
    original_renderer = projection.ProjectionRender
    class NoMarginRenderer(original_renderer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if a.no_depth_margin:
                self.bake_unreliable_kernel_size = 0
            self.export_source_components = a.export_source_components
    projection.ProjectionRender = NoMarginRenderer
run(a.job, a.out/'projection', None, None, atlas_path=a.atlas,
    source_pbr=source, best_source=True, front_back_only=a.front_back_only,
    color_glb=a.out/'diagnostic_color.glb', pbr_glb=a.out/'diagnostic_pbr.glb')
data = np.load(a.out/'projection/projection_components.npz', allow_pickle=False)
base, selected, weight = (data[k] for k in ('base', 'selected', 'strongest_weight'))
# Incidence is confidence in source ownership, not optical transparency.
# Full ownership above 0.5; smooth transition from no support avoids a hard cutoff.
t = np.clip(weight / .5, 0, 1)
ownership = t*t*(3-2*t)
color = base*(1-ownership) + selected*ownership
assert np.isfinite(color).all()
atlas = a.out/'albedo_ownership.png'
Image.fromarray((color.clip(0,1)*255).round().astype('uint8')).save(atlas)
report = replace(source, atlas, a.out/'candidate.glb')
report.update(method='best_reference_smooth_ownership', full_ownership_threshold=.5,
    front_back_only=a.front_back_only,
    full_ownership_texels=int((weight >= .5).sum()), production_accepted=False,
    limitation='Cannot repair wrong image-to-surface registration; verify source boundaries')
(a.out/'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
