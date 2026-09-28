"""Fixture-only dry splice diagnostic for the mechanical bust.

Cuts a front ROI from the whole-bust mesh and inserts the already registered and
locally warped TRELLIS detail patch WITHOUT welding the boundaries.  This gives
us a reversible whole-object preview plus measurable seam-gap diagnostics before
we attempt any topology fusion.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "detail_registered_localwarp.glb"
PREVIEW_PATH = ROOT / "detail_dry_splice_preview.glb"
SCENE_PATH = ROOT / "detail_dry_splice_scene.glb"
REPORT_PATH = ROOT / "detail_dry_splice.json"

base = trimesh.load(BASE_PATH, force="mesh", process=False)
detail = trimesh.load(DETAIL_PATH, force="mesh", process=False)

bv = np.asarray(base.vertices, dtype=np.float64)
bf = np.asarray(base.faces, dtype=np.int64)
dv = np.asarray(detail.vertices, dtype=np.float64)
df = np.asarray(detail.faces, dtype=np.int64)


def patch_roi(v):
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


# Keep a triangle only if all its vertices lie in the patch ROI. This makes the
# patch boundary conservative and avoids long triangles crossing the cut.
detail_vertex_roi = patch_roi(dv)
detail_face_keep = detail_vertex_roi[df].all(axis=1)
assert detail_face_keep.sum() > 100, "Detail patch unexpectedly small"

# Remove base triangles if their centroid lies in a slightly smaller front ROI.
# The smaller cut gives the replacement patch a deliberate overlap rim.
base_centroids = bv[bf].mean(axis=1)
cut_roi = (
    (np.abs(base_centroids[:, 0]) < 0.058)
    & (base_centroids[:, 1] > 0.096)
    & (base_centroids[:, 1] < 0.177)
    & (base_centroids[:, 2] > -0.006)
)
assert cut_roi.sum() > 50, "Base cut unexpectedly small"

base_cut = base.submesh([~cut_roi], append=True, repair=False)
patch = detail.submesh([detail_face_keep], append=True, repair=False)
assert base_cut is not None and patch is not None

# Ensure the recovered central lens region is represented in the replacement.
patch_protected = protected_lens_roi(np.asarray(patch.vertices))
assert patch_protected.sum() > 100, "Protected lens geometry missing from patch"


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
    return np.asarray(mesh.vertices)[np.unique(boundary_edges)]


patch_boundary = boundary_vertices(patch)
base_boundary_all = boundary_vertices(base_cut)

# The source whole bust can already contain unrelated open boundaries. Restrict
# seam diagnostics to the cut neighbourhood.
base_boundary_mask = (
    (np.abs(base_boundary_all[:, 0]) < 0.080)
    & (base_boundary_all[:, 1] > 0.080)
    & (base_boundary_all[:, 1] < 0.195)
    & (base_boundary_all[:, 2] > -0.025)
)
base_boundary = base_boundary_all[base_boundary_mask]
assert len(patch_boundary) > 10 and len(base_boundary) > 10, (
    f"Missing usable boundaries: patch={len(patch_boundary)} base={len(base_boundary)}"
)

base_tree = cKDTree(base_boundary)
patch_tree = cKDTree(patch_boundary)
patch_to_base, _ = base_tree.query(patch_boundary)
base_to_patch, _ = patch_tree.query(base_boundary)

# Create a disconnected but whole-object preview. No welding/boolean operation.
preview = trimesh.util.concatenate([base_cut, patch])
preview.export(PREVIEW_PATH)
scene = trimesh.Scene()
scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
scene.export(SCENE_PATH)

report = {
    "scope": "fixed bust fixture; dry splice preview only; no welding or boolean fusion",
    "base": str(BASE_PATH),
    "detail": str(DETAIL_PATH),
    "preview": str(PREVIEW_PATH),
    "scene": str(SCENE_PATH),
    "base_faces_original": int(len(base.faces)),
    "base_faces_removed": int(cut_roi.sum()),
    "base_faces_remaining": int(len(base_cut.faces)),
    "patch_faces": int(len(patch.faces)),
    "patch_vertices": int(len(patch.vertices)),
    "protected_patch_vertices": int(patch_protected.sum()),
    "patch_boundary_vertices": int(len(patch_boundary)),
    "base_cut_boundary_vertices": int(len(base_boundary)),
    "patch_to_base_boundary_median_mm": float(np.median(patch_to_base) * 1000),
    "patch_to_base_boundary_p90_mm": float(np.quantile(patch_to_base, 0.90) * 1000),
    "patch_to_base_boundary_max_mm": float(np.max(patch_to_base) * 1000),
    "base_to_patch_boundary_median_mm": float(np.median(base_to_patch) * 1000),
    "base_to_patch_boundary_p90_mm": float(np.quantile(base_to_patch, 0.90) * 1000),
    "base_to_patch_boundary_max_mm": float(np.max(base_to_patch) * 1000),
    "preview_components": int(len(preview.split(only_watertight=False))),
    "production_accepted": False,
    "note": (
        "The patch and base remain disconnected. Boundary distances only measure "
        "whether a later seam operation is plausible. Visual confirmation that "
        "the three-lens detail sits correctly on the full bust is still required."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
