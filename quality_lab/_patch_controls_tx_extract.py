"""Update tx_extract control to validate fixed face_iso_extract_micro_delta."""
from pathlib import Path

p = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\run_face_iso_transform_controls.py")
t = p.read_text(encoding="utf-8")

old_import = "from project_hybrid_a3 import apply_face_local_warp, face_landmark_quality, face_center_translation  # noqa: E402"
new_import = "from project_hybrid_a3 import apply_face_local_warp, face_landmark_quality, face_center_translation, face_iso_extract_micro_delta  # noqa: E402"
assert old_import in t
t = t.replace(old_import, new_import, 1)

# Point controls OUT to v2 controls folder under NEW sidecar after bake; for now keep under face_iso/controls
# but also write a fixed_extract check.

old_fn = '''def control_tx_extract_bug() -> dict:
    """Reproduce: similarity with scale!=1 yields large tx; stripping to translation is wrong vs center delta."""
    # Synthetic: src face markers at known places, dst = scale about origin-ish + small true shift
    h, w = 512, 512
    src = np.zeros((h, w, 3), dtype=np.float32)
    dst = np.zeros((h, w, 3), dtype=np.float32)
    # Not using detector — geometric proof with estimateAffinePartial2D directly
    sk = np.array([[100, 100], [200, 100], [150, 160], [120, 200], [180, 200], [150, 220]], dtype=np.float32)
    true_scale = 1.09
    true_dx, true_dy = 5.0, 8.0  # small real translation after scale about (0,0) for clarity
    # Actually similarity about image center is more realistic
    pivot = np.array([256.0, 256.0], dtype=np.float32)
    dk = true_scale * (sk - pivot) + pivot + np.array([true_dx, true_dy], dtype=np.float32)
    M, _ = cv2.estimateAffinePartial2D(sk, dk, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    M = M.astype(np.float32)
    tx, ty = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    # face_iso path: if rotation tiny, use pure translation (tx,ty) dropping scale
    stripped = np.array([[1.0, 0.0, tx], [0.0, 1.0, ty]], dtype=np.float32)
    # Correct center-to-center translation for already-aligned-ish faces:
    src_c = sk.mean(axis=0)
    dst_c = dk.mean(axis=0)
    center_dx = float(dst_c[0] - src_c[0])
    center_dy = float(dst_c[1] - src_c[1])
    # Error if we apply stripped translation to src keypoints vs true dst
    ones = np.ones((len(sk), 1), dtype=np.float32)
    pred_stripped = (stripped @ np.concatenate([sk, ones], 1).T).T
    err_stripped = float(np.median(np.linalg.norm(pred_stripped - dk, axis=1)))
    pred_full = (M @ np.concatenate([sk, ones], 1).T).T
    err_full = float(np.median(np.linalg.norm(pred_full - dk, axis=1)))
    # Also compare to face_center style
    return {
        "name": "tx_extract_from_scaled_similarity",
        "pass": err_stripped <= 3.0,  # expect FAIL when scale!=1
        "true_scale": true_scale,
        "true_center_shift": [true_dx, true_dy],
        "estimated_scale": scale,
        "estimated_tx_ty": [tx, ty],
        "center_to_center_dx_dy": [center_dx, center_dy],
        "median_err_full_affine_px": err_full,
        "median_err_stripped_translation_px": err_stripped,
        "note": "face_iso takes Mq tx/ty and applies as pure translation when |rot| small — drops scale. "
        "For scale~1.09 this invents ~-(s-1)*center translation (~tens of px), matching failed run dx~-65.",
    }
'''

new_fn = '''def control_tx_extract_bug() -> dict:
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
'''

assert old_fn in t, "old control_tx_extract_bug missing"
t = t.replace(old_fn, new_fn, 1)

# Update verdict logic: tx_extract should now PASS
old_verdict = '''    results["verdict"] = (
        "MECHANICAL_WARP_OK_BUT_TX_EXTRACT_BUG"
        if results["mechanical_warp_pass"] and not results["tx_extract_control"]["pass"]
        else (
            "MECHANICAL_WARP_FAIL"
            if not results["mechanical_warp_pass"]
            else "ALL_CONTROLS_PASS"
        )
    )
'''
new_verdict = '''    results["verdict"] = (
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
'''
assert old_verdict in t
t = t.replace(old_verdict, new_verdict, 1)

p.write_text(t, encoding="utf-8")
print("controls updated")
