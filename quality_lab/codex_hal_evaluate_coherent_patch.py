"""HAL gate evaluation for the coherent patch-boundary arm.

Dry-splices the coherent patch onto the whole-bust base (no weld). Measures the
NEW seam loop only, including reverse coverage and protected-lens vertices on
the seam BEFORE exclusion. Compares against the smoother remeshed head lineage
(e191f9b8), not the torn native export. Does not widen thresholds or raise snaps.
production_accepted remains false. No topology/UV/texture/scale/second-fixture.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from codex_splice_boundary_audit import audit

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
OUT = Path("../quality_runs/headprobe_coherent_patch_hal")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
PATCH_PATH = Path("../quality_runs/headprobe_coherent_patch_boundary/coherent_patch.glb")
PATCH_REPORT = Path("../quality_runs/headprobe_coherent_patch_boundary/report.json")
SMOOTHER_HEAD = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"
SMOOTHER_CLAY = Path("../quality_runs/trellis_headprobe_full_clay")

# Existing conservative caps — do NOT raise.
PATCH_SURFACE_KEEP_M = 0.007
CUT_SURFACE_DIST_M = 0.003
CUT_RIM_EXCLUDE_M = 0.001
SEAM_NEAR_M = 0.008
SNAP_SURFACE_MAX_M = 0.003
SNAP_SEAM_MAX_M = 0.003
LOOP_MED_MAX_MM = 3.0
LOOP_P90_MAX_MM = 6.0
PROTECTED_MOVE_EPS_M = 1e-9
GATE_P90_MM = 3.0
GATE_MAX_MM = 5.0
GATE_COV = 0.90


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_lens_roi(v: np.ndarray) -> np.ndarray:
    return (
        (np.abs(v[:, 0]) < 0.048)
        & (v[:, 1] > 0.100)
        & (v[:, 1] < 0.172)
        & (v[:, 2] > 0.0)
    )


def patch_roi_box(v: np.ndarray) -> np.ndarray:
    return (
        (np.abs(v[:, 0]) < 0.066)
        & (v[:, 1] > 0.090)
        & (v[:, 1] < 0.183)
        & (v[:, 2] > -0.010)
    )


def boundary_edges(mesh: trimesh.Trimesh) -> np.ndarray:
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.sort(np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    return unique[counts == 1]


def boundary_vertices(mesh: trimesh.Trimesh):
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
        comps.append(np.asarray(edges, dtype=np.int64))
    comps.sort(key=len, reverse=True)
    return comps


def dist_stats(d):
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


def face_component_count(mesh: trimesh.Trimesh) -> int:
    faces = np.asarray(mesh.faces, dtype=np.int64)
    if len(faces) == 0:
        return 0
    edges = np.sort(
        np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])),
        axis=1,
    )
    # Face adjacency via shared edges (count==2).
    # Map edge -> faces
    from collections import defaultdict as dd

    e2f = dd(list)
    for fi in range(len(faces)):
        for a, b in (
            (int(faces[fi, 0]), int(faces[fi, 1])),
            (int(faces[fi, 1]), int(faces[fi, 2])),
            (int(faces[fi, 2]), int(faces[fi, 0])),
        ):
            if a > b:
                a, b = b, a
            e2f[(a, b)].append(fi)
    rows, cols = [], []
    for flist in e2f.values():
        if len(flist) == 2:
            a, b = flist
            rows.extend([a, b])
            cols.extend([b, a])
    if not rows:
        return int(len(faces) > 0)
    graph = coo_matrix(
        (np.ones(len(rows)), (rows, cols)), shape=(len(faces), len(faces))
    ).tocsr()
    n, _ = connected_components(graph)
    return int(n)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)
    hashes = {
        "base": sha256(BASE_PATH),
        "patch": sha256(PATCH_PATH),
        "smoother_head_e191f9b8": sha256(SMOOTHER_HEAD),
    }
    assert hashes["smoother_head_e191f9b8"] == (
        "e191f9b8e3f0b874c2a92ba92f7ca1b68bd4d4ef393c7a7a165e64829cfd3783"
    ), hashes["smoother_head_e191f9b8"]

    patch_meta = json.loads(PATCH_REPORT.read_text(encoding="utf-8"))
    base = trimesh.load(BASE_PATH, force="mesh", process=False)
    patch_src = trimesh.load(PATCH_PATH, force="mesh", process=False)
    base_comps_before = face_component_count(base)

    bv = np.asarray(base.vertices, dtype=np.float64)
    bf = np.asarray(base.faces, dtype=np.int64)
    pv = np.asarray(patch_src.vertices, dtype=np.float64).copy()
    pf = np.asarray(patch_src.faces, dtype=np.int64)

    base_open, _ = boundary_vertices(base)
    # Patch already is a cut surface; treat its existing boundary as "prior open"
    # so "new" vs prior is about base cut. For patch seam we use all patch boundary.
    base_open_tree = cKDTree(base_open) if len(base_open) else cKDTree([[1e9, 1e9, 1e9]])
    base_surface_tree = cKDTree(bv)

    patch = trimesh.Trimesh(pv, pf, process=False)
    prot = protected_lens_roi(pv)
    pv_before = pv.copy()
    normals_before = patch.face_normals.copy()

    pb_pts, pb_vids = boundary_vertices(patch)

    # Surface snap (capped) — non-protected only.
    snap_ids = pb_vids[~prot[pb_vids]] if len(pb_vids) else np.array([], dtype=np.int64)
    if len(snap_ids):
        _, nn_i = base_surface_tree.query(pv[snap_ids])
        delta = bv[nn_i] - pv[snap_ids]
        dn = np.linalg.norm(delta, axis=1)
        scale = np.minimum(1.0, SNAP_SURFACE_MAX_M / np.maximum(dn, 1e-12))
        pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
        patch.vertices = pv
        pb_pts, pb_vids = boundary_vertices(patch)

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
        if loose.any() and len(pv_local):
            d_surf[loose], _ = patch_tree.query(cents[loose])
        if loose.any() and len(pb_local):
            d_bound[loose], _ = pb_tree.query(cents[loose])
        return loose & (d_surf < CUT_SURFACE_DIST_M) & (d_bound > CUT_RIM_EXCLUDE_M)

    cut_roi = make_cut(pv, pb_pts)
    if int(cut_roi.sum()) < 50:
        # Still produce report FAIL rather than crash — cut too small.
        cut_too_small = True
        base_cut = base.copy()
        Vcut = bv
        be_new = np.empty((0, 2), dtype=np.int64)
        comps = []
        primary_vids = np.array([], dtype=np.int64)
        primary_loop_pts = np.empty((0, 3), dtype=np.float64)
        kept_comp_meta = []
        orphan_verts = 0
    else:
        cut_too_small = False
        base_cut = base.submesh([~cut_roi], append=True, repair=False)
        Vcut = np.asarray(base_cut.vertices, dtype=np.float64)
        be_new = new_boundary_edges(base_cut, base_open_tree)
        comps = connected_edge_components(be_new)
        pb_tree = cKDTree(pb_pts) if len(pb_pts) else cKDTree([[1e9, 1e9, 1e9]])
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
        if kept_vids:
            primary_vids = np.unique(np.concatenate(kept_vids))
            primary_loop_pts = Vcut[primary_vids]
        else:
            primary_vids = np.array([], dtype=np.int64)
            primary_loop_pts = np.empty((0, 3), dtype=np.float64)

    # Lateral snap toward primary loop (capped), non-protected only.
    snap_seam_moved_max_m = 0.0
    if len(primary_loop_pts) and len(pb_vids):
        snap_ids = pb_vids[~prot[pb_vids]]
        if len(snap_ids):
            _, nn_i = cKDTree(primary_loop_pts).query(pv[snap_ids])
            delta = primary_loop_pts[nn_i] - pv[snap_ids]
            dn = np.linalg.norm(delta, axis=1)
            scale = np.minimum(1.0, SNAP_SEAM_MAX_M / np.maximum(dn, 1e-12))
            snap_seam_moved_max_m = float((dn * scale).max()) if len(dn) else 0.0
            pv[snap_ids] = pv[snap_ids] + delta * scale[:, None]
            patch.vertices = pv
            pb_pts, pb_vids = boundary_vertices(patch)

    protected_move_max_m = (
        float(np.linalg.norm(pv[prot] - pv_before[prot], axis=1).max())
        if prot.any()
        else 0.0
    )

    # Normals after snap (same faces).
    patch_after = trimesh.Trimesh(pv, pf, process=False)
    normals_after = patch_after.face_normals.copy()
    # Guard length mismatch if winding issues
    n = min(len(normals_before), len(normals_after))
    dots = np.sum(normals_before[:n] * normals_after[:n], axis=1)
    flipped = int((dots < 0).sum())

    # Seam metrics — include protected BEFORE filtering.
    if len(primary_loop_pts) and len(pb_pts):
        d_to_patch, _ = cKDTree(pb_pts).query(primary_loop_pts)
        base_seam = primary_loop_pts[d_to_patch < SEAM_NEAR_M]
        d_to_base, _ = cKDTree(base_seam).query(pb_pts) if len(base_seam) else (
            np.full(len(pb_pts), np.inf),
            None,
        )
        mask = d_to_base < SEAM_NEAR_M
        patch_seam = pb_pts[mask]
        patch_seam_vids = pb_vids[mask]
        bridges = d_to_base[mask]
        prot_on_seam_before = patch_seam_vids[prot[patch_seam_vids]]
        nonprot = ~prot[patch_seam_vids]
        p2b_all = dist_stats(bridges)
        p2b_nonprot = dist_stats(bridges[nonprot]) if nonprot.any() else dist_stats([])
        if len(base_seam) and nonprot.any():
            b2, _ = cKDTree(patch_seam[nonprot]).query(base_seam)
            b2p = dist_stats(b2)
        elif len(base_seam) and len(patch_seam):
            b2, _ = cKDTree(patch_seam).query(base_seam)
            b2p = dist_stats(b2)
        else:
            b2p = dist_stats([])
        # Reverse coverage always on full near-seam sets (before protected drop).
        if len(base_seam) and len(patch_seam):
            b2_all, _ = cKDTree(patch_seam).query(base_seam)
            b2p_all = dist_stats(b2_all)
            p2_all2, _ = cKDTree(base_seam).query(patch_seam)
            p2b_all2 = dist_stats(p2_all2)
        else:
            b2p_all = dist_stats([])
            p2b_all2 = dist_stats([])
    else:
        base_seam = np.empty((0, 3))
        patch_seam = np.empty((0, 3))
        patch_seam_vids = np.array([], dtype=np.int64)
        prot_on_seam_before = np.array([], dtype=np.int64)
        nonprot = np.array([], dtype=bool)
        p2b_all = p2b_nonprot = b2p = b2p_all = p2b_all2 = dist_stats([])

    # Export seam loop artifact (path + hash for Issue #1).
    seam_npz = OUT / "new_seam_loop.npz"
    np.savez_compressed(
        seam_npz,
        primary_loop_points_m=primary_loop_pts,
        primary_vids=primary_vids,
        patch_seam_points_m=patch_seam,
        patch_seam_vids=patch_seam_vids,
        protected_on_seam_vids_before_filter=prot_on_seam_before,
    )
    # Also write a thin line GLB for visual/hash of geometry bytes of the loop.
    if len(primary_loop_pts) >= 2:
        # Encode loop as degenerate triangle soup of consecutive segments via
        # tiny ribbons is overkill; export point cloud mesh with zero faces for hash.
        seam_mesh = trimesh.Trimesh(
            vertices=primary_loop_pts,
            faces=np.zeros((0, 3), dtype=np.int64),
            process=False,
        )
        # trimesh may reject empty faces; write ply points instead.
        seam_ply = OUT / "new_seam_loop_points.ply"
        seam_ply.write_text(
            "ply\nformat ascii 1.0\nelement vertex %d\nproperty float x\n"
            "property float y\nproperty float z\nend_header\n"
            % len(primary_loop_pts)
            + "\n".join("%.9f %.9f %.9f" % tuple(p) for p in primary_loop_pts)
            + "\n",
            encoding="utf-8",
        )
        seam_mesh_path = seam_ply
    else:
        seam_mesh_path = seam_npz
    seam_loop_sha = sha256(seam_mesh_path)

    # Preview scene (disconnected dry splice — no weld).
    preview = trimesh.util.concatenate([base_cut, patch])
    preview_path = OUT / "dry_splice_preview.glb"
    preview.export(preview_path)
    scene = trimesh.Scene()
    scene.add_geometry(base_cut, geom_name="base_cut", node_name="base_cut")
    scene.add_geometry(patch, geom_name="detail_patch", node_name="detail_patch")
    scene_path = OUT / "dry_splice_scene.glb"
    scene.export(scene_path)
    patch.export(OUT / "patch_after_snap.glb", include_normals=True)

    preview_comps = face_component_count(preview)
    # New component vs base alone: preview should be base_cut components + patch components.
    base_cut_comps = face_component_count(base_cut)
    patch_comps = face_component_count(patch)
    # "No new connected component" for stitch preparation means the preparation
    # itself should not shatter the mesh into extras beyond the intentional
    # disconnected dry-splice (base_cut + patch = 2 intentional pieces if each
    # is one component). Flag growth beyond that.
    intentional_parts = base_cut_comps + patch_comps
    new_component_violation = bool(preview_comps > intentional_parts or patch_comps > 1)

    # HAL seam checks (one miss = FAIL). Use bidirectional ALL-sample coverage
    # (before protected exclusion) as required by steering; also report nonprot.
    seam_checks = {
        "p2b_p90_mm_le_3": bool(
            p2b_all2.get("p90_mm") is not None and p2b_all2["p90_mm"] <= GATE_P90_MM
        ),
        "p2b_max_mm_le_5": bool(
            p2b_all2.get("max_mm") is not None and p2b_all2["max_mm"] <= GATE_MAX_MM
        ),
        "b2p_p90_mm_le_3": bool(
            b2p_all.get("p90_mm") is not None and b2p_all["p90_mm"] <= GATE_P90_MM
        ),
        "b2p_max_mm_le_5": bool(
            b2p_all.get("max_mm") is not None and b2p_all["max_mm"] <= GATE_MAX_MM
        ),
        "p2b_coverage_le_3mm_ge_0_90": bool(
            p2b_all2.get("coverage_le_3mm") is not None
            and p2b_all2["coverage_le_3mm"] >= GATE_COV
        ),
        "b2p_coverage_le_3mm_ge_0_90": bool(
            b2p_all.get("coverage_le_3mm") is not None
            and b2p_all["coverage_le_3mm"] >= GATE_COV
        ),
        "protected_on_seam_before_filter_eq_0": bool(len(prot_on_seam_before) == 0),
        "protected_move_max_m_eq_0": bool(protected_move_max_m <= PROTECTED_MOVE_EPS_M),
        "no_new_flipped_normals": bool(flipped == 0),
        "no_new_connected_component": bool(not new_component_violation),
        "cut_not_too_small": bool(not cut_too_small),
        "primary_loop_present": bool(len(primary_loop_pts) > 0),
    }
    seam_pass = all(seam_checks.values())

    # Coherence of source patch (from prior report) — informational for HAL.
    coherence_passed = bool(patch_meta.get("coherence_gate", {}).get("passed"))

    # Whole-bust visual gate is filled after Blender inspection / left pending.
    visual_gate = {
        "required": [
            "three lenses front",
            "three lenses 3/4",
            "no double hood",
            "no floating shell",
            "silhouette outside ROI stable",
            "hose/grill outside ROI not worse vs smoother-head baseline context",
        ],
        "compare_against": {
            "smoother_head_sha256": hashes["smoother_head_e191f9b8"],
            "smoother_clay_dir": str(SMOOTHER_CLAY.resolve()),
            "do_not_use_torn_native_as_base": True,
        },
        "pending_blender_renders": True,
        "passed": None,
        "notes": "Filled after independent clay front/+35 of dry_splice_preview.glb",
    }

    rejection = [k for k, v in seam_checks.items() if not v]
    if not coherence_passed:
        rejection.append("source_patch_coherence_gate_failed")

    # Old v5 numbers recorded as already-FAIL control (do not count as this arm).
    old_v5_control = {
        "note": "Prior auto-ROI v5 dry-splice already FAIL; not this arm's result",
        "p2b_p90_mm": 4.400,
        "b2p_p90_mm": 4.015,
        "p2b_max_mm": 7.926,
        "b2p_max_mm": 6.148,
        "p2b_cov3": 0.835,
        "b2p_cov3": 0.785,
        "verdict": "FAIL",
    }

    overall = {
        "seam_gate_passed": seam_pass,
        "visual_gate_passed": None,
        "coherence_gate_passed": coherence_passed,
        "hal_pass": False,  # requires BOTH seam and visual; visual pending
        "one_miss_equals_fail": True,
    }

    report = {
        "scope": (
            "HAL evaluation of coherent patch-boundary arm on smoother remeshed "
            "head lineage e191f9b8 / fan-repair registered crop. No weld, no "
            "threshold widening, no snap raise, no UV/texture/scale/second fixture."
        ),
        "source_hashes": hashes,
        "patch_boundary_report": str(PATCH_REPORT.resolve()),
        "patch_topology_at_source": patch_meta.get("hop_sweep", {}).get("selected_topology"),
        "coherence_gate_at_source": patch_meta.get("coherence_gate"),
        "cut": {
            "base_faces_removed": int(cut_roi.sum()) if not cut_too_small else 0,
            "cut_too_small": cut_too_small,
            "new_boundary_components_total": int(len(comps)),
            "primary_loop_components_kept": int(len(kept_comp_meta)),
            "primary_loop_vertices": int(len(primary_vids)),
            "orphan_component_vertices_dropped": int(orphan_verts),
            "kept_components": kept_comp_meta[:20],
        },
        "seam_metrics_before_protected_filter": {
            "patch_to_base": p2b_all2,
            "base_to_patch": b2p_all,
            "protected_on_seam_vertex_count": int(len(prot_on_seam_before)),
            "protected_on_seam_vids_sample": prot_on_seam_before[:32].tolist(),
        },
        "seam_metrics_nonprot_only": {
            "patch_to_base": p2b_nonprot,
            "base_to_patch": b2p,
            "note": "Reported for continuity with older scripts; HAL uses before-filter",
        },
        "protected_move_max_m": protected_move_max_m,
        "snap_seam_moved_max_m": snap_seam_moved_max_m,
        "flipped_normals_vs_pre_snap": flipped,
        "components": {
            "base_before": base_comps_before,
            "base_cut": base_cut_comps,
            "patch": patch_comps,
            "preview": preview_comps,
            "new_component_violation": new_component_violation,
        },
        "seam_checks": seam_checks,
        "seam_rejection_reasons": rejection,
        "old_v5_already_fail_control": old_v5_control,
        "visual_gate": visual_gate,
        "overall": overall,
        "seam_loop_artifact": {
            "path": str(Path(seam_mesh_path).resolve()),
            "sha256": seam_loop_sha,
            "npz_path": str(seam_npz.resolve()),
            "npz_sha256": sha256(seam_npz),
            "primary_loop_point_count": int(len(primary_loop_pts)),
        },
        "outputs": {
            "preview": str(preview_path.resolve()),
            "scene": str(scene_path.resolve()),
            "patch_after_snap": str((OUT / "patch_after_snap.glb").resolve()),
        },
        "topology_fusion_performed": False,
        "thresholds_widened": False,
        "snaps_raised": False,
        "production_accepted": False,
        "studio_defaults_changed": False,
    }

    for label, path in [
        ("base", BASE_PATH),
        ("patch", PATCH_PATH),
        ("smoother", SMOOTHER_HEAD),
    ]:
        assert sha256(path) == hashes[
            "base" if label == "base" else "patch" if label == "patch" else "smoother_head_e191f9b8"
        ]

    (OUT / "hal_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(
        "HAL_SEAM_DONE",
        "seam_pass=" + str(seam_pass),
        "seam_loop_sha=" + seam_loop_sha,
        "seam_loop_path=" + str(Path(seam_mesh_path).resolve()),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
