"""Fixture-only dry splice ROI v3: tighten seam for stitch readiness.

Builds on v2. Still no welding/boolean. production_accepted=false.

Diagnosis of remaining ~7 mm after v2:
1. Protected-AABB verts on seam (~47) inflated stitch rejection but only mildly
   the distance (nonprot p90 still ~6.7 mm).
2. Worst bridges sit on the lower cheek rim (y~0.10), where the patch ROI clip
   hangs off the base surface (~7 mm to surface) AND is laterally offset from
   the proximity-cut hole rim.
3. CUT_RIM_EXCLUDE / keep distances create a deliberate gap; AABB cut tracking
   alone cannot close lateral mismatch.

v3 changes:
- Exclude protected lens verts from seam samples used for stitch metrics.
- Tighter proximity cut (din=3 mm, rim=1 mm, near=8 mm).
- Cap non-protected new-boundary snap: 3 mm toward base surface, then 3 mm
  toward base new-boundary; reject if protected verts move.
- Optional one grow iteration of the cut after snap.
- Report stitch-gate evaluation (p90<=3, max<=5, coverage@3mm>=0.9) without
  mutating topology for fusion.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "detail_registered.glb"
PREVIEW_PATH = ROOT / "detail_dry_splice_roiv3_preview.glb"
SCENE_PATH = ROOT / "detail_dry_splice_roiv3_scene.glb"
REPORT_PATH = ROOT / "detail_dry_splice_roiv3.json"

PATCH_SURFACE_KEEP_M = 0.007
CUT_SURFACE_DIST_M = 0.003
CUT_RIM_EXCLUDE_M = 0.001
SEAM_NEAR_M = 0.008
SNAP_SURFACE_MAX_M = 0.003
SNAP_SEAM_MAX_M = 0.003
GROW_CUT_AFTER_SNAP = True
PROTECTED_MOVE_EPS_M = 1e-9

# Stitch readiness gates (same as stitch_bust_detail_v1)
GATE_P90_M = 0.003
GATE_MAX_M = 0.005
GATE_COV = 0.90

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail_src = trimesh.load(DETAIL_PATH, force="mesh", process=False)
bv = np.asarray(base.vertices, dtype=np.float64)
bf = np.asarray(base.faces, dtype=np.int64)
dv = np.asarray(detail_src.vertices, dtype=np.float64).copy()
df = np.asarray(detail_src.faces, dtype=np.int64)


def patch_roi_box(v):
    return (
        (np.abs(v[:, 0]) < 0.066)
        & (v[:, 1] > 0.090)
        & (v[:, 1] < 0.183)
        & (v[:, 2] > -0.010)
    )


def protected_lens_roi(v):
    return (
        (np.abs(v[:, 0]) < 0.048)
        & (v[:, 1] > 0.100)
        & (v[:, 1] < 0.172)
        & (v[:, 2] > 0.0)
    )


def boundary_vertices(mesh):
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.sort(
        np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])),
        axis=1,
    )
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary_edges = unique[counts == 1]
    if len(boundary_edges) == 0:
        return np.empty((0, 3), dtype=np.float64), np.empty((0,), dtype=np.int64)
    vids = np.unique(boundary_edges)
    return np.asarray(mesh.vertices, dtype=np.float64)[vids], vids


def new_boundary(mesh, prior_open_tree, tol=1e-9):
    pts, vids = boundary_vertices(mesh)
    if len(pts) == 0:
        return pts, vids
    dist, _ = prior_open_tree.query(pts)
    keep = dist >= tol
    return pts[keep], vids[keep]


def dist_stats_from_d(d):
    d = np.asarray(d, dtype=np.float64)
    if len(d) == 0:
        return {
            "n": 0,
            "median_mm": None,
            "p90_mm": None,
            "max_mm": None,
            "coverage_le_3mm": None,
            "coverage_le_5mm": None,
            "empty": True,
        }
    return {
        "n": int(len(d)),
        "median_mm": float(np.median(d) * 1000),
        "p90_mm": float(np.quantile(d, 0.90) * 1000),
        "max_mm": float(np.max(d) * 1000),
        "coverage_le_3mm": float(np.mean(d <= 0.003)),
        "coverage_le_5mm": float(np.mean(d <= 0.005)),
        "empty": False,
    }


base_open, _ = boundary_vertices(base)
detail_open, _ = boundary_vertices(detail_src)
base_open_tree = cKDTree(base_open)
detail_open_tree = cKDTree(detail_open)
base_surface_tree = cKDTree(bv)

d_to_base, _ = base_surface_tree.query(dv)
prot_src = protected_lens_roi(dv)
vert_keep = patch_roi_box(dv) & ((d_to_base < PATCH_SURFACE_KEEP_M) | prot_src)
detail_face_keep = vert_keep[df].all(axis=1)
assert int(detail_face_keep.sum()) > 500, "Detail patch unexpectedly small"

detail = detail_src.copy()
detail.vertices = dv
patch = detail.submesh([detail_face_keep], append=True, repair=False)
assert patch is not None
pv = np.asarray(patch.vertices, dtype=np.float64)
prot = protected_lens_roi(pv)
assert int(prot.sum()) > 100, "Protected lens geometry missing from patch"
pv_before_snap = pv.copy()

pb_new, pb_vids = new_boundary(patch, detail_open_tree)
assert len(pb_new) > 10, "Missing patch cut-loop boundary"

# Surface snap (non-protected new-boundary only)
if SNAP_SURFACE_MAX_M > 0 and len(pb_vids):
    snap_ids = pb_vids[~prot[pb_vids]]
    if len(snap_ids):
        _, nn_i = base_surface_tree.query(pv[snap_ids])
        delta = bv[nn_i] - pv[snap_ids]
        dn = np.linalg.norm(delta, axis=1)
        scale = np.minimum(1.0, SNAP_SURFACE_MAX_M / np.maximum(dn, 1e-12))
        pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
        patch.vertices = pv
        pb_new, pb_vids = new_boundary(patch, detail_open_tree)

cents = bv[bf].mean(axis=1)
loose = (
    (np.abs(cents[:, 0]) < 0.070)
    & (cents[:, 1] > 0.088)
    & (cents[:, 1] < 0.185)
    & (cents[:, 2] > -0.012)
)


def make_cut(pv_local, pb_local):
    patch_tree = cKDTree(pv_local)
    pb_tree = cKDTree(pb_local)
    d_surf = np.full(len(cents), np.inf)
    d_bound = np.full(len(cents), np.inf)
    d_surf[loose], _ = patch_tree.query(cents[loose])
    d_bound[loose], _ = pb_tree.query(cents[loose])
    return loose & (d_surf < CUT_SURFACE_DIST_M) & (d_bound > CUT_RIM_EXCLUDE_M)


cut_roi = make_cut(pv, pb_new)
assert int(cut_roi.sum()) > 50, "Base cut unexpectedly small"
base_cut = base.submesh([~cut_roi], append=True, repair=False)
assert base_cut is not None
bb_new, _ = new_boundary(base_cut, base_open_tree)
assert len(bb_new) > 10, "Missing base cut-loop boundary"

# Lateral snap toward base new-boundary (non-protected only)
snap_seam_moved_max_m = 0.0
if SNAP_SEAM_MAX_M > 0 and len(pb_vids) and len(bb_new):
    snap_ids = pb_vids[~prot[pb_vids]]
    if len(snap_ids):
        _, nn_i = cKDTree(bb_new).query(pv[snap_ids])
        delta = bb_new[nn_i] - pv[snap_ids]
        dn = np.linalg.norm(delta, axis=1)
        scale = np.minimum(1.0, SNAP_SEAM_MAX_M / np.maximum(dn, 1e-12))
        moved = dn * scale
        snap_seam_moved_max_m = float(moved.max()) if len(moved) else 0.0
        pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
        patch.vertices = pv
        pb_new, pb_vids = new_boundary(patch, detail_open_tree)
        if GROW_CUT_AFTER_SNAP:
            cut2 = make_cut(pv, pb_new)
            if int(cut2.sum()) >= 50:
                cut_roi = cut2
                base_cut = base.submesh([~cut_roi], append=True, repair=False)
                bb_new, _ = new_boundary(base_cut, base_open_tree)

protected_move = np.linalg.norm(pv[prot] - pv_before_snap[prot], axis=1)
protected_move_max_m = float(protected_move.max()) if prot.any() else 0.0
protected_ok = protected_move_max_m <= PROTECTED_MOVE_EPS_M
assert protected_ok, f"Protected lens moved {protected_move_max_m} m — hard reject"

# Seam samples: new boundaries, mutual near-filter, exclude protected
d_to_patch, _ = cKDTree(pb_new).query(bb_new)
base_seam = bb_new[d_to_patch < SEAM_NEAR_M]
d_to_base, nn_base = cKDTree(base_seam).query(pb_new)
mask = d_to_base < SEAM_NEAR_M
patch_seam = pb_new[mask]
patch_seam_vids = pb_vids[mask]
bridges = d_to_base[mask]
nonprot = ~prot[patch_seam_vids]
assert int(nonprot.sum()) > 20 and len(base_seam) > 10

p2b_all = dist_stats_from_d(bridges)
p2b = dist_stats_from_d(bridges[nonprot])
b2_all, _ = cKDTree(patch_seam).query(base_seam)
b2, _ = cKDTree(patch_seam[nonprot]).query(base_seam)
b2p_all = dist_stats_from_d(b2_all)
b2p = dist_stats_from_d(b2)

stitch_gate_pass = bool(
    (not p2b["empty"])
    and (not b2p["empty"])
    and p2b["p90_mm"] <= GATE_P90_M * 1000
    and p2b["max_mm"] <= GATE_MAX_M * 1000
    and p2b["coverage_le_3mm"] >= GATE_COV
    and b2p["p90_mm"] <= GATE_P90_M * 1000
    and b2p["max_mm"] <= GATE_MAX_M * 1000
    and protected_ok
    and int((~nonprot).sum()) == 0  # after exclusion, raw protected-on-seam count for candidates is removed
)

preview = trimesh.util.concatenate([base_cut, patch])
preview.export(PREVIEW_PATH)
scene = trimesh.Scene()
scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
scene.export(SCENE_PATH)

report = {
    "scope": (
        "fixed bust fixture; dry splice ROI v3; tighter cut + capped non-protected "
        "rim snaps; protected excluded from seam metrics; no welding"
    ),
    "version": "dry_splice_roi_v3",
    "base": str(BASE_PATH),
    "detail": str(DETAIL_PATH),
    "preview": str(PREVIEW_PATH),
    "scene": str(SCENE_PATH),
    "parameters": {
        "patch_surface_keep_m": PATCH_SURFACE_KEEP_M,
        "cut_surface_dist_m": CUT_SURFACE_DIST_M,
        "cut_rim_exclude_m": CUT_RIM_EXCLUDE_M,
        "seam_near_m": SEAM_NEAR_M,
        "snap_surface_max_m": SNAP_SURFACE_MAX_M,
        "snap_seam_max_m": SNAP_SEAM_MAX_M,
        "grow_cut_after_snap": GROW_CUT_AFTER_SNAP,
    },
    "base_faces_original": int(len(base.faces)),
    "base_faces_removed": int(cut_roi.sum()),
    "base_faces_remaining": int(len(base_cut.faces)),
    "patch_faces": int(len(patch.faces)),
    "patch_vertices": int(len(patch.vertices)),
    "protected_patch_vertices": int(prot.sum()),
    "protected_move_max_m": protected_move_max_m,
    "protected_ok": protected_ok,
    "snap_seam_moved_max_m": snap_seam_moved_max_m,
    "patch_boundary_vertices_new": int(len(pb_new)),
    "base_cut_boundary_vertices_new": int(len(bb_new)),
    "patch_seam_vertices_all": int(len(patch_seam)),
    "patch_seam_vertices_nonprot": int(nonprot.sum()),
    "protected_on_seam_before_exclusion": int((~nonprot).sum()),
    "base_seam_vertices": int(len(base_seam)),
    # Primary stitch-oriented metrics (protected excluded)
    "patch_to_base_boundary_median_mm": p2b["median_mm"],
    "patch_to_base_boundary_p90_mm": p2b["p90_mm"],
    "patch_to_base_boundary_max_mm": p2b["max_mm"],
    "patch_to_base_coverage_le_3mm": p2b["coverage_le_3mm"],
    "patch_to_base_coverage_le_5mm": p2b["coverage_le_5mm"],
    "base_to_patch_boundary_median_mm": b2p["median_mm"],
    "base_to_patch_boundary_p90_mm": b2p["p90_mm"],
    "base_to_patch_boundary_max_mm": b2p["max_mm"],
    "base_to_patch_coverage_le_3mm": b2p["coverage_le_3mm"],
    # Diagnostic including protected-on-seam samples
    "all_seam_patch_to_base_p90_mm": p2b_all["p90_mm"],
    "all_seam_patch_to_base_max_mm": p2b_all["max_mm"],
    "compared_to_roiv2_patch_to_base_p90_mm": 7.39649663010494,
    "compared_to_roiv2_patch_to_base_max_mm": 11.99151347330205,
    "compared_to_roiv2_base_to_patch_p90_mm": 7.169978333574654,
    "compared_to_roiv2_base_to_patch_max_mm": 11.6666708590448,
    "stitch_gates": {
        "p90_mm": GATE_P90_M * 1000,
        "max_mm": GATE_MAX_M * 1000,
        "coverage_le_3mm": GATE_COV,
    },
    "stitch_gates_would_pass": stitch_gate_pass,
    "preview_components": int(len(preview.split(only_watertight=False))),
    "topology_fusion_performed": False,
    "production_accepted": False,
    "floor_note": (
        "If stitch_gates_would_pass is false, the remaining gap is largely "
        "lateral base-hole vs patch-rim mismatch after capped snaps; further "
        "snap would exceed SNAP_*_MAX and risk distorting non-lens hood detail. "
        "Do not weld."
    ),
    "note": (
        "Fixture-specific ROI. Protected lens verts are kept in the patch and "
        "must not move; they are excluded from seam/stitch metrics. No bridge "
        "triangles inserted."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
