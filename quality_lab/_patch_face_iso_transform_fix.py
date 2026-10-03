"""Patch face_iso transform extraction + soft-ROI warp (Issue #1 QUALITY_JUMP_FACE_ISO_TRANSFORM_DIAG)."""
from pathlib import Path

PATHS = [
    Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\project_hybrid_a3.py"),
    Path(r"D:\SF3D_QualityLab\project_hybrid_a3.py"),
]

# --- 1) Replace apply_face_local_warp to warp soft ROI with same delta ---
OLD_WARP = '''def apply_face_local_warp(
    warped_rgba: np.ndarray,
    delta: np.ndarray,
    roi: tuple[int, int, int, int],
    feather: int = 40,
    feather_bottom: int | None = None,
) -> np.ndarray:
    """Warp only inside soft face ROI; keep body from bbox-aligned image.

    feather_bottom: if set, use a taller/softer falloff at the ROI bottom (jaw/neck)
    so micro-align translation does not smear into the neck.
    """
    h, w = warped_rgba.shape[:2]
    full = cv2.warpAffine(warped_rgba, delta, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    x0, y0, x1, y1 = roi
    fb = int(feather_bottom) if feather_bottom is not None else int(feather)
    pad_x = feather + 8
    pad_top = feather + 8
    pad_bot = fb + 8
    x0, y0 = max(0, x0 - pad_x), max(0, y0 - pad_top)
    x1, y1 = min(w, x1 + pad_x), min(h, y1 + pad_bot)
    mask = np.zeros((h, w), dtype=np.float32)
    mask[y0:y1, x0:x1] = 1.0
    # Horizontal / top blur
    mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, feather * 0.5))
    if feather_bottom is not None and fb > feather:
        # Extra vertical softening toward bottom: build a bottom-weighted attenuation
        yy = np.linspace(0, 1, y1 - y0, dtype=np.float32) if y1 > y0 else np.array([0], dtype=np.float32)
        # Keep top sharp-ish; ramp down influence in lower 45% of ROI
        vert = np.ones_like(yy)
        ramp_start = 0.55
        for i, t in enumerate(yy):
            if t > ramp_start:
                vert[i] = max(0.0, 1.0 - (t - ramp_start) / max(1e-3, 1.0 - ramp_start))
        mask[y0:y1, x0:x1] *= vert[:, None]
        mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, fb * 0.35))
    mask = mask[:, :, None]
    out = warped_rgba.astype(np.float32) * (1.0 - mask) + full.astype(np.float32) * mask
    return np.clip(out, 0, 255).astype(np.uint8)
'''

NEW_WARP = '''def apply_face_local_warp(
    warped_rgba: np.ndarray,
    delta: np.ndarray,
    roi: tuple[int, int, int, int],
    feather: int = 40,
    feather_bottom: int | None = None,
) -> np.ndarray:
    """Warp only inside soft face ROI; keep body from bbox-aligned image.

    feather_bottom: if set, use a taller/softer falloff at the ROI bottom (jaw/neck)
    so micro-align translation does not smear into the neck.

    Soft ROI is warped with the SAME delta as the image, then unioned with the
    unwarped soft mask so both the vacated and landing footprints are covered
    (avoids ghost/duplicate features at the ROI rim).
    """
    h, w = warped_rgba.shape[:2]
    full = cv2.warpAffine(warped_rgba, delta, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    x0, y0, x1, y1 = roi
    fb = int(feather_bottom) if feather_bottom is not None else int(feather)
    pad_x = feather + 8
    pad_top = feather + 8
    pad_bot = fb + 8
    x0, y0 = max(0, x0 - pad_x), max(0, y0 - pad_top)
    x1, y1 = min(w, x1 + pad_x), min(h, y1 + pad_bot)
    mask = np.zeros((h, w), dtype=np.float32)
    mask[y0:y1, x0:x1] = 1.0
    # Horizontal / top blur
    mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, feather * 0.5))
    if feather_bottom is not None and fb > feather:
        # Extra vertical softening toward bottom: build a bottom-weighted attenuation
        yy = np.linspace(0, 1, y1 - y0, dtype=np.float32) if y1 > y0 else np.array([0], dtype=np.float32)
        # Keep top sharp-ish; ramp down influence in lower 45% of ROI
        vert = np.ones_like(yy)
        ramp_start = 0.55
        for i, t in enumerate(yy):
            if t > ramp_start:
                vert[i] = max(0.0, 1.0 - (t - ramp_start) / max(1e-3, 1.0 - ramp_start))
        mask[y0:y1, x0:x1] *= vert[:, None]
        mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, fb * 0.35))
    # Warp soft ROI with same transform; union covers vacated + landing footprints
    mask_w = cv2.warpAffine(mask, delta, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    mask = np.maximum(mask, mask_w)
    mask = mask[:, :, None]
    out = warped_rgba.astype(np.float32) * (1.0 - mask) + full.astype(np.float32) * mask
    return np.clip(out, 0, 255).astype(np.uint8)
'''

