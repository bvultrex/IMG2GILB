"""One tighter seam on the same smoother head. No weld, no snap raise, no wider gates.

Precommitted rule (not a sweep):
  Start from the same ROI box and protected lens seeds as the failed coherent patch.
  Keep a face only if it is a protected seed OR every vertex is within 3.0 mm of the
  bust base surface (the coverage gate distance, not a looser 6 mm loop-keep).
  Grow only by face adjacency inside the unchanged box.
  Snap caps stay 3.0 mm. Thresholds stay p90<=3, max<=5, cov>=0.90.
  Measure both directions BEFORE dropping protected vertices.
  Failed HAL folder and torn native are not touched.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
OUT = Path(r"C:\Users\Shadow\Documents\ComfyUI\quality_runs\headprobe_tighter_seam")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
HEAD_REG = Path(
    r"C:\Users\Shadow\Documents\ComfyUI\quality_runs\headprobe_coherent_patch_boundary\registered_improved_head.glb"
)
OLD_PATCH = Path(
    r"C:\Users\Shadow\Documents\ComfyUI\quality_runs\headprobe_coherent_patch_boundary\coherent_patch.glb"
)
SMOOTHER_HEAD = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"
FAIL_CONTROL = Path(r"C:\Users\Shadow\Documents\ComfyUI\quality_runs\headprobe_coherent_patch_hal")

COLLAR_M = 0.003  # same as coverage gate; not raised
CUT_SURFACE_DIST_M = 0.003
CUT_RIM_EXCLUDE_M = 0.001
SEAM_NEAR_M = 0.008
SNAP_SURFACE_MAX_M = 0.003
SNAP_SEAM_MAX_M = 0.003
PROTECTED_MOVE_EPS_M = 1e-9
GATE_P90_MM = 3.0
GATE_MAX_MM = 5.0
GATE_COV = 0.90
# Same loose keep the FAIL control used, so the comparison is the boundary, not a new filter.
LOOP_MED_MAX_MM = 3.0
LOOP_P90_MAX_MM = 6.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def face_adjacency(faces):
    edge_to_faces = defaultdict(list)
    n = len(faces)
    for fi in range(n):
        for e in (
            (int(faces[fi, 0]), int(faces[fi, 1])),
            (int(faces[fi, 1]), int(faces[fi, 2])),
            (int(faces[fi, 2]), int(faces[fi, 0])),
        ):
            a, b = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            edge_to_faces[(a, b)].append(fi)
    adj = [[] for _ in range(n)]
    for faces_on_edge in edge_to_faces.values():
        if len(faces_on_edge) == 2:
            a, b = faces_on_edge
            adj[a].append(b)
            adj[b].append(a)
    return adj


def connected_keep_from_seeds(eligible, seeds, adj):
    keep = np.zeros(len(eligible), dtype=bool)
    q = deque()
    for i in np.flatnonzero(seeds & eligible):
        keep[i] = True
        q.append(int(i))
    while q:
        fi = q.popleft()
        for nb in adj[fi]:
            if eligible[nb] and not keep[nb]:
                keep[nb] = True
                q.append(nb)
    return keep


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


def face_component_count(mesh):
    faces = np.asarray(mesh.faces, dtype=np.int64)
    if len(faces) == 0:
        return 0
    e2f = defaultdict(list)
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
        return 1
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(faces), len(faces))).tocsr()
    n, _ = connected_components(graph)
    return int(n)


def surface_distance(base_mesh, pts, k=32):
    """Exact-enough point-to-mesh distance without rtree.

    k nearest triangle centroids, then point-triangle distance. If the k-th
    centroid is still inside best+max triangle radius, expand with a ball query.
    """
    from trimesh.triangles import closest_point

    pts = np.asarray(pts, dtype=np.float64)
    if len(pts) == 0:
        return np.empty((0,), dtype=np.float64)
    tris = np.asarray(base_mesh.triangles, dtype=np.float64)
    cents = tris.mean(axis=1)
    rad = np.linalg.norm(tris - cents[:, None, :], axis=2).max(axis=1)
    max_rad = float(rad.max()) if len(rad) else 0.0
    tree = cKDTree(cents)
    kk = min(k, len(tris))
    d_k, ix = tree.query(pts, k=kk)
    if kk == 1:
        d_k = d_k[:, None]
        ix = ix[:, None]
    best = np.empty(len(pts), dtype=np.float64)
    chunk = 1500
    for s in range(0, len(pts), chunk):
        e = min(len(pts), s + chunk)
        sel = ix[s:e]
        tri = tris[sel].reshape(-1, 3, 3)
        p = np.repeat(pts[s:e], kk, axis=0)
        cp = closest_point(tri, p)
        dist = np.linalg.norm(cp - p, axis=1).reshape(-1, kk)
        best[s:e] = dist.min(axis=1)
    kth = d_k[:, -1]
    missed = np.flatnonzero(kth < (best + max_rad + 1e-9))
    if len(missed):
        print("surface_distance expanding", int(len(missed)), "points", flush=True)
        for i in missed.tolist():
            cand = tree.query_ball_point(pts[i], float(best[i] + max_rad + 1e-8))
            if not cand:
                continue
            tri = tris[np.asarray(cand, dtype=np.int64)]
            p = np.repeat(pts[i:i + 1], len(cand), axis=0)
            cp = closest_point(tri, p)
            best[i] = float(np.linalg.norm(cp - p, axis=1).min())
    return best


def hist_mm(d):
    dmm = np.asarray(d, dtype=np.float64) * 1000.0
    if len(dmm) == 0:
        return {"n": 0}
    qs = [0, 10, 25, 50, 75, 90, 95, 99, 100]
    vals = np.percentile(dmm, qs)
    return {
        "n": int(len(dmm)),
        "percentiles_mm": {str(q): float(v) for q, v in zip(qs, vals)},
        "frac_le_3mm": float(np.mean(dmm <= 3.0)),
        "frac_le_2mm": float(np.mean(dmm <= 2.0)),
        "frac_gt_5mm": float(np.mean(dmm > 5.0)),
    }


def evaluate(base, patch_src, label):
    base_comps_before = face_component_count(base)
    bv = np.asarray(base.vertices, dtype=np.float64)
    bf = np.asarray(base.faces, dtype=np.int64)
    pv = np.asarray(patch_src.vertices, dtype=np.float64).copy()
    pf = np.asarray(patch_src.faces, dtype=np.int64)
    base_open, _ = boundary_vertices(base)
    base_open_tree = cKDTree(base_open) if len(base_open) else cKDTree([[1e9, 1e9, 1e9]])
    base_surface_tree = cKDTree(bv)
    patch = trimesh.Trimesh(pv, pf, process=False)
    prot = protected_lens_roi(pv)
    pv_before = pv.copy()
    normals_before = np.asarray(patch.face_normals, dtype=np.float64).copy()
    pb_pts, pb_vids = boundary_vertices(patch)
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
        pb_tree = cKDTree(pb_local) if len(pb_local) else None
        d_surf = np.full(len(cents), np.inf)
        d_bound = np.full(len(cents), np.inf)
        if loose.any() and len(pv_local):
            d_surf[loose], _ = patch_tree.query(cents[loose])
        if loose.any() and pb_tree is not None:
            d_bound[loose], _ = pb_tree.query(cents[loose])
        return loose & (d_surf < CUT_SURFACE_DIST_M) & (d_bound > CUT_RIM_EXCLUDE_M)

    cut_roi = make_cut(pv, pb_pts)
    if int(cut_roi.sum()) < 50:
        cut_too_small = True
        base_cut = base.copy()
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
        float(np.linalg.norm(pv[prot] - pv_before[prot], axis=1).max()) if prot.any() else 0.0
    )
    patch_after = trimesh.Trimesh(pv, pf, process=False)
    normals_after = np.asarray(patch_after.face_normals, dtype=np.float64)
    n = min(len(normals_before), len(normals_after))
    dots = np.sum(normals_before[:n] * normals_after[:n], axis=1)
    flipped = int((dots < 0).sum())

    if len(primary_loop_pts) and len(pb_pts):
        d_to_patch, _ = cKDTree(pb_pts).query(primary_loop_pts)
        base_seam = primary_loop_pts[d_to_patch < SEAM_NEAR_M]
        d_to_base, _ = (
            cKDTree(base_seam).query(pb_pts)
            if len(base_seam)
            else (np.full(len(pb_pts), np.inf), None)
        )
        mask = d_to_base < SEAM_NEAR_M
        patch_seam = pb_pts[mask]
        patch_seam_vids = pb_vids[mask]
        bridges = d_to_base[mask]
        prot_on_seam_before = patch_seam_vids[prot[patch_seam_vids]] if len(patch_seam_vids) else np.array([], dtype=np.int64)
        nonprot = ~prot[patch_seam_vids] if len(patch_seam_vids) else np.array([], dtype=bool)
        p2b_nonprot = dist_stats(bridges[nonprot]) if nonprot.any() else dist_stats([])
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
        p2b_nonprot = b2p_all = p2b_all2 = dist_stats([])

    preview = trimesh.util.concatenate([base_cut, patch_after])
    preview_comps = face_component_count(preview)
    base_cut_comps = face_component_count(base_cut)
    patch_comps = face_component_count(patch_after)
    new_component_violation = bool(preview_comps > (base_cut_comps + patch_comps) or patch_comps > 1)

    p2b = p2b_all2
    b2p = b2p_all
    checks = {
        "p2b_p90_mm_le_3": bool(p2b.get("p90_mm") is not None and p2b["p90_mm"] <= GATE_P90_MM),
        "p2b_max_mm_le_5": bool(p2b.get("max_mm") is not None and p2b["max_mm"] <= GATE_MAX_MM),
        "b2p_p90_mm_le_3": bool(b2p.get("p90_mm") is not None and b2p["p90_mm"] <= GATE_P90_MM),
        "b2p_max_mm_le_5": bool(b2p.get("max_mm") is not None and b2p["max_mm"] <= GATE_MAX_MM),
        "p2b_coverage_le_3mm_ge_0_90": bool(
            p2b.get("coverage_le_3mm") is not None and p2b["coverage_le_3mm"] >= GATE_COV
        ),
        "b2p_coverage_le_3mm_ge_0_90": bool(
            b2p.get("coverage_le_3mm") is not None and b2p["coverage_le_3mm"] >= GATE_COV
        ),
        "protected_on_seam_before_filter_eq_0": bool(len(prot_on_seam_before) == 0),
        "protected_move_max_m_le_1e-9": bool(protected_move_max_m <= PROTECTED_MOVE_EPS_M),
        "no_new_flipped_normals": bool(flipped == 0),
        "no_new_connected_component": bool(not new_component_violation),
        "cut_not_too_small": bool(not cut_too_small),
        "primary_loop_present": bool(len(primary_loop_pts) > 0),
    }
    return {
        "label": label,
        "patch_faces": int(len(pf)),
        "patch_boundary_vertices": int(len(pb_vids)),
        "cut_faces_removed": int(cut_roi.sum()) if not cut_too_small else 0,
        "cut_too_small": cut_too_small,
        "new_boundary_components_total": int(len(comps)),
        "primary_loop_components_kept": int(len(kept_comp_meta)),
        "primary_loop_vertices": int(len(primary_vids)),
        "orphan_component_vertices_dropped": int(orphan_verts),
        "kept_components_head": kept_comp_meta[:12],
        "patch_to_base": p2b,
        "base_to_patch": b2p,
        "protected_on_seam_before_exclusion": int(len(prot_on_seam_before)),
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
        "checks": checks,
        "seam_gate_passed": bool(all(checks.values())),
        "primary_loop_pts": primary_loop_pts,
        "patch_after": patch_after,
        "base_cut": base_cut,
        "preview": preview,
    }


def slim(result):
    skip = {"primary_loop_pts", "patch_after", "base_cut", "preview"}
    return {k: v for k, v in result.items() if k not in skip}


def main():
    if OUT.exists():
        raise SystemExit("refusing to overwrite " + str(OUT))
    head_sha = sha256(SMOOTHER_HEAD)
    assert head_sha == "e191f9b8e3f0b874c2a92ba92f7ca1b68bd4d4ef393c7a7a165e64829cfd3783", head_sha
    fail_ply = FAIL_CONTROL / "new_seam_loop_points.ply"
    fail_sha = sha256(fail_ply)

    base = trimesh.load(BASE_PATH, force="mesh", process=False)
    head = trimesh.load(HEAD_REG, force="mesh", process=False)
    v = np.asarray(head.vertices, dtype=np.float64)
    f = np.asarray(head.faces, dtype=np.int64)
    print("loaded", "base_faces", len(base.faces), "head_faces", len(f), flush=True)

    print("closest_point on head vertices...", flush=True)
    vdist = surface_distance(base, v)
    box_vert = patch_roi_box(v)
    prot_vert = protected_lens_roi(v)
    box_face = box_vert[f].all(axis=1)
    seed_face = prot_vert[f].any(axis=1) & box_face
    adj = face_adjacency(f)

    # Diagnostic: where does this head actually sit on the bust?
    box_vids = np.flatnonzero(box_vert)
    prot_vids = np.flatnonzero(prot_vert & box_vert)
    diag = {
        "box_vertex_distance_to_base_surface": hist_mm(vdist[box_vids]),
        "protected_vertex_distance_to_base_surface": hist_mm(vdist[prot_vids]),
        "box_faces": int(box_face.sum()),
        "seed_faces": int(seed_face.sum()),
        "protected_verts_in_box": int(len(prot_vids)),
    }
    fully_close = (vdist[f].max(axis=1) <= COLLAR_M) & box_face
    diag["box_faces_fully_within_3mm"] = int(fully_close.sum())
    diag["box_faces_fully_within_3mm_frac"] = float(fully_close.mean()) if len(fully_close) else 0.0
    # Boundary of the OLD box-connected patch: distance of those boundary verts.
    old = trimesh.load(OLD_PATCH, force="mesh", process=False)
    old_bpts, _ = boundary_vertices(old)
    old_bd = surface_distance(base, old_bpts)
    diag["old_patch_boundary_distance_to_base_surface"] = hist_mm(old_bd)
    print(json.dumps({"diagnostic": diag}, indent=2), flush=True)

    eligible = fully_close | seed_face
    mask = connected_keep_from_seeds(eligible, seed_face, adj)
    # Do not keep seed faces that fell outside the box.
    mask = mask & (box_face | seed_face)
    prot_coverage = float(np.isin(prot_vids, np.unique(f[mask])).mean()) if len(prot_vids) else 1.0
    if int(mask.sum()) == 0:
        raise SystemExit("tighter mask empty")
    patch = head.submesh([mask], append=True, repair=False)
    OUT.mkdir(parents=True, exist_ok=False)
    patch.export(OUT / "tighter_patch.glb", include_normals=True)

    # Boundary component count before snap, for coherence.
    be = boundary_edges(patch)
    bcomps = connected_edge_components(be)
    topo = {
        "faces": int(len(patch.faces)),
        "vertices": int(len(patch.vertices)),
        "boundary_edges": int(len(be)),
        "boundary_components": int(len(bcomps)),
        "largest_boundary_edges": int(len(bcomps[0])) if bcomps else 0,
        "protected_vertex_coverage": prot_coverage,
    }
    print(json.dumps({"tighter_topology_before_snap": topo}, indent=2), flush=True)

    print("evaluate tighter patch...", flush=True)
    result = evaluate(base, patch, "tighter_3mm_collar")
    # Persist artifacts from the tighter attempt only.
    result["preview"].export(OUT / "dry_splice_preview.glb")
    scene = trimesh.Scene()
    scene.add_geometry(result["base_cut"], geom_name="base_cut", node_name="base_cut")
    scene.add_geometry(result["patch_after"], geom_name="detail_patch", node_name="detail_patch")
    scene.export(OUT / "dry_splice_scene.glb")
    result["patch_after"].export(OUT / "patch_after_snap.glb", include_normals=True)
    pts = result["primary_loop_pts"]
    ply = OUT / "new_seam_loop_points.ply"
    if len(pts) >= 1:
        ply.write_text(
            "ply\nformat ascii 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\nend_header\n"
            % len(pts)
            + "\n".join("%.9f %.9f %.9f" % tuple(p) for p in pts)
            + "\n",
            encoding="utf-8",
        )
    else:
        ply.write_text("ply\nformat ascii 1.0\nelement vertex 0\nproperty float x\nproperty float y\nproperty float z\nend_header\n", encoding="utf-8")
    np.savez_compressed(OUT / "new_seam_loop.npz", primary_loop_points_m=pts)

    p2b = result["patch_to_base"]
    b2p = result["base_to_patch"]
    # FAIL control numbers (fixed, from hal_report, not re-filtered).
    fail = {
        "p2b_p90_mm": 5.5316071607224835,
        "p2b_cov": 0.75,
        "p2b_max_mm": 7.996877677993381,
        "b2p_p90_mm": 4.714441968136141,
        "b2p_cov": 0.7730061349693251,
        "b2p_max_mm": 6.2574967232274705,
        "protected_on_seam": 1,
        "flipped_normals": 274,
    }

    def closer(new_cov, new_p90, old_cov, old_p90):
        if new_cov is None or new_p90 is None:
            return False
        # Clearly closer: coverage up by >= 0.08 AND p90 down by >= 0.8 mm,
        # and not still sitting on the stop-rule (cov ~0.75 and p90 > 5).
        cov_gain = new_cov - old_cov
        p90_drop = old_p90 - new_p90
        still_bad = new_cov < 0.80 and new_p90 > 5.0
        return (not still_bad) and cov_gain >= 0.08 and p90_drop >= 0.8

    p2b_closer = closer(
        p2b.get("coverage_le_3mm"), p2b.get("p90_mm"), fail["p2b_cov"], fail["p2b_p90_mm"]
    )
    b2p_closer = closer(
        b2p.get("coverage_le_3mm"), b2p.get("p90_mm"), fail["b2p_cov"], fail["b2p_p90_mm"]
    )
    # Stop rule from Danny: if coverage still ~0.75 and p90 still >5, not promising.
    still_stop = (
        (p2b.get("coverage_le_3mm") is None or p2b.get("coverage_le_3mm") < 0.80)
        and (p2b.get("p90_mm") is None or p2b.get("p90_mm") > 5.0)
    ) or (
        (b2p.get("coverage_le_3mm") is None or b2p.get("coverage_le_3mm") < 0.80)
        and (b2p.get("p90_mm") is None or b2p.get("p90_mm") > 5.0)
        and (p2b.get("coverage_le_3mm") is None or p2b.get("coverage_le_3mm") < 0.85)
    )
    promising = bool(p2b_closer and b2p_closer and not still_stop and not result["cut_too_small"])

    report = {
        "scope": "One tighter-boundary attempt on the same smoother head. 3 mm surface collar inside the unchanged ROI box. No weld, snaps not raised, thresholds not widened.",
        "rule": "Face kept iff protected-lens seed OR all vertices within 3.0 mm of bust base surface, seed-connected, same box. Snap caps 3.0 mm.",
        "source_hashes": {
            "base": sha256(BASE_PATH),
            "registered_improved_head": sha256(HEAD_REG),
            "smoother_head_e191f9b8": head_sha,
            "old_coherent_patch": sha256(OLD_PATCH),
            "fail_control_seam_loop_c081bb9b": fail_sha,
        },
        "diagnostic": diag,
        "tighter_topology_before_snap": topo,
        "fail_control": fail,
        "tighter": slim(result),
        "comparison": {
            "p2b_closer": p2b_closer,
            "b2p_closer": b2p_closer,
            "still_on_stop_rule": still_stop,
            "promising": promising,
        },
        "visual_gate": {
            "ran": False,
            "reason": "Metric stop rule decides this one attempt. No Blender, no weld.",
        },
        "topology_fusion_performed": False,
        "thresholds_widened": False,
        "snaps_raised": False,
        "production_accepted": False,
        "studio_defaults_changed": False,
        "seam_loop_sha256": sha256(ply),
        "outputs": {
            "dir": str(OUT),
            "ply": str(ply),
            "preview": str(OUT / "dry_splice_preview.glb"),
        },
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print("TIGHTER_SEAM_DONE", "promising=" + str(promising), "sha=" + report["seam_loop_sha256"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
