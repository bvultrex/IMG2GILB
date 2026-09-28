"""Fixture-only local non-rigid registration diagnostic.

Takes detail_registered.glb from register_bust_detail.py and deforms only the
outer hood/support neighbourhood toward the whole-bust support surface.
The central lens region is explicitly protected. No mesh fusion is performed.
"""
from pathlib import Path
import json

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "detail_registered.glb"
OUT_PATH = ROOT / "detail_registered_localwarp.glb"
REPORT_PATH = ROOT / "detail_localwarp.json"

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)
src = np.asarray(detail.vertices, dtype=np.float64)
dst = np.asarray(base.vertices, dtype=np.float64)


def support(v):
    return (
        (v[:, 1] > 0.10)
        & (v[:, 2] > 0)
        & ((np.abs(v[:, 0]) > 0.044) | (v[:, 1] > 0.169))
        & (np.abs(v[:, 0]) < 0.087)
    )


source_ids = np.flatnonzero(support(src))
target = dst[support(dst)]
assert len(source_ids) > 100 and len(target) > 100

source_support = src[source_ids]
source_support_tree = cKDTree(source_support)
target_tree = cKDTree(target)

before_src_dist, _ = target_tree.query(source_support)
before_rev_dist, target_to_source_local = source_support_tree.query(target)

# Build controls from target -> nearest source support. This specifically attacks
# support areas that the one-way source->target metric can miss.
raw_control_dist = before_rev_dist
raw_control_ids = source_ids[target_to_source_local]
raw_control_targets = target

# Reject only the largest gross mismatches and cap per-control displacement so
# the diagnostic cannot drag the hood across large gaps.
distance_limit = min(float(np.quantile(raw_control_dist, 0.90)), 0.010)
keep = raw_control_dist <= distance_limit
raw_control_ids = raw_control_ids[keep]
raw_control_targets = raw_control_targets[keep]

# Multiple target points can map to the same source vertex. Aggregate by median.
grouped = {}
for vertex_id, target_point in zip(raw_control_ids.tolist(), raw_control_targets):
    grouped.setdefault(vertex_id, []).append(target_point)

control_ids = np.array(sorted(grouped), dtype=np.int64)
control_positions = src[control_ids]
control_targets = np.array([np.median(grouped[i], axis=0) for i in control_ids])
control_disp = control_targets - control_positions

max_control = 0.006
control_norm = np.linalg.norm(control_disp, axis=1)
clip = np.minimum(1.0, max_control / np.maximum(control_norm, 1e-12))
control_disp *= clip[:, None]

assert len(control_ids) >= 20, f"Too few local-warp controls: {len(control_ids)}"

# Smooth kNN displacement interpolation.
control_tree = cKDTree(control_positions)
k = min(12, len(control_ids))
dist, ids = control_tree.query(src, k=k)
if k == 1:
    dist = dist[:, None]
    ids = ids[:, None]
sigma = 0.012
weights = np.exp(-0.5 * (dist / sigma) ** 2)
weights /= np.maximum(weights.sum(axis=1, keepdims=True), 1e-12)
field = np.sum(control_disp[ids] * weights[:, :, None], axis=1)

# Only the front/upper hood neighbourhood may deform.
deform_zone = (
    (src[:, 1] > 0.085)
    & (src[:, 2] > -0.020)
    & (np.abs(src[:, 0]) < 0.105)
)

# Influence fades away from the registered support surface.
support_tree = cKDTree(source_support)
distance_to_support, _ = support_tree.query(src)
support_influence = np.exp(-0.5 * (distance_to_support / 0.012) ** 2)

# Protect the central front region containing the recovered lenses. Add a smooth
# moat around it so the deformation cannot kink exactly on the protected edge.
protected = (
    (src[:, 2] > 0)
    & (np.abs(src[:, 0]) < 0.048)
    & (src[:, 1] > 0.100)
    & (src[:, 1] < 0.172)
)
assert protected.any()
protected_tree = cKDTree(src[protected])
distance_to_protected, _ = protected_tree.query(src)
protect_taper = np.clip(distance_to_protected / 0.010, 0.0, 1.0)
protect_taper = protect_taper * protect_taper * (3.0 - 2.0 * protect_taper)

influence = support_influence * protect_taper * deform_zone.astype(np.float64)
influence[protected] = 0.0
local_delta = field * influence[:, None]