# --- 2) Insert helper before face_center_translation ---
HELPER = '''
def face_iso_extract_micro_delta(
    Mq: np.ndarray,
    face_center_M: np.ndarray | None,
    face_center_meta: dict | None,
    landmark_meta: dict,
    max_t: float = 24.0,
    scale_tol: float = 0.02,
    agree_px: float = 12.0,
) -> tuple[np.ndarray | None, dict]:
    """Build a safe face_iso micro delta from landmark similarity.

    NEVER strip scaled similarity translation terms (M[:,2]) into a pure
    translation when |scale-1| is non-trivial — those tx/ty absorb -(s-1)*pos
    and invent large bogus shifts (failed face_iso: scale~1.09 → dx~-65).

    Preference order:
      1) face_center bbox translation (capped)
      2) landmark/bbox center-to-center translation (capped)
      3) raw M[:,2] ONLY if |scale-1|<=scale_tol, rotation tiny, and agrees
         with face_center within agree_px
      4) near-identity partial affine with tight scale/translation caps
    """
    meta: dict = {"mode": "face_iso_extract_micro_delta"}
    scale = float(np.sqrt(Mq[0, 0] ** 2 + Mq[0, 1] ** 2))
    rot_a, rot_b = float(Mq[0, 1]), float(Mq[1, 0])
    rot_small = abs(rot_a) < 0.08 and abs(rot_b) < 0.08
    raw_tx, raw_ty = float(Mq[0, 2]), float(Mq[1, 2])
    meta.update({"scale": scale, "raw_tx": raw_tx, "raw_ty": raw_ty, "rot_small": bool(rot_small)})

    # Center-to-center from landmark bboxes (true face shift, scale-independent)
    center_dx = center_dy = None
    sb = landmark_meta.get("src_bbox")
    db = landmark_meta.get("dst_bbox")
    if sb is not None and db is not None:
        scx = (float(sb[0]) + float(sb[2])) * 0.5
        scy = (float(sb[1]) + float(sb[3])) * 0.5
        dcx = (float(db[0]) + float(db[2])) * 0.5
        dcy = (float(db[1]) + float(db[3])) * 0.5
        center_dx, center_dy = dcx - scx, dcy - scy
        meta["bbox_center_dx"] = float(center_dx)
        meta["bbox_center_dy"] = float(center_dy)

    fc_dx = fc_dy = None
    if face_center_M is not None:
        fc_dx, fc_dy = float(face_center_M[0, 2]), float(face_center_M[1, 2])
        meta["face_center_dx"] = fc_dx
        meta["face_center_dy"] = fc_dy
    elif face_center_meta and "dx" in face_center_meta and "dy" in face_center_meta:
        # may be rejected/unavailable; still record if present
        try:
            fc_dx = float(face_center_meta["dx"])
            fc_dy = float(face_center_meta["dy"])
            meta["face_center_dx"] = fc_dx
            meta["face_center_dy"] = fc_dy
        except (TypeError, ValueError, KeyError):
            pass

    def _cap_translation(dx: float, dy: float, tag: str) -> tuple[np.ndarray | None, dict]:
        if abs(dx) > max_t or abs(dy) > max_t:
            c = min(1.0, max_t / max(abs(dx), abs(dy), 1e-3))
            dx2, dy2 = dx * c, dy * c
            info = {"chosen": tag + "_clamped", "dx": float(dx2), "dy": float(dy2), "clamp_scale": float(c), "uncapped_dx": float(dx), "uncapped_dy": float(dy)}
            # If uncapped was huge opposite of a known good center, reject instead of clamping wrong direction
            if abs(dx) > max_t * 2 or abs(dy) > max_t * 2:
                info["chosen"] = tag + "_rejected_too_large"
                return None, info
            return np.array([[1.0, 0.0, dx2], [0.0, 1.0, dy2]], dtype=np.float32), info
        return np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32), {"chosen": tag, "dx": float(dx), "dy": float(dy), "clamp_scale": 1.0}

    scale_off = abs(scale - 1.0) > scale_tol

    # Path A: scale off or rotation non-trivial → NEVER use raw M[:,2] as translation
    if scale_off or not rot_small:
        meta["path"] = "prefer_center_not_raw_tx"
        if fc_dx is not None and fc_dy is not None and abs(fc_dx) <= 48 and abs(fc_dy) <= 48:
            delta, info = _cap_translation(fc_dx, fc_dy, "face_iso_face_center_vs_scaled_sim")
            meta.update(info)
            return delta, meta
        if center_dx is not None and center_dy is not None:
            delta, info = _cap_translation(float(center_dx), float(center_dy), "face_iso_bbox_center_vs_scaled_sim")
            meta.update(info)
            return delta, meta
        # Tight full partial affine only if scale nearly 1 after all (shouldn't hit often)
        if 0.97 <= scale <= 1.03 and abs(raw_tx) <= 16 and abs(raw_ty) <= 16 and rot_small:
            meta["chosen"] = "face_iso_landmark_partial_affine_tight"
            return Mq.astype(np.float32), meta
        meta["chosen"] = "face_iso_extract_reject"
        meta["reason"] = "scaled_similarity_no_safe_center"
        return None, meta

    # Path B: scale≈1, rot tiny — raw tx/ty ≈ true translation; still require face_center agreement
    meta["path"] = "near_unity_scale"
    if fc_dx is not None and fc_dy is not None:
        agree = float(np.hypot(raw_tx - fc_dx, raw_ty - fc_dy))
        meta["agree_face_center_px"] = agree
        if agree > agree_px:
            # Prefer face_center (trusted bbox centers) over disagreeing raw tx
            delta, info = _cap_translation(fc_dx, fc_dy, "face_iso_face_center_disagree_raw")
            meta.update(info)
            meta["raw_rejected_disagree"] = True
            return delta, meta
    delta, info = _cap_translation(raw_tx, raw_ty, "face_iso_landmark_translation")
    meta.update(info)
    return delta, meta


'''

