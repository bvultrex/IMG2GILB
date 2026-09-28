"""Deterministic automatic ROI proposal for the mechanical-bust fixture.

The proposal itself uses ONLY the prepared front image's BRIA alpha silhouette.
The known fixture crop is used strictly after inference for evaluation.

This is an experiment, not production ROI selection.
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
        raise RuntimeError("BRIA alpha contains no foreground.")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    return labels == int(np.argmax(sizes))


def smooth_rows(values: np.ndarray, radius: int = 3) -> np.ndarray:
    if len(values) == 0:
        return values
    size = radius * 2 + 1
    return ndimage.median_filter(values.astype(np.float64), size=size, mode="nearest")


def propose_from_alpha(alpha: np.ndarray, threshold: float = 0.50) -> dict:
    h, w = alpha.shape
    mask = largest_component(alpha >= threshold)
    ys, xs = np.where(mask)
    if len(xs) < 100:
        raise RuntimeError("Foreground component is too small for ROI inference.")

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    object_h = max(1, y1 - y0)

    rows = np.arange(y0, y1)
    left = np.full(len(rows), np.nan, dtype=np.float64)
    right = np.full(len(rows), np.nan, dtype=np.float64)
    width = np.zeros(len(rows), dtype=np.float64)
    for i, y in enumerate(rows):
        row_x = np.flatnonzero(mask[y])
        if len(row_x):
            left[i] = row_x[0]
            right[i] = row_x[-1] + 1
            width[i] = right[i] - left[i]

    valid = width > 0
    if valid.sum() < 20:
        raise RuntimeError("Too few valid foreground rows.")

    # Estimate the hood/head silhouette before shoulders/robe broaden the object.
    probe_a = y0 + int(round(0.06 * object_h))
    probe_b = y0 + int(round(0.27 * object_h))
    probe = (rows >= probe_a) & (rows <= probe_b) & valid
    if probe.sum() < 8:
        probe = (rows <= y0 + int(round(0.32 * object_h))) & valid

    head_width = float(np.median(width[probe]))
    smooth_width = smooth_rows(width, radius=3)

    # Detect the first persistent widening that marks transition into shoulders.
    search_start = y0 + int(round(0.20 * object_h))
    search_end = y0 + int(round(0.46 * object_h))
    widening = 1.40 * head_width
    bottom = None
    persistence = max(5, int(round(0.008 * h)))
    for y in range(search_start, min(search_end, y1)):
        i = y - y0
        j = min(len(smooth_width), i + persistence)
        if j - i >= 3 and np.median(smooth_width[i:j]) >= widening:
            bottom = y
            break

    # Conservative deterministic fallback if silhouette widening is ambiguous.
    if bottom is None:
        bottom = y0 + int(round(0.36 * object_h))

    min_bottom = y0 + int(round(0.28 * object_h))
    max_bottom = y0 + int(round(0.43 * object_h))
    bottom = int(np.clip(bottom, min_bottom, max_bottom))

    # Estimate horizontal hood span only from rows above the shoulder transition.
    band_a = y0 + int(round(0.04 * object_h))
    band_b = max(band_a + 1, bottom - int(round(0.02 * object_h)))
    band = (rows >= band_a) & (rows < band_b) & valid
    band_left = left[band]
    band_right = right[band]
    if len(band_left) < 8:
        raise RuntimeError("Insufficient upper-silhouette rows for ROI bounds.")

    hood_left = float(np.nanmedian(band_left))
    hood_right = float(np.nanmedian(band_right))
    hood_width = max(1.0, hood_right - hood_left)
    center_x = 0.5 * (hood_left + hood_right)

    # Slight padding captures the hood rim without intentionally swallowing shoulders.
    horizontal_pad = 0.055 * hood_width
    proposal_left = center_x - 0.5 * hood_width - horizontal_pad
    proposal_right = center_x + 0.5 * hood_width + horizontal_pad
    vertical_pad_top = 0.006 * object_h
    vertical_pad_bottom = 0.012 * object_h

    proposal = np.array(
        [
            proposal_left / w,
            max(0.0, (y0 - vertical_pad_top) / h),
            proposal_right / w,
            min(1.0, (bottom + vertical_pad_bottom) / h),
        ],
        dtype=np.float64,
    )
    proposal[[0, 2]] = np.clip(proposal[[0, 2]], 0.0, 1.0)
    proposal[[1, 3]] = np.clip(proposal[[1, 3]], 0.0, 1.0)

    return {
        "proposal": proposal,
        "image_size": [int(w), int(h)],
        "foreground_bbox": [x0 / w, y0 / h, x1 / w, y1 / h],
        "foreground_pixels": int(mask.sum()),
        "head_width_px": head_width,
        "hood_width_px": hood_width,
        "shoulder_transition_y_px": int(bottom),
        "alpha_threshold": float(threshold),
    }


def rect_area(rect: np.ndarray) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def rect_intersection(a: np.ndarray, b: np.ndarray) -> float:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def rect_metrics(proposal: np.ndarray, known: np.ndarray) -> dict:
    inter = rect_intersection(proposal, known)
    pa = rect_area(proposal)
    ka = rect_area(known)
    union = pa + ka - inter
    pc = np.array([(proposal[0] + proposal[2]) * 0.5, (proposal[1] + proposal[3]) * 0.5])
    kc = np.array([(known[0] + known[2]) * 0.5, (known[1] + known[3]) * 0.5])
    return {
        "bbox_iou": float(inter / union) if union > 0 else 0.0,
        "known_crop_coverage": float(inter / ka) if ka > 0 else 0.0,
        "proposal_coverage_by_known": float(inter / pa) if pa > 0 else 0.0,
        "center_error_normalized": float(np.linalg.norm(pc - kc)),
        "corner_mae_normalized": float(np.abs(proposal - known).mean()),
        "proposal_area_normalized": float(pa),
        "known_area_normalized": float(ka),
    }


def resolve_default_image(root: Path, lab: Path) -> Path:
    record_path = root / "test.json"
    if not record_path.exists():
        raise FileNotFoundError(f"Fixture record not found: {record_path}")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    job = record.get("job")
    if not job:
        raise RuntimeError(f"No job id in {record_path}")
    image = lab / "app_jobs" / str(job) / "prepared" / "front.png"
    if not image.exists():
        raise FileNotFoundError(f"Prepared front image not found: {image}")
    return image


def draw_overlay(image: Image.Image, proposal: np.ndarray, known: np.ndarray, output: Path) -> None:
    rgba = image.convert("RGBA")
    draw = ImageDraw.Draw(rgba)
    w, h = rgba.size

    def px(rect):
        return tuple(int(round(v * (w if i % 2 == 0 else h))) for i, v in enumerate(rect))

    # Luminance-coded overlay: known crop dark double-line, proposal bright line.
    kb = px(known)
    pb = px(proposal)
    draw.rectangle(kb, outline=(0, 0, 0, 255), width=8)
    draw.rectangle(kb, outline=(150, 150, 150, 255), width=3)
    draw.rectangle(pb, outline=(255, 255, 255, 255), width=4)
    output.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--lab", type=Path, default=DEFAULT_LAB)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v1.json",
    )
    parser.add_argument(
        "--overlay",
        type=Path,
        default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v1_overlay.png",
    )
    args = parser.parse_args()

    image_path = args.image or resolve_default_image(args.root, args.lab)
    image = Image.open(image_path).convert("RGBA")
    alpha = np.asarray(image, dtype=np.uint8)[:, :, 3].astype(np.float64) / 255.0

    main_result = propose_from_alpha(alpha, 0.50)
    proposal = main_result["proposal"]
    comparison = rect_metrics(proposal, KNOWN_CROP)

    thresholds = [0.35, 0.50, 0.65]
    threshold_results = {}
    pairwise_iou = []
    baseline = proposal
    for threshold in thresholds:
        result = propose_from_alpha(alpha, threshold)
        rect = result["proposal"]
        threshold_results[str(threshold)] = rect.tolist()
        if threshold != 0.50:
            pairwise_iou.append(rect_metrics(rect, baseline)["bbox_iou"])

    min_threshold_stability_iou = float(min(pairwise_iou)) if pairwise_iou else 1.0
    fixture_gate = bool(
        comparison["bbox_iou"] >= 0.60
        and comparison["known_crop_coverage"] >= 0.75
        and min_threshold_stability_iou >= 0.90
    )

    report = {
        "scope": "mechanical-bust fixture; deterministic BRIA-alpha ROI proposal; experimental only",
        "input": str(image_path),
        "proposal_normalized_xyxy": proposal.tolist(),
        "known_fixture_crop_normalized_xyxy": KNOWN_CROP.tolist(),
        **comparison,
        "threshold_proposals": threshold_results,
        "min_threshold_stability_iou": min_threshold_stability_iou,
        "fixture_gate_thresholds": {
            "bbox_iou_min": 0.60,
            "known_crop_coverage_min": 0.75,
            "alpha_threshold_stability_iou_min": 0.90,
        },
        "fixture_gate_passed": fixture_gate,
        "production_accepted": False,
        "method": {
            "foreground": "largest BRIA-alpha connected component",
            "vertical_roi": "upper silhouette until persistent shoulder widening",
            "horizontal_roi": "median upper-silhouette span plus small deterministic padding",
            "known_crop_used_for_inference": False,
        },
        "diagnostics": {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in main_result.items()
            if key != "proposal"
        },
        "limitations": [
            "Single fixture validation only.",
            "Silhouette-based ROI does not semantically prove lens identity.",
            "The known crop is evaluation ground truth for this fixture, not an inference input.",
            "Passing this gate does not authorize registration, stitching, UI promotion, or Meshy-parity claims.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    draw_overlay(image, proposal, KNOWN_CROP, args.overlay)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
