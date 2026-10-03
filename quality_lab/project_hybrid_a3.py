"""Hybrid A3: Paint atlas fill + ortho reference projection (visibility/incidence).

Texture-only; never overwrites textured_*.glb / output.glb.
Alignment: bbox + IoU-refined similarity + front face/ECC micro-align (optional landmarks JSON).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import trimesh
from PIL import Image
from scipy.spatial import Delaunay
from face_transform_math import ecc_to_forward, face_feature_indices

LAB = Path(__file__).resolve().parent
if LAB.name == "quality_lab":
    LAB = Path(r"D:\SF3D_QualityLab")
HUNYUAN = Path(r"C:\Users\Shadow\Documents\ComfyUI\Hunyuan3D-2-Lab")
sys.path.insert(0, str(HUNYUAN))

from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender, transform_pos  # noqa: E402


class ProjectionRender(MeshRender):
    """Upstream _render keeps a stale glctx arg; sample texture via grid_sample."""

    def _render(self, mvp, pos, pos_idx, uv, uv_idx, tex, resolution, max_mip_level, keep_alpha, filter_mode):
        clip = transform_pos(mvp, pos)
        rast, _ = self.raster_rasterize(clip, pos_idx, resolution=resolution)
        coords, _ = self.raster_interpolate(uv[None, ...], rast, uv_idx)
        color = torch.nn.functional.grid_sample(
            tex.permute(2, 0, 1)[None, ...],
            coords * 2 - 1,
            mode="bilinear",
            padding_mode="border",
            align_corners=True,
        ).permute(0, 2, 3, 1)
        mask = rast[..., -1:].clamp(0, 1)
        return torch.cat([color * mask, mask], dim=-1)[0]


VIEW_SPECS = [
    ("front", 0, 0),
    ("right", 0, 90),
    ("back", 0, 180),
    ("left", 0, 270),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_mr_from_source_pbr(source_pbr: Path) -> tuple[Image.Image, float, float]:
    """Copy metallicRoughnessTexture pixels + factors from a baseline PBR GLB (albedo-only control)."""
    scene = trimesh.load(str(source_pbr), force="scene", process=False)
    mesh = list(scene.geometry.values())[0]
    mat = mesh.visual.material
    mr = getattr(mat, "metallicRoughnessTexture", None)
    if mr is None:
        raise ValueError(f"no metallicRoughnessTexture in {source_pbr}")
    # Exact pixel copy — do not re-pack or re-encode from raw paint MR atlas
    arr = np.asarray(mr)
    mr_img = Image.fromarray(arr.copy())
    if mr.mode and mr_img.mode != mr.mode:
        mr_img = mr_img.convert(mr.mode)
    metal = float(getattr(mat, "metallicFactor", 1.0) or 1.0)
    rough = float(getattr(mat, "roughnessFactor", 1.0) or 1.0)
    return mr_img, metal, rough


def pack_mr_from_atlas(mr_path: Path) -> Image.Image:
    """Legacy paint MR atlas pack (occlusion unused, G=rough, B=metal). Prefer load_mr_from_source_pbr."""
    mr = np.array(Image.open(mr_path).convert("RGB"))
    packed = np.stack([np.full_like(mr[:, :, 0], 255), mr[:, :, 1], mr[:, :, 0]], axis=-1)
    return Image.fromarray(packed)




def bbox(mask: np.ndarray) -> np.ndarray:
    y, x = np.where(mask)
    if len(x) == 0:
        return np.array([0, 0, 1, 1], dtype=float)
    return np.array([x.min(), y.min(), x.max(), y.max()], dtype=float)


def silhouette_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def warp_rgba(rgba: np.ndarray, matrix: np.ndarray, size: int = 2048) -> np.ndarray:
    return cv2.warpAffine(rgba, matrix, (size, size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def bbox_matrix(source_mask: np.ndarray, target_mask: np.ndarray) -> np.ndarray:
    sb, tb = bbox(source_mask), bbox(target_mask)
    scale = (tb[2:] - tb[:2]) / np.maximum(sb[2:] - sb[:2], 1e-3)
    offset = tb[:2] - sb[:2] * scale
    return np.array([[scale[0], 0, offset[0]], [0, scale[1], offset[1]]], dtype=np.float32)


def apply_similarity(matrix: np.ndarray, scale: float, dx: float, dy: float, pivot: np.ndarray) -> np.ndarray:
    """Compose extra uniform scale about pivot + translation onto 2x3 affine."""
    s = float(scale)
    m = matrix.copy()
    # map p -> scale*(p-pivot)+pivot + (dx,dy) after original affine
    # new = S * (M * p) effectively: first M, then scale about pivot
    a, b, tx = m[0]
    c, d, ty = m[1]
    # After M: q = M p. Then q' = s*(q - pivot) + pivot + delta
    # q' = s*a x + s*b y + (s*tx + (1-s)*px + dx)
    px, py = pivot
    return np.array(
        [
            [s * a, s * b, s * tx + (1 - s) * px + dx],
            [s * c, s * d, s * ty + (1 - s) * py + dy],
        ],
        dtype=np.float32,
    )


def refine_alignment(rgba: np.ndarray, target: np.ndarray, base: np.ndarray, size: int = 2048) -> tuple[np.ndarray, float, dict]:
    """BBox init + coarse IoU search on uniform scale and translation."""
    source = rgba[:, :, 3] > 127
    if source.sum() < 100 or target.sum() < 100:
        return base, 0.0, {"mode": "empty_mask"}

    best_m = base
    warped0 = warp_rgba(rgba, base, size)
    best_iou = silhouette_iou(warped0[:, :, 3] > 127, target)
    best = {"scale": 1.0, "dx": 0.0, "dy": 0.0, "iou_bbox": best_iou}

    tb = bbox(target)
    pivot = np.array([(tb[0] + tb[2]) * 0.5, (tb[1] + tb[3]) * 0.5], dtype=float)
    # Coarse grid — keep cheap; projection itself is the heavy part.
    for scale in (0.92, 0.96, 1.0, 1.04, 1.08):
        for dx in (-48, -24, 0, 24, 48):
            for dy in (-48, -24, 0, 24, 48):
                m = apply_similarity(base, scale, dx, dy, pivot)
                w = warp_rgba(rgba, m, size)
                iou = silhouette_iou(w[:, :, 3] > 127, target)
                if iou > best_iou:
                    best_iou = iou
                    best_m = m
                    best = {"scale": scale, "dx": dx, "dy": dy, "iou_bbox": float(silhouette_iou(warped0[:, :, 3] > 127, target))}

    # Fine pass around best
    s0, dx0, dy0 = best["scale"], best["dx"], best["dy"]
    for scale in (s0 - 0.02, s0, s0 + 0.02):
        for dx in (dx0 - 12, dx0, dx0 + 12):
            for dy in (dy0 - 12, dy0, dy0 + 12):
                m = apply_similarity(base, scale, dx, dy, pivot)
                w = warp_rgba(rgba, m, size)
                iou = silhouette_iou(w[:, :, 3] > 127, target)
                if iou > best_iou:
                    best_iou = iou
                    best_m = m
                    best.update({"scale": scale, "dx": dx, "dy": dy})

    best["iou"] = float(best_iou)
    best["mode"] = "bbox_iou_refine"
    return best_m, float(best_iou), best




def _try_anime_face_keypoints(bgr: np.ndarray):
    """Return Nx2 keypoints if anime-face-detector is available; else None."""
    try:
        import os
        lab = Path(r"D:\SF3D_QualityLab")
        import sys as _sys
        for p in (lab / "research" / "anime-face-detector", lab / "face_detector_deps"):
            sp = str(p)
            if sp not in _sys.path:
                _sys.path.insert(0, sp)
        from anime_face_detector import create_detector
        # cache detector on function attr
        if not hasattr(_try_anime_face_keypoints, "_det"):
            _try_anime_face_keypoints._det = create_detector("yolov3", device="cpu")
        faces = _try_anime_face_keypoints._det(bgr)
        if not faces:
            return None, None
        best = max(faces, key=lambda f: float(f["bbox"][2] - f["bbox"][0]) * float(f["bbox"][3] - f["bbox"][1]))
        kps = np.array([[float(x), float(y)] for x, y, *_ in best["keypoints"]], dtype=np.float32)
        bbox = best["bbox"][:4].astype(np.float32)
        return kps, bbox
    except Exception as exc:
        return None, None


def face_roi_from_silhouette(mask: np.ndarray) -> tuple[int, int, int, int]:
    """Heuristic upper-body/face window from silhouette bbox (top ~38%)."""
    y, x = np.where(mask)
    if len(x) == 0:
        h, w = mask.shape
        return 0, 0, w, h
    x0, x1 = int(x.min()), int(x.max())
    y0, y1 = int(y.min()), int(y.max())
    hh = max(1, y1 - y0)
    # Face/head occupies top portion of full-body ortho
    fy1 = y0 + int(hh * 0.38)
    pad = int(0.04 * max(mask.shape))
    return max(0, x0 - pad), max(0, y0 - pad), min(mask.shape[1], x1 + pad), min(mask.shape[0], fy1 + pad)


def ecc_micro_align(src_rgb: np.ndarray, dst_rgb: np.ndarray, src_mask: np.ndarray, dst_mask: np.ndarray, roi: tuple[int, int, int, int]) -> tuple[np.ndarray | None, float, dict]:
    """ECC similarity on grayscale ROI; returns 2x3 delta (maps src?dst) or None."""
    x0, y0, x1, y1 = roi
    if x1 - x0 < 32 or y1 - y0 < 32:
        return None, 0.0, {"mode": "ecc_roi_too_small"}
    g1 = cv2.cvtColor((np.clip(src_rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    g2 = cv2.cvtColor((np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    # Mask outside ROI / silhouette
    m1 = (src_mask.astype(np.uint8) * 255)
    m2 = (dst_mask.astype(np.uint8) * 255)
    roi_m = np.zeros_like(m1)
    roi_m[y0:y1, x0:x1] = 255
    m1 = cv2.bitwise_and(m1, roi_m)
    m2 = cv2.bitwise_and(m2, roi_m)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5)
        cc, warp = cv2.findTransformECC(g2, g1, warp, cv2.MOTION_EUCLIDEAN, criteria, inputMask=m2, gaussFiltSize=5)
        # findTransformECC with template=g2, input=g1 ? warp maps g1?g2
        meta = {"mode": "ecc_euclidean", "cc": float(cc), "roi": [x0, y0, x1, y1]}
        if cc < 0.15:
            return None, float(cc), {**meta, "rejected": "low_cc"}
        # Bound micro motion ? reject wild warps
        dx, dy = float(warp[0, 2]), float(warp[1, 2])
        if abs(dx) > 80 or abs(dy) > 80:
            return None, float(cc), {**meta, "rejected": "large_translation", "dx": dx, "dy": dy}
        return warp, float(cc), meta
    except cv2.error as exc:
        return None, 0.0, {"mode": "ecc_failed", "error": str(exc)[:200]}


def anime_face_micro_align(src_rgb: np.ndarray, dst_rgb: np.ndarray) -> tuple[np.ndarray | None, dict]:
    """Similarity from anime face keypoints (source warped RGB vs rendered baseline)."""
    src_u8 = (np.clip(src_rgb, 0, 1) * 255).astype(np.uint8)
    dst_u8 = (np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8)
    sk, sb = _try_anime_face_keypoints(cv2.cvtColor(src_u8, cv2.COLOR_RGB2BGR))
    dk, db = _try_anime_face_keypoints(cv2.cvtColor(dst_u8, cv2.COLOR_RGB2BGR))
    if sk is None or dk is None or len(sk) < 5 or len(dk) < 5:
        return None, {"mode": "anime_face_unavailable", "src": sk is not None, "dst": dk is not None}
    n = min(len(sk), len(dk))
    sk, dk = sk[:n], dk[:n]
    # Filter low-spread
    if np.linalg.norm(sk.std(axis=0)) < 5 or np.linalg.norm(dk.std(axis=0)) < 5:
        return None, {"mode": "anime_face_degenerate"}
    M, inliers = cv2.estimateAffinePartial2D(sk, dk, method=cv2.RANSAC, ransacReprojThreshold=6.0)
    if M is None:
        return None, {"mode": "anime_face_estimate_failed"}
    dx, dy = float(M[0, 2]), float(M[1, 2])
    scale = float(np.sqrt(M[0, 0] ** 2 + M[0, 1] ** 2))
    if abs(dx) > 100 or abs(dy) > 100 or scale < 0.85 or scale > 1.15:
        return None, {"mode": "anime_face_rejected", "dx": dx, "dy": dy, "scale": scale}
    nin = int(inliers.sum()) if inliers is not None else 0
    return M.astype(np.float32), {"mode": "anime_face_partial_affine", "inliers": nin, "dx": dx, "dy": dy, "scale": scale, "n_kps": int(n)}


def compose_affine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compose 2x3 affines: apply a first, then b. Result maps p -> b(a(p))."""
    A = np.vstack([a, [0, 0, 1]])
    B = np.vstack([b, [0, 0, 1]])
    C = B @ A
    return C[:2].astype(np.float32)



