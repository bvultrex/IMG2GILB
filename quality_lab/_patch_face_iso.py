# patch_face_iso.py — add --face-iso to project_hybrid_a3.py (P2 torso freeze, coherent face)
from pathlib import Path

PATHS = [
    Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\project_hybrid_a3.py"),
    Path(r"D:\SF3D_QualityLab\project_hybrid_a3.py"),
]

FACE_ISO_FUNCS = r'''

def face_iso_weight_map(
    mask: np.ndarray,
    face_roi: tuple[int, int, int, int],
    project_face: bool,
    face_boost: float = 1.55,
    body_scale: float = 1.00,
    paint_face: float = 0.02,
) -> np.ndarray:
    """Isolated face correction weight map (Zenko Phase2b scorecard).

    Freeze P2 torso/back: body_scale=1.0 (no chest damp, no steeper incidence here).
    Coherent face source — NEVER soft-blend mid-face features:
      project_face=True  -> uniform high projection across entire face ROI (soft edge only at perimeter)
      project_face=False -> near-zero projection across entire face ROI (Paint fill = one coherent face)
    """
    h, w = mask.shape
    x0, y0, x1, y1 = face_roi
    fh = max(1.0, float(y1 - y0))
    fw = max(1.0, float(x1 - x0))
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    face_cx = (x0 + x1) * 0.5
    face_cy = y0 + fh * 0.45
    rx, ry = max(1.0, fw * 0.52), max(1.0, fh * 0.55)
    # Soft perimeter only — interior is flat so eyes/mouth/nose share one source
    dist = np.sqrt(((xx - face_cx) / rx) ** 2 + ((yy - face_cy) / ry) ** 2)
    face = np.clip(1.0 - (dist - 0.72) / 0.28, 0.0, 1.0)  # 1 inside ~0.72, ramp to 0 at 1.0
    face = face * face  # slightly tighter falloff at rim
    face_val = float(face_boost) if project_face else float(paint_face)
    wmap = body_scale + (face_val - body_scale) * face
    wmap = wmap * mask.astype(np.float32)
    return wmap.astype(np.float32)


def face_landmark_quality(src_rgb: np.ndarray, dst_rgb: np.ndarray) -> dict:
    """Score eyes/nose/mouth landmark registration before any face blend.

    Returns dict with ok bool, residual_px, n_kps, and optional partial affine.
    Gate: need >=5 kps, residual median <= 6px after similarity, scale in [0.90, 1.12].
    """
    src_u8 = (np.clip(src_rgb, 0, 1) * 255).astype(np.uint8)
    dst_u8 = (np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8)
    sk, sb = _try_anime_face_keypoints(cv2.cvtColor(src_u8, cv2.COLOR_RGB2BGR))
    dk, db = _try_anime_face_keypoints(cv2.cvtColor(dst_u8, cv2.COLOR_RGB2BGR))
    meta = {"mode": "face_landmark_quality", "ok": False, "src": sk is not None, "dst": dk is not None}
    if sk is None or dk is None or len(sk) < 5 or len(dk) < 5:
        meta["reason"] = "insufficient_keypoints"
        return meta
    n = min(len(sk), len(dk))
    sk, dk = sk[:n], dk[:n]
    # Prefer eye/nose/mouth subset when detector returns dense anime landmarks (>=17)
    # Typical anime-face-detector: 0-1 brow-ish, eyes clustered, nose, mouth around mid indices.
    if n >= 17:
        # Use a stable subset: approximate left-eye, right-eye, nose, mouth corners / chin-ish
        idxs = [0, 1, 2, 3, 4]  # first 5 are usually eyes+nose style in many packs
        # Also include mid and lower if present
        for extra in (11, 12, 16, 17, 23, 24, 26):
            if extra < n:
                idxs.append(extra)
        idxs = sorted(set(i for i in idxs if i < n))
        sk_use, dk_use = sk[idxs], dk[idxs]
    else:
        sk_use, dk_use = sk, dk
    M, inliers = cv2.estimateAffinePartial2D(sk_use, dk_use, method=cv2.RANSAC, ransacReprojThreshold=5.0)
    if M is None:
        meta["reason"] = "estimate_failed"
        return meta
    # residuals
    ones = np.ones((len(sk_use), 1), dtype=np.float32)
    src_h = np.concatenate([sk_use, ones], axis=1)
    pred = (M @ src_h.T).T
    resid = np.linalg.norm(pred - dk_use, axis=1)
    med = float(np.median(resid))
    p90 = float(np.percentile(resid, 90))
    dx, dy = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    nin = int(inliers.sum()) if inliers is not None else 0
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(dx) <= 36
        and abs(dy) <= 36
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

MARKER = "def steeper_incidence("


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "def face_iso_weight_map(" in text:
        print(f"SKIP funcs already present: {path}")
    else:
        if MARKER not in text:
            raise SystemExit(f"marker missing in {path}")
        text = text.replace(MARKER, FACE_ISO_FUNCS + "\n" + MARKER, 1)
        print(f"INSERTED funcs: {path}")

    # micro_align_front signature
    old_sig = "def micro_align_front(warped_rgba: np.ndarray, rendered: np.ndarray, matrix: np.ndarray, jaw_blend: bool = False, phase2b: bool = False) -> tuple[np.ndarray, np.ndarray, float, dict, np.ndarray]:"
    new_sig = "def micro_align_front(warped_rgba: np.ndarray, rendered: np.ndarray, matrix: np.ndarray, jaw_blend: bool = False, phase2b: bool = False, face_iso: bool = False) -> tuple[np.ndarray, np.ndarray, float, dict, np.ndarray]:"
    if "face_iso: bool = False" not in text:
        if old_sig not in text:
            raise SystemExit("micro_align_front sig not found")
        text = text.replace(old_sig, new_sig, 1)

    # After meta phase2b flags, add face_iso handling block before jaw shrink
    anchor = '    meta["phase2b"] = bool(phase2b)\n    jaw_blend = use_jaw  # reuse jaw ROI shrink / feather path'
    insert = '''    meta["phase2b"] = bool(phase2b)
    meta["face_iso"] = bool(face_iso)
    # Face-iso: do NOT reuse jaw_blend mid-face Paint band (that caused eye/mouth mix).
    if face_iso:
        jaw_blend = False
        use_jaw = False
    else:
        jaw_blend = use_jaw  # reuse jaw ROI shrink / feather path'''
    if 'meta["face_iso"] = bool(face_iso)' not in text:
        if anchor not in text:
            raise SystemExit("jaw_blend anchor missing")
        text = text.replace(anchor, insert, 1)

    # Before ECC / after phase2b anime affine block, add face_iso landmark quality + optional affine
    # Find: "if delta is None:\n        # 2) ECC translation-only"
    ecc_anchor = "    if delta is None:\n        # 2) ECC translation-only on tight face ROI"
    face_iso_block = '''    # Face-iso: landmark quality gate (eyes/nose/mouth) before any mid-face blend
    if face_iso:
        q = face_landmark_quality(rgb, dst_rgb)
        meta["landmark_quality"] = {k: v for k, v in q.items() if k != "affine"}
        meta["project_face"] = bool(q.get("ok"))
        if q.get("ok") and delta is None and "affine" in q:
            Mq = np.array(q["affine"], dtype=np.float32)
            dx, dy = float(Mq[0, 2]), float(Mq[1, 2])
            # Prefer translation-only extract if rotation tiny; else capped partial affine
            scale = float(np.sqrt(Mq[0, 0] ** 2 + Mq[0, 1] ** 2))
            if abs(Mq[0, 1]) < 0.08 and abs(Mq[1, 0]) < 0.08 and abs(dx) <= 28 and abs(dy) <= 28:
                delta = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)
                meta["chosen"] = "face_iso_landmark_translation"
            elif abs(dx) <= 28 and abs(dy) <= 28 and 0.92 <= scale <= 1.08:
                delta = Mq
                meta["chosen"] = "face_iso_landmark_partial_affine"
            else:
                meta["steps"].append({"mode": "face_iso_affine_rejected", "dx": dx, "dy": dy, "scale": scale})
        elif not q.get("ok"):
            meta["chosen"] = meta.get("chosen") or "face_iso_paint_fallback"
            meta["steps"].append({"mode": "face_iso_gate_fail", "reason": q.get("reason")})

    if delta is None:
        # 2) ECC translation-only on tight face ROI'''
    if "face_iso_landmark_translation" not in text:
        if ecc_anchor not in text:
            raise SystemExit("ECC anchor missing")
        text = text.replace(ecc_anchor, face_iso_block, 1)

    # Weight map selection when accepted
    old_wm = '''            if jaw_blend:
                # Use original detected face ROI (pre-shrink) for jaw band placement if available
                weight_roi = tuple(meta.get("roi_silhouette", roi))
                if meta.get("roi_source") == "anime_face_bbox" and "roi" in meta:
                    # Prefer detector bbox before jaw shrink — stored earlier as roi before overwrite
                    # Fall back: expand shrunk roi bottom back
                    x0, y0, x1, y1 = roi
                    weight_roi = (x0, y0, x1, min(h, y1 + int(max(1, y1 - y0) * 0.40)))
                # Better: recover from steps face bbox
                for step in meta.get("steps", []):
                    if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                        db = step["dst_bbox"]
                        pad = 28
                        weight_roi = (
                            max(0, int(db[0]) - pad),
                            max(0, int(db[1]) - pad),
                            min(w, int(db[2]) + pad),
                            min(h, int(db[3]) + pad),
                        )
                        break
                if phase2b:
                    wmap = phase2b_weight_map(
                        warped2[:, :, 3] > 127, weight_roi, face_boost=1.45, chest_scale=1.00, jaw_paint=0.04
                    )
                    meta["weight_map"] = "phase2b_hard_jaw_paint"
                else:
                    wmap = jaw_blend_weight_map(
                        warped2[:, :, 3] > 127, weight_roi, face_boost=1.70, chest_scale=1.00, jaw_paint=0.18
                    )
                    meta["weight_map"] = "jaw_blend"
                meta["weight_roi"] = list(weight_roi)
            else:
                wmap = soft_face_weight_map(warped2[:, :, 3] > 127, roi, face_boost=1.55, body_scale=0.80)
                meta["weight_map"] = "soft_face"'''

    new_wm = '''            if face_iso:
                weight_roi = roi
                for step in meta.get("steps", []):
                    if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                        db = step["dst_bbox"]
                        pad = 28
                        weight_roi = (
                            max(0, int(db[0]) - pad),
                            max(0, int(db[1]) - pad),
                            min(w, int(db[2]) + pad),
                            min(h, int(db[3]) + pad),
                        )
                        break
                if "dst_bbox" in meta.get("landmark_quality", {}):
                    db = meta["landmark_quality"]["dst_bbox"]
                    pad = 28
                    weight_roi = (
                        max(0, int(db[0]) - pad),
                        max(0, int(db[1]) - pad),
                        min(w, int(db[2]) + pad),
                        min(h, int(db[3]) + pad),
                    )
                project_face = bool(meta.get("project_face", True))
                wmap = face_iso_weight_map(
                    warped2[:, :, 3] > 127, weight_roi, project_face=project_face, face_boost=1.55, body_scale=1.00
                )
                meta["weight_map"] = "face_iso_project" if project_face else "face_iso_paint"
                meta["weight_roi"] = list(weight_roi)
            elif jaw_blend:
                # Use original detected face ROI (pre-shrink) for jaw band placement if available
                weight_roi = tuple(meta.get("roi_silhouette", roi))
                if meta.get("roi_source") == "anime_face_bbox" and "roi" in meta:
                    # Prefer detector bbox before jaw shrink — stored earlier as roi before overwrite
                    # Fall back: expand shrunk roi bottom back
                    x0, y0, x1, y1 = roi
                    weight_roi = (x0, y0, x1, min(h, y1 + int(max(1, y1 - y0) * 0.40)))
                # Better: recover from steps face bbox
                for step in meta.get("steps", []):
                    if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                        db = step["dst_bbox"]
                        pad = 28
                        weight_roi = (
                            max(0, int(db[0]) - pad),
                            max(0, int(db[1]) - pad),
                            min(w, int(db[2]) + pad),
                            min(h, int(db[3]) + pad),
                        )
                        break
                if phase2b:
                    wmap = phase2b_weight_map(
                        warped2[:, :, 3] > 127, weight_roi, face_boost=1.45, chest_scale=1.00, jaw_paint=0.04
                    )
                    meta["weight_map"] = "phase2b_hard_jaw_paint"
                else:
                    wmap = jaw_blend_weight_map(
                        warped2[:, :, 3] > 127, weight_roi, face_boost=1.70, chest_scale=1.00, jaw_paint=0.18
                    )
                    meta["weight_map"] = "jaw_blend"
                meta["weight_roi"] = list(weight_roi)
            else:
                wmap = soft_face_weight_map(warped2[:, :, 3] > 127, roi, face_boost=1.55, body_scale=0.80)
                meta["weight_map"] = "soft_face"'''

    if "face_iso_project" not in text:
        if old_wm not in text:
            raise SystemExit("accepted weight-map block not found exactly")
        text = text.replace(old_wm, new_wm, 1)

    # Fallback weight map when micro not accepted
    old_fb = '''    if jaw_blend:
        weight_roi = roi
        for step in meta.get("steps", []):
            if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                db = step["dst_bbox"]
                pad = 28
                weight_roi = (
                    max(0, int(db[0]) - pad),
                    max(0, int(db[1]) - pad),
                    min(w, int(db[2]) + pad),
                    min(h, int(db[3]) + pad),
                )
                break
        if phase2b:
            wmap = phase2b_weight_map(src_mask, weight_roi, face_boost=1.30, chest_scale=1.00, jaw_paint=0.04)
            meta["weight_map"] = "phase2b_hard_jaw_paint_no_micro"
            meta["fallback_no_micro"] = True
        else:
            wmap = jaw_blend_weight_map(src_mask, weight_roi, face_boost=1.55, chest_scale=0.95, jaw_paint=0.22)
            meta["weight_map"] = "jaw_blend_no_micro"
        meta["weight_roi"] = list(weight_roi)
    else:
        wmap = soft_face_weight_map(src_mask, roi, face_boost=1.35, body_scale=0.85)
        meta["weight_map"] = "soft_face"
    meta["accepted"] = False
    return warped_rgba, matrix, float(base_iou), meta, wmap'''

    new_fb = '''    if face_iso:
        weight_roi = roi
        for step in meta.get("steps", []):
            if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                db = step["dst_bbox"]
                pad = 28
                weight_roi = (
                    max(0, int(db[0]) - pad),
                    max(0, int(db[1]) - pad),
                    min(w, int(db[2]) + pad),
                    min(h, int(db[3]) + pad),
                )
                break
        # Alignment failed / rejected → coherent Paint face (do not mix features)
        meta["project_face"] = False
        wmap = face_iso_weight_map(src_mask, weight_roi, project_face=False, body_scale=1.00)
        meta["weight_map"] = "face_iso_paint_no_micro"
        meta["weight_roi"] = list(weight_roi)
        meta["fallback_no_micro"] = True
    elif jaw_blend:
        weight_roi = roi
        for step in meta.get("steps", []):
            if step.get("mode", "").startswith("face_center") and "dst_bbox" in step:
                db = step["dst_bbox"]
                pad = 28
                weight_roi = (
                    max(0, int(db[0]) - pad),
                    max(0, int(db[1]) - pad),
                    min(w, int(db[2]) + pad),
                    min(h, int(db[3]) + pad),
                )
                break
        if phase2b:
            wmap = phase2b_weight_map(src_mask, weight_roi, face_boost=1.30, chest_scale=1.00, jaw_paint=0.04)
            meta["weight_map"] = "phase2b_hard_jaw_paint_no_micro"
            meta["fallback_no_micro"] = True
        else:
            wmap = jaw_blend_weight_map(src_mask, weight_roi, face_boost=1.55, chest_scale=0.95, jaw_paint=0.22)
            meta["weight_map"] = "jaw_blend_no_micro"
        meta["weight_roi"] = list(weight_roi)
    else:
        wmap = soft_face_weight_map(src_mask, roi, face_boost=1.35, body_scale=0.85)
        meta["weight_map"] = "soft_face"
    meta["accepted"] = False
    return warped_rgba, matrix, float(base_iou), meta, wmap'''

    if "face_iso_paint_no_micro" not in text:
        if old_fb not in text:
            raise SystemExit("fallback weight-map block not found")
        text = text.replace(old_fb, new_fb, 1)

    # run() signature
    old_run = "def run(job: Path, out_dir: Path, landmarks_path: Path | None, vis_dir: Path | None, atlas_size: int = 2048, atlas_path: Path | None = None, color_glb: Path | None = None, pbr_glb: Path | None = None, jaw_blend: bool = False, phase2b: bool = False, extra_render_azims: list[float] | None = None, no_face_micro: bool = False, source_pbr: Path | None = None, mr_atlas: Path | None = None) -> dict:"
    new_run = "def run(job: Path, out_dir: Path, landmarks_path: Path | None, vis_dir: Path | None, atlas_size: int = 2048, atlas_path: Path | None = None, color_glb: Path | None = None, pbr_glb: Path | None = None, jaw_blend: bool = False, phase2b: bool = False, extra_render_azims: list[float] | None = None, no_face_micro: bool = False, source_pbr: Path | None = None, mr_atlas: Path | None = None, face_iso: bool = False) -> dict:"
    if "face_iso: bool = False) -> dict:" not in text:
        if old_run not in text:
            raise SystemExit("run() sig not found")
        text = text.replace(old_run, new_run, 1)

    # phase2b implies jaw; face_iso must NOT enable phase2b incidence
    old_p2b = '''    if phase2b:
        jaw_blend = True  # Phase2b builds on jaw ROI machinery + harder falloff
    report = {
        "method": "hybrid_a3_paint_fill_plus_ortho_projection" + ("_phase2b" if phase2b else ("_jaw_blend" if jaw_blend else "")),
        "jaw_blend": bool(jaw_blend),
        "phase2b": bool(phase2b),
        "no_face_micro": bool(no_face_micro),'''
    new_p2b = '''    if face_iso:
        # Isolated face arm: keep P2 incidence (phase2b=False); no jaw mid-face Paint band
        phase2b = False
        jaw_blend = False
    elif phase2b:
        jaw_blend = True  # Phase2b builds on jaw ROI machinery + harder falloff
    method_suffix = "_face_iso" if face_iso else ("_phase2b" if phase2b else ("_jaw_blend" if jaw_blend else ""))
    report = {
        "method": "hybrid_a3_paint_fill_plus_ortho_projection" + method_suffix,
        "jaw_blend": bool(jaw_blend),
        "phase2b": bool(phase2b),
        "face_iso": bool(face_iso),
        "no_face_micro": bool(no_face_micro),'''
    if '"face_iso": bool(face_iso)' not in text:
        if old_p2b not in text:
            raise SystemExit("phase2b report block not found")
        text = text.replace(old_p2b, new_p2b, 1)

    # Wire face_iso into micro_align_front call
    old_call = "warped, matrix, iou, micro_meta, face_wmap = micro_align_front(warped, rendered, matrix, jaw_blend=jaw_blend, phase2b=phase2b)"
    new_call = "warped, matrix, iou, micro_meta, face_wmap = micro_align_front(warped, rendered, matrix, jaw_blend=jaw_blend, phase2b=phase2b, face_iso=face_iso)"
    if "face_iso=face_iso)" not in text:
        if old_call not in text:
            raise SystemExit("micro_align_front call not found")
        text = text.replace(old_call, new_call, 1)

    # When landmarks used on front with face_iso, still apply face_iso weight map
    old_lm = '''        face_wmap = None
        if name == "front" and not used_landmarks:'''
    new_lm = '''        face_wmap = None
        if name == "front" and used_landmarks and face_iso:
            # Landmarks already warped whole image; still apply coherent face source gate
            src_mask = warped[:, :, 3] > 127
            dst_mask = rendered[:, :, 3] > 0.5
            h, w = dst_mask.shape
            roi = face_roi_from_silhouette(dst_mask)
            dst_u8 = (np.clip(rendered[:, :, :3], 0, 1) * 255).astype(np.uint8)
            _dk, db = _try_anime_face_keypoints(cv2.cvtColor(dst_u8, cv2.COLOR_RGB2BGR))
            if db is not None:
                pad = 28
                roi = (
                    max(0, int(db[0]) - pad),
                    max(0, int(db[1]) - pad),
                    min(w, int(db[2]) + pad),
                    min(h, int(db[3]) + pad),
                )
            q = face_landmark_quality(warped[:, :, :3].astype(np.float32) / 255.0, rendered[:, :, :3])
            project_face = bool(q.get("ok"))
            face_wmap = face_iso_weight_map(src_mask, roi, project_face=project_face, body_scale=1.00)
            align_meta["micro"] = {
                "accepted": True,
                "face_iso_after_landmarks": True,
                "project_face": project_face,
                "landmark_quality": {k: v for k, v in q.items() if k != "affine"},
                "weight_map": "face_iso_project" if project_face else "face_iso_paint",
                "roi": list(roi),
            }
            align_meta["mode"] = "landmarks_piecewise_affine+face_iso"
        if name == "front" and not used_landmarks:'''
    if "face_iso_after_landmarks" not in text:
        if old_lm not in text:
            raise SystemExit("face_wmap None block not found")
        text = text.replace(old_lm, new_lm, 1)

    # Also handle no_face_micro + face_iso in forced path
    old_nfm = '''                if phase2b:
                    face_wmap = phase2b_weight_map(src_mask, roi, face_boost=1.30, chest_scale=1.00, jaw_paint=0.04)
                    wm = "phase2b_hard_jaw_paint_forced_no_micro"
                elif jaw_blend:
                    face_wmap = jaw_blend_weight_map(src_mask, roi, face_boost=1.55, chest_scale=0.95, jaw_paint=0.22)
                    wm = "jaw_blend_forced_no_micro"
                else:
                    face_wmap = soft_face_weight_map(src_mask, roi)
                    wm = "soft_face_forced_no_micro"'''
    new_nfm = '''                if face_iso:
                    face_wmap = face_iso_weight_map(src_mask, roi, project_face=False, body_scale=1.00)
                    wm = "face_iso_paint_forced_no_micro"
                elif phase2b:
                    face_wmap = phase2b_weight_map(src_mask, roi, face_boost=1.30, chest_scale=1.00, jaw_paint=0.04)
                    wm = "phase2b_hard_jaw_paint_forced_no_micro"
                elif jaw_blend:
                    face_wmap = jaw_blend_weight_map(src_mask, roi, face_boost=1.55, chest_scale=0.95, jaw_paint=0.22)
                    wm = "jaw_blend_forced_no_micro"
                else:
                    face_wmap = soft_face_weight_map(src_mask, roi)
                    wm = "soft_face_forced_no_micro"'''
    if "face_iso_paint_forced_no_micro" not in text:
        if old_nfm not in text:
            raise SystemExit("no_face_micro weight block not found")
        text = text.replace(old_nfm, new_nfm, 1)

    # argparse
    if "--face-iso" not in text:
        text = text.replace(
            '    p.add_argument("--no-face-micro", action="store_true", help="Skip face micro-align; keep phase2b/jaw weight maps only (explicit fallback)")\n',
            '    p.add_argument("--no-face-micro", action="store_true", help="Skip face micro-align; keep phase2b/jaw weight maps only (explicit fallback)")\n'
            '    p.add_argument("--face-iso", action="store_true", help="Isolated face correction: P2 incidence; coherent face source (project-all or paint-all); freeze torso/back")\n',
            1,
        )

    old_main_run = "    run(job, out, landmarks, vis, atlas_path=atlas, color_glb=color_glb, pbr_glb=pbr_glb, jaw_blend=bool(args.jaw_blend), phase2b=bool(args.phase2b), no_face_micro=bool(args.no_face_micro), source_pbr=source_pbr, mr_atlas=mr_atlas)"
    new_main_run = "    run(job, out, landmarks, vis, atlas_path=atlas, color_glb=color_glb, pbr_glb=pbr_glb, jaw_blend=bool(args.jaw_blend), phase2b=bool(args.phase2b), no_face_micro=bool(args.no_face_micro), source_pbr=source_pbr, mr_atlas=mr_atlas, face_iso=bool(args.face_iso))"
    if "face_iso=bool(args.face_iso)" not in text:
        if old_main_run not in text:
            raise SystemExit("main run() call not found")
        text = text.replace(old_main_run, new_main_run, 1)

    path.write_text(text, encoding="utf-8")
    print(f"PATCHED OK: {path}")


for p in PATHS:
    if p.exists():
        patch_one(p)
    else:
        print(f"MISSING: {p}")
print("DONE")
