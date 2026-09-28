"""A/B densified registration for fixed crop vs automatic ROI v3.

This is a read-only fixture diagnostic. It never mutates the source meshes and
does not perform any splice/fusion.  Auto ROI inference never reads the fixed crop.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from PIL import Image

import auto_roi_bust_v2 as roi_v2
import auto_roi_bust_v3 as roi_v3

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BUST_ROOT = Path(r"D:\SF3D_QualityLab\bust_validation")
LAB = Path(r"D:\SF3D_QualityLab")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"
REPORT_PATH = ROOT / "auto_roi_registration_v1.json"
KNOWN_CROP = np.array([0.32, 0.015, 0.675, 0.36], dtype=np.float64)

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)
dst_vertices = np.asarray(base.vertices, dtype=np.float64)


def support(v):
    return (
        (v[:, 1] > 0.10)
        & (v[:, 2] > 0)
        & ((np.abs(v[:, 0]) > 0.044) | (v[:, 1] > 0.169))
        & (np.abs(v[:, 0]) < 0.087)
    )


def deterministic_surface_target(mesh, count=3000):
    """Area-weighted deterministic surface densification inside the support mask.

    The previous implementation only considered vertices/edge-midpoints/centroids
    and could produce fewer candidates than the requested 3000 samples.  This
    version samples the actual triangle surface with a fixed NumPy seed, then
    filters by the unchanged support predicate.
    """
    sample_count = max(600000, count * 200)

    # trimesh.sample.sample_surface uses NumPy's global RNG. Preserve caller state
    # so this diagnostic is deterministic without perturbing later optimization.
    state = np.random.get_state()
    try:
        np.random.seed(42)
        sampled, _ = trimesh.sample.sample_surface(mesh, sample_count)
    finally:
        np.random.set_state(state)

    candidates = np.asarray(sampled, dtype=np.float64)
    candidates = candidates[support(candidates)]
    if len(candidates) < count:
        raise RuntimeError(
            f"Only {len(candidates)} support surface samples from {sample_count} "
            f"deterministic area-weighted samples; need {count}."
        )

    # Preserve spatial distribution deterministically rather than randomly
    # subsampling the already-filtered set a second time.
    ids = np.linspace(0, len(candidates) - 1, count, dtype=np.int64)
    return candidates[ids]


target = deterministic_surface_target(base, 3000)
target_tree = cKDTree(target)


def rotation_matrix_xyz(angles):
    ax, ay, az = angles
    sx, cx = np.sin(ax), np.cos(ax)
    sy, cy = np.sin(ay), np.cos(ay)
    sz, cz = np.sin(az), np.cos(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def run_registration(crop):
    crop = np.asarray(crop, dtype=np.float64)
    height = base.extents[1]
    initial_scale = (crop[3] - crop[1]) * height / detail.extents[1]
    center = np.array(
        [(crop[0] + crop[2]) * 0.5 - 0.5, 0.5 - (crop[1] + crop[3]) * 0.5, 0.0]
    ) * height
    src = (np.asarray(detail.vertices, dtype=np.float64) - detail.bounds.mean(0)) * initial_scale + center

    source_ids = np.flatnonzero(support(src))
    if len(source_ids) < 100:
        raise RuntimeError(f"Too few source support points: {len(source_ids)}")
    train_ids = source_ids[::2]
    validation_ids = source_ids[1::2]

    translation = np.zeros(3)
    for _ in range(40):
        points = src[train_ids] + translation
        dist, ids = target_tree.query(points)
        keep = dist <= np.quantile(dist, 0.75)
        step = np.median(target[ids[keep]] - points[keep], axis=0)
        translation += step
        if np.linalg.norm(step) < 1e-6:
            break

    def transform(parameters):
        scale = parameters[:3]
        angles = parameters[3:6]
        trans = parameters[6:9]
        local = (src - center) * scale
        return local @ rotation_matrix_xyz(angles).T + center + trans

    def objective(parameters):
        points = transform(parameters)[train_ids]
        _, ids = target_tree.query(points)
        return np.concatenate(
            [
                (points - target[ids]).ravel(),
                0.01 * (parameters[:3] - 1.0),
                0.0025 * parameters[3:6],
            ]
        )

    angle_limit = np.deg2rad(8.0)
    lower = np.r_[np.full(3, 0.85), np.full(3, -angle_limit), np.full(3, -0.025)]
    upper = np.r_[np.full(3, 1.15), np.full(3, angle_limit), np.full(3, 0.025)]
    start = np.r_[np.ones(3), np.zeros(3), translation]
    fit = least_squares(
        objective,
        start,
        bounds=(lower, upper),
        loss="soft_l1",
        f_scale=0.002,
        max_nfev=160,
    )

    registered = transform(fit.x)
    residual, _ = target_tree.query(registered[validation_ids])
    scale = fit.x[:3]
    angles = fit.x[3:6]
    trans = fit.x[6:9]

    near_scale = bool(
        np.any(scale <= lower[:3] + 1e-3) or np.any(scale >= upper[:3] - 1e-3)
    )
    near_rot = bool(
        np.any(angles <= lower[3:6] + np.deg2rad(0.25))
        or np.any(angles >= upper[3:6] - np.deg2rad(0.25))
    )
    near_trans = bool(
        np.any(trans <= lower[6:9] + 1e-3) or np.any(trans >= upper[6:9] - 1e-3)
    )

    median_mm = float(np.median(residual) * 1000)
    p90_mm = float(np.quantile(residual, 0.90) * 1000)
    accepted = bool(
        fit.success
        and p90_mm <= 3.0
        and median_mm <= 2.0
        and not near_scale
        and not near_rot
        and not near_trans
    )

    return {
        "crop_normalized_xyxy": crop.tolist(),
        "initial_scale": float(initial_scale),
        "axis_scale_correction": scale.tolist(),
        "rotation_deg": np.rad2deg(angles).tolist(),
        "translation_m": trans.tolist(),
        "translation_norm_mm": float(np.linalg.norm(trans) * 1000),
        "fit_success": bool(fit.success),
        "fit_status": int(fit.status),
        "fit_message": str(fit.message),
        "support_source_points": int(len(source_ids)),
        "target_surface_samples": int(len(target)),
        "validation_points": int(len(validation_ids)),
        "heldout_median_mm": median_mm,
        "heldout_p90_mm": p90_mm,
        "near_scale_bound": near_scale,
        "near_rotation_bound": near_rot,
        "near_translation_bound": near_trans,
        "geometric_gate_passed": accepted,
    }


front_path = roi_v2.resolve_default_image(BUST_ROOT, LAB)
front = Image.open(front_path).convert("RGBA")
auto_result = roi_v3.propose(front, 0.50)
auto_crop = np.asarray(auto_result["proposal"], dtype=np.float64)

fixed = run_registration(KNOWN_CROP)
automatic = run_registration(auto_crop)

report = {
    "scope": "mechanical-bust fixture; fixed crop vs automatic ROI v3 densified registration A/B",
    "primary_approach": "crop-side post-ROI tightening; registration gates unchanged",
    "input_front": str(front_path),
    "base_mesh": str(BASE_PATH),
    "detail_mesh": str(DETAIL_PATH),
    "fixed_crop": fixed,
    "automatic_roi_v3": automatic,
    "acceptance": {
        "heldout_p90_mm_max": 3.0,
        "heldout_median_mm_max": 2.0,
        "require_optimizer_converged": True,
        "require_no_parameter_bound_hits": True,
    },
    "automatic_interchangeable_with_fixed_crop": bool(automatic["geometric_gate_passed"]),
    "production_accepted": False,
    "note": "No topology mutation or fusion performed. Fixed crop is A/B control only and is not used by auto ROI inference.",
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