def jaw_blend_weight_map(
    mask: np.ndarray,
    face_roi: tuple[int, int, int, int],
    face_boost: float = 1.70,
    chest_scale: float = 1.00,
    jaw_paint: float = 0.20,
) -> np.ndarray:
    """Boost upper-face projection; prefer Paint fill in jaw/neck band; keep chest at chest_scale.

    Jaw smear comes from ortho stretch on neck curvature — feathering toward Paint there
    while keeping face + chest projection preserves the Hybrid chest win.
    """
    h, w = mask.shape
    x0, y0, x1, y1 = face_roi
    fh = max(1.0, float(y1 - y0))
    fw = max(1.0, float(x1 - x0))
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    face_cx = (x0 + x1) * 0.5
    # Upper-face center (eyes/forehead), not full bbox center
    face_cy = y0 + fh * 0.38
    rx, ry = max(1.0, fw * 0.48), max(1.0, fh * 0.40)
    face = np.exp(-0.5 * (((xx - face_cx) / rx) ** 2 + ((yy - face_cy) / ry) ** 2))
    face = np.clip(face, 0.0, 1.0)

    # Jaw/neck band: lower face through upper neck
    jaw_y0 = y0 + fh * 0.52
    jaw_y1 = y1 + fh * 0.95
    mid = 0.5 * (jaw_y0 + jaw_y1)
    half = max(1.0, 0.5 * (jaw_y1 - jaw_y0) * 0.70)
    jaw = np.exp(-0.5 * ((yy - mid) / half) ** 2)
    jaw_rx = max(1.0, fw * 0.70)
    jaw = jaw * np.exp(-0.5 * ((xx - face_cx) / jaw_rx) ** 2)
    jaw = np.clip(jaw, 0.0, 1.0)

    wmap = chest_scale + (face_boost - chest_scale) * face
    # Lerp toward paint-prefer weight inside jaw/neck band
    wmap = wmap * (1.0 - jaw) + float(jaw_paint) * jaw
    wmap = wmap * mask.astype(np.float32)
    return wmap.astype(np.float32)




