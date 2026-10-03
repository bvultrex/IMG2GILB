"""Fixture registration v3: Auto-ROI v2 crop + densified support (A/B vs fixed crop).

Loads proposal_normalized_xyxy from auto_roi_bust_v2.json (does not hardcode the
known fixture crop for the auto-roi arm). Keeps register_v2 densified target
support (3000 samples) and lens-protected support mask.

Writes:
  detail_registration_v3_autoroiv2.json  (A/B report)
  detail_registered_v3_autoroiv2.glb     (auto-roi arm mesh only)

Does not overwrite detail_registered_v2.* or ChatGPT auto_roi_* files.
production_accepted remains false. No fusion.
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
AUTO_ROI_JSON = ROOT / "auto_roi_bust_v2.json"
OUT_MESH = ROOT / "detail_registered_v3_autoroiv2.glb"
OUT_REPORT = ROOT / "detail_registration_v3_autoroiv2.json"

FIXED_CROP = np.array([0.32, 0.015, 0.675, 0.36], dtype=np.float64)
TARGET_SAMPLE_COUNT = 3000
TARGET_SAMPLE_SEED = 0

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)
dst = np.asarray(base.vertices, dtype=np.float64)
faces = np.asarray(base.faces, dtype=np.int64)
height = float(base.extents[1])

auto = json.loads(AUTO_ROI_JSON.read_text(encoding="utf-8"))
auto_crop = np.array(auto["proposal_normalized_xyxy"], dtype=np.float64)
assert auto.get("fixture_gate_passed") is True, "Auto-ROI v2 fixture gate not passed"


def support(v):
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


def rotation_matrix_xyz(angles):
    ax, ay, az = angles
    sx, cx = np.sin(ax), np.cos(ax)
    sy, cy = np.sin(ay), np.cos(ay)
    sz, cz = np.sin(az), np.cos(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def register_with_crop(crop, label):
    initial_scale = (crop[3] - crop[1]) * height / float(detail.extents[1])
    center = np.array(
        [(crop[0] + crop[2]) / 2 - 0.5, 0.5 - (crop[1] + crop[3]) / 2, 0.0]
    ) * height
    src = (detail.vertices - detail.bounds.mean(0)) * initial_scale + center

    target = sample_support_surface(support)
    source_ids = np.flatnonzero(support(src))
    sparse_target = dst[support(dst)]
    assert len(target) > 100 and len(source_ids) > 100, f"{label}: too few support points"

    tree = cKDTree(target)
    sparse_tree = cKDTree(sparse_target)
    train_ids = source_ids[::2]
    validation_ids = source_ids[1::2]

    translation = np.zeros(3)
    for _ in range(40):
        points = src[train_ids] + translation
        dist, ids = tree.query(points)
        keep = dist <= np.quantile(dist, 0.75)
        step = np.median(target[ids[keep]] - points[keep], axis=0)
        translation += step
        if np.linalg.norm(step) < 1e-6:
            break

    def transform_st(parameters):
        return (src - center) * parameters[:3] + center + parameters[3:]

    def transform_srt(parameters):
        scale = parameters[:3]
        angles = parameters[3:6]
        translation_value = parameters[6:9]
        local = (src - center) * scale
        return local @ rotation_matrix_xyz(angles).T + center + translation_value

    def objective_st(parameters):
        points = transform_st(parameters)[train_ids]
        _, ids = tree.query(points)
        return np.concatenate([(points - target[ids]).ravel(), 0.01 * (parameters[:3] - 1)])

    def objective_srt(parameters):
        points = transform_srt(parameters)[train_ids]
        _, ids = tree.query(points)
        return np.concatenate(
            [
                (points - target[ids]).ravel(),
                0.01 * (parameters[:3] - 1),
                0.0025 * parameters[3:6],
            ]
        )

    st_lower = np.r_[np.full(3, 0.75), np.full(3, -0.025)]
    st_upper = np.r_[np.full(3, 1.25), np.full(3, 0.025)]
    st_fit = least_squares(
        objective_st,
        np.r_[np.ones(3), translation],
        bounds=(st_lower, st_upper),
        loss="soft_l1",
        f_scale=0.002,
        max_nfev=100,
    )
    st_registered = transform_st(st_fit.x)
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
        objective_srt,
        srt_start,
        bounds=(srt_lower, srt_upper),
        loss="soft_l1",
        f_scale=0.002,
        max_nfev=160,
    )
    srt_registered = transform_srt(srt_fit.x)
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

    sparse_residual, _ = sparse_tree.query(registered[validation_ids])
    reverse_tree = cKDTree(registered[source_ids])
    reverse_residual, _ = reverse_tree.query(target)

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
    return {
        "label": label,
        "crop_normalized_xyxy": crop.tolist(),
        "initial_scale": float(initial_scale),
        "selected_model": selected_model,
        "axis_scale_correction": scale.tolist(),
        "rotation_deg": np.rad2deg(angles).tolist(),
        "translation_m": final_translation.tolist(),
        "translation_norm_mm": translation_norm * 1000,
        "fit_success": bool(selected_fit.success),
        "support_target_surface_samples": int(len(target)),
        "support_source_points": int(len(source_ids)),
        "heldout_median_mm": float(np.median(residual) * 1000),
        "heldout_p90_mm": heldout_p90 * 1000,
        "sparse_vertex_heldout_p90_mm": float(np.quantile(sparse_residual, 0.9) * 1000),
        "reverse_support_p90_mm": float(np.quantile(reverse_residual, 0.9) * 1000),
        "scale_translation_heldout_p90_mm": st_p90 * 1000,
        "scale_rotation_translation_heldout_p90_mm": srt_p90 * 1000,
        "near_scale_bound": near_scale_bound,
        "near_rotation_bound": near_rotation_bound,
        "near_translation_bound": near_translation_bound,
        "geometric_gate_passed": accepted,
        "production_accepted": False,
        "registered_vertices": registered,
    }


fixed = register_with_crop(FIXED_CROP, "fixed_known_crop_register_v2_style")
auto_arm = register_with_crop(auto_crop, "auto_roi_v2_proposal_crop")

# Export auto-roi mesh only
mesh = detail.copy()
mesh.vertices = auto_arm["registered_vertices"]
mesh.export(OUT_MESH)

def strip(arm):
    out = {k: v for k, v in arm.items() if k != "registered_vertices"}
    return out

report = {
    "scope": (
        "fixed bust fixture; registration A/B: densified-support register_v2 style "
        "with fixed known crop vs Auto-ROI v2 proposal crop; no fusion"
    ),
    "version": "register_bust_detail_v3_autoroiv2",
    "base": str(BASE_PATH),
    "detail": str(DETAIL_PATH),
    "auto_roi_json": str(AUTO_ROI_JSON),
    "auto_roi_fixture_gate_passed": bool(auto["fixture_gate_passed"]),
    "auto_roi_bbox_iou": float(auto["bbox_iou"]),
    "auto_roi_known_crop_coverage": float(auto["known_crop_coverage"]),
    "auto_roi_min_threshold_stability_iou": float(auto["min_threshold_stability_iou"]),
    "output_mesh_auto_roi_arm": str(OUT_MESH),
    "fixed_crop_arm": strip(fixed),
    "auto_roi_arm": strip(auto_arm),
    "comparison": {
        "fixed_heldout_p90_mm": fixed["heldout_p90_mm"],
        "auto_heldout_p90_mm": auto_arm["heldout_p90_mm"],
        "fixed_geometric_gate_passed": fixed["geometric_gate_passed"],
        "auto_geometric_gate_passed": auto_arm["geometric_gate_passed"],
        "auto_better_heldout_p90": bool(auto_arm["heldout_p90_mm"] < fixed["heldout_p90_mm"]),
    },
    "production_accepted": False,
    "note": (
        "Known crop used only for the fixed A/B arm and Auto-ROI evaluation. "
        "Auto-ROI arm uses proposal_normalized_xyxy from auto_roi_bust_v2.json. "
        "Passing registration gate does not authorize stitching or UI promotion."
    ),
}
OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