# Insert helper before face_center_translation
ANCHOR = "def face_center_translation(src_rgb: np.ndarray, dst_rgb: np.ndarray) -> tuple[np.ndarray | None, dict]:"

# --- 3) Update face_landmark_quality gate: report center delta; gate on center when scale off ---
OLD_GATE = '''    dx, dy = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    nin = int(inliers.sum()) if inliers is not None else 0
    # Prefer residual quality over absolute translation: large dx/dy is OK if landmarks fit tightly.
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(dx) <= 96
        and abs(dy) <= 96
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )
    meta.update(
        {
            "ok": bool(ok),
            "residual_median_px": med,
            "residual_p90_px": p90,
            "dx": dx,
            "dy": dy,
            "scale": scale,
            "inliers": nin,
            "n_kps": int(len(sk_use)),
            "reason": "pass" if ok else "gate_fail",
            "affine": M.astype(np.float32).tolist(),
        }
    )
    if sb is not None:
        meta["src_bbox"] = sb.tolist()
    if db is not None:
        meta["dst_bbox"] = db.tolist()
    return meta
'''

NEW_GATE = '''    dx, dy = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    nin = int(inliers.sum()) if inliers is not None else 0
    # Scale-independent face shift from detector bboxes (do NOT gate on raw M[:,2] when scale≠1)
    center_dx = center_dy = None
    if sb is not None and db is not None:
        center_dx = float(((db[0] + db[2]) * 0.5) - ((sb[0] + sb[2]) * 0.5))
        center_dy = float(((db[1] + db[3]) * 0.5) - ((sb[1] + sb[3]) * 0.5))
    # Gate translation on center delta when available; fall back to raw only if |scale-1|<=0.02
    if center_dx is not None:
        t_dx, t_dy = center_dx, center_dy
    elif abs(scale - 1.0) <= 0.02:
        t_dx, t_dy = dx, dy
    else:
        t_dx, t_dy = dx, dy  # will fail the tighter 24px gate when scale invents large tx
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(t_dx) <= 24
        and abs(t_dy) <= 24
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )
    meta.update(
        {
            "ok": bool(ok),
            "residual_median_px": med,
            "residual_p90_px": p90,
            "dx": dx,
            "dy": dy,
            "center_dx": center_dx,
            "center_dy": center_dy,
            "gate_dx": float(t_dx) if t_dx is not None else None,
            "gate_dy": float(t_dy) if t_dy is not None else None,
            "scale": scale,
            "inliers": nin,
            "n_kps": int(len(sk_use)),
            "reason": "pass" if ok else "gate_fail",
            "affine": M.astype(np.float32).tolist(),
        }
    )
    if sb is not None:
        meta["src_bbox"] = sb.tolist()
    if db is not None:
        meta["dst_bbox"] = db.tolist()
    return meta
'''

