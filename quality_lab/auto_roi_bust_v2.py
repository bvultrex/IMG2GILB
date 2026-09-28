"""Deterministic appearance-guided automatic ROI proposal for the bust fixture.

V2 keeps BRIA alpha for foreground isolation, but localizes the inner hood/lens
assembly with RGB edge/detail energy. The known fixture crop is evaluation-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

DEFAULT_ROOT = Path(r"D:\SF3D_QualityLab\bust_validation")
DEFAULT_LAB = Path(r"D:\SF3D_QualityLab")
KNOWN_CROP = np.array([0.32, 0.015, 0.675, 0.36], dtype=np.float64)


def largest_component(mask: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        raise RuntimeError("No foreground in BRIA alpha.")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    return labels == int(np.argmax(sizes))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    keep = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(keep):
        raise RuntimeError("No positive weights for weighted quantile.")
    values = values[keep]
    weights = weights[keep]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights)
    cutoff = q * cumulative[-1]
    return float(values[min(len(values) - 1, np.searchsorted(cumulative, cutoff, side="left"))])


def rect_area(rect: np.ndarray) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def rect_intersection(a: np.ndarray, b: np.ndarray) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def rect_metrics(proposal: np.ndarray, known: np.ndarray) -> dict:
    inter = rect_intersection(proposal, known)
    pa, ka = rect_area(proposal), rect_area(known)
    union = pa + ka - inter
    pc = np.array([(proposal[0] + proposal[2]) * 0.5, (proposal[1] + proposal[3]) * 0.5])
    kc = np.array([(known[0] + known[2]) * 0.5, (known[1] + known[3]) * 0.5])
    return {
        "bbox_iou": float(inter / union) if union else 0.0,
        "known_crop_coverage": float(inter / ka) if ka else 0.0,
        "proposal_coverage_by_known": float(inter / pa) if pa else 0.0,
        "center_error_normalized": float(np.linalg.norm(pc - kc)),
        "corner_mae_normalized": float(np.abs(proposal - known).mean()),
        "proposal_area_normalized": float(pa),
        "known_area_normalized": float(ka),
    }


def detail_energy(rgb: np.ndarray, foreground: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[np.ndarray, dict]:
    h, w, _ = rgb.shape
    x0, y0, x1, y1 = bbox
    object_h = max(1, y1 - y0)
    object_w = max(1, x1 - x0)

    # Luminance and multi-scale gradient.  The Gaussian prefilter suppresses
    # single-pixel texture noise but retains mechanical edges/lens rings.
    rgbf = rgb.astype(np.float64) / 255.0
    lum = 0.2126 * rgbf[:, :, 0] + 0.7152 * rgbf[:, :, 1] + 0.0722 * rgbf[:, :, 2]
    smooth = ndimage.gaussian_filter(lum, sigma=max(1.0, min(h, w) * 0.0015))
    gx = ndimage.sobel(smooth, axis=1, mode="nearest")
    gy = ndimage.sobel(smooth, axis=0, mode="nearest")
    grad = np.hypot(gx, gy)

    # Remove the outer alpha silhouette so it cannot dominate the ROI.
    erosion_px = max(4, int(round(min(h, w) * 0.008)))
    inner = ndimage.binary_erosion(foreground, iterations=erosion_px)
    if inner.sum() < 100:
        inner = foreground.copy()

    # The known failure is a local upper-body detail. This broad relative band is
    # semantic task context, not fixture crop coordinates.
    upper_limit = min(y1, y0 + int(round(0.47 * object_h)))
    band = np.zeros_like(inner)
    band[y0:upper_limit, x0:x1] = True
    valid = inner & band

    vals = grad[valid]
    if vals.size < 100:
        raise RuntimeError("Too few valid pixels for detail-energy ROI.")

    # Robustly suppress weak shading gradients and retain structural detail.
    floor = float(np.quantile(vals, 0.60))
    cap = float(np.quantile(vals, 0.995))
    energy = np.clip(grad - floor, 0.0, max(cap - floor, 1e-12))
    energy *= valid

    # Prefer the central upper-object cluster. This is deliberately soft, so
    # asymmetric lens placement can still pull the ROI away from exact center.
    cx = 0.5 * (x0 + x1)
    xx = np.arange(w, dtype=np.float64)
    sigma_x = max(1.0, 0.28 * object_w)
    center_prior = np.exp(-0.5 * ((xx - cx) / sigma_x) ** 2)
    energy *= center_prior[None, :]

    # Convert sparse edges into a stable density map.
    sigma_density = max(2.0, min(h, w) * 0.010)
    density = ndimage.gaussian_filter(energy, sigma=sigma_density)
    density *= valid

    return density, {
        "erosion_px": erosion_px,
        "upper_limit_y_px": int(upper_limit),
        "gradient_floor": floor,
        "gradient_cap": cap,
        "density_sigma_px": float(sigma_density),
    }


def propose(image: Image.Image, alpha_threshold: float = 0.50) -> dict:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3].astype(np.float64) / 255.0
    h, w = alpha.shape

    foreground = largest_component(alpha >= alpha_threshold)
    ys, xs = np.where(foreground)
    if len(xs) < 100:
        raise RuntimeError("Foreground too small.")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    object_h = max(1, y1 - y0)
    object_w = max(1, x1 - x0)

    density, energy_diag = detail_energy(rgb, foreground, (x0, y0, x1, y1))
    total = float(density.sum())
    if total <= 0:
        raise RuntimeError("No usable detail energy.")

    x_weights = density.sum(axis=0)
    x_coords = np.arange(w, dtype=np.float64)
    # Central 76% of weighted detail energy, then modest context padding.
    ql = weighted_quantile(x_coords, x_weights, 0.12)
    qr = weighted_quantile(x_coords, x_weights, 0.88)
    raw_w = max(1.0, qr - ql)
    pad_x = 0.10 * raw_w
    left, right = ql - pad_x, qr + pad_x

    # Keep the inferred width in a broad, task-level range relative to the object.
    # This is not fitted to the ground-truth crop and mainly rejects pathological
    # "whole upper body" selections.
    min_width = 0.28 * object_w
    max_width = 0.58 * object_w
    center = 0.5 * (left + right)
    width = float(np.clip(right - left, min_width, max_width))
    left, right = center - width * 0.5, center + width * 0.5

    # Use detail energy for the lower edge. The hood crop should start at the
    # foreground top, while the lower edge follows where upper mechanical detail
    # energy has mostly accumulated.
    y_weights = density[:, max(0, int(left)):min(w, int(np.ceil(right)))].sum(axis=1)
    y_coords = np.arange(h, dtype=np.float64)
    y_energy_92 = weighted_quantile(y_coords, y_weights, 0.92)
    bottom = y_energy_92 + 0.035 * object_h
    bottom = float(np.clip(bottom, y0 + 0.28 * object_h, y0 + 0.42 * object_h))

    top = float(max(0.0, y0 - 0.006 * object_h))
    proposal = np.array([left / w, top / h, right / w, bottom / h], dtype=np.float64)
    proposal[[0, 2]] = np.clip(proposal[[0, 2]], 0.0, 1.0)
    proposal[[1, 3]] = np.clip(proposal[[1, 3]], 0.0, 1.0)

    return {
        "proposal": proposal,
        "foreground_bbox": [x0 / w, y0 / h, x1 / w, y1 / h],
        "image_size": [int(w), int(h)],
        "foreground_pixels": int(foreground.sum()),
        "object_width_px": int(object_w),
        "object_height_px": int(object_h),
        "detail_energy_total": total,
        "x_energy_q12_px": float(ql),
        "x_energy_q88_px": float(qr),
        "y_energy_q92_px": float(y_energy_92),
        "alpha_threshold": float(alpha_threshold),
        **energy_diag,
    }


def resolve_default_image(root: Path, lab: Path) -> Path:
    record = json.loads((root / "test.json").read_text(encoding="utf-8"))
    path = lab / "app_jobs" / str(record["job"]) / "prepared" / "front.png"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def overlay(image: Image.Image, proposal: np.ndarray, known: np.ndarray, output: Path) -> None:
    im = image.convert("RGBA")
    draw = ImageDraw.Draw(im)
    w, h = im.size

    def box(rect):
        return tuple(int(round(v * (w if i % 2 == 0 else h))) for i, v in enumerate(rect))

    # Grayscale-coded for color-vision accessibility.
    kb, pb = box(known), box(proposal)
    draw.rectangle(kb, outline=(0, 0, 0, 255), width=8)
    draw.rectangle(kb, outline=(145, 145, 145, 255), width=3)
    draw.rectangle(pb, outline=(255, 255, 255, 255), width=4)
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--lab", type=Path, default=DEFAULT_LAB)
    parser.add_argument("--output", type=Path, default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v2.json")
    parser.add_argument("--overlay", type=Path, default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v2_overlay.png")
    args = parser.parse_args()

    path = args.image or resolve_default_image(args.root, args.lab)
    image = Image.open(path).convert("RGBA")

    main_result = propose(image, 0.50)
    proposal = main_result["proposal"]
    comparison = rect_metrics(proposal, KNOWN_CROP)

    thresholds = [0.35, 0.50, 0.65]
    threshold_proposals = {}
    stability = []
    for threshold in thresholds:
        result = propose(image, threshold)
        rect = result["proposal"]
        threshold_proposals[str(threshold)] = rect.tolist()
        if threshold != 0.50:
            stability.append(rect_metrics(rect, proposal)["bbox_iou"])
    min_stability = float(min(stability)) if stability else 1.0

    fixture_gate = bool(
        comparison["bbox_iou"] >= 0.60
        and comparison["known_crop_coverage"] >= 0.75
        and min_stability >= 0.90
    )

    report = {
        "scope": "mechanical-bust fixture; deterministic appearance-guided ROI; experimental only",
        "input": str(path),
        "proposal_normalized_xyxy": proposal.tolist(),
        "known_fixture_crop_normalized_xyxy": KNOWN_CROP.tolist(),
        **comparison,
        "threshold_proposals": threshold_proposals,
        "min_threshold_stability_iou": min_stability,
        "fixture_gate_thresholds": {
            "bbox_iou_min": 0.60,
            "known_crop_coverage_min": 0.75,
            "alpha_threshold_stability_iou_min": 0.90,
        },
        "fixture_gate_passed": fixture_gate,
        "production_accepted": False,
        "method": {
            "foreground": "largest BRIA-alpha connected component",
            "detail_localizer": "RGB luminance Sobel energy inside eroded upper foreground",
            "horizontal_roi": "weighted detail-energy quantiles with task-level width sanity bounds",
            "vertical_roi": "foreground top to weighted detail-energy lower quantile",
            "known_crop_used_for_inference": False,
        },
        "diagnostics": {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in main_result.items()
            if key != "proposal"
        },
        "limitations": [
            "Single fixture validation only.",
            "Appearance detail energy is not semantic lens detection.",
            "Known crop is evaluation-only.",
            "Passing this gate does not authorize stitching or UI promotion.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    overlay(image, proposal, KNOWN_CROP, args.overlay)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
