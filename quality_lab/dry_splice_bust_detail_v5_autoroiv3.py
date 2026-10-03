"""Grok-owned dry-splice A/B: fixed crop vs Auto-ROI v3 (ROI-v4 seam logic).

Registers the headprobe detail with densified target sampling for BOTH the fixed
known crop and ChatGPT Auto-ROI v3 proposal (loaded from auto_roi_bust_v3.json),
then runs the same dry-splice ROI-v4 pipeline (surface-distance cut, capped snaps,
primary cut-loop / orphan drop) on each registered mesh.

Does NOT edit ChatGPT auto_roi_* files. No topology weld/fusion.
production_accepted remains false.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json

import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_SRC_PATH = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"
AUTO_ROI_JSON = ROOT / "auto_roi_bust_v3.json"
REPORT_PATH = ROOT / "detail_dry_splice_v5_autoroiv3_ab.json"

FIXED_CROP = np.array([0.32, 0.015, 0.675, 0.36], dtype=np.float64)

PATCH_SURFACE_KEEP_M = 0.007
CUT_SURFACE_DIST_M = 0.003
CUT_RIM_EXCLUDE_M = 0.001
SEAM_NEAR_M = 0.008
SNAP_SURFACE_MAX_M = 0.003
SNAP_SEAM_MAX_M = 0.003
GROW_CUT_AFTER_SNAP = False
LOOP_MED_MAX_MM = 3.0
LOOP_P90_MAX_MM = 6.0
PROTECTED_MOVE_EPS_M = 1e-9
GATE_P90_M = 0.003
GATE_MAX_M = 0.005
GATE_COV = 0.90
TARGET_SAMPLE_COUNT = 3000


def support(v):
    return (
        (v[:, 1] > 0.10)
        & (v[:, 2] > 0)
        & ((np.abs(v[:, 0]) > 0.044) | (v[:, 1] > 0.169))
        & (np.abs(v[:, 0]) < 0.087)
    )


def protected_lens_roi(v):
    return (
        (np.abs(v[:, 0]) < 0.048)
        & (v[:, 1] > 0.100)
        & (v[:, 1] < 0.172)
        & (v[:, 2] > 0.0)
    )


def patch_roi_box(v):
    return (
        (np.abs(v[:, 0]) < 0.066)
        & (v[:, 1] > 0.090)
        & (v[:, 1] < 0.183)
        & (v[:, 2] > -0.010)
    )


def rotation_matrix_xyz(angles):
    ax, ay, az = angles
    sx, cx = np.sin(ax), np.cos(ax)
    sy, cy = np.sin(ay), np.cos(ay)
    sz, cz = np.sin(az), np.cos(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def deterministic_surface_target(mesh, count=TARGET_SAMPLE_COUNT):
    sample_count = max(600000, count * 200)
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
            f"Only {len(candidates)} support samples from {sample_count}; need {count}."
        )
    ids = np.linspace(0, len(candidates) - 1, count, dtype=np.int64)
    return candidates[ids]


def register_with_crop(base, detail, target, crop, tag):
    crop = np.asarray(crop, dtype=np.float64)
    height = float(base.extents[1])
    initial_scale = (crop[3] - crop[1]) * height / float(detail.extents[1])
    center = (
        np.array(
            [(crop[0] + crop[2]) * 0.5 - 0.5, 0.5 - (crop[1] + crop[3]) * 0.5, 0.0]
        )
        * height
    )
    src = (np.asarray(detail.vertices, dtype=np.float64) - detail.bounds.mean(0)) * initial_scale + center
    target_tree = cKDTree(target)

    source_ids = np.flatnonzero(support(src))
    if len(source_ids) < 100:
        raise RuntimeError(f"{tag}: too few source support points: {len(source_ids)}")
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
        objective, start, bounds=(lower, upper), loss="soft_l1", f_scale=0.002, max_nfev=160
    )
    registered = transform(fit.x)
    residual, _ = target_tree.query(registered[validation_ids])
    scale = fit.x[:3]
    angles = fit.x[3:6]
    trans = fit.x[6:9]
    near_scale = bool(np.any(scale <= lower[:3] + 1e-3) or np.any(scale >= upper[:3] - 1e-3))
    near_rot = bool(
        np.any(angles <= lower[3:6] + np.deg2rad(0.25))
        or np.any(angles >= upper[3:6] - np.deg2rad(0.25))
    )
    near_trans = bool(np.any(trans <= lower[6:9] + 1e-3) or np.any(trans >= upper[6:9] - 1e-3))
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

    out_mesh = ROOT / f"detail_registered_v5_{tag}.glb"
    mesh = trimesh.Trimesh(registered, np.asarray(detail.faces, dtype=np.int64), process=False)
    mesh.export(out_mesh)

    metrics = {
        "tag": tag,
        "crop_normalized_xyxy": crop.tolist(),
        "initial_scale": float(initial_scale),
        "axis_scale_correction": scale.tolist(),
        "rotation_deg": np.rad2deg(angles).tolist(),
        "translation_m": trans.tolist(),
        "translation_norm_mm": float(np.linalg.norm(trans) * 1000),
        "fit_success": bool(fit.success),
        "support_source_points": int(len(source_ids)),
        "target_surface_samples": int(len(target)),
        "validation_points": int(len(validation_ids)),
        "heldout_median_mm": median_mm,
        "heldout_p90_mm": p90_mm,
        "near_scale_bound": near_scale,
        "near_rotation_bound": near_rot,
        "near_translation_bound": near_trans,
        "geometric_gate_passed": accepted,
        "output_mesh": str(out_mesh),
    }
    return mesh, metrics


def boundary_edges(mesh):
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.sort(np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])), axis=1)
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


def dry_splice_roiv4(base, detail_src, tag):
    preview_path = ROOT / f"detail_dry_splice_v5_{tag}_preview.glb"
    scene_path = ROOT / f"detail_dry_splice_v5_{tag}_scene.glb"
    arm_report_path = ROOT / f"detail_dry_splice_v5_{tag}.json"

    bv = np.asarray(base.vertices, dtype=np.float64)
    bf = np.asarray(base.faces, dtype=np.int64)
    dv = np.asarray(detail_src.vertices, dtype=np.float64).copy()
    df = np.asarray(detail_src.faces, dtype=np.int64)

    base_open, _ = boundary_vertices(base)
    detail_open, _ = boundary_vertices(detail_src)
    base_open_tree = cKDTree(base_open)
    detail_open_tree = cKDTree(detail_open)
    base_surface_tree = cKDTree(bv)

    d_to_base, _ = base_surface_tree.query(dv)
    prot_src = protected_lens_roi(dv)
    vert_keep = patch_roi_box(dv) & ((d_to_base < PATCH_SURFACE_KEEP_M) | prot_src)
    detail_face_keep = vert_keep[df].all(axis=1)
    if int(detail_face_keep.sum()) <= 500:
        raise RuntimeError(f"{tag}: too few patch faces {int(detail_face_keep.sum())}")

    detail = detail_src.copy()
    detail.vertices = dv
    patch = detail.submesh([detail_face_keep], append=True, repair=False)
    pv = np.asarray(patch.vertices, dtype=np.float64)
    prot = protected_lens_roi(pv)
    if int(prot.sum()) <= 100:
        raise RuntimeError(f"{tag}: too few protected verts {int(prot.sum())}")
    pv_before_snap = pv.copy()

    pb_pts, pb_vids = boundary_vertices(patch)
    d_open, _ = detail_open_tree.query(pb_pts)
    keep_b = d_open >= 1e-9
    pb_vids = pb_vids[keep_b]

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
    if int(cut_roi.sum()) <= 50:
        raise RuntimeError(f"{tag}: cut too small {int(cut_roi.sum())}")
    base_cut = base.submesh([~cut_roi], append=True, repair=False)
    Vcut = np.asarray(base_cut.vertices, dtype=np.float64)

    be_new = new_boundary_edges(base_cut, base_open_tree)
    comps = connected_edge_components(be_new)
    if not comps:
        raise RuntimeError(f"{tag}: no new boundary components")

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
    if not kept_vids:
        raise RuntimeError(f"{tag}: no primary cut-loop near patch")
    primary_vids = np.unique(np.concatenate(kept_vids))
    primary_loop_pts = Vcut[primary_vids]

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

    protected_move_max_m = (
        float(np.linalg.norm(pv[prot] - pv_before_snap[prot], axis=1).max()) if prot.any() else 0.0
    )
    if protected_move_max_m > PROTECTED_MOVE_EPS_M:
        raise RuntimeError(f"{tag}: protected moved {protected_move_max_m}")

    d_to_patch, _ = cKDTree(pb_new).query(primary_loop_pts)
    base_seam = primary_loop_pts[d_to_patch < SEAM_NEAR_M]
    d_to_base, _ = cKDTree(base_seam).query(pb_new)
    mask = d_to_base < SEAM_NEAR_M
    patch_seam = pb_new[mask]
    patch_seam_vids = pb_vids[mask]
    bridges = d_to_base[mask]
    nonprot = ~prot[patch_seam_vids]
    if int(nonprot.sum()) <= 20 or len(base_seam) <= 10:
        raise RuntimeError(
            f"{tag}: seam too sparse nonprot={int(nonprot.sum())} base={len(base_seam)}"
        )

    p2b = dist_stats_from_d(bridges[nonprot])
    b2, _ = cKDTree(patch_seam[nonprot]).query(base_seam)
    b2p = dist_stats_from_d(b2)

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
    rejection = []
    if p2b["p90_mm"] > GATE_P90_M * 1000:
        rejection.append(f"p2b_p90={p2b['p90_mm']:.4f}>3")
    if p2b["max_mm"] > GATE_MAX_M * 1000:
        rejection.append(f"p2b_max={p2b['max_mm']:.4f}>5")
    if p2b["coverage_le_3mm"] < GATE_COV:
        rejection.append(f"p2b_cov3={p2b['coverage_le_3mm']:.4f}<0.9")
    if b2p["p90_mm"] > GATE_P90_M * 1000:
        rejection.append(f"b2p_p90={b2p['p90_mm']:.4f}>3")
    if b2p["max_mm"] > GATE_MAX_M * 1000:
        rejection.append(f"b2p_max={b2p['max_mm']:.4f}>5")

    preview = trimesh.util.concatenate([base_cut, patch])
    preview.export(preview_path)
    scene = trimesh.Scene()
    scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
    scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
    scene.export(scene_path)

    report = {
        "tag": tag,
        "version": "dry_splice_roi_v4_logic_on_v5_registration",
        "preview": str(preview_path),
        "scene": str(scene_path),
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
        "kept_components": kept_comp_meta[:20],
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
        "stitch_gates": {"p90_mm": 3.0, "max_mm": 5.0, "coverage_le_3mm": 0.9},
        "stitch_gates_would_pass": stitch_gate_pass,
        "stitch_rejection_reasons": rejection,
        "topology_fusion_performed": False,
        "production_accepted": False,
    }
    arm_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    auto = json.loads(AUTO_ROI_JSON.read_text(encoding="utf-8"))
    auto_crop = np.array(auto["proposal_normalized_xyxy"], dtype=np.float64)

    base = trimesh.load(BASE_PATH, force="mesh", process=False)
    detail = trimesh.load(DETAIL_SRC_PATH, force="mesh", process=False)
    target = deterministic_surface_target(base, TARGET_SAMPLE_COUNT)

    fixed_mesh, fixed_reg = register_with_crop(base, detail, target, FIXED_CROP, "fixed")
    auto_mesh, auto_reg = register_with_crop(base, detail, target, auto_crop, "autoroiv3")

    fixed_splice = dry_splice_roiv4(base, fixed_mesh, "fixed")
    auto_splice = dry_splice_roiv4(base, auto_mesh, "autoroiv3")

    def seam_delta(a, b, key):
        if a.get(key) is None or b.get(key) is None:
            return None
        return float(a[key] - b[key])

    comparison = {
        "auto_minus_fixed_p2b_p90_mm": seam_delta(
            auto_splice, fixed_splice, "patch_to_base_boundary_p90_mm"
        ),
        "auto_minus_fixed_p2b_max_mm": seam_delta(
            auto_splice, fixed_splice, "patch_to_base_boundary_max_mm"
        ),
        "auto_minus_fixed_b2p_p90_mm": seam_delta(
            auto_splice, fixed_splice, "base_to_patch_boundary_p90_mm"
        ),
        "auto_minus_fixed_b2p_max_mm": seam_delta(
            auto_splice, fixed_splice, "base_to_patch_boundary_max_mm"
        ),
        "auto_minus_fixed_cov3": seam_delta(
            auto_splice, fixed_splice, "patch_to_base_coverage_le_3mm"
        ),
        "auto_helps_seam": bool(
            auto_splice["patch_to_base_boundary_p90_mm"]
            < fixed_splice["patch_to_base_boundary_p90_mm"]
            and auto_splice["base_to_patch_boundary_p90_mm"]
            < fixed_splice["base_to_patch_boundary_p90_mm"]
        ),
        "either_stitch_ready": bool(
            fixed_splice["stitch_gates_would_pass"] or auto_splice["stitch_gates_would_pass"]
        ),
    }

    report = {
        "scope": (
            "mechanical-bust fixture; densified register fixed vs Auto-ROI v3 then "
            "dry-splice ROI-v4 A/B; Grok-owned; no ChatGPT file edits; no weld"
        ),
        "version": "dry_splice_bust_detail_v5_autoroiv3",
        "auto_roi_source": str(AUTO_ROI_JSON),
        "auto_roi_proposal_normalized_xyxy": auto_crop.tolist(),
        "fixed_crop_normalized_xyxy": FIXED_CROP.tolist(),
        "registration": {"fixed": fixed_reg, "autoroiv3": auto_reg},
        "dry_splice": {"fixed": fixed_splice, "autoroiv3": auto_splice},
        "comparison": comparison,
        "stitch_gates": {"p90_mm": 3.0, "max_mm": 5.0, "coverage_le_3mm": 0.9},
        "topology_fusion_performed": False,
        "production_accepted": False,
        "note": (
            "Same ROI-v4 cut/snap/orphan-drop parameters on both arms. "
            "Auto crop loaded from auto_roi_bust_v3.json (no inference re-run)."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