def phase2b_weight_map(
    mask: np.ndarray,
    face_roi: tuple[int, int, int, int],
    face_boost: float = 1.45,
    chest_scale: float = 1.00,
    jaw_paint: float = 0.04,
) -> np.ndarray:
    """Phase2b: hard Paint-prefer on jaw/upper-neck ONLY; stop before collar/necklace; keep chest/back.

    Zenko 5958774240: no soft blend of mismatched features (doubles); P2 torso win must survive.
    """
    h, w = mask.shape
    x0, y0, x1, y1 = face_roi
    fh = max(1.0, float(y1 - y0))
    fw = max(1.0, float(x1 - x0))
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    face_cx = (x0 + x1) * 0.5
    face_cy = y0 + fh * 0.38
    rx, ry = max(1.0, fw * 0.48), max(1.0, fh * 0.40)
    face = np.exp(-0.5 * (((xx - face_cx) / rx) ** 2 + ((yy - face_cy) / ry) ** 2))
    face = np.clip(face, 0.0, 1.0)
    # Tight jaw/chin band — ends near face_roi bottom; does NOT extend into necklace/collar
    jaw_y0 = y0 + fh * 0.58
    jaw_y1 = y1 + fh * 0.18  # was ~0.95 in jaw_blend — that ate collar
    mid = 0.5 * (jaw_y0 + jaw_y1)
    half = max(1.0, 0.5 * (jaw_y1 - jaw_y0) * 0.85)
    jaw = np.exp(-0.5 * ((yy - mid) / half) ** 2)
    jaw_rx = max(1.0, fw * 0.55)
    jaw = jaw * np.exp(-0.5 * ((xx - face_cx) / jaw_rx) ** 2)
    jaw = np.clip(jaw, 0.0, 1.0)
    wmap = chest_scale + (face_boost - chest_scale) * face
    wmap = wmap * (1.0 - jaw) + float(jaw_paint) * jaw
    wmap = wmap * mask.astype(np.float32)
    return wmap.astype(np.float32)




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
    idxs = face_feature_indices(n)
    sk_use, dk_use = sk[idxs], dk[idxs]
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
    # Scale-independent face shift from detector bboxes (do NOT gate on raw M[:,2] when scale≠1)
    center_dx = center_dy = None
    if sb is not None and db is not None:
        center_dx = float(((db[0] + db[2]) * 0.5) - ((sb[0] + sb[2]) * 0.5))
        center_dy = float(((db[1] + db[3]) * 0.5) - ((sb[1] + sb[3]) * 0.5))
    # Gate: residual + scale + inliers. Translation magnitude uses center (≤48, matches
    # face_center_translation); extract clamps applied delta to 24. Raw M[:,2] only when scale≈1.
    if center_dx is not None:
        t_dx, t_dy = center_dx, center_dy
        t_lim = 48.0
    elif abs(scale - 1.0) <= 0.02:
        t_dx, t_dy = dx, dy
        t_lim = 24.0
    else:
        # Scaled similarity without bboxes: raw tx untrustworthy → fail gate (paint fallback)
        t_dx, t_dy = dx, dy
        t_lim = 0.0  # force fail unless somehow zero
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(t_dx) <= t_lim
        and abs(t_dy) <= t_lim
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


def steeper_incidence(cos: "torch.Tensor", phase2b: bool = False) -> "torch.Tensor":
    """Map cosine to [0,1] weight. Phase2b: steeper front/back→side falloff (no global blur)."""
    if phase2b:
        # Require more face-on normals; softstep then square for faster side decay
        t = ((cos - 0.68) / 0.27).clamp(0, 1)
        t = t * t * (3 - 2 * t)
        return t * t
    t = ((cos - 0.5) / 0.35).clamp(0, 1)
    return t * t * (3 - 2 * t)