# --- 4) Replace face_iso landmark application block ---
OLD_FACE_ISO_APPLY = '''    # Face-iso: landmark quality gate (eyes/nose/mouth) before any mid-face blend
    if face_iso:
        q = face_landmark_quality(rgb, dst_rgb)
        meta["landmark_quality"] = {k: v for k, v in q.items() if k != "affine"}
        meta["project_face"] = bool(q.get("ok"))
        if q.get("ok") and "affine" in q:
            # Landmark registration overrides prior face_center guess
            Mq = np.array(q["affine"], dtype=np.float32)
            dx, dy = float(Mq[0, 2]), float(Mq[1, 2])
            # Prefer translation-only extract if rotation tiny; else capped partial affine
            scale = float(np.sqrt(Mq[0, 0] ** 2 + Mq[0, 1] ** 2))
            # Cap applied motion to 48px / small scale; clamp if larger but gate passed
            if abs(Mq[0, 1]) < 0.08 and abs(Mq[1, 0]) < 0.08:
                c = min(1.0, 48.0 / max(abs(dx), abs(dy), 1e-3))
                delta = np.array([[1.0, 0.0, dx * c], [0.0, 1.0, dy * c]], dtype=np.float32)
                meta["chosen"] = "face_iso_landmark_translation" + ("_clamped" if c < 1.0 else "")
                meta["clamp_scale"] = float(c)
            elif 0.92 <= scale <= 1.08:
                c = min(1.0, 48.0 / max(abs(dx), abs(dy), 1e-3))
                Mq2 = Mq.copy()
                Mq2[0, 2] *= c
                Mq2[1, 2] *= c
                delta = Mq2
                meta["chosen"] = "face_iso_landmark_partial_affine" + ("_clamped" if c < 1.0 else "")
                meta["clamp_scale"] = float(c)
            else:
                meta["steps"].append({"mode": "face_iso_affine_rejected", "dx": dx, "dy": dy, "scale": scale})
        elif not q.get("ok"):
            delta = None  # coherent Paint face: no micro warp of mismatched ortho
            meta["chosen"] = "face_iso_paint_fallback"
            meta["steps"].append({"mode": "face_iso_gate_fail", "reason": q.get("reason")})
'''

