"""Automatic bust ROI v3: deterministic post-tightening of the accepted v2 ROI.

Primary strategy: crop-side fix.  The v2 appearance-guided proposal is inferred
without the known fixture crop, then weak-context margins are removed by fixed
fractions.  The known crop remains evaluation-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import auto_roi_bust_v2 as v2

DEFAULT_ROOT = Path(r"D:\SF3D_QualityLab\bust_validation")
DEFAULT_LAB = Path(r"D:\SF3D_QualityLab")
KNOWN_CROP = v2.KNOWN_CROP.copy()

SIDE_TRIM_FRACTION = 0.10
BOTTOM_TRIM_FRACTION = 0.12


def tighten(rect: np.ndarray) -> np.ndarray:
    rect = np.asarray(rect, dtype=np.float64).copy()
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    rect[0] += SIDE_TRIM_FRACTION * width
    rect[2] -= SIDE_TRIM_FRACTION * width
    rect[3] -= BOTTOM_TRIM_FRACTION * height
    return np.clip(rect, 0.0, 1.0)


def propose(image: Image.Image, alpha_threshold: float = 0.50) -> dict:
    base = v2.propose(image, alpha_threshold)
    base_rect = np.asarray(base["proposal"], dtype=np.float64)
    tight = tighten(base_rect)
    return {
        **base,
        "proposal_v2": base_rect,
        "proposal": tight,
        "post_tighten": {
            "side_trim_fraction_each": SIDE_TRIM_FRACTION,
            "bottom_trim_fraction": BOTTOM_TRIM_FRACTION,
            "top_trim_fraction": 0.0,
        },
    }


def overlay(image: Image.Image, proposal: np.ndarray, known: np.ndarray, output: Path) -> None:
    im = image.convert("RGBA")
    draw = ImageDraw.Draw(im)
    w, h = im.size

    def box(rect):
        return tuple(int(round(val * (w if i % 2 == 0 else h))) for i, val in enumerate(rect))

    known_box = box(known)
    proposal_box = box(proposal)
    draw.rectangle(known_box, outline=(0, 0, 0, 255), width=8)
    draw.rectangle(known_box, outline=(145, 145, 145, 255), width=3)
    draw.rectangle(proposal_box, outline=(255, 255, 255, 255), width=4)
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--lab", type=Path, default=DEFAULT_LAB)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v3.json",
    )
    parser.add_argument(
        "--overlay",
        type=Path,
        default=DEFAULT_ROOT / "shape_ablation" / "auto_roi_bust_v3_overlay.png",
    )
    args = parser.parse_args()

    path = args.image or v2.resolve_default_image(args.root, args.lab)
    image = Image.open(path).convert("RGBA")

    main_result = propose(image, 0.50)
    proposal = np.asarray(main_result["proposal"], dtype=np.float64)
    comparison = v2.rect_metrics(proposal, KNOWN_CROP)

    threshold_proposals = {}
    stability = []
    for threshold in (0.35, 0.50, 0.65):
        result = propose(image, threshold)
        rect = np.asarray(result["proposal"], dtype=np.float64)
        threshold_proposals[str(threshold)] = rect.tolist()
        if threshold != 0.50:
            stability.append(v2.rect_metrics(rect, proposal)["bbox_iou"])
    min_stability = float(min(stability)) if stability else 1.0

    fixture_gate = bool(
        comparison["bbox_iou"] >= 0.60
        and comparison["known_crop_coverage"] >= 0.75
        and min_stability >= 0.90
    )

    report = {
        "scope": "mechanical-bust fixture; auto ROI v2 plus deterministic post-tightening; experimental only",
        "input": str(path),
        "primary_approach": "automatic post-ROI crop tightening before registration",
        "proposal_v2_normalized_xyxy": np.asarray(main_result["proposal_v2"]).tolist(),
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
        "post_tighten": main_result["post_tighten"],
        "known_crop_used_for_inference": False,
        "limitations": [
            "Single fixture validation only.",
            "Fixed fractional post-tightening is automatic but not semantic lens detection.",
            "Known crop is evaluation-only and is not read by proposal inference.",
            "Passing ROI/registration gates does not authorize stitching or UI promotion.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    overlay(image, proposal, KNOWN_CROP, args.overlay)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
