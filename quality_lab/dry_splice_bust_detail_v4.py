"""Fixture-only dry splice ROI v4: primary cut-loop extraction.

Builds on v3 (capped snaps, protected exclusion). Still no welding/boolean.

v3 left base→patch p90 ~6 mm because NEW base-boundary after the proximity cut
fragments into many edge components; orphan fragments far from the patch polluted
the seam. v4 keeps only near-patch new-boundary components (union of components
with median distance to patch new-boundary < 3 mm and p90 < 6 mm) as the
primary cut-loop set for seam metrics and snap targeting.

Preview still uses the same proximity cut (hole unchanged for visuals); seam
diagnostics and stitch readiness use the cleaned primary loop only.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from collections import defaultdict

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "detail_registered.glb"
PREVIEW_PATH = ROOT / "detail_dry_splice_roiv4_preview.glb"
SCENE_PATH = ROOT / "detail_dry_splice_roiv4_scene.glb"
REPORT_PATH = ROOT / "detail_dry_splice_roiv4.json"

PATCH_SURFACE_KEEP_M = 0.007
CUT_SURFACE_DIST_M = 0.003
CUT_RIM_EXCLUDE_M = 0.001
SEAM_NEAR_M = 0.008
SNAP_SURFACE_MAX_M = 0.003
SNAP_SEAM_MAX_M = 0.003
GROW_CUT_AFTER_SNAP = False
# Primary-loop keep: component vs patch new-boundary
LOOP_MED_MAX_MM = 3.0
LOOP_P90_MAX_MM = 6.0
PROTECTED_MOVE_EPS_M = 1e-9
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


def boundary_edges(mesh):
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.sort(
        np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])),
        axis=1,
    )
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    return unique[counts == 1]


def boundary_vertices(mesh):
    be = boundary_edges(mesh)
    if len(be) == 0:
        return np.empty((0, 3), dtype=np.float64), np.empty((0,), dtype=np.int64)
    vids = np.unique(be)
    return np.asarray(mesh.vertices, dtype=np.float64)[vids], vids


def new_boundary_edges(mesh, prior_open_tree, tol=1e-9):
    be = boundary_edges(mesh)
    if len(be) == 0:
        return be
    V = np.asarray(mesh.vertices, dtype=np.float64)
    d0, _ = prior_open_tree.query(V[be[:, 0]])
    d1, _ = prior_open_tree.query(V[be[:, 1]])
    return be[(d0 >= tol) & (d1 >= tol)]


def connected_edge_components(be):
    if len(be) == 0:
        return []
    adj = defaultdict(list)
    for i, (a, b) in enumerate(be):
        adj[int(a)].append(i)
        adj[int(b)].append(i)
    seen = np.zeros(len(be), dtype=bool)
    comps = []
    for i in range(len(be)):
        if seen[i]:
            continue
        stack = [i]
        seen[i] = True
        edges = []
        while stack:
            e = stack.pop()
            edges.append(e)
            for v in (int(be[e, 0]), int(be[e, 1])):
                for ei in adj[v]:
                    if not seen[ei]:
                        seen[ei] = True
                        stack.append(ei)
        comps.append(np.array(edges, dtype=np.int64))
    comps.sort(key=len, reverse=True)
    return comps


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
assert int(detail_face_keep.sum()) > 500

detail = detail_src.copy()
detail.vertices = dv
patch = detail.submesh([detail_face_keep], append=True, repair=False)
pv = np.asarray(patch.vertices, dtype=np.float64)
prot = protected_lens_roi(pv)
assert int(prot.sum()) > 100
pv_before_snap = pv.copy()

pb_pts, pb_vids = boundary_vertices(patch)
d_open, _ = detail_open_tree.query(pb_pts)
keep_b = d_open >= 1e-9
pb_vids = pb_vids[keep_b]

# Surface snap
snap_ids = pb_vids[~prot[pb_vids]]
if len(snap_ids):
    _, nn_i = base_surface_tree.query(pv[snap_ids])
    delta = bv[nn_i] - pv[snap_ids]
    dn = np.linalg.norm(delta, axis=1)
    scale = np.minimum(1.0, SNAP_SURFACE_MAX_M / np.maximum(dn, 1e-12))
    pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
    patch.vertices = pv
    pb_pts, pb_vids = boundary_vertices(patch)
    d_open, _ = detail_open_tree.query(pb_pts)
    keep_b = d_open >= 1e-9
    pb_new = pb_pts[keep_b]
    pb_vids = pb_vids[keep_b]
else:
    pb_new = pb_pts[keep_b]

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
assert int(cut_roi.sum()) > 50
base_cut = base.submesh([~cut_roi], append=True, repair=False)
Vcut = np.asarray(base_cut.vertices, dtype=np.float64)

be_new = new_boundary_edges(base_cut, base_open_tree)
comps = connected_edge_components(be_new)
assert len(comps) > 0

pb_tree = cKDTree(pb_new)
kept_comp_meta = []
kept_vids = []
orphan_verts = 0
for ci, eidx in enumerate(comps):
    be_c = be_new[eidx]
    vids = np.unique(be_c)
    pts = Vcut[vids]
    d, _ = pb_tree.query(pts)
    med = float(np.median(d) * 1000)
    p90 = float(np.quantile(d, 0.90) * 1000)
    meta = {
        "comp": int(ci),
        "n_edges": int(len(be_c)),
        "n_verts": int(len(vids)),
        "med_to_patch_mm": med,
        "p90_to_patch_mm": p90,
        "kept": bool(med < LOOP_MED_MAX_MM and p90 < LOOP_P90_MAX_MM),
    }
    if meta["kept"]:
        kept_comp_meta.append(meta)
        kept_vids.append(vids)
    else:
        orphan_verts += int(len(vids))

assert kept_vids, "No primary cut-loop components near patch"
primary_vids = np.unique(np.concatenate(kept_vids))
primary_loop_pts = Vcut[primary_vids]

# Lateral snap toward primary loop only
snap_seam_moved_max_m = 0.0
snap_ids = pb_vids[~prot[pb_vids]]
if len(snap_ids) and len(primary_loop_pts):
    _, nn_i = cKDTree(primary_loop_pts).query(pv[snap_ids])
    delta = primary_loop_pts[nn_i] - pv[snap_ids]
    dn = np.linalg.norm(delta, axis=1)
    scale = np.minimum(1.0, SNAP_SEAM_MAX_M / np.maximum(dn, 1e-12))
    snap_seam_moved_max_m = float((dn * scale).max()) if len(dn) else 0.0
    pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
    patch.vertices = pv
    pb_pts, pb_vids = boundary_vertices(patch)
    d_open, _ = detail_open_tree.query(pb_pts)
    keep_b = d_open >= 1e-9
    pb_new = pb_pts[keep_b]
    pb_vids = pb_vids[keep_b]
    if GROW_CUT_AFTER_SNAP:
        cut2 = make_cut(pv, pb_new)
        if int(cut2.sum()) >= 50:
            cut_roi = cut2
            base_cut = base.submesh([~cut_roi], append=True, repair=False)
            Vcut = np.asarray(base_cut.vertices, dtype=np.float64)
            # Re-extract primary loop on updated cut
            be_new = new_boundary_edges(base_cut, base_open_tree)
            comps = connected_edge_components(be_new)
            pb_tree = cKDTree(pb_new)
            kept_comp_meta = []
            kept_vids = []
            orphan_verts = 0
            for ci, eidx in enumerate(comps):
                be_c = be_new[eidx]
                vids = np.unique(be_c)
                pts = Vcut[vids]
                d, _ = pb_tree.query(pts)
                med = float(np.median(d) * 1000)
                p90 = float(np.quantile(d, 0.90) * 1000)
                meta = {
                    "comp": int(ci),
                    "n_edges": int(len(be_c)),
                    "n_verts": int(len(vids)),
                    "med_to_patch_mm": med,
                    "p90_to_patch_mm": p90,
                    "kept": bool(med < LOOP_MED_MAX_MM and p90 < LOOP_P90_MAX_MM),
                }
                if meta["kept"]:
                    kept_comp_meta.append(meta)
                    kept_vids.append(vids)
                else:
                    orphan_verts += int(len(vids))
            assert kept_vids, "Primary loop lost after grow"
            primary_vids = np.unique(np.concatenate(kept_vids))
            primary_loop_pts = Vcut[primary_vids]

protected_move_max_m = (
    float(np.linalg.norm(pv[prot] - pv_before_snap[prot], axis=1).max())
    if prot.any()
    else 0.0
)
assert protected_move_max_m <= PROTECTED_MOVE_EPS_M

# Seam metrics on primary loop only
d_to_patch, _ = cKDTree(pb_new).query(primary_loop_pts)
base_seam = primary_loop_pts[d_to_patch < SEAM_NEAR_M]
d_to_base, _ = cKDTree(base_seam).query(pb_new)
mask = d_to_base < SEAM_NEAR_M
patch_seam = pb_new[mask]
patch_seam_vids = pb_vids[mask]
bridges = d_to_base[mask]
nonprot = ~prot[patch_seam_vids]
assert int(nonprot.sum()) > 20 and len(base_seam) > 10

p2b = dist_stats_from_d(bridges[nonprot])
b2, _ = cKDTree(patch_seam[nonprot]).query(base_seam)
b2p = dist_stats_from_d(b2)

# Compare polluted (all new boundary verts) for documentation
all_new_vids = np.unique(be_new) if len(be_new) else np.empty((0,), dtype=np.int64)
all_new_pts = Vcut[all_new_vids] if len(all_new_vids) else np.empty((0, 3))
if len(all_new_pts) and len(pb_new):
    d_all_to_patch, _ = cKDTree(pb_new).query(all_new_pts)
    all_base = all_new_pts[d_all_to_patch < SEAM_NEAR_M]
    if len(all_base):
        d_all, _ = cKDTree(all_base).query(pb_new)
        m_all = d_all < SEAM_NEAR_M
        polluted_p2b = dist_stats_from_d(d_all[m_all][ ~prot[pb_vids[m_all]] ]) if m_all.any() else dist_stats_from_d([])
        # safer polluted: use same nonprot logic
        ps_all = pb_new[m_all]
        ps_vids_all = pb_vids[m_all]
        br_all = d_all[m_all]
        np_all = ~prot[ps_vids_all]
        polluted_p2b = dist_stats_from_d(br_all[np_all]) if np_all.any() else dist_stats_from_d([])
        b2_all, _ = cKDTree(ps_all[np_all]).query(all_base) if np_all.any() else (np.array([]), None)
        polluted_b2p = dist_stats_from_d(b2_all)
    else:
        polluted_p2b = dist_stats_from_d([])
        polluted_b2p = dist_stats_from_d([])
else:
    polluted_p2b = dist_stats_from_d([])
    polluted_b2p = dist_stats_from_d([])

stitch_gate_pass = bool(
    (not p2b["empty"])
    and (not b2p["empty"])
    and p2b["p90_mm"] <= GATE_P90_M * 1000
    and p2b["max_mm"] <= GATE_MAX_M * 1000
    and p2b["coverage_le_3mm"] >= GATE_COV
    and b2p["p90_mm"] <= GATE_P90_M * 1000
    and b2p["max_mm"] <= GATE_MAX_M * 1000
    and protected_move_max_m <= PROTECTED_MOVE_EPS_M
)

preview = trimesh.util.concatenate([base_cut, patch])
preview.export(PREVIEW_PATH)
scene = trimesh.Scene()
scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
scene.export(SCENE_PATH)

report = {
    "scope": (
        "fixed bust fixture; dry splice ROI v4; primary near-patch cut-loop union; "
        "orphan base-boundary components dropped from seam metrics; no welding"
    ),
    "version": "dry_splice_roi_v4",
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
        "loop_med_max_mm": LOOP_MED_MAX_MM,
        "loop_p90_max_mm": LOOP_P90_MAX_MM,
    },
    "base_faces_removed": int(cut_roi.sum()),
    "base_faces_remaining": int(len(base_cut.faces)),
    "patch_faces": int(len(patch.faces)),
    "protected_patch_vertices": int(prot.sum()),
    "protected_move_max_m": protected_move_max_m,
    "snap_seam_moved_max_m": snap_seam_moved_max_m,
    "new_boundary_components_total": int(len(comps)),
    "primary_loop_components_kept": int(len(kept_comp_meta)),
    "primary_loop_vertices": int(len(primary_vids)),
    "orphan_component_vertices_dropped": int(orphan_verts),
    "kept_components": kept_comp_meta[:40],
    "patch_seam_vertices_nonprot": int(nonprot.sum()),
    "base_seam_vertices_primary": int(len(base_seam)),
    "protected_on_seam_before_exclusion": int((~nonprot).sum()),
    "patch_to_base_boundary_median_mm": p2b["median_mm"],
    "patch_to_base_boundary_p90_mm": p2b["p90_mm"],
    "patch_to_base_boundary_max_mm": p2b["max_mm"],
    "patch_to_base_coverage_le_3mm": p2b["coverage_le_3mm"],
    "patch_to_base_coverage_le_5mm": p2b["coverage_le_5mm"],
    "base_to_patch_boundary_median_mm": b2p["median_mm"],
    "base_to_patch_boundary_p90_mm": b2p["p90_mm"],
    "base_to_patch_boundary_max_mm": b2p["max_mm"],
    "base_to_patch_coverage_le_3mm": b2p["coverage_le_3mm"],
    "polluted_all_new_boundary_p2b_p90_mm": polluted_p2b.get("p90_mm"),
    "polluted_all_new_boundary_b2p_p90_mm": polluted_b2p.get("p90_mm"),
    "compared_to_roiv3_patch_to_base_p90_mm": 2.9851153815907834,
    "compared_to_roiv3_patch_to_base_max_mm": 7.679708807151269,
    "compared_to_roiv3_base_to_patch_p90_mm": 6.040002907929537,
    "compared_to_roiv3_base_to_patch_max_mm": 7.950178828933032,
    "compared_to_roiv3_coverage_le_3mm": 0.9022346368715084,
    "stitch_gates": {"p90_mm": 3.0, "max_mm": 5.0, "coverage_le_3mm": 0.9},
    "stitch_gates_would_pass": stitch_gate_pass,
    "topology_fusion_performed": False,
    "production_accepted": False,
    "floor_note": (
        "If gates still fail, remaining outliers are on the cleaned primary "
        "near-patch loop itself (not robe orphans). Do not raise snap caps; do not weld."
    ),
    "note": (
        "Primary loop = union of NEW base-boundary edge components near the patch. "
        "Orphan far components dropped from seam metrics only. Fixture-specific."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

