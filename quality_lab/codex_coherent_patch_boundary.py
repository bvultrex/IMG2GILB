"""Surface-connected coherent patch boundary on the smoother remeshed/improved head.

Unlike box-only crop (17 boundary components), grow face-adjacency from the
protected lens interior inside the historical outer fixture box, keep only the
seed-connected component, then sweep dual-graph hop radii to prefer a single
simple closed seam. No fusion, no Studio default, no warp revival.
production_accepted remains false. Torn native no-remesh export is a rejected
control and is not overwritten.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh

from codex_splice_boundary_audit import audit


ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
OUT = Path("../quality_runs/headprobe_coherent_patch_boundary")
HIST_SRC = ROOT / "trellis1024_direct_headprobe_100000_remesh512.glb"  # e191f9b8...
HIST_REG = ROOT / "detail_registered_v5_autoroiv3.glb"
# Fan-repaired voxel768 cleanup lineage (smoother than torn native).
IMPROVED = Path("../quality_runs/headprobe_fan_repair/candidate.glb")
# Rejected control (do not overwrite).
NATIVE_REJECTED = Path("../quality_runs/headprobe_native_standard/candidate.glb")


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def face_adjacency(faces: np.ndarray) -> list[list[int]]:
    edges = np.sort(
        np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])),
        axis=1,
    )
    edge_to_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    n = len(faces)
    for fi in range(n):
        for e in (
            (int(faces[fi, 0]), int(faces[fi, 1])),
            (int(faces[fi, 1]), int(faces[fi, 2])),
            (int(faces[fi, 2]), int(faces[fi, 0])),
        ):
            a, b = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            edge_to_faces[(a, b)].append(fi)
    adj: list[list[int]] = [[] for _ in range(n)]
    for faces_on_edge in edge_to_faces.values():
        if len(faces_on_edge) == 2:
            a, b = faces_on_edge
            adj[a].append(b)
            adj[b].append(a)
        elif len(faces_on_edge) > 2:
            # Nonmanifold: still allow hops among all incident faces.
            for i, a in enumerate(faces_on_edge):
                for b in faces_on_edge[i + 1 :]:
                    adj[a].append(b)
                    adj[b].append(a)
    return adj


def connected_keep_from_seeds(
    eligible: np.ndarray, seeds: np.ndarray, adj: list[list[int]]
) -> np.ndarray:
    keep = np.zeros(len(eligible), dtype=bool)
    q: deque[int] = deque()
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


def hop_distances_from_seeds(
    seeds: np.ndarray, eligible: np.ndarray, adj: list[list[int]]
) -> np.ndarray:
    dist = np.full(len(eligible), -1, dtype=np.int32)
    q: deque[int] = deque()
    for i in np.flatnonzero(seeds & eligible):
        dist[i] = 0
        q.append(int(i))
    while q:
        fi = q.popleft()
        d = int(dist[fi])
        for nb in adj[fi]:
            if eligible[nb] and dist[nb] < 0:
                dist[nb] = d + 1
                q.append(nb)
    return dist


def extract_patch(mesh: trimesh.Trimesh, face_mask: np.ndarray) -> trimesh.Trimesh:
    if int(face_mask.sum()) == 0:
        raise RuntimeError("empty patch mask")
    patch = mesh.submesh([face_mask], append=True, repair=False)
    return patch


def score_boundary(topo: dict) -> tuple:
    """Lower is better: prefer one simple closed loop, zero branches."""
    comps = int(topo.get("boundary_components") or 0)
    simple = int(topo.get("closed_simple_loops") or 0)
    branched = int(topo.get("branched_boundary_vertices") or 0)
    endpoints = int(topo.get("boundary_endpoints") or 0)
    nm = int(topo.get("nonmanifold_edges") or 0)
    # Primary goal: single simple closed loop.
    not_single = 0 if (comps == 1 and simple == 1) else 1
    return (not_single, comps, branched, endpoints, nm, -simple)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)

    hashes = {str(p): sha256(p) for p in [HIST_SRC, HIST_REG, IMPROVED]}
    if NATIVE_REJECTED.exists():
        hashes[str(NATIVE_REJECTED)] = sha256(NATIVE_REJECTED)

    hist_src = trimesh.load(HIST_SRC, force="mesh", process=False)
    hist_reg = trimesh.load(HIST_REG, force="mesh", process=False)
    assert np.array_equal(hist_src.faces, hist_reg.faces), "registration face mismatch"
    affine = np.linalg.lstsq(
        np.c_[hist_src.vertices, np.ones(len(hist_src.vertices))],
        hist_reg.vertices,
        rcond=None,
    )[0]
    transfer_err = float(
        np.linalg.norm(
            np.c_[hist_src.vertices, np.ones(len(hist_src.vertices))] @ affine
            - hist_reg.vertices,
            axis=1,
        ).max()
    )
    assert transfer_err < 1e-7, transfer_err

    mesh = trimesh.load(IMPROVED, force="mesh", process=False)
    matrix = np.eye(4)
    matrix[:3, :] = affine.T
    mesh.apply_transform(matrix)
    mesh.export(OUT / "registered_improved_head.glb", include_normals=True)

    v = np.asarray(mesh.vertices, dtype=np.float64)
    f = np.asarray(mesh.faces, dtype=np.int64)
    adj = face_adjacency(f)

    box_vert = patch_roi_box(v)
    prot_vert = protected_lens_roi(v)
    box_face = box_vert[f].all(axis=1)
    seed_face = prot_vert[f].all(axis=1)
    # Allow seeds that touch protected verts even if not all verts protected,
    # so lens interior is not eroded by the strict all-vert check alone.
    seed_face_soft = prot_vert[f].any(axis=1) & box_face
    seed_face = seed_face | seed_face_soft

    # Control A: historical box-only (fragmented; expected reject for coherence).
    box_only = extract_patch(mesh, box_face)
    box_only.export(OUT / "control_box_only_patch.glb", include_normals=True)
    box_topo = audit(box_only)

    # Control B: seed-connected within box, no hop limit.
    connected = connected_keep_from_seeds(box_face, seed_face, adj)
    connected_patch = extract_patch(mesh, connected)
    connected_patch.export(OUT / "connected_box_patch.glb", include_normals=True)
    connected_topo = audit(connected_patch)

    # Arm C: hop-radius sweep from seeds inside the box; pick best coherent seam.
    hops = hop_distances_from_seeds(seed_face, box_face, adj)
    reachable = hops >= 0
    max_hop = int(hops[reachable].max()) if reachable.any() else -1
    sweep = []
    best = None
    best_mask = None
    for radius in range(0, max_hop + 1):
        mask = (hops >= 0) & (hops <= radius)
        # Always force full seed set.
        mask = mask | seed_face
        # Drop unreachable fragments outside seed growth.
        mask = connected_keep_from_seeds(mask, seed_face, adj)
        if int(mask.sum()) == 0:
            continue
        patch = extract_patch(mesh, mask)
        topo = audit(patch)
        prot_kept = bool(prot_vert[f[mask]].any()) and bool(
            np.all(prot_vert[np.unique(f[seed_face])] <= True)
            or True
        )
        # Protected coverage: every protected vertex that lies in the box must
        # remain in the patch if it was seed-adjacent.
        prot_vids = np.flatnonzero(prot_vert & box_vert)
        patch_vids = np.unique(f[mask])
        prot_coverage = float(np.isin(prot_vids, patch_vids).mean()) if len(prot_vids) else 1.0
        entry = {
            "hop_radius": radius,
            "faces": int(mask.sum()),
            "topology": topo,
            "protected_vertex_coverage": prot_coverage,
            "score": list(score_boundary(topo)),
        }
        sweep.append(entry)
        # Require strong protected coverage before accepting a candidate.
        if prot_coverage < 0.999:
            continue
        key = (score_boundary(topo), -int(mask.sum()), radius)
        if best is None or key < best[0]:
            best = (key, radius, mask, topo, prot_coverage)
            best_mask = mask

    if best_mask is None:
        # Fallback: connected-in-box if sweep never covered protected verts.
        best_mask = connected
        best_topo = connected_topo
        best_radius = None
        best_prot = float(
            np.isin(
                np.flatnonzero(prot_vert & box_vert), np.unique(f[best_mask])
            ).mean()
        ) if (prot_vert & box_vert).any() else 1.0
    else:
        _, best_radius, best_mask, best_topo, best_prot = best

    best_patch = extract_patch(mesh, best_mask)
    best_patch.export(OUT / "coherent_patch.glb", include_normals=True)

    # Boundary loop stats for the chosen patch.
    be = np.sort(
        np.vstack(
            (
                best_patch.faces[:, [0, 1]],
                best_patch.faces[:, [1, 2]],
                best_patch.faces[:, [2, 0]],
            )
        ),
        axis=1,
    )
    unique_e, counts = np.unique(be, axis=0, return_counts=True)
    boundary = unique_e[counts == 1]
    boundary_len = int(len(boundary))

    coherent_gate = bool(
        best_topo.get("boundary_components") == 1
        and best_topo.get("closed_simple_loops") == 1
        and best_topo.get("branched_boundary_vertices", 0) == 0
        and best_topo.get("boundary_endpoints", 0) == 0
        and best_prot >= 0.999
    )

    report = {
        "scope": (
            "Coherent surface-connected patch boundary on smoother fan-repaired "
            "head (e191f9b8 remesh lineage via historical registration transfer). "
            "Box-only kept as fragmented control. Torn native no-remesh remains "
            "rejected control and was not modified. No fusion / Studio default."
        ),
        "source_hashes": hashes,
        "registration_transfer_max_error_m": transfer_err,
        "improved_head_sha256_pre_transform": hashes[str(IMPROVED)],
        "historical_remesh_sha256": hashes[str(HIST_SRC)],
        "controls": {
            "box_only": {
                "faces": int(len(box_only.faces)),
                "topology": box_topo,
                "note": "Historical AABB crop; fragmented seam expected",
            },
            "connected_in_box": {
                "faces": int(len(connected_patch.faces)),
                "topology": connected_topo,
                "seed_faces": int(seed_face.sum()),
                "eligible_box_faces": int(box_face.sum()),
            },
            "native_no_remesh_rejected": {
                "path": str(NATIVE_REJECTED.resolve()) if NATIVE_REJECTED.exists() else None,
                "sha256": hashes.get(str(NATIVE_REJECTED)),
                "verdict": "REJECT (torn hood/hoses; recorded in ceefe199)",
            },
        },
        "hop_sweep": {
            "max_reachable_hop": max_hop,
            "candidates_evaluated": len(sweep),
            "selected_hop_radius": best_radius,
            "selected_faces": int(best_mask.sum()),
            "selected_topology": best_topo,
            "selected_protected_vertex_coverage": best_prot,
            "selected_boundary_edges": boundary_len,
            "top_candidates": sorted(sweep, key=lambda e: tuple(e["score"]))[:8],
        },
        "coherence_gate": {
            "required": "1 boundary component, 1 closed simple loop, 0 branched, 0 endpoints, protected coverage >= 0.999",
            "passed": coherent_gate,
        },
        "outputs": {
            "registered_improved_head": str((OUT / "registered_improved_head.glb").resolve()),
            "coherent_patch": str((OUT / "coherent_patch.glb").resolve()),
            "control_box_only_patch": str((OUT / "control_box_only_patch.glb").resolve()),
            "connected_box_patch": str((OUT / "connected_box_patch.glb").resolve()),
        },
        "topology_fusion_performed": False,
        "production_accepted": False,
        "studio_defaults_changed": False,
        "next_if_pass": "Only if coherent_gate.passed: dry-splice readiness vs whole bust; still no weld until seam gates pass",
        "next_if_fail": "Inspect remaining branches / multi-loops; do not widen box or revive warp; consider local cut-loop simplification on this arm only",
    }

    # Source immutability checks.
    for p, h in hashes.items():
        assert sha256(Path(p)) == h, p

    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("COHERENT_PATCH_DONE", "gate=" + str(coherent_gate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