NEW_FACE_ISO_APPLY = '''    # Face-iso: landmark quality gate (eyes/nose/mouth) before any mid-face blend
    if face_iso:
        q = face_landmark_quality(rgb, dst_rgb)
        meta["landmark_quality"] = {k: v for k, v in q.items() if k != "affine"}
        meta["project_face"] = bool(q.get("ok"))
        if q.get("ok") and "affine" in q:
            Mq = np.array(q["affine"], dtype=np.float32)
            # NEVER strip scaled similarity M[:,2] into pure translation (TRANSFORM_DIAG root cause).
            # Prefer face_center / bbox-center delta; raw tx only when scale≈1 and agrees.
            delta2, extract_meta = face_iso_extract_micro_delta(
                Mq,
                face_center_M=M_face,
                face_center_meta=face_meta if isinstance(face_meta, dict) else None,
                landmark_meta=q,
                max_t=24.0,
                scale_tol=0.02,
                agree_px=12.0,
            )
            meta["steps"].append(extract_meta)
            meta["extract"] = {k: v for k, v in extract_meta.items() if k != "affine"}
            if delta2 is not None:
                delta = delta2
                meta["chosen"] = str(extract_meta.get("chosen", "face_iso_extract"))
                if "clamp_scale" in extract_meta:
                    meta["clamp_scale"] = float(extract_meta["clamp_scale"])
            else:
                delta = None
                meta["chosen"] = "face_iso_paint_fallback"
                meta["steps"].append({"mode": "face_iso_extract_reject", "reason": extract_meta.get("reason")})
                meta["project_face"] = False
        elif not q.get("ok"):
            delta = None  # coherent Paint face: no micro warp of mismatched ortho
            meta["chosen"] = "face_iso_paint_fallback"
            meta["steps"].append({"mode": "face_iso_gate_fail", "reason": q.get("reason")})
'''

# --- 5) Stricter IoU for face_iso ---
OLD_IOU = '''        # Face-local with tight ROI: allow tiny IoU dip
        if iou + 0.01 >= base_iou * 0.96:
'''

NEW_IOU = '''        # Face-local with tight ROI: allow tiny IoU dip (face_iso: stricter — no 4% regression)
        iou_ok = (iou + 0.002 >= base_iou) if face_iso else (iou + 0.01 >= base_iou * 0.96)
        if iou_ok:
'''

for p in PATHS:
    t = p.read_text(encoding="utf-8")
    assert OLD_WARP in t, f"OLD_WARP missing in {p}"
    assert OLD_GATE in t, f"OLD_GATE missing in {p}"
    assert OLD_FACE_ISO_APPLY in t, f"OLD_FACE_ISO_APPLY missing in {p}"
    assert OLD_IOU in t, f"OLD_IOU missing in {p}"
    assert ANCHOR in t, f"ANCHOR missing in {p}"
    assert "def face_iso_extract_micro_delta" not in t, f"helper already present in {p}"

    t = t.replace(OLD_WARP, NEW_WARP, 1)
    t = t.replace(OLD_GATE, NEW_GATE, 1)
    t = t.replace(ANCHOR, HELPER + ANCHOR, 1)
    t = t.replace(OLD_FACE_ISO_APPLY, NEW_FACE_ISO_APPLY, 1)
    t = t.replace(OLD_IOU, NEW_IOU, 1)

    p.write_text(t, encoding="utf-8")
    print("patched", p)

print("DONE")
