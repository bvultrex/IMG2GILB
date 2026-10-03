"""Fixture-only dry splice v2: align cut to patch and clean seam diagnostics.

v1 ~30 mm boundary p90 was dominated by inherited open edges (detail holes /
base robe scrap) mixed into the seam metric, plus an axis-aligned cut box that
did not follow the registered patch surface.

v2 changes (still no welding / boolean fusion):
1. Prefer detail_registered.glb (skip localwarp; A/B showed warp did not help seams).
2. Keep patch faces in the fixture hood ROI only if near the base surface, while
   always retaining the protected lens region.
3. Cut base faces by proximity to the patch INTERIOR (surface distance + rim
   exclusion), not a smaller independent AABB.
4. Seam metrics use only NEW boundary loops (exclude pre-existing open edges)
   and optionally mutual near-neighbourhood filtering around the cut.

Still fixture-specific. NOT automatic ROI detection. production_accepted=false.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
# Skip localwarp: after registration v2 it did not improve both directions and
# did not shrink dry-splice gaps.
DETAIL_PATH = ROOT / "detail_registered.glb"
PREVIEW_PATH = ROOT / "detail_dry_splice_roiv2_preview.glb"
SCENE_PATH = ROOT / "detail_dry_splice_roiv2_scene.glb"
REPORT_PATH = ROOT / "detail_dry_splice_roiv2.json"

# Winning ablation: kd0.007_din0.006_rim0.003_near0.012
PATCH_SURFACE_KEEP_M = 0.007
CUT_SURFACE_DIST_M = 0.006
CUT_RIM_EXCLUDE_M = 0.003
SEAM_NEAR_M = 0.012

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)

bv = np.asarray(base.vertices, dtype=np.float64)
bf = np.asarray(base.faces, dtype=np.int64)
dv = np.asarray(detail.vertices, dtype=np.float64)
df = np.asarray(detail.faces, dtype=np.int64)


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
        return np.empty((0, 3), dtype=np.float64)
    return np.asarray(mesh.vertices, dtype=np.float64)[np.unique(boundary_edges)]


def new_boundary_vertices(mesh, prior_open_tree, tol=1e-9):
    """Boundary verts created by the splice cut, excluding pre-existing opens."""
    b = boundary_vertices(mesh)
    if len(b) == 0:
        return b
    dist, _ = prior_open_tree.query(b)
    return b[dist >= tol]


def dist_stats(a, b):
    if len(a) == 0 or len(b) == 0:
        return {
            "n_a": int(len(a)),
            "n_b": int(len(b)),
            "median_mm": None,
            "p90_mm": None,
            "max_mm": None,
            "empty": True,
        }
    d, _ = cKDTree(b).query(a)
    return {
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "median_mm": float(np.median(d) * 1000),
        "p90_mm": float(np.quantile(d, 0.90) * 1000),
        "max_mm": float(np.max(d) * 1000),
        "empty": False,
    }


base_open = boundary_vertices(base)
detail_open = boundary_vertices(detail)
base_open_tree = cKDTree(base_open)
detail_open_tree = cKDTree(detail_open)
base_surface_tree = cKDTree(bv)

# Patch: fixture hood box, trimmed to base surface, lenses always kept.
d_to_base, _ = base_surface_tree.query(dv)
vert_keep = patch_roi_box(dv) & ((d_to_base < PATCH_SURFACE_KEEP_M) | protected_lens_roi(dv))
detail_face_keep = vert_keep[df].all(axis=1)
assert int(detail_face_keep.sum()) > 500, "Detail patch unexpectedly small"

patch = detail.submesh([detail_face_keep], append=True, repair=False)
assert patch is not None
pv = np.asarray(patch.vertices, dtype=np.float64)
patch_protected = protected_lens_roi(pv)
assert int(patch_protected.sum()) > 100, "Protected lens geometry missing from patch"

patch_new_boundary = new_boundary_vertices(patch, detail_open_tree)
assert len(patch_new_boundary) > 10, "Missing patch cut-loop boundary"
patch_tree = cKDTree(pv)
patch_boundary_tree = cKDTree(patch_new_boundary)

# Cut base faces that sit on the patch interior (not the seam rim).
cents = bv[bf].mean(axis=1)
loose = (
    (np.abs(cents[:, 0]) < 0.070)
    & (cents[:, 1] > 0.088)
    & (cents[:, 1] < 0.185)
    & (cents[:, 2] > -0.012)
)
d_surf = np.full(len(cents), np.inf)
d_bound = np.full(len(cents), np.inf)
d_surf[loose], _ = patch_tree.query(cents[loose])
d_bound[loose], _ = patch_boundary_tree.query(cents[loose])
cut_roi = loose & (d_surf < CUT_SURFACE_DIST_M) & (d_bound > CUT_RIM_EXCLUDE_M)
assert int(cut_roi.sum()) > 50, "Base cut unexpectedly small"

base_cut = base.submesh([~cut_roi], append=True, repair=False)
assert base_cut is not None

base_new_boundary_all = new_boundary_vertices(base_cut, base_open_tree)
assert len(base_new_boundary_all) > 10, "Missing base cut-loop boundary"

# Restrict seam diagnostics to mutually nearby new-boundary samples.
d_to_patch_loop, _ = cKDTree(patch_new_boundary).query(base_new_boundary_all)
base_seam = base_new_boundary_all[d_to_patch_loop < SEAM_NEAR_M]
d_to_base_loop, _ = cKDTree(base_seam).query(patch_new_boundary)
patch_seam = patch_new_boundary[d_to_base_loop < SEAM_NEAR_M]
assert len(base_seam) > 10 and len(patch_seam) > 10, (
    f"Seam loops too small after near-filter: patch={len(patch_seam)} base={len(base_seam)}"
)

p2b = dist_stats(patch_seam, base_seam)
b2p = dist_stats(base_seam, patch_seam)

# Legacy polluted metric (all boundaries + loose hood filter) for comparison only.
patch_boundary_all = boundary_vertices(patch)
base_boundary_all = boundary_vertices(base_cut)
legacy_mask = (
    (np.abs(base_boundary_all[:, 0]) < 0.080)
    & (base_boundary_all[:, 1] > 0.080)
    & (base_boundary_all[:, 1] < 0.195)
    & (base_boundary_all[:, 2] > -0.025)
)
legacy_base = base_boundary_all[legacy_mask]
legacy_p2b = dist_stats(patch_boundary_all, legacy_base)
legacy_b2p = dist_stats(legacy_base, patch_boundary_all)

preview = trimesh.util.concatenate([base_cut, patch])
preview.export(PREVIEW_PATH)
scene = trimesh.Scene()
scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
scene.export(SCENE_PATH)

report = {
    "scope": (
        "fixed bust fixture; dry splice ROI v2; patch-aligned proximity cut; "
        "new-boundary-only seam metrics; no welding or boolean fusion"
    ),
    "version": "dry_splice_roi_v2",
    "base": str(BASE_PATH),
    "detail": str(DETAIL_PATH),
    "detail_choice": "detail_registered.glb (skip localwarp)",
    "preview": str(PREVIEW_PATH),
    "scene": str(SCENE_PATH),
    "parameters": {
        "patch_roi_box": {
            "abs_x_lt": 0.066,
            "y_gt": 0.090,
            "y_lt": 0.183,
            "z_gt": -0.010,
        },
        "patch_surface_keep_m": PATCH_SURFACE_KEEP_M,
        "cut_surface_dist_m": CUT_SURFACE_DIST_M,
        "cut_rim_exclude_m": CUT_RIM_EXCLUDE_M,
        "seam_near_m": SEAM_NEAR_M,
        "protected_lens_roi": {
            "abs_x_lt": 0.048,
            "y_gt": 0.100,
            "y_lt": 0.172,
            "z_gt": 0.0,
        },
    },
    "base_faces_original": int(len(base.faces)),
    "base_faces_removed": int(cut_roi.sum()),
    "base_faces_remaining": int(len(base_cut.faces)),
    "patch_faces": int(len(patch.faces)),
    "patch_vertices": int(len(patch.vertices)),
    "protected_patch_vertices": int(patch_protected.sum()),
    "detail_preexisting_open_vertices": int(len(detail_open)),
    "base_preexisting_open_vertices": int(len(base_open)),
    "patch_boundary_vertices_all": int(len(patch_boundary_all)),
    "patch_boundary_vertices_new": int(len(patch_new_boundary)),
    "patch_seam_vertices": int(len(patch_seam)),
    "base_cut_boundary_vertices_all": int(len(base_boundary_all)),
    "base_cut_boundary_vertices_new": int(len(base_new_boundary_all)),
    "base_seam_vertices": int(len(base_seam)),
    "patch_to_base_boundary_median_mm": p2b["median_mm"],
    "patch_to_base_boundary_p90_mm": p2b["p90_mm"],
    "patch_to_base_boundary_max_mm": p2b["max_mm"],
    "base_to_patch_boundary_median_mm": b2p["median_mm"],
    "base_to_patch_boundary_p90_mm": b2p["p90_mm"],
    "base_to_patch_boundary_max_mm": b2p["max_mm"],
    "legacy_polluted_patch_to_base_p90_mm": legacy_p2b["p90_mm"],
    "legacy_polluted_base_to_patch_p90_mm": legacy_b2p["p90_mm"],
    "compared_to_after_reg_v2_patch_to_base_p90_mm": 30.34528953458491,
    "compared_to_after_reg_v2_patch_to_base_max_mm": 43.16583959055141,
    "compared_to_after_reg_v2_base_to_patch_p90_mm": 28.882346266616523,
    "compared_to_after_reg_v2_base_to_patch_max_mm": 51.653950355977926,
    "preview_components": int(len(preview.split(only_watertight=False))),
    "production_accepted": False,
    "note": (
        "Primary seam metrics exclude pre-existing open edges (detail holes, "
        "base robe scrap) and keep only mutually nearby new cut-loop samples. "
        "legacy_polluted_* reproduces the v1 neighbourhood metric for comparison. "
        "Crop/ROI remain fixture-specific; not automatic ROI detection. "
        "No welding performed. Visual confirmation of three-lens placement still required."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
