"""Fixture-only registration v2: densify target support surface samples.

Same fixed bust crop and same lens-protected support mask as register_bust_detail.py.
The v1 failure mode was sparse base vertices in the hood support region (229 points),
which made nearest-neighbour correspondences noisy and left held-out p90 ~3.6 mm.
v2 samples the support surface densely (face centroids + barycentric samples) so the
fit and held-out gate measure distance to the base *surface*, not to an undersampled
vertex subset.

Still fixture-specific. NOT automatic ROI detection. No fusion. production_accepted
remains false.
"""
from pathlib import Path
import json

import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"
OUT_MESH = ROOT / "detail_registered_v2.glb"
OUT_REPORT = ROOT / "detail_registration_v2.json"

TARGET_SAMPLE_COUNT = 3000
TARGET_SAMPLE_SEED = 0

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)

# Crop coordinates from the diagnostic normalized front image. glTF is Y-up, +Z front.
crop = np.array([0.32, 0.015, 0.675, 0.36], dtype=np.float64)
height = float(base.extents[1])
initial_scale = (crop[3] - crop[1]) * height / float(detail.extents[1])
center = np.array(
    [(crop[0] + crop[2]) / 2 - 0.5, 0.5 - (crop[1] + crop[3]) / 2, 0.0]
) * height
src = (detail.vertices - detail.bounds.mean(0)) * initial_scale + center
dst = np.asarray(base.vertices, dtype=np.float64)
faces = np.asarray(base.faces, dtype=np.int64)


def support(v):
    """Hood upper/lateral support; deliberately holds out central lens region.

    Fixture-specific. NOT automatic ROI detection.
    """
    return (
        (v[:, 1] > 0.10)
        & (v[:, 2] > 0)
        & ((np.abs(v[:, 0]) > 0.044) | (v[:, 1] > 0.169))
        & (np.abs(v[:, 0]) < 0.087)
    )


def sample_support_surface(mask_fn, n=TARGET_SAMPLE_COUNT, seed=TARGET_SAMPLE_SEED):
    cents = dst[faces].mean(axis=1)
    face_ids = np.flatnonzero(mask_fn(cents))
    assert len(face_ids) > 50, f"Too few support faces: {len(face_ids)}"
    rng = np.random.default_rng(seed)
    parts = [cents[face_ids]]
    need = max(0, n - len(face_ids))
    if need:
        pick = rng.choice(face_ids, size=need, replace=True)
        tri = dst[faces[pick]]
        r1 = np.sqrt(rng.random(need))
        r2 = rng.random(need)
        a = 1.0 - r1
        b = r1 * (1.0 - r2)
        c = r1 * r2
        parts.append(a[:, None] * tri[:, 0] + b[:, None] * tri[:, 1] + c[:, None] * tri[:, 2])
    return np.vstack(parts)


target = sample_support_surface(support)
source_ids = np.flatnonzero(support(src))
sparse_target = dst[support(dst)]
assert len(target) > 100 and len(source_ids) > 100

tree = cKDTree(target)
sparse_tree = cKDTree(sparse_target)
train_ids = source_ids[::2]
validation_ids = source_ids[1::2]

initial_residual, _ = tree.query(src[validation_ids])

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