def soft_face_weight_map(mask: np.ndarray, roi: tuple[int, int, int, int], face_boost: float = 1.35, body_scale: float = 0.85) -> np.ndarray:
    """Image-space weight: boost face ROI, slightly damp body (face-region-limited transfer)."""
    h, w = mask.shape
    x0, y0, x1, y1 = roi
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    rx, ry = max(1.0, (x1 - x0) * 0.55), max(1.0, (y1 - y0) * 0.55)
    face = np.exp(-0.5 * (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    face = np.clip(face, 0, 1)
    # body base * (1 + (boost-1)*face)
    wmap = body_scale + (face_boost - body_scale) * face
    wmap = wmap * mask.astype(np.float32)
    return wmap.astype(np.float32)



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


def face_center_translation(src_rgb: np.ndarray, dst_rgb: np.ndarray) -> tuple[np.ndarray | None, dict]:
    """Safe translation-only from anime face bbox centers (no scale/rotation)."""
    src_u8 = (np.clip(src_rgb, 0, 1) * 255).astype(np.uint8)
    dst_u8 = (np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8)
    sk, sb = _try_anime_face_keypoints(cv2.cvtColor(src_u8, cv2.COLOR_RGB2BGR))
    dk, db = _try_anime_face_keypoints(cv2.cvtColor(dst_u8, cv2.COLOR_RGB2BGR))
    if sb is None or db is None:
        return None, {"mode": "face_center_unavailable", "src": sb is not None, "dst": db is not None}
    sc = np.array([(sb[0] + sb[2]) * 0.5, (sb[1] + sb[3]) * 0.5], dtype=np.float32)
    dc = np.array([(db[0] + db[2]) * 0.5, (db[1] + db[3]) * 0.5], dtype=np.float32)
    dx, dy = float(dc[0] - sc[0]), float(dc[1] - sc[1])
    # Cap: micro only
    if abs(dx) > 48 or abs(dy) > 48:
        return None, {"mode": "face_center_rejected", "dx": dx, "dy": dy}
    M = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)
    return M, {"mode": "face_center_translation", "dx": dx, "dy": dy, "src_bbox": sb.tolist(), "dst_bbox": db.tolist()}


def apply_face_local_warp(
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


def micro_align_front(warped_rgba: np.ndarray, rendered: np.ndarray, matrix: np.ndarray, jaw_blend: bool = False, phase2b: bool = False, face_iso: bool = False) -> tuple[np.ndarray, np.ndarray, float, dict, np.ndarray]:
    """Face-region-limited micro-align: translation/ECC on face only; body stays bbox-aligned.

    jaw_blend: tighten lower ROI, asymmetric bottom feather, Paint-prefer jaw/neck weights.
    """
    rgb = warped_rgba[:, :, :3].astype(np.float32) / 255.0
    src_mask = warped_rgba[:, :, 3] > 127
    dst_rgb = rendered[:, :, :3]
    dst_mask = rendered[:, :, 3] > 0.5
    h, w = dst_mask.shape
    roi = face_roi_from_silhouette(dst_mask)
    meta = {"roi_silhouette": list(roi), "steps": []}
    delta = None

    # Prefer tight detector face bbox on *destination* (mesh render) as ROI
    dst_u8 = (np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8)
    _dk, db = _try_anime_face_keypoints(cv2.cvtColor(dst_u8, cv2.COLOR_RGB2BGR))
    if db is not None:
        pad = 28
        roi = (
            max(0, int(db[0]) - pad),
            max(0, int(db[1]) - pad),
            min(w, int(db[2]) + pad),
            min(h, int(db[3]) + pad),
        )
        meta["roi_source"] = "anime_face_bbox"
    else:
        # Tighten heuristic: top 22% of silhouette instead of 38%
        y, x = np.where(dst_mask)
        if len(x):
            x0, x1 = int(x.min()), int(x.max())
            y0, y1 = int(y.min()), int(y.max())
            fy1 = y0 + int(max(1, y1 - y0) * 0.22)
            pad = int(0.03 * max(h, w))
            # Narrow horizontally to central 55% of silhouette width
            mid = (x0 + x1) * 0.5
            half = (x1 - x0) * 0.28
            roi = (max(0, int(mid - half) - pad), max(0, y0 - pad), min(w, int(mid + half) + pad), min(h, fy1 + pad))
        meta["roi_source"] = "tight_silhouette_head"
    meta["roi"] = list(roi)
    use_jaw = bool(jaw_blend) or bool(phase2b)
    meta["jaw_blend"] = bool(jaw_blend)
    meta["phase2b"] = bool(phase2b)
    meta["face_iso"] = bool(face_iso)
    # Face-iso: do NOT reuse jaw_blend mid-face Paint band (that caused eye/mouth mix).
    if face_iso:
        jaw_blend = False
        use_jaw = False
    else:
        jaw_blend = use_jaw  # reuse jaw ROI shrink / feather path

    # Jaw-blend: shrink ROI bottom so micro-warp stays on eyes/forehead, not neck
    if jaw_blend:
        x0, y0, x1, y1 = roi
        fh = max(1, y1 - y0)
        y1b = y0 + int(fh * 0.72)  # drop lower ~28% (jaw)
        roi = (x0, y0, x1, min(h, y1b))
        meta["roi_jaw_shrunk"] = list(roi)
        meta["roi"] = list(roi)

    # 1) Face-center translation (safe, no scale), capped tighter
    M_face, face_meta = face_center_translation(rgb, dst_rgb)
    meta["steps"].append(face_meta)
    if M_face is not None:
        # Re-cap to 24px for face-local
        dx, dy = float(M_face[0, 2]), float(M_face[1, 2])
        if abs(dx) <= 24 and abs(dy) <= 24:
            delta = M_face
            meta["chosen"] = "face_center_translation"
        else:
            # Shrink toward limit
            scale = min(24.0 / max(abs(dx), 1e-3), 24.0 / max(abs(dy), 1e-3), 1.0)
            delta = np.array([[1.0, 0.0, dx * scale], [0.0, 1.0, dy * scale]], dtype=np.float32)
            meta["chosen"] = "face_center_translation_clamped"
            meta["clamp_scale"] = float(scale)
    # Phase2b: try anime-face partial affine (face-local) before ECC — better registration, less mush blend
    if delta is None and phase2b:
        M_aff, aff_meta = anime_face_micro_align(rgb, dst_rgb)
        meta["steps"].append(aff_meta)
        if M_aff is not None:
            dx, dy = float(M_aff[0, 2]), float(M_aff[1, 2])
            # Cap translation component; keep small scale from affine but clamp
            scale = float(np.sqrt(M_aff[0, 0] ** 2 + M_aff[0, 1] ** 2))
            if abs(dx) <= 28 and abs(dy) <= 28 and 0.92 <= scale <= 1.08:
                delta = M_aff
                meta["chosen"] = "anime_face_partial_affine"
            else:
                meta["steps"].append({"mode": "anime_face_phase2b_rejected", "dx": dx, "dy": dy, "scale": scale})

    # Face-iso: landmark quality gate (eyes/nose/mouth) before any mid-face blend
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

    if delta is None:
        # 2) ECC translation-only on tight face ROI
        g1 = cv2.cvtColor((np.clip(rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        g2 = cv2.cvtColor((np.clip(dst_rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        x0, y0, x1, y1 = roi
        warp = np.eye(2, 3, dtype=np.float32)
        m2 = np.zeros_like(g2, dtype=np.uint8)
        m2[y0:y1, x0:x1] = 255
        m2 = cv2.bitwise_and(m2, (dst_mask.astype(np.uint8) * 255))
        try:
            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5)
            cc, warp = cv2.findTransformECC(g2, g1, warp, cv2.MOTION_TRANSLATION, criteria, inputMask=m2, gaussFiltSize=5)
            # ECC supplies template->input sampling coordinates. apply_face_local_warp
            # uses warpAffine without WARP_INVERSE_MAP, so it needs input->template.
            sampling_warp = warp.copy()
            warp = ecc_to_forward(warp)
            dx, dy = float(warp[0, 2]), float(warp[1, 2])
            ecc_meta = {"mode": "ecc_translation", "cc": float(cc), "dx": dx, "dy": dy, "sampling_warp": sampling_warp.tolist(), "direction": "input_to_template"}
            meta["steps"].append(ecc_meta)
            if cc >= 0.2 and abs(dx) <= 24 and abs(dy) <= 24:
                delta = warp
                meta["chosen"] = "ecc_translation"
            else:
                meta["chosen"] = "none"
        except cv2.error as exc:
            meta["steps"].append({"mode": "ecc_failed", "error": str(exc)[:160]})
            meta["chosen"] = "none"

    base_iou = silhouette_iou(src_mask, dst_mask)
    feather = 20 if jaw_blend else 24
    feather_bottom = 56 if jaw_blend else None
    if delta is not None:
        warped2 = apply_face_local_warp(warped_rgba, delta, roi, feather=feather, feather_bottom=feather_bottom)
        iou = silhouette_iou(warped2[:, :, 3] > 127, dst_mask)
        # Face-local with tight ROI: allow tiny IoU dip (face_iso: stricter — no 4% regression)
        iou_ok = (iou + 0.002 >= base_iou) if face_iso else (iou + 0.01 >= base_iou * 0.96)
        if iou_ok:
            if face_iso:
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
                meta["weight_map"] = "soft_face"
            meta["accepted"] = True
            meta["iou_before"] = float(base_iou)
            meta["iou_after"] = float(iou)
            meta["face_local"] = True
            return warped2, matrix, float(iou), meta, wmap
        meta["accepted"] = False
        meta["reject_reason"] = "iou_regression"
        meta["iou_before"] = float(base_iou)
        meta["iou_after"] = float(iou)

    if face_iso:
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
    return warped_rgba, matrix, float(base_iou), meta, wmap


def landmark_warp(warped: np.ndarray, pairs_1024: list, size: int = 2048) -> np.ndarray:
    """Piecewise affine from landmark pairs in 1024-space (same as seed42 JSON)."""
    pairs = np.array(pairs_1024, dtype=np.float32) * (size / 1024.0)
    corners = np.array([[0, 0], [size - 1, 0], [0, size - 1], [size - 1, size - 1]], dtype=np.float32)
    srcpts = np.concatenate([pairs[:, 0], corners])
    dstpts = np.concatenate([pairs[:, 1], corners])
    triangulation = Delaunay(dstpts)
    yy, xx = np.mgrid[:size, :size]
    points = np.column_stack([xx.ravel(), yy.ravel()])
    idx = triangulation.find_simplex(points)
    if (idx < 0).any():
        # Fall back: skip landmark warp if triangulation fails
        return warped
    transform = triangulation.transform[idx]
    bc = np.einsum("nij,nj->ni", transform[:, :2], points - transform[:, 2])
    bc = np.column_stack([bc, 1 - bc.sum(axis=1)])
    mapped = np.einsum("ni,nij->nj", bc, srcpts[triangulation.simplices[idx]]).reshape(size, size, 2).astype(np.float32)
    return cv2.remap(warped, mapped[:, :, 0], mapped[:, :, 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def load_rgba(path: Path, size: int = 2048) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    # Fit inside square canvas preserving aspect (center), matching typical paint pad.
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    w, h = im.size
    scale = min(size / w, size / h)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2))
    return np.array(canvas)


def save_overlay(rgb: np.ndarray, target: np.ndarray, mask: np.ndarray, path: Path) -> None:
    overlay = rgb * 0.55 + np.zeros_like(rgb)
    # show baseline render tint via target region gray
    overlay = overlay.copy()
    overlay[target] = overlay[target] * 0.5 + 0.25
    out = (np.clip(overlay, 0, 1) * 255).astype(np.uint8)
    for m, col in [(target.astype(np.uint8), (255, 50, 50)), (mask.astype(np.uint8), (50, 255, 50))]:
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, contours, -1, col, 2)
    Image.fromarray(out).resize((1024, 1024)).save(path)


def make_sbs(input_img: Image.Image, a0: Image.Image, a3: Image.Image, crop: tuple[int, int, int, int], out: Path, labels=("input", "A0 paint", "A3 hybrid")) -> None:
    crops = []
    for im, lab in zip((input_img, a0, a3), labels):
        c = im.crop(crop).resize((512, 512), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (512, 544), (20, 20, 24))
        canvas.paste(c.convert("RGB"), (0, 32))
        arr = np.array(canvas)
        arr[:32, :] = (40, 40, 48)
        cv2.putText(arr, lab, (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 230), 1, cv2.LINE_AA)
        crops.append(Image.fromarray(arr))
    w = sum(c.width for c in crops) + 16 * (len(crops) - 1)
    sheet = Image.new("RGB", (w, crops[0].height), (12, 12, 16))
    x = 0
    for c in crops:
        sheet.paste(c, (x, 0))
        x += c.width + 16
    sheet.save(out)


def resolve_views(job: Path, views: list[str]) -> list[tuple[str, float, float, Path]]:
    prepared = job / "prepared"
    mapping = []
    # Candidate azims for left/right — pick better IoU later per view.
    azim_guess = {"front": 0, "back": 180, "right": 90, "left": 270}
    elev = 0.0
    for name in views:
        p = prepared / f"{name}.png"
        if not p.exists():
            continue
        mapping.append((name, elev, float(azim_guess.get(name, 0)), p))
    return mapping


def pick_azim(renderer: ProjectionRender, rgba: np.ndarray, elev: float, candidates: list[float]) -> tuple[float, float, np.ndarray]:
    best_az, best_iou, best_target = candidates[0], -1.0, None
    source = rgba[:, :, 3] > 127
    for az in candidates:
        rendered = renderer.render(elev, az, return_type="np")
        target = rendered[:, :, 3] > 0.5
        m = bbox_matrix(source, target)
        warped = warp_rgba(rgba, m)
        iou = silhouette_iou(warped[:, :, 3] > 127, target)
        if iou > best_iou:
            best_az, best_iou, best_target = az, iou, target
    return best_az, best_iou, best_target


def run(job: Path, out_dir: Path, landmarks_path: Path | None, vis_dir: Path | None, atlas_size: int = 2048, atlas_path: Path | None = None, color_glb: Path | None = None, pbr_glb: Path | None = None, jaw_blend: bool = False, phase2b: bool = False, extra_render_azims: list[float] | None = None, no_face_micro: bool = False, source_pbr: Path | None = None, mr_atlas: Path | None = None, face_iso: bool = False, exclusive_face: bool = False, search_oblique: bool = False, best_source: bool = False, front_back_only: bool = False, camera_azims: dict | None = None) -> dict:
    job = job.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if vis_dir:
        vis_dir.mkdir(parents=True, exist_ok=True)

    uv_path = job / "controls" / "uv_mesh.npz"
    if atlas_path is None:
        atlas_path = job / "paint" / "albedo_atlas_2K.png"
    else:
        atlas_path = Path(atlas_path)
    if not uv_path.exists():
        raise FileNotFoundError(f"missing UV cache: {uv_path}")
    if not atlas_path.exists():
        raise FileNotFoundError(f"missing Paint atlas: {atlas_path}")

    data = np.load(uv_path)
    mesh = trimesh.Trimesh(
        vertices=data["vertices"],
        faces=data["faces"],
        process=False,
        visual=trimesh.visual.TextureVisuals(uv=data["uv"]),
    )
    mesh.vertex_normals = data["vertex_normals"]
    base = np.asarray(Image.open(atlas_path).convert("RGB"), dtype=np.float32) / 255.0

    renderer = ProjectionRender(default_resolution=atlas_size, texture_size=atlas_size)
    renderer.load_mesh(mesh)
    renderer.set_texture(base)

    landmarks = {}
    if landmarks_path and landmarks_path.exists():
        landmarks = json.loads(landmarks_path.read_text(encoding="utf-8"))

    spec = json.loads((job / "project.json").read_text(encoding="utf-8"))
    view_names = [v for v in spec.get("views", ["front", "back", "left", "right"]) if (job / "prepared" / f"{v}.png").exists()]
    if not view_names:
        view_names = [p.stem for p in sorted((job / "prepared").glob("*.png"))]

    if front_back_only:
        view_names = [name for name in view_names if name in ("front", "back")]

    if face_iso:
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
        "no_face_micro": bool(no_face_micro),
        "job": str(job),
        "alignment": "bbox_iou_refine+front_micro" + ("+landmarks" if landmarks else ""),
        "production_accepted": False,
        "views": [],
        "blockers": [],
        "limitations": [
            "auto-align is silhouette IoU refine, not semantic landmarks",
            "reference lighting remains baked into projected regions",
            "geometry errors are unchanged",
            "no Meshy/Tripo parity claim",
        ],
    }
    start = time.monotonic()

    blend_sum = torch.zeros((atlas_size, atlas_size, 3), device="cuda")
    exclusive_front = None
    best_color = torch.zeros_like(blend_sum) if best_source else None
    best_weight = torch.zeros((atlas_size, atlas_size, 1), device="cuda") if best_source else None
    weight_sum = torch.zeros((atlas_size, atlas_size, 1), device="cuda")

    IOU_WARN = 0.72
    aligned_preview = {}

    for name in view_names:
        src_path = job / "prepared" / f"{name}.png"
        print(f"PROJECT {name}", flush=True)
        rgba = load_rgba(src_path, atlas_size)

        if name in ("front", "back"):
            candidates = [0.0] if name == "front" else [180.0]
            elev = 0.0
        elif name == "right":
            candidates = [90.0, 270.0]
            elev = 0.0
        elif name == "left":
            candidates = [270.0, 90.0]
            elev = 0.0
        else:
            candidates = [0.0]
            elev = 0.0

        if search_oblique and name in ("left", "right"):
            candidates = [90.,270.,30.,45.,60.,75.,285.,300.,315.,330.]

        if camera_azims and name in camera_azims:
            candidates = [float(camera_azims[name])]

        # Pick azim by bbox IoU when ambiguous
        best_az = candidates[0]
        best_pre_iou = -1.0
        best_target = None
        best_rendered = None
        source_mask = rgba[:, :, 3] > 127
        candidate_scores = []
        for az in candidates:
            rendered = renderer.render(elev, az, return_type="np")
            target = rendered[:, :, 3] > 0.5
            m0 = bbox_matrix(source_mask, target)
            w0 = warp_rgba(rgba, m0, atlas_size)
            iou0 = silhouette_iou(w0[:, :, 3] > 127, target)
            candidate_scores.append({"azim":az,"bbox_iou":float(iou0)})
            if iou0 > best_pre_iou:
                best_pre_iou, best_az, best_target, best_rendered = iou0, az, target, rendered

        elev, azim = elev, best_az
        rendered = best_rendered
        target = best_target

        base_m = bbox_matrix(source_mask, target)
        matrix, iou, align_meta = refine_alignment(rgba, target, base_m, atlas_size)
        align_meta["camera_candidates"] = candidate_scores
        warped = warp_rgba(rgba, matrix, atlas_size)

        used_landmarks = False
        if name in landmarks and isinstance(landmarks[name], list) and landmarks[name]:
            warped = landmark_warp(warped, landmarks[name], atlas_size)
            iou = silhouette_iou(warped[:, :, 3] > 127, target)
            used_landmarks = True
            align_meta["mode"] = "landmarks_piecewise_affine"
            align_meta["iou"] = float(iou)

        face_wmap = None
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
        if name == "front" and not used_landmarks:
            if no_face_micro:
                # Explicit fallback: weight map only, no micro warp (Zenko region-specific compare)
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
                else:
                    y, x = np.where(dst_mask)
                    if len(x):
                        x0, x1 = int(x.min()), int(x.max())
                        y0, y1 = int(y.min()), int(y.max())
                        fy1 = y0 + int(max(1, y1 - y0) * 0.22)
                        pad = int(0.03 * max(h, w))
                        mid = (x0 + x1) * 0.5
                        half = (x1 - x0) * 0.28
                        roi = (max(0, int(mid - half) - pad), max(0, y0 - pad), min(w, int(mid + half) + pad), min(h, fy1 + pad))
                if face_iso:
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
                    wm = "soft_face_forced_no_micro"
                micro_meta = {"accepted": False, "forced_no_micro": True, "weight_map": wm, "roi": list(roi)}
                align_meta["micro"] = micro_meta
                align_meta["mode"] = "bbox_iou_refine+forced_no_micro"
            else:
                warped, matrix, iou, micro_meta, face_wmap = micro_align_front(warped, rendered, matrix, jaw_blend=jaw_blend, phase2b=phase2b, face_iso=face_iso)
                align_meta["micro"] = micro_meta
                align_meta["iou"] = float(iou)
                if micro_meta.get("accepted"):
                    align_meta["mode"] = "bbox_iou_refine+" + str(micro_meta.get("chosen"))

        mask = (warped[:, :, 3] > 250).astype(np.uint8)
        alpha = np.clip(cv2.distanceTransform(mask, cv2.DIST_L2, 5) / 18.0, 0, 1)
        rgb = warped[:, :, :3].astype(np.float32) / 255.0
        if face_wmap is not None:
            alpha = np.clip(alpha * face_wmap, 0, 1)

        Image.fromarray(warped).resize((1024, 1024)).save(out_dir / f"{name}_aligned.png")
        save_overlay(rgb, target, mask > 0, out_dir / f"{name}_alignment_overlay.png")
        Image.fromarray((rendered.clip(0, 1) * 255).astype("uint8")).resize((1024, 1024)).save(out_dir / f"{name}_baseline.png")

        skip_project = (iou < IOU_WARN) and (not used_landmarks) and (name not in ("front", "back") or iou < 0.80)
        # Front/back: still project if IoU >= 0.80 (silhouette OK); sides skip below IOU_WARN to avoid wrap bleed.
        if name in ("left", "right") and iou < IOU_WARN and not used_landmarks:
            skip_project = True
        elif name in ("front", "back") and iou < 0.80 and not used_landmarks:
            skip_project = True
        else:
            skip_project = False

        if skip_project:
            view_report = {
                "name": name,
                "source": str(src_path),
                "sha256": sha256(src_path),
                "elev": elev,
                "azim": azim,
                "affine": matrix.tolist(),
                "align": align_meta,
                "silhouette_iou": float(iou),
                "used_landmarks": used_landmarks,
                "skipped_projection": True,
                "atlas_pixels_weight_above_half": 0,
            }
            report["views"].append(view_report)
            report["blockers"].append(
                {
                    "view": name,
                    "kind": "auto_align_low_iou_skipped",
                    "iou": float(iou),
                    "threshold": IOU_WARN if name in ("left", "right") else 0.80,
                    "note": "Projection skipped; Paint fill retained. Manual landmarks or better semantic align needed for this view.",
                }
            )
            aligned_preview[name] = (rgb, mask > 0, rendered)
            continue

        premult = np.concatenate([rgb * alpha[:, :, None], alpha[:, :, None]], axis=-1)
        tex, cos, _ = renderer.back_project(premult, elev, azim)
        a = tex[:, :, 3:4].clamp(0, 1)
        color = tex[:, :, :3] / a.clamp_min(1e-6)
        incidence = steeper_incidence(cos, phase2b=phase2b)
        # Slightly stronger front/back trust (HANDOFF note); Phase2b sides even lower if ever projected
        if phase2b:
            view_boost = 1.0 if name in ("front", "back") else 0.35
        else:
            view_boost = 1.0 if name in ("front", "back") else 0.55
        weight = a * incidence * view_boost
        if exclusive_face and name == 'front' and face_wmap is not None and align_meta.get('micro', {}).get('project_face'):
            # Experimental single-source mid-face: no Paint/side-view mixing here.
            face_mask = np.clip((face_wmap - 1.0) / 0.55, 0, 1)
            face_tex, _, _ = renderer.back_project(np.repeat(face_mask[:, :, None], 3, axis=2), elev, azim)
            gate = face_tex[:, :, :1].clamp(0, 1) * (a > .95) * (cos > .3)
            exclusive_front = (color, gate)
        if best_source:
            replace = weight > best_weight
            best_color = torch.where(replace, color, best_color)
            best_weight = torch.maximum(weight, best_weight)
        blend_sum += color * weight
        weight_sum += weight

        conf_img = (weight[:, :, 0].detach().cpu().numpy() * 255).astype("uint8")
        Image.fromarray(conf_img).save(out_dir / f"{name}_atlas_confidence.png")

        view_report = {
            "name": name,
            "source": str(src_path),
            "sha256": sha256(src_path),
            "elev": elev,
            "azim": azim,
            "affine": matrix.tolist(),
            "align": align_meta,
            "silhouette_iou": float(iou),
            "used_landmarks": used_landmarks,
            "atlas_pixels_weight_above_half": int((weight > 0.5).sum().item()),
        }
        report["views"].append(view_report)
        if iou < IOU_WARN and not used_landmarks:
            report["blockers"].append(
                {
                    "view": name,
                    "kind": "auto_align_low_iou",
                    "iou": float(iou),
                    "threshold": IOU_WARN,
                    "note": "IoU below soft warn but above skip threshold; projection applied with incidence gating.",
                }
            )
        aligned_preview[name] = (rgb, mask > 0, rendered)

    confidence = weight_sum.clamp(0, 1)
    projected = best_color if best_source else blend_sum / weight_sum.clamp_min(1e-6)
    report["projection_mix"] = "best_source_same_confidence" if best_source else "weighted_average"
    if best_source:
        np.savez_compressed(out_dir / "projection_components.npz",
                            base=np.asarray(base,dtype=np.float32),
                            selected=projected.detach().cpu().numpy(),
                            averaged=(blend_sum / weight_sum.clamp_min(1e-6)).detach().cpu().numpy(),
                            confidence=confidence.detach().cpu().numpy(),
                            strongest_weight=best_weight.detach().cpu().numpy())
    mixed = torch.as_tensor(base, device="cuda") * (1 - confidence) + projected * confidence
    if exclusive_front is not None:
        front_color, face_gate = exclusive_front
        mixed = mixed * (1 - face_gate) + front_color * face_gate
        report['exclusive_face_pixels'] = int((face_gate > .99).sum().item())
    atlas = Image.fromarray((mixed.clamp(0, 1).cpu().numpy() * 255).round().astype("uint8"))
    atlas_out = out_dir / "albedo_atlas_hybrid_a3_2K.png"
    atlas.save(atlas_out)
    Image.fromarray((confidence[:, :, 0].detach().cpu().numpy() * 255).astype("uint8")).save(out_dir / "confidence_atlas.png")

    # Export GLB next to job — do not touch textured_*.glb / output.glb
    mesh.visual.material = trimesh.visual.material.PBRMaterial(
        baseColorTexture=atlas, metallicFactor=0.0, roughnessFactor=0.8
    )
    mesh.vertex_normals = data["vertex_normals"]
    glb_color = Path(color_glb) if color_glb else (job / "textured_hybrid_a3_color.glb")
    glb_color.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(glb_color)

    # Optional PBR sibling: retain A0/source-bake MR pixels unchanged (albedo-only control).
    # Zenko invariant (Issue #1): hybrid PBR metallicRoughnessTexture RGBA hash must match A0 PBR.
    glb_pbr = None
    mr_tex = None
    metal_f, rough_f = 1.0, 1.0
    mr_retain_mode = None
    source_pbr_path = Path(source_pbr) if source_pbr else None
    mr_atlas_path = Path(mr_atlas) if mr_atlas else None
    if source_pbr_path and source_pbr_path.exists():
        mr_tex, metal_f, rough_f = load_mr_from_source_pbr(source_pbr_path)
        mr_retain_mode = "source_pbr_pixels"
    else:
        # Prefer MR atlas next to overridden --atlas (Phase1 A0 bake sibling)
        sibling = None
        if atlas_path is not None:
            cand = Path(atlas_path).parent / "mr_atlas_2K.png"
            if cand.exists():
                sibling = cand
        if mr_atlas_path and mr_atlas_path.exists():
            mr_tex = pack_mr_from_atlas(mr_atlas_path)
            mr_retain_mode = "mr_atlas_repack"
        elif sibling is not None:
            mr_tex = pack_mr_from_atlas(sibling)
            mr_retain_mode = "atlas_sibling_repack"
        elif (job / "paint" / "mr_atlas_2K.png").exists():
            mr_tex = pack_mr_from_atlas(job / "paint" / "mr_atlas_2K.png")
            mr_retain_mode = "job_paint_repack_WARN_may_break_A0_invariant"
            report["blockers"].append(
                {
                    "kind": "mr_source_fallback_job_paint",
                    "note": "PBR MR packed from job/paint/mr_atlas_2K.png; may differ from A0 Phase1 MR. Pass --source-pbr A0 PBR GLB to retain exact pixels.",
                }
            )
    if mr_tex is not None:
        mesh.visual.material = trimesh.visual.material.PBRMaterial(
            baseColorTexture=atlas,
            metallicRoughnessTexture=mr_tex,
            metallicFactor=metal_f,
            roughnessFactor=rough_f,
        )
        mesh.vertex_normals = data["vertex_normals"]
        glb_pbr = Path(pbr_glb) if pbr_glb else (job / "textured_hybrid_a3_pbr.glb")
        glb_pbr.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(glb_pbr)
        report["mr_retain_mode"] = mr_retain_mode
        report["mr_source_pbr"] = str(source_pbr_path) if source_pbr_path else None

    renderer.set_texture(np.array(atlas, dtype=np.float32) / 255.0)
    # Also render A0 baseline flat views for A/B
    a0_renderer = ProjectionRender(default_resolution=atlas_size, texture_size=atlas_size)
    a0_renderer.load_mesh(mesh)
    a0_renderer.set_texture(base)

    flat = {}
    azim_list = [("front", 0), ("back", 180), ("side", 90), ("m35", -35), ("p35", 35), ("m90", -90), ("p90", 90)]
    if extra_render_azims:
        for i, az in enumerate(extra_render_azims):
            azim_list.append((f"az{int(az)}" if az == int(az) else f"az{az}", float(az)))
    # dedupe by angle
    seen = set()
    uniq = []
    for label, ang in azim_list:
        key = float(ang) % 360.0
        if key in seen:
            continue
        seen.add(key)
        uniq.append((label, float(ang)))
    conf_np = confidence[:, :, 0].detach().cpu().numpy()
    for label, ang in uniq:
        im_a3 = renderer.render(0, ang, return_type="np")
        im_a0 = a0_renderer.render(0, ang, return_type="np")
        p_a3 = out_dir / f"{label}_result_a3.png"
        p_a0 = out_dir / f"{label}_result_a0.png"
        Image.fromarray((im_a3.clip(0, 1) * 255).astype("uint8")).resize((1024, 1024)).save(p_a3)
        Image.fromarray((im_a0.clip(0, 1) * 255).astype("uint8")).resize((1024, 1024)).save(p_a0)
        flat[label] = (Image.open(p_a0).convert("RGB"), Image.open(p_a3).convert("RGB"))
        # Screen-space coverage proxy: silhouette mask of hybrid render
        cov = (im_a3[:, :, 3] > 0.5).astype(np.uint8) * 255
        Image.fromarray(cov).resize((1024, 1024), Image.Resampling.NEAREST).save(out_dir / f"{label}_coverage_mask.png")
    # Atlas confidence already saved; also write normalized preview
    Image.fromarray((np.clip(conf_np, 0, 1) * 255).astype("uint8")).resize((1024, 1024)).save(out_dir / "confidence_atlas_preview.png")

    # Side-by-side crops into vis_dir
    if vis_dir:
        # Front face / chest / full
        front_in = Image.open(job / "prepared" / "front.png").convert("RGB")
        # Normalize input to 1024 square letterbox for fair crop coords
        fin = Image.new("RGB", (1024, 1024), (0, 0, 0))
        w, h = front_in.size
        sc = min(1024 / w, 1024 / h)
        nw, nh = int(w * sc), int(h * sc)
        front_in_sq = front_in.resize((nw, nh), Image.Resampling.LANCZOS)
        fin.paste(front_in_sq, ((1024 - nw) // 2, (1024 - nh) // 2))
        a0f, a3f = flat["front"]
        crops = {
            "front_face": (380, 40, 644, 320),
            "front_jaw": (380, 160, 644, 420),
            "front_chest": (360, 280, 664, 560),
            "front_full": (256, 0, 768, 1024),
            "back_full": (256, 0, 768, 1024),
            "side_full": (256, 0, 768, 1024),
        }
        for key, box in crops.items():
            if key.startswith("front"):
                make_sbs(fin, a0f, a3f, box, vis_dir / f"sbs_{key}.png")
            elif key.startswith("back"):
                binp = Image.open(job / "prepared" / "back.png").convert("RGB")
                bsq = Image.new("RGB", (1024, 1024), (0, 0, 0))
                w, h = binp.size
                sc = min(1024 / w, 1024 / h)
                nw, nh = int(w * sc), int(h * sc)
                bsq.paste(binp.resize((nw, nh), Image.Resampling.LANCZOS), ((1024 - nw) // 2, (1024 - nh) // 2))
                make_sbs(bsq, flat["back"][0], flat["back"][1], box, vis_dir / f"sbs_{key}.png")
            else:
                # side: use left prepared if present
                side_src = job / "prepared" / "left.png"
                if not side_src.exists():
                    side_src = job / "prepared" / "right.png"
                sinp = Image.open(side_src).convert("RGB")
                ssq = Image.new("RGB", (1024, 1024), (0, 0, 0))
                w, h = sinp.size
                sc = min(1024 / w, 1024 / h)
                nw, nh = int(w * sc), int(h * sc)
                ssq.paste(sinp.resize((nw, nh), Image.Resampling.LANCZOS), ((1024 - nw) // 2, (1024 - nh) // 2))
                make_sbs(ssq, flat["side"][0], flat["side"][1], box, vis_dir / f"sbs_{key}.png")

        # Also copy flat results into vis
        for label in ("front", "back", "side"):
            flat[label][0].save(vis_dir / f"a0_{label}.png")
            flat[label][1].save(vis_dir / f"a3_{label}.png")
        atlas.save(vis_dir / "albedo_atlas_hybrid_a3_2K.png")
        Image.fromarray((base * 255).astype("uint8")).save(vis_dir / "albedo_atlas_a0_2K.png")

    report.update(
        {
            "seconds": time.monotonic() - start,
            "atlas": str(atlas_out),
            "glb_color": str(glb_color),
            "glb_pbr": str(glb_pbr) if glb_pbr else None,
            "vis_dir": str(vis_dir) if vis_dir else None,
            "confidence_pixels_above_half": int((confidence > 0.5).sum().item()),
            "mean_confidence": float(confidence.mean().item()),
        }
    )
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return report


def main():
    p = argparse.ArgumentParser(description="Hybrid A3 Paint-fill + ortho projection")
    p.add_argument("--job", required=True, help="Studio/lab job directory")
    p.add_argument("--out", default=None, help="Output folder (default: <job>/hybrid_a3)")
    p.add_argument("--landmarks", default=None, help="Optional landmarks JSON (seed42-style)")
    p.add_argument("--vis", default=None, help="Side-by-side export dir")
    p.add_argument("--atlas", default=None, help="Override paint albedo atlas (e.g. Phase1 A0 bake)")
    p.add_argument("--color-glb", default=None, help="Override color GLB output path")
    p.add_argument("--pbr-glb", default=None, help="Override PBR GLB output path")
    p.add_argument("--jaw-blend", action="store_true", help="Face-local micro + Paint-prefer jaw/neck feather; keep chest projection")
    p.add_argument("--phase2b", action="store_true", help="Phase2b: jaw ROI + steeper side falloff + anime-face align; hard jaw Paint; extra ±35/±90 renders")
    p.add_argument("--no-face-micro", action="store_true", help="Skip face micro-align; keep phase2b/jaw weight maps only (explicit fallback)")
    p.add_argument("--face-iso", action="store_true", help="Isolated face correction: P2 incidence; coherent face source (project-all or paint-all); freeze torso/back")
    p.add_argument("--source-pbr", default=None, help="Baseline PBR GLB whose metallicRoughnessTexture pixels are retained unchanged (A0 bake)")
    p.add_argument("--mr-atlas", default=None, help="Optional raw MR atlas to pack (prefer --source-pbr for exact A0 pixel retain)")
    args = p.parse_args()
    job = Path(args.job)
    out = Path(args.out) if args.out else job / "hybrid_a3"
    landmarks = Path(args.landmarks) if args.landmarks else None
    # default landmarks next to job or lab if present and matching
    if landmarks is None:
        cand = job / "projection_landmarks.json"
        if cand.exists():
            landmarks = cand
    vis = Path(args.vis) if args.vis else None
    atlas = Path(args.atlas) if args.atlas else None
    color_glb = Path(args.color_glb) if args.color_glb else None
    pbr_glb = Path(args.pbr_glb) if args.pbr_glb else None
    source_pbr = Path(args.source_pbr) if args.source_pbr else None
    mr_atlas = Path(args.mr_atlas) if args.mr_atlas else None
    run(job, out, landmarks, vis, atlas_path=atlas, color_glb=color_glb, pbr_glb=pbr_glb, jaw_blend=bool(args.jaw_blend), phase2b=bool(args.phase2b), no_face_micro=bool(args.no_face_micro), source_pbr=source_pbr, mr_atlas=mr_atlas, face_iso=bool(args.face_iso))


if __name__ == "__main__":
    main()