warped = src + local_delta

after_source_support = warped[source_ids]
after_source_tree = cKDTree(after_source_support)
after_src_dist, _ = target_tree.query(after_source_support)
after_rev_dist, _ = after_source_tree.query(target)

# Geometry-change diagnostics relative to the registered input.
old_triangles = src[np.asarray(detail.faces)]
new_triangles = warped[np.asarray(detail.faces)]
old_cross = np.cross(
    old_triangles[:, 1] - old_triangles[:, 0],
    old_triangles[:, 2] - old_triangles[:, 0],
)
new_cross = np.cross(
    new_triangles[:, 1] - new_triangles[:, 0],
    new_triangles[:, 2] - new_triangles[:, 0],
)
old_area2 = np.linalg.norm(old_cross, axis=1)
new_area2 = np.linalg.norm(new_cross, axis=1)
valid = (old_area2 > 1e-12) & (new_area2 > 1e-12)
normal_dot = np.ones(len(detail.faces), dtype=np.float64)
normal_dot[valid] = np.einsum(
    "ij,ij->i",
    old_cross[valid] / old_area2[valid, None],
    new_cross[valid] / new_area2[valid, None],
)
area_ratio = np.ones(len(detail.faces), dtype=np.float64)
area_ratio[old_area2 > 1e-12] = (
    new_area2[old_area2 > 1e-12] / old_area2[old_area2 > 1e-12]
)

warped_mesh = detail.copy()
warped_mesh.vertices = warped
warped_mesh.export(OUT_PATH)

before_src_p90 = float(np.quantile(before_src_dist, 0.90))
before_rev_p90 = float(np.quantile(before_rev_dist, 0.90))
after_src_p90 = float(np.quantile(after_src_dist, 0.90))
after_rev_p90 = float(np.quantile(after_rev_dist, 0.90))

delta_norm = np.linalg.norm(local_delta, axis=1)
protected_delta = delta_norm[protected]

report = {
    "scope": "fixed bust fixture; local support warp with protected lens region; no fusion",
    "input": str(DETAIL_PATH),
    "target": str(BASE_PATH),
    "output": str(OUT_PATH),
    "controls": int(len(control_ids)),
    "control_distance_limit_mm": distance_limit * 1000,
    "control_displacement_median_mm": float(np.median(np.linalg.norm(control_disp, axis=1)) * 1000),
    "control_displacement_p90_mm": float(np.quantile(np.linalg.norm(control_disp, axis=1), 0.90) * 1000),
    "source_to_target_before_median_mm": float(np.median(before_src_dist) * 1000),
    "source_to_target_before_p90_mm": before_src_p90 * 1000,
    "source_to_target_after_median_mm": float(np.median(after_src_dist) * 1000),
    "source_to_target_after_p90_mm": after_src_p90 * 1000,
    "target_to_source_before_median_mm": float(np.median(before_rev_dist) * 1000),
    "target_to_source_before_p90_mm": before_rev_p90 * 1000,
    "target_to_source_after_median_mm": float(np.median(after_rev_dist) * 1000),
    "target_to_source_after_p90_mm": after_rev_p90 * 1000,
    "moved_vertices": int((delta_norm > 1e-6).sum()),
    "vertex_displacement_median_mm": float(np.median(delta_norm[delta_norm > 1e-9]) * 1000) if np.any(delta_norm > 1e-9) else 0.0,
    "vertex_displacement_p90_mm": float(np.quantile(delta_norm, 0.90) * 1000),
    "vertex_displacement_max_mm": float(delta_norm.max() * 1000),
    "protected_vertices": int(protected.sum()),
    "protected_displacement_max_mm": float(protected_delta.max() * 1000),
    "changed_face_normal_flip_fraction": float((normal_dot < 0).mean()),
    "area_ratio_p01": float(np.quantile(area_ratio, 0.01)),
    "area_ratio_p99": float(np.quantile(area_ratio, 0.99)),
    "diagnostic_improved_both_directions": bool(
        after_src_p90 < before_src_p90 and after_rev_p90 < before_rev_p90
    ),
    "production_accepted": False,
    "note": (
        "This only tests whether a protected-detail local warp can improve hood "
        "surface agreement. It does not verify lens semantics, seam topology, "
        "watertightness, printability or whole-bust fusion."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
