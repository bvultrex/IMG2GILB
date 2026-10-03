"""face_iso transform controls: identity + known-translation.

Diagnose coordinate/ROI/warp path in apply_face_local_warp / landmark tx extract.
Does NOT re-run hybrid bake. Does NOT touch failed face_iso sidecars except NEW controls/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

# Import from checkout (authoritative patched copy)
ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
sys.path.insert(0, str(ROOT))
from project_hybrid_a3 import apply_face_local_warp, face_landmark_quality, face_center_translation, face_iso_extract_micro_delta  # noqa: E402

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513")
FACE_ISO = JOB / "quality_jump_face_iso"
HW = FACE_ISO / "hybrid_work"
OUT = FACE_ISO / "controls"
OUT.mkdir(parents=True, exist_ok=True)
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso\controls")
VIS.mkdir(parents=True, exist_ok=True)

# Also mirror under checkout docs folder for git visibility
DOC_CTRL = ROOT / "_face_iso_controls"
DOC_CTRL.mkdir(parents=True, exist_ok=True)


def load_rgba_png(p: Path) -> np.ndarray:
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(p)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    if img.shape[2] == 3:
        a = np.full(img.shape[:2] + (1,), 255, dtype=np.uint8)
        img = np.concatenate([img, a], axis=2)
    # BGRA -> RGBA
    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)


def to_bgr(rgba: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def maxabs(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.max(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def make_synthetic_rgba(h=512, w=512) -> tuple[np.ndarray, dict]:
    """Checker + colored markers so translation is measurable."""
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    # checker body
    for y in range(0, h, 32):
        for x in range(0, w, 32):
            if ((x // 32) + (y // 32)) % 2 == 0:
                rgba[y : y + 32, x : x + 32, :3] = (40, 40, 40)
            else:
                rgba[y : y + 32, x : x + 32, :3] = (200, 200, 200)
    rgba[:, :, 3] = 255
    # markers: red at (100,100), green at (300,150), blue at (200,300), cyan block at (120,380)
    markers = {
        "red": (100, 100),
        "green": (300, 150),
        "blue": (200, 300),
        "cyan_block_tl": (120, 380),
    }
    cv2.circle(rgba, markers["red"], 12, (255, 0, 0, 255), -1)
    cv2.circle(rgba, markers["green"], 12, (0, 255, 0, 255), -1)
    cv2.circle(rgba, markers["blue"], 12, (0, 0, 255, 255), -1)
    rgba[380:430, 120:220] = (0, 220, 220, 255)  # cyan collar-like block
    # face-ish ROI rectangle outline
    cv2.rectangle(rgba, (80, 60), (340, 340), (255, 255, 0, 255), 2)
    return rgba, markers


def find_color_peak(rgb: np.ndarray, color: str) -> tuple[int, int]:
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    if color == "red":
        score = r.astype(np.int16) - g.astype(np.int16) - b.astype(np.int16)
    elif color == "green":
        score = g.astype(np.int16) - r.astype(np.int16) - b.astype(np.int16)
    elif color == "blue":
        score = b.astype(np.int16) - r.astype(np.int16) - g.astype(np.int16)
    else:
        raise ValueError(color)
    idx = np.argmax(score)
    y, x = divmod(int(idx), rgb.shape[1])
    return x, y


def control_identity(rgba: np.ndarray, roi: tuple[int, int, int, int], tag: str) -> dict:
    delta = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    out = apply_face_local_warp(rgba, delta, roi, feather=24)
    # Interior of ROI (exclude feather pad roughly)
    x0, y0, x1, y1 = roi
    inset = 40
    xi0, yi0 = x0 + inset, y0 + inset
    xi1, yi1 = max(xi0 + 1, x1 - inset), max(yi0 + 1, y1 - inset)
    interior_mae = mae(out[yi0:yi1, xi0:xi1], rgba[yi0:yi1, xi0:xi1])
    full_mae = mae(out, rgba)
    full_max = maxabs(out, rgba)
    # Alpha channel must match (same transform)
    a_mae = mae(out[:, :, 3], rgba[:, :, 3])
    passed = full_max <= 1.0 and a_mae <= 0.5  # allow rounding
    cv2.imwrite(str(OUT / f"{tag}_identity_in.png"), to_bgr(rgba))
    cv2.imwrite(str(OUT / f"{tag}_identity_out.png"), to_bgr(out))
    diff = np.clip(np.abs(out.astype(np.float32) - rgba.astype(np.float32)) * 8, 0, 255).astype(np.uint8)
    cv2.imwrite(str(OUT / f"{tag}_identity_diffx8.png"), to_bgr(diff))
    for p in (VIS, DOC_CTRL):
        cv2.imwrite(str(p / f"{tag}_identity_diffx8.png"), to_bgr(diff))
    return {
        "name": f"{tag}_identity",
        "pass": bool(passed),
        "full_mae": full_mae,
        "full_maxabs": full_max,
        "interior_mae": interior_mae,
        "alpha_mae": a_mae,
        "roi": list(roi),
        "delta": delta.tolist(),
        "expect": "identity warp must leave RGBA unchanged (image+mask share transform; blend of identical = id)",
    }


def control_known_translation(
    rgba: np.ndarray,
    roi: tuple[int, int, int, int],
    dx: float,
    dy: float,
    tag: str,
    markers: dict | None = None,
) -> dict:
    delta = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)
    out = apply_face_local_warp(rgba, delta, roi, feather=24)
    # Full warp reference (no ROI blend) — image AND alpha
    full = cv2.warpAffine(rgba, delta, (rgba.shape[1], rgba.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    x0, y0, x1, y1 = roi
    inset = 48  # inside feather
    xi0, yi0 = x0 + inset, y0 + inset
    xi1, yi1 = max(xi0 + 1, x1 - inset), max(yi0 + 1, y1 - inset)
    interior_vs_full = mae(out[yi0:yi1, xi0:xi1], full[yi0:yi1, xi0:xi1])
    # Outside ROI (far from pad): should equal original
    outside = np.ones(rgba.shape[:2], dtype=bool)
    pad = 24 + 8 + 20
    outside[max(0, y0 - pad) : min(rgba.shape[0], y1 + pad), max(0, x0 - pad) : min(rgba.shape[1], x1 + pad)] = False
    if outside.any():
        outside_mae = mae(out[outside], rgba[outside])
    else:
        outside_mae = float("nan")
    # Alpha: interior of local warp must match full-warp alpha (same delta on A)
    alpha_interior_mae = mae(out[yi0:yi1, xi0:xi1, 3], full[yi0:yi1, xi0:xi1, 3])

    marker_results = {}
    if markers:
        for name, (mx, my) in markers.items():
            if name.endswith("_tl"):
                continue
            # Only test markers that land inside ROI after warp
            nx, ny = int(mx + dx), int(my + dy)
            if xi0 <= nx < xi1 and yi0 <= ny < yi1 and name in ("red", "green", "blue"):
                ox, oy = find_color_peak(out[:, :, :3], name)
                marker_results[name] = {
                    "src": [mx, my],
                    "expected": [nx, ny],
                    "observed_peak": [ox, oy],
                    "err_px": float(np.hypot(ox - nx, oy - ny)),
                }

    # Pass criteria:
    # 1) interior matches full warp (local warp applies same delta inside)
    # 2) outside matches original
    # 3) alpha shares transform
    # 4) markers (if any) within 2px
    marker_ok = all(v["err_px"] <= 2.0 for v in marker_results.values()) if marker_results else True
    passed = (
        interior_vs_full <= 2.0
        and (np.isnan(outside_mae) or outside_mae <= 1.0)
        and alpha_interior_mae <= 1.0
        and marker_ok
    )
    cv2.imwrite(str(OUT / f"{tag}_known_in.png"), to_bgr(rgba))
    cv2.imwrite(str(OUT / f"{tag}_known_out.png"), to_bgr(out))
    cv2.imwrite(str(OUT / f"{tag}_known_fullwarp.png"), to_bgr(full))
    # overlay arrows
    vis = to_bgr(out).copy()
    cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 255, 255), 2)
    cv2.putText(vis, f"dx={dx} dy={dy}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.imwrite(str(OUT / f"{tag}_known_vis.png"), vis)
    for p in (VIS, DOC_CTRL):
        cv2.imwrite(str(p / f"{tag}_known_vis.png"), vis)
        cv2.imwrite(str(p / f"{tag}_known_out.png"), to_bgr(out))

    return {
        "name": f"{tag}_known_translation",
        "pass": bool(passed),
        "dx": dx,
        "dy": dy,
        "roi": list(roi),
        "interior_vs_full_mae": interior_vs_full,
        "outside_mae": outside_mae,
        "alpha_interior_mae": alpha_interior_mae,
        "markers": marker_results,
        "expect": "inside ROI matches full warpAffine(delta); outside equals original; alpha same delta as RGB",
    }


def control_tx_extract_bug() -> dict:
    """Prove: stripping scaled similarity tx is wrong; fixed extractor uses center delta instead."""
    sk = np.array([[100, 100], [200, 100], [150, 160], [120, 200], [180, 200], [150, 220]], dtype=np.float32)
    true_scale = 1.09
    true_dx, true_dy = 5.0, 8.0
    pivot = np.array([256.0, 256.0], dtype=np.float32)
    dk = true_scale * (sk - pivot) + pivot + np.array([true_dx, true_dy], dtype=np.float32)
    M, _ = cv2.estimateAffinePartial2D(sk, dk, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    M = M.astype(np.float32)
    tx, ty = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    stripped = np.array([[1.0, 0.0, tx], [0.0, 1.0, ty]], dtype=np.float32)
    src_c = sk.mean(axis=0)
    dst_c = dk.mean(axis=0)
    center_dx = float(dst_c[0] - src_c[0])
    center_dy = float(dst_c[1] - src_c[1])
    ones = np.ones((len(sk), 1), dtype=np.float32)
    pred_stripped = (stripped @ np.concatenate([sk, ones], 1).T).T
    err_stripped = float(np.median(np.linalg.norm(pred_stripped - dk, axis=1)))
    pred_full = (M @ np.concatenate([sk, ones], 1).T).T
    err_full = float(np.median(np.linalg.norm(pred_full - dk, axis=1)))

    # Synthetic face_center M = true small shift (what detector bbox centers would give if no scale)
    # Use bbox-like extents around keypoints
    sb = [float(sk[:, 0].min()), float(sk[:, 1].min()), float(sk[:, 0].max()), float(sk[:, 1].max())]
    db = [float(dk[:, 0].min()), float(dk[:, 1].min()), float(dk[:, 0].max()), float(dk[:, 1].max())]
    fc_dx = ((db[0] + db[2]) * 0.5) - ((sb[0] + sb[2]) * 0.5)
    fc_dy = ((db[1] + db[3]) * 0.5) - ((sb[1] + sb[3]) * 0.5)
    face_center_M = np.array([[1.0, 0.0, fc_dx], [0.0, 1.0, fc_dy]], dtype=np.float32)
    landmark_meta = {"src_bbox": sb, "dst_bbox": db, "scale": scale, "dx": tx, "dy": ty}
    delta_fix, extract_meta = face_iso_extract_micro_delta(
        M, face_center_M=face_center_M, face_center_meta={"dx": fc_dx, "dy": fc_dy},
        landmark_meta=landmark_meta, max_t=24.0, scale_tol=0.02, agree_px=12.0,
    )
    assert delta_fix is not None, extract_meta
    # Fixed delta must be near face/bbox center shift, NOT near bogus stripped tx/ty
    fdx, fdy = float(delta_fix[0, 2]), float(delta_fix[1, 2])
    err_vs_center = float(np.hypot(fdx - center_dx, fdy - center_dy))
    err_vs_stripped = float(np.hypot(fdx - tx, fdy - ty))
    # Must NOT invent forehead-eye shift: |fixed| << |stripped| when scale!=1
    fixed_ok = (
        err_stripped > 3.0  # bug still demos
        and err_vs_center <= 3.0
        and err_vs_stripped > 10.0
        and abs(fdx) <= 24 and abs(fdy) <= 24
        and str(extract_meta.get("chosen", "")).startswith("face_iso_")
        and "scaled_sim" in str(extract_meta.get("chosen", "")) or "face_center" in str(extract_meta.get("chosen", "")) or "bbox_center" in str(extract_meta.get("chosen", ""))
    )
    # clarify fixed_ok boolean (avoid operator precedence pitfall)
    fixed_ok = (
        err_stripped > 3.0
        and err_vs_center <= 3.0
        and err_vs_stripped > 10.0
        and abs(fdx) <= 24
        and abs(fdy) <= 24
        and delta_fix is not None
        and (
            "scaled_sim" in str(extract_meta.get("chosen", ""))
            or "face_center" in str(extract_meta.get("chosen", ""))
            or "bbox_center" in str(extract_meta.get("chosen", ""))
        )
    )
    return {
        "name": "tx_extract_from_scaled_similarity",
        "pass": bool(fixed_ok),
        "true_scale": true_scale,
        "true_center_shift": [true_dx, true_dy],
        "estimated_scale": scale,
        "estimated_tx_ty": [tx, ty],
        "center_to_center_dx_dy": [center_dx, center_dy],
        "median_err_full_affine_px": err_full,
        "median_err_stripped_translation_px": err_stripped,
        "fixed_extract": {
            "dx_dy": [fdx, fdy],
            "err_vs_center_px": err_vs_center,
            "err_vs_stripped_px": err_vs_stripped,
            "meta": extract_meta,
        },
        "note": "OLD path stripped M[:,2] (FAIL). NEW face_iso_extract_micro_delta uses face/bbox center when scale!=1 (PASS).",
    }


def analyze_failed_run_meta() -> dict:
    summary = json.loads((FACE_ISO / "face_iso_summary.json").read_text(encoding="utf-8"))
    micro = summary["front_micro"]
    lq = micro["landmark_quality"]
    # Reconstruct applied delta
    dx, dy = float(lq["dx"]), float(lq["dy"])
    c = float(micro.get("clamp_scale", 1.0))
    applied = [dx * c, dy * c]
    face_center = None
    for step in micro.get("steps", []):
        if str(step.get("mode", "")).startswith("face_center"):
            face_center = step
            break
    # Live check on saved front_aligned vs front_baseline if present
    live = {}
    fa = HW / "front_aligned.png"
    fb = HW / "front_baseline.png"
    if fa.exists() and fb.exists():
        src = load_rgba_png(fa)
        # baseline may be RGB float-ish png
        dst_bgr = cv2.imread(str(fb), cv2.IMREAD_COLOR)
        dst_rgb = cv2.cvtColor(dst_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        src_rgb = src[:, :, :3].astype(np.float32) / 255.0
        q = face_landmark_quality(src_rgb, dst_rgb)
        Mc, mc = face_center_translation(src_rgb, dst_rgb)
        live = {
            "recomputed_landmark_quality": {k: v for k, v in q.items() if k != "affine"},
            "recomputed_face_center": mc,
            "face_center_M": None if Mc is None else Mc.tolist(),
        }
        if "affine" in q:
            Mq = np.array(q["affine"], dtype=np.float32)
            live["affine_scale"] = float(np.sqrt(Mq[0, 0] ** 2 + Mq[0, 1] ** 2))
            live["affine_rot_approx"] = [float(Mq[0, 1]), float(Mq[1, 0])]
            live["affine_tx_ty"] = [float(Mq[0, 2]), float(Mq[1, 2])]
            # center deltas from bboxes
            if q.get("src_bbox") and q.get("dst_bbox"):
                sb, db = q["src_bbox"], q["dst_bbox"]
                sc = [(sb[0] + sb[2]) * 0.5, (sb[1] + sb[3]) * 0.5]
                dc = [(db[0] + db[2]) * 0.5, (db[1] + db[3]) * 0.5]
                live["bbox_center_delta"] = [dc[0] - sc[0], dc[1] - sc[1]]
                # predicted tx if scale applied about origin vs about face center
                s = live["affine_scale"]
                live["naive_scale_induced_tx_ty_about_origin"] = [-(s - 1) * sc[0], -(s - 1) * sc[1]]
                live["center_delta_minus_scale_induced"] = [
                    live["affine_tx_ty"][0] - live["naive_scale_induced_tx_ty_about_origin"][0],
                    live["affine_tx_ty"][1] - live["naive_scale_induced_tx_ty_about_origin"][1],
                ]
    return {
        "chosen": micro.get("chosen"),
        "clamp_scale": micro.get("clamp_scale"),
        "landmark_dx_dy": [dx, dy],
        "applied_delta_dx_dy": applied,
        "landmark_scale": lq.get("scale"),
        "project_face": micro.get("project_face"),
        "weight_map": micro.get("weight_map"),
        "roi": micro.get("roi"),
        "weight_roi": micro.get("weight_roi"),
        "face_center_step": face_center,
        "iou_before_after": [micro.get("iou_before"), micro.get("iou_after")],
        "live_recompute": live,
        "hypothesis": (
            "Landmark partial-affine scale~1.09 produces large tx/ty; face_iso strips to translation "
            "and clamps to 48px, shifting face up-left into hair and pulling cyan collar into cheek via "
            "apply_face_local_warp ROI blend (warped interior + unwarped exterior = ghost fragments)."
        ),
    }


def main():
    results = {"controls": [], "failed_run": analyze_failed_run_meta()}

    # A) Synthetic identity + known translation
    syn, markers = make_synthetic_rgba()
    syn_roi = (80, 60, 340, 340)
    results["controls"].append(control_identity(syn, syn_roi, "synthetic"))
    results["controls"].append(
        control_known_translation(syn, syn_roi, dx=16.0, dy=-12.0, tag="synthetic", markers=markers)
    )
    results["controls"].append(control_tx_extract_bug())

    # B) Real front_aligned identity + known translation (if available)
    fa = HW / "front_aligned.png"
    if fa.exists():
        real = load_rgba_png(fa)
        # Use failed-run ROI
        roi = tuple(results["failed_run"]["roi"] or [905, 206, 1152, 468])
        results["controls"].append(control_identity(real, roi, "front_aligned"))
        results["controls"].append(
            control_known_translation(real, roi, dx=16.0, dy=0.0, tag="front_aligned", markers=None)
        )
        # Also replay the FAILED applied delta on front_aligned for visual smoking gun
        adx, ady = results["failed_run"]["applied_delta_dx_dy"]
        delta = np.array([[1.0, 0.0, adx], [0.0, 1.0, ady]], dtype=np.float32)
        replay = apply_face_local_warp(real, delta, roi, feather=24)
        cv2.imwrite(str(OUT / "front_aligned_replay_failed_delta.png"), to_bgr(replay))
        cv2.imwrite(str(VIS / "front_aligned_replay_failed_delta.png"), to_bgr(replay))
        cv2.imwrite(str(DOC_CTRL / "front_aligned_replay_failed_delta.png"), to_bgr(replay))
        # side-by-side crop face
        x0, y0, x1, y1 = roi
        pad = 40
        crop_in = real[max(0, y0 - pad) : y1 + pad, max(0, x0 - pad) : x1 + pad]
        crop_out = replay[max(0, y0 - pad) : y1 + pad, max(0, x0 - pad) : x1 + pad]
        sbs = np.concatenate([to_bgr(crop_in), to_bgr(crop_out)], axis=1)
        cv2.putText(sbs, "aligned IN", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.putText(sbs, f"replay dx={adx:.1f} dy={ady:.1f}", (crop_in.shape[1] + 20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        cv2.imwrite(str(OUT / "sbs_replay_failed_delta_face.png"), sbs)
        cv2.imwrite(str(VIS / "sbs_replay_failed_delta_face.png"), sbs)
        cv2.imwrite(str(DOC_CTRL / "sbs_replay_failed_delta_face.png"), sbs)
        results["replay_failed_delta"] = {
            "dx": adx,
            "dy": ady,
            "artifact": str(OUT / "sbs_replay_failed_delta_face.png"),
        }

    # Summary pass/fail
    results["all_ mechanial_pass"] = all(
        c.get("pass", False)
        for c in results["controls"]
        if c["name"] in ("synthetic_identity", "synthetic_known_translation", "front_aligned_identity", "front_aligned_known_translation")
    )
    # Fix typo key
    mech = [
        c
        for c in results["controls"]
        if c["name"]
        in (
            "synthetic_identity",
            "synthetic_known_translation",
            "front_aligned_identity",
            "front_aligned_known_translation",
        )
    ]
    results["mechanical_warp_pass"] = all(c.get("pass", False) for c in mech)
    results["tx_extract_control"] = next(c for c in results["controls"] if c["name"] == "tx_extract_from_scaled_similarity")
    results["verdict"] = (
        "MECHANICAL_WARP_OK_BUT_TX_EXTRACT_BUG"
        if results["mechanical_warp_pass"] and not results["tx_extract_control"]["pass"]
        else (
            "MECHANICAL_WARP_FAIL"
            if not results["mechanical_warp_pass"]
            else (
                "ALL_CONTROLS_PASS"
                if results["tx_extract_control"]["pass"]
                else "TX_EXTRACT_STILL_FAIL"
            )
        )
    )
    results.pop("all_ mechanial_pass", None)

    out_json = OUT / "control_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (DOC_CTRL / "control_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (VIS / "control_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": results["verdict"], "out": str(out_json), "n": len(results["controls"])}, indent=2))
    for c in results["controls"]:
        print(f"  [{('PASS' if c.get('pass') else 'FAIL'):4s}] {c['name']}")


if __name__ == "__main__":
    main()
