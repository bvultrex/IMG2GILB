"""General deterministic automatic ROI proposal.

Modes:
- bust: delegates to the already accepted mechanical-bust v3 proposer.
- fullbody: proposes a head/upper-torso detail ROI from foreground + detail energy.
- object: proposes a central detail-rich ROI without body-specific vertical limits.

No evaluation reference crop is read by inference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import auto_roi_bust_v2 as bust_v2
import auto_roi_bust_v3 as bust_v3

REPO = Path(__file__).resolve().parents[1]
DEFAULT_RANGER = REPO / "fixtures" / "ranger_ortho_v1" / "front.png"
DEFAULT_RANGER_OUT = Path(r"D:\SF3D_QualityLab\ranger_validation\ortho_v1")


def largest_component(mask: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        raise RuntimeError("No foreground component found.")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    return labels == int(np.argmax(sizes))


def rect_area(rect: np.ndarray) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def rect_intersection(a: np.ndarray, b: np.ndarray) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def rect_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = rect_intersection(a, b)
    union = rect_area(a) + rect_area(b) - inter
    return float(inter / union) if union > 0 else 0.0


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    keep = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(keep):
        raise RuntimeError("No positive weights for quantile.")
    values, weights = values[keep], weights[keep]
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cumulative = np.cumsum(weights)
    cutoff = q * cumulative[-1]
    idx = min(len(values) - 1, np.searchsorted(cumulative, cutoff, side="left"))
    return float(values[idx])


def foreground_mask(image: Image.Image, sensitivity: float = 1.0) -> tuple[np.ndarray, dict]:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[:, :, :3].astype(np.float64) / 255.0
    alpha = rgba[:, :, 3].astype(np.float64) / 255.0
    h, w = alpha.shape

    alpha_span = float(alpha.max() - alpha.min())
    alpha_fraction_nonopaque = float(np.mean(alpha < 0.995))
    if alpha_span > 0.20 and alpha_fraction_nonopaque > 0.01:
        threshold = float(np.clip(0.50 * sensitivity, 0.20, 0.80))
        raw = alpha >= threshold
        source = "alpha"
        source_threshold = threshold
    else:
        border = max(2, int(round(min(h, w) * 0.025)))
        border_pixels = np.concatenate(
            [
                rgb[:border].reshape(-1, 3),
                rgb[-border:].reshape(-1, 3),
                rgb[:, :border].reshape(-1, 3),
                rgb[:, -border:].reshape(-1, 3),
            ],
            axis=0,
        )
        bg = np.median(border_pixels, axis=0)
        dist = np.linalg.norm(rgb - bg[None, None, :], axis=2)
        border_dist = np.concatenate(
            [
                dist[:border].ravel(),
                dist[-border:].ravel(),
                dist[:, :border].ravel(),
                dist[:, -border:].ravel(),
            ]
        )
        base = max(0.055, float(np.quantile(border_dist, 0.995)) + 0.020)
        threshold = float(base * sensitivity)
        raw = dist >= threshold
        source = "border_rgb_distance"
        source_threshold = threshold

    # Stabilize masks from anti-aliased outlines and tiny detached specks.
    close_iter = max(1, int(round(min(h, w) * 0.002)))
    raw = ndimage.binary_closing(raw, iterations=close_iter)
    raw = ndimage.binary_fill_holes(raw)
    foreground = largest_component(raw)

    ys, xs = np.where(foreground)
    if len(xs) < 100:
        raise RuntimeError("Foreground is too small.")
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]

    return foreground, {
        "foreground_source": source,
        "foreground_threshold": source_threshold,
        "background_rgb": bg.tolist() if source == "border_rgb_distance" else None,
        "foreground_pixels": int(foreground.sum()),
        "foreground_bbox_px": bbox,
    }


def detail_density(rgb_u8: np.ndarray, foreground: np.ndarray, mode: str, bbox: list[int]) -> tuple[np.ndarray, dict]:
    h, w, _ = rgb_u8.shape
    x0, y0, x1, y1 = bbox
    object_h = max(1, y1 - y0)
    object_w = max(1, x1 - x0)

    rgb = rgb_u8.astype(np.float64) / 255.0
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    smooth = ndimage.gaussian_filter(lum, sigma=max(1.0, min(h, w) * 0.0015))
    gx = ndimage.sobel(smooth, axis=1, mode="nearest")
    gy = ndimage.sobel(smooth, axis=0, mode="nearest")
    grad = np.hypot(gx, gy)

    erosion = max(2, int(round(min(h, w) * 0.004)))
    inner = ndimage.binary_erosion(foreground, iterations=erosion)
    if inner.sum() < 100:
        inner = foreground.copy()

    valid = inner.copy()
    if mode == "fullbody":
        upper_limit = min(y1, y0 + int(round(0.48 * object_h)))
        band = np.zeros_like(valid)
        band[y0:upper_limit, x0:x1] = True
        valid &= band
    else:
        upper_limit = y1

    vals = grad[valid]
    if vals.size < 100:
        raise RuntimeError("Too few pixels for detail-energy localization.")

    floor = float(np.quantile(vals, 0.55))
    cap = float(np.quantile(vals, 0.995))
    energy = np.clip(grad - floor, 0.0, max(cap - floor, 1e-12))
    energy *= valid

    # Suppress full-width T-pose arms and broad object extremities without forcing
    # exact symmetry. Object mode uses a weaker center preference.
    cx = 0.5 * (x0 + x1)
    xx = np.arange(w, dtype=np.float64)
    sigma_fraction = 0.20 if mode == "fullbody" else 0.32
    sigma_x = max(1.0, sigma_fraction * object_w)
    center_prior = np.exp(-0.5 * ((xx - cx) / sigma_x) ** 2)
    energy *= center_prior[None, :]

    sigma = max(2.0, min(h, w) * 0.009)
    density = ndimage.gaussian_filter(energy, sigma=sigma)
    density *= valid

    return density, {
        "erosion_px": erosion,
        "detail_upper_limit_y_px": int(upper_limit),
        "gradient_floor": floor,
        "gradient_cap": cap,
        "density_sigma_px": float(sigma),
    }


def propose_nonbust(image: Image.Image, mode: str, sensitivity: float = 1.0) -> dict:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[:, :, :3]
    h, w, _ = rgb.shape

    foreground, fg_diag = foreground_mask(image, sensitivity)
    x0, y0, x1, y1 = fg_diag["foreground_bbox_px"]
    object_h = max(1, y1 - y0)
    object_w = max(1, x1 - x0)

    density, density_diag = detail_density(rgb, foreground, mode, [x0, y0, x1, y1])
    if density.sum() <= 0:
        raise RuntimeError("No usable detail density.")

    xw = density.sum(axis=0)
    yw = density.sum(axis=1)
    xs = np.arange(w, dtype=np.float64)
    ys = np.arange(h, dtype=np.float64)

    if mode == "fullbody":
        q_left, q_right = 0.10, 0.90
        min_width, max_width = 0.20 * object_w, 0.46 * object_w
        min_height, max_height = 0.20 * object_h, 0.42 * object_h
        q_bottom = 0.94
    else:
        q_left, q_right = 0.08, 0.92
        min_width, max_width = 0.22 * object_w, 0.70 * object_w
        min_height, max_height = 0.20 * object_h, 0.70 * object_h
        q_bottom = 0.92

    left_raw = weighted_quantile(xs, xw, q_left)
    right_raw = weighted_quantile(xs, xw, q_right)
    center_x = 0.5 * (left_raw + right_raw)
    width = float(np.clip((right_raw - left_raw) * 1.12, min_width, max_width))
    left, right = center_x - width * 0.5, center_x + width * 0.5

    top_energy = weighted_quantile(ys, yw, 0.03)
    bottom_energy = weighted_quantile(ys, yw, q_bottom)
    if mode == "fullbody":
        top = min(float(y0), top_energy - 0.015 * object_h)
    else:
        top = top_energy - 0.04 * object_h
    bottom = bottom_energy + 0.035 * object_h
    height = bottom - top
    target_h = float(np.clip(height, min_height, max_height))
    if height != target_h:
        center_y = 0.5 * (top + bottom)
        top, bottom = center_y - target_h * 0.5, center_y + target_h * 0.5

    if mode == "fullbody":
        top = max(0.0, min(top, y0 + 0.04 * object_h))
        bottom = min(bottom, y0 + 0.48 * object_h)

    rect = np.array([left / w, top / h, right / w, bottom / h], dtype=np.float64)
    rect[[0, 2]] = np.clip(rect[[0, 2]], 0.0, 1.0)
    rect[[1, 3]] = np.clip(rect[[1, 3]], 0.0, 1.0)

    return {
        "proposal": rect,
        "foreground": foreground,
        "object_bbox_normalized": [x0 / w, y0 / h, x1 / w, y1 / h],
        "object_bbox_px": [x0, y0, x1, y1],
        "image_size": [w, h],
        "mode": mode,
        "sensitivity": float(sensitivity),
        **fg_diag,
        **density_diag,
    }


def proposal_metrics(result: dict) -> dict:
    rect = np.asarray(result["proposal"], dtype=np.float64)
    fg = result["foreground"]
    h, w = fg.shape
    x0, y0, x1, y1 = result["object_bbox_px"]
    object_h = max(1, y1 - y0)
    object_w = max(1, x1 - x0)

    px = np.array(
        [
            int(np.floor(rect[0] * w)),
            int(np.floor(rect[1] * h)),
            int(np.ceil(rect[2] * w)),
            int(np.ceil(rect[3] * h)),
        ]
    )
    px[[0, 2]] = np.clip(px[[0, 2]], 0, w)
    px[[1, 3]] = np.clip(px[[1, 3]], 0, h)

    roi_mask = np.zeros_like(fg)
    roi_mask[px[1]:px[3], px[0]:px[2]] = True

    # Evaluation-only proxy for fullbody: central upper silhouette, not a golden crop.
    cx = 0.5 * (x0 + x1)
    eval_left = int(max(x0, cx - 0.28 * object_w))
    eval_right = int(min(x1, cx + 0.28 * object_w))
    eval_bottom = int(min(y1, y0 + 0.42 * object_h))
    upper_central = np.zeros_like(fg)
    upper_central[y0:eval_bottom, eval_left:eval_right] = True
    upper_central &= fg
    central_total = int(upper_central.sum())
    central_covered = int((upper_central & roi_mask).sum())

    object_area = max(1, (x1 - x0) * (y1 - y0))
    roi_area_px = max(0, (px[2] - px[0]) * (px[3] - px[1]))
    top_offset = (px[1] - y0) / object_h
    bottom_position = (px[3] - y0) / object_h

    return {
        "central_upper_silhouette_coverage": float(central_covered / central_total) if central_total else 0.0,
        "proposal_area_fraction_of_object_bbox": float(roi_area_px / object_area),
        "proposal_top_offset_object_height": float(top_offset),
        "proposal_bottom_position_object_height": float(bottom_position),
        "evaluation_upper_central_bbox_px": [eval_left, y0, eval_right, eval_bottom],
    }


def draw_overlay(image: Image.Image, result: dict, output: Path) -> None:
    im = image.convert("RGBA")
    draw = ImageDraw.Draw(im)
    w, h = im.size
    rect = np.asarray(result["proposal"])

    proposal = (
        int(round(rect[0] * w)),
        int(round(rect[1] * h)),
        int(round(rect[2] * w)),
        int(round(rect[3] * h)),
    )
    obj = tuple(result["object_bbox_px"])
    eval_box = tuple(proposal_metrics(result)["evaluation_upper_central_bbox_px"])

    # Grayscale-coded: object bbox dark, evaluation proxy mid-gray, proposal white.
    draw.rectangle(obj, outline=(35, 35, 35, 255), width=3)
    draw.rectangle(eval_box, outline=(145, 145, 145, 255), width=3)
    draw.rectangle(proposal, outline=(255, 255, 255, 255), width=5)
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output)


def run_general(image: Image.Image, mode: str) -> dict:
    sensitivities = [0.85, 1.0, 1.15]
    variants = []
    for sensitivity in sensitivities:
        variants.append(propose_nonbust(image, mode, sensitivity))

    baseline = variants[1]
    base_rect = np.asarray(baseline["proposal"], dtype=np.float64)
    stability = [
        rect_iou(np.asarray(v["proposal"], dtype=np.float64), base_rect)
        for i, v in enumerate(variants)
        if i != 1
    ]
    metrics = proposal_metrics(baseline)

    if mode == "fullbody":
        gate = bool(
            min(stability) >= 0.80
            and metrics["central_upper_silhouette_coverage"] >= 0.60
            and 0.04 <= metrics["proposal_area_fraction_of_object_bbox"] <= 0.35
            and metrics["proposal_top_offset_object_height"] <= 0.08
            and metrics["proposal_bottom_position_object_height"] <= 0.50
        )
    else:
        gate = bool(
            min(stability) >= 0.80
            and 0.04 <= metrics["proposal_area_fraction_of_object_bbox"] <= 0.55
        )

    return {
        "proposal_normalized_xyxy": base_rect.tolist(),
        "mode": mode,
        "foreground_source": baseline["foreground_source"],
        "object_bbox_normalized": baseline["object_bbox_normalized"],
        "sensitivity_proposals": {
            str(s): variants[i]["proposal"].tolist() for i, s in enumerate(sensitivities)
        },
        "min_sensitivity_stability_iou": float(min(stability)),
        **metrics,
        "general_fixture_gate_passed": gate,
        "production_accepted": False,
        "method": {
            "foreground": "alpha when informative, otherwise border-RGB-distance largest component",
            "localizer": "luminance gradient detail density within foreground",
            "mode_policy": "fullbody uses upper-region and stronger center prior; object uses whole foreground",
            "golden_crop_used_for_inference": False,
        },
        "diagnostics": {
            key: value
            for key, value in baseline.items()
            if key not in {"proposal", "foreground"}
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["bust", "fullbody", "object"], required=True)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args()

    if args.mode == "bust":
        if args.image:
            image_path = args.image
        else:
            image_path = bust_v2.resolve_default_image(
                Path(r"D:\SF3D_QualityLab\bust_validation"),
                Path(r"D:\SF3D_QualityLab"),
            )
        image = Image.open(image_path).convert("RGBA")
        result = bust_v3.propose(image, 0.50)
        rect = np.asarray(result["proposal"], dtype=np.float64)
        report = {
            "mode": "bust",
            "input": str(image_path),
            "proposal_normalized_xyxy": rect.tolist(),
            "implementation": "delegates to accepted auto_roi_bust_v3",
            "production_accepted": False,
        }
        output = args.output or Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_general_bust.json")
        overlay_path = args.overlay or Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation\auto_roi_general_bust_overlay.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        # No golden crop in generic overlay, only proposal.
        generic = image.copy()
        draw = ImageDraw.Draw(generic)
        w, h = generic.size
        draw.rectangle(
            (int(rect[0]*w), int(rect[1]*h), int(rect[2]*w), int(rect[3]*h)),
            outline=(255,255,255,255),
            width=5,
        )
        generic.save(overlay_path)
        print(json.dumps(report, indent=2))
        return

    image_path = args.image or DEFAULT_RANGER
    if not image_path.exists():
        raise FileNotFoundError(f"Input fixture not found: {image_path}")
    image = Image.open(image_path).convert("RGBA")
    report = run_general(image, args.mode)
    report["input"] = str(image_path)

    root = DEFAULT_RANGER_OUT
    output = args.output or root / f"auto_roi_general_v1_{args.mode}.json"
    overlay_path = args.overlay or root / f"auto_roi_general_v1_{args.mode}_overlay.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    baseline = propose_nonbust(image, args.mode, 1.0)
    draw_overlay(image, baseline, overlay_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
