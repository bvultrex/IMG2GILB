"""Fixture-only local registration experiment. Never modifies either input mesh.

The script aligns the diagnostic TRELLIS head-only reconstruction to the whole-bust
TRELLIS reconstruction.  It is deliberately a registration gate only: no geometry
fusion is performed here.
"""
from pathlib import Path
import json

import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
base = trimesh.load(ROOT / "trellis1024_direct_100000.glb", force="mesh", process=False)
detail = trimesh.load(
    ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb",
    force="mesh",
    process=False,
)

# Crop coordinates from the diagnostic normalized front image. glTF is Y-up, +Z front.
crop = np.array([0.32, 0.015, 0.675, 0.36])
height = base.extents[1]
initial_scale = (crop[3] - crop[1]) * height / detail.extents[1]
center = np.array(
    [(crop[0] + crop[2]) / 2 - 0.5, 0.5 - (crop[1] + crop[3]) / 2, 0.0]
) * height
src = (detail.vertices - detail.bounds.mean(0)) * initial_scale + center
dst = base.vertices


# Register the hood's upper/lateral support region and deliberately hold out the
# central lens region.  This is fixture-specific and is NOT automatic ROI detection.
def support(v):
    return (
        (v[:, 1] > 0.10)
        & (v[:, 2] > 0)
        & ((np.abs(v[:, 0]) > 0.044) | (v[:, 1] > 0.169))
        & (np.abs(v[:, 0]) < 0.087)
    )


target = dst[support(dst)]
source_ids = np.flatnonzero(support(src))
assert len(target) > 100 and len(source_ids) > 100

tree = cKDTree(target)
train_ids = source_ids[::2]
validation_ids = source_ids[1::2]

initial_residual, _ = tree.query(src[validation_ids])

# Robust translation-only warm start.
translation = np.zeros(3)
for _ in range(40):
    points = src[train_ids] + translation
    dist, ids = tree.query(points)
    keep = dist <= np.quantile(dist, 0.75)
    step = np.median(target[ids[keep]] - points[keep], axis=0)
    translation += step
    if np.linalg.norm(step) < 1e-6:
        break

translated_residual, _ = tree.query(src[validation_ids] + translation)


def transform(parameters):
    return (src - center) * parameters[:3] + center + parameters[3:]


def objective(parameters):
    points = transform(parameters)[train_ids]
    _, ids = tree.query(points)
    # The second term discourages anisotropic scale from "winning" by simply
    # shrinking the probe onto the support surface.
    return np.concatenate([(points - target[ids]).ravel(), 0.01 * (parameters[:3] - 1)])


lower = np.r_[np.full(3, 0.75), np.full(3, -0.025)]
upper = np.r_[np.full(3, 1.25), np.full(3, 0.025)]
fit = least_squares(
    objective,
    np.r_[np.ones(3), translation],
    bounds=(lower, upper),
    loss="soft_l1",
    f_scale=0.002,
    max_nfev=100,
)

registered = transform(fit.x)
residual, _ = tree.query(registered[validation_ids])

# Symmetric support distance is diagnostic only.  The detail crop and the whole
# bust do not have identical surface coverage, so the production gate remains
# the held-out source->target distance.
registered_support = registered[source_ids]
reverse_tree = cKDTree(registered_support)
reverse_residual, _ = reverse_tree.query(target)

scale = fit.x[:3]
final_translation = fit.x[3:]
near_scale_bound = bool(np.any(scale <= lower[:3] + 1e-3) or np.any(scale >= upper[:3] - 1e-3))
near_translation_bound = bool(
    np.any(final_translation <= lower[3:] + 1e-3)
    or np.any(final_translation >= upper[3:] - 1e-3)
)
heldout_p90 = float(np.quantile(residual, 0.9))
translation_norm = float(np.linalg.norm(final_translation))

# Registration gate only.  Passing this does NOT mean the lenses themselves are
# semantically aligned and does NOT authorize fusion.
accepted = bool(
    fit.success
    and heldout_p90 < 0.003
    and translation_norm < 0.025
    and not near_scale_bound
    and not near_translation_bound
)

registered_mesh = detail.copy()
registered_mesh.vertices = registered
registered_mesh.export(ROOT / "detail_registered.glb")

report = {
    "scope": "fixed bust fixture; robust translation warm-start + bounded XYZ scale/translation fit; no automatic ROI detection",
    "source": str(ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"),
    "target": str(ROOT / "trellis1024_direct_100000.glb"),
    "initial_scale": float(initial_scale),
    "axis_scale_correction": scale.tolist(),
    "translation_warm_start_m": translation.tolist(),
    "translation_m": final_translation.tolist(),
    "translation_norm_mm": translation_norm * 1000,
    "fit_success": bool(fit.success),
    "fit_status": int(fit.status),
    "fit_message": str(fit.message),
    "support_target_points": int(len(target)),
    "support_source_points": int(len(source_ids)),
    "validation_points": int(len(validation_ids)),
    "initial_heldout_median_mm": float(np.median(initial_residual) * 1000),
    "initial_heldout_p90_mm": float(np.quantile(initial_residual, 0.9) * 1000),
    "translation_only_heldout_median_mm": float(np.median(translated_residual) * 1000),
    "translation_only_heldout_p90_mm": float(np.quantile(translated_residual, 0.9) * 1000),
    "heldout_median_mm": float(np.median(residual) * 1000),
    "heldout_p90_mm": heldout_p90 * 1000,
    "reverse_support_median_mm": float(np.median(reverse_residual) * 1000),
    "reverse_support_p90_mm": float(np.quantile(reverse_residual, 0.9) * 1000),
    "near_scale_bound": near_scale_bound,
    "near_translation_bound": near_translation_bound,
    "geometric_gate_passed": accepted,
    "production_accepted": False,
    "note": (
        "Nearest-surface support distance does not verify lens placement, depth "
        "correspondence, seam topology or watertightness. No fusion performed."
    ),
}
(ROOT / "detail_registration.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