def rotation_matrix_xyz(angles):
    ax, ay, az = angles
    sx, cx = np.sin(ax), np.cos(ax)
    sy, cy = np.sin(ay), np.cos(ay)
    sz, cz = np.sin(az), np.cos(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def transform_scale_translation(parameters):
    return (src - center) * parameters[:3] + center + parameters[3:]


def transform_scale_rotation_translation(parameters):
    scale = parameters[:3]
    angles = parameters[3:6]
    translation_value = parameters[6:9]
    local = (src - center) * scale
    return local @ rotation_matrix_xyz(angles).T + center + translation_value


def objective_scale_translation(parameters):
    points = transform_scale_translation(parameters)[train_ids]
    _, ids = tree.query(points)
    return np.concatenate([(points - target[ids]).ravel(), 0.01 * (parameters[:3] - 1)])


def objective_scale_rotation_translation(parameters):
    points = transform_scale_rotation_translation(parameters)[train_ids]
    _, ids = tree.query(points)
    scale = parameters[:3]
    angles = parameters[3:6]
    return np.concatenate(
        [
            (points - target[ids]).ravel(),
            0.01 * (scale - 1),
            0.0025 * angles,
        ]
    )


st_lower = np.r_[np.full(3, 0.75), np.full(3, -0.025)]
st_upper = np.r_[np.full(3, 1.25), np.full(3, 0.025)]
st_fit = least_squares(
    objective_scale_translation,
    np.r_[np.ones(3), translation],
    bounds=(st_lower, st_upper),
    loss="soft_l1",
    f_scale=0.002,
    max_nfev=100,
)
st_registered = transform_scale_translation(st_fit.x)
st_residual, _ = tree.query(st_registered[validation_ids])

angle_limit_deg = 8.0
angle_limit = np.deg2rad(angle_limit_deg)
srt_lower = np.r_[np.full(3, 0.85), np.full(3, -angle_limit), np.full(3, -0.025)]
srt_upper = np.r_[np.full(3, 1.15), np.full(3, angle_limit), np.full(3, 0.025)]
srt_start = np.r_[
    np.clip(st_fit.x[:3], 0.86, 1.14),
    np.zeros(3),
    np.clip(st_fit.x[3:], -0.024, 0.024),
]
srt_fit = least_squares(
    objective_scale_rotation_translation,
    srt_start,
    bounds=(srt_lower, srt_upper),
    loss="soft_l1",
    f_scale=0.002,
    max_nfev=160,
)
srt_registered = transform_scale_rotation_translation(srt_fit.x)
srt_residual, _ = tree.query(srt_registered[validation_ids])

st_p90 = float(np.quantile(st_residual, 0.9))
srt_p90 = float(np.quantile(srt_residual, 0.9))
if srt_p90 + 1e-6 < st_p90:
    selected_model = "scale_rotation_translation"
    selected_fit = srt_fit
    registered = srt_registered
    residual = srt_residual
    scale = srt_fit.x[:3]
    angles = srt_fit.x[3:6]
    final_translation = srt_fit.x[6:9]
    lower = srt_lower
    upper = srt_upper
else:
    selected_model = "scale_translation"
    selected_fit = st_fit
    registered = st_registered
    residual = st_residual
    scale = st_fit.x[:3]
    angles = np.zeros(3)
    final_translation = st_fit.x[3:]
    lower = st_lower
    upper = st_upper

registered_support = registered[source_ids]
reverse_tree = cKDTree(registered_support)
reverse_residual, _ = reverse_tree.query(target)
sparse_residual, _ = sparse_tree.query(registered[validation_ids])

near_scale_bound = bool(
    np.any(scale <= lower[:3] + 1e-3) or np.any(scale >= upper[:3] - 1e-3)
)
if selected_model == "scale_rotation_translation":
    near_rotation_bound = bool(
        np.any(angles <= lower[3:6] + np.deg2rad(0.25))
        or np.any(angles >= upper[3:6] - np.deg2rad(0.25))
    )
    translation_lower = lower[6:9]
    translation_upper = upper[6:9]
else:
    near_rotation_bound = False
    translation_lower = lower[3:6]
    translation_upper = upper[3:6]

near_translation_bound = bool(
    np.any(final_translation <= translation_lower + 1e-3)
    or np.any(final_translation >= translation_upper - 1e-3)
)
heldout_p90 = float(np.quantile(residual, 0.9))
translation_norm = float(np.linalg.norm(final_translation))

accepted = bool(
    selected_fit.success
    and heldout_p90 < 0.003
    and translation_norm < 0.025
    and not near_scale_bound
    and not near_rotation_bound
    and not near_translation_bound
)

registered_mesh = detail.copy()
registered_mesh.vertices = registered
registered_mesh.export(OUT_MESH)

report = {
    "scope": (
        "fixed bust fixture; v2 densifies target support surface samples under the "
        "same lens-protected support mask; robust translation warm-start + bounded "
        "XYZ scale/small-angle rotation/translation fit; no automatic ROI detection"
    ),
    "version": "v2_dense_target_support",
    "source": str(DETAIL_PATH),
    "target": str(BASE_PATH),
    "output_mesh": str(OUT_MESH),
    "initial_scale": float(initial_scale),
    "crop_normalized": crop.tolist(),
    "selected_model": selected_model,
    "axis_scale_correction": scale.tolist(),
    "rotation_deg": np.rad2deg(angles).tolist(),
    "rotation_limit_deg": angle_limit_deg,
    "translation_warm_start_m": translation.tolist(),
    "translation_m": final_translation.tolist(),
    "translation_norm_mm": translation_norm * 1000,
    "fit_success": bool(selected_fit.success),
    "fit_status": int(selected_fit.status),
    "fit_message": str(selected_fit.message),
    "support_target_vertex_points": int(len(sparse_target)),
    "support_target_surface_samples": int(len(target)),
    "support_source_points": int(len(source_ids)),
    "validation_points": int(len(validation_ids)),
    "target_sample_count_requested": TARGET_SAMPLE_COUNT,
    "target_sample_seed": TARGET_SAMPLE_SEED,
    "initial_heldout_median_mm": float(np.median(initial_residual) * 1000),
    "initial_heldout_p90_mm": float(np.quantile(initial_residual, 0.9) * 1000),
    "translation_only_heldout_median_mm": float(np.median(translated_residual) * 1000),
    "translation_only_heldout_p90_mm": float(np.quantile(translated_residual, 0.9) * 1000),
    "scale_translation_heldout_median_mm": float(np.median(st_residual) * 1000),
    "scale_translation_heldout_p90_mm": st_p90 * 1000,
    "scale_rotation_translation_heldout_median_mm": float(np.median(srt_residual) * 1000),
    "scale_rotation_translation_heldout_p90_mm": srt_p90 * 1000,
    "heldout_median_mm": float(np.median(residual) * 1000),
    "heldout_p90_mm": heldout_p90 * 1000,
    "sparse_vertex_heldout_median_mm": float(np.median(sparse_residual) * 1000),
    "sparse_vertex_heldout_p90_mm": float(np.quantile(sparse_residual, 0.9) * 1000),
    "reverse_support_median_mm": float(np.median(reverse_residual) * 1000),
    "reverse_support_p90_mm": float(np.quantile(reverse_residual, 0.9) * 1000),
    "near_scale_bound": near_scale_bound,
    "near_rotation_bound": near_rotation_bound,
    "near_translation_bound": near_translation_bound,
    "geometric_gate_passed": accepted,
    "production_accepted": False,
    "compared_to_v1_heldout_p90_mm": 3.597909584322093,
    "note": (
        "Gate uses held-out source->dense target-surface distance under the fixture "
        "support mask. sparse_vertex_* metrics are diagnostic only for comparison "
        "with v1's undersampled vertex target. Nearest-surface support distance does "
        "not verify lens placement, depth correspondence, seam topology or "
        "watertightness. No fusion performed. Crop/support remain fixture-specific."
    ),
}
OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
