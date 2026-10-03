"""Ranger face_iso_v2 transform controls on Ranger front_aligned."""
from __future__ import annotations
import json, sys
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
sys.path.insert(0, str(ROOT))
from project_hybrid_a3 import apply_face_local_warp, face_iso_extract_micro_delta
import run_face_iso_transform_controls as c

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833")
OUT = JOB / "quality_jump_ranger_face_iso_v2"
CTRL = OUT / "controls"
CTRL.mkdir(parents=True, exist_ok=True)
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_face_iso_v2\controls")
VIS.mkdir(parents=True, exist_ok=True)

c.OUT = CTRL
c.VIS = VIS
c.DOC_CTRL = ROOT / "_face_iso_controls_ranger_v2"
c.DOC_CTRL.mkdir(parents=True, exist_ok=True)
c.FACE_ISO = OUT
c.HW = OUT  # flat layout (no hybrid_work subfolder)

def main():
    results = {"controls": [], "ranger_micro": None}
    rep = json.loads((OUT / "report.json").read_text(encoding="utf-8"))
    micro = (rep["views"][0].get("align") or {}).get("micro") or {}
    extract = micro.get("extract") or {}
    results["ranger_micro"] = {
        "chosen": micro.get("chosen"),
        "accepted": micro.get("accepted"),
        "reject_reason": micro.get("reject_reason"),
        "fallback_no_micro": micro.get("fallback_no_micro"),
        "weight_map": micro.get("weight_map"),
        "iou_before": micro.get("iou_before"),
        "iou_after": micro.get("iou_after"),
        "extract": extract,
        "project_face": micro.get("project_face"),
        "roi": micro.get("roi"),
    }
    fa = OUT / "front_aligned.png"
    real = c.load_rgba_png(fa)
    roi = tuple(micro.get("roi") or [902, 134, 1152, 395])
    h, w = real.shape[:2]
    if max(h, w) <= 1024 and max(roi) > 1024:
        roi = tuple(int(x * 0.5) for x in roi)
        results["roi_scaled_for_preview"] = True
    results["controls"].append(c.control_identity(real, roi, "ranger_front_aligned_v2"))
    results["controls"].append(c.control_known_translation(real, roi, dx=16.0, dy=0.0, tag="ranger_front_aligned_v2", markers=None))
    results["controls"].append(c.control_tx_extract_bug())

    # Replay: old bad forehead delta vs ranger extract on this front_aligned
    old_dx, old_dy = -48.0, -47.5
    new_dx = float(extract.get("dx", 0))
    new_dy = float(extract.get("dy", 0))
    if max(h, w) <= 1024:
        old_dx, old_dy = old_dx * 0.5, old_dy * 0.5
        new_dx_p, new_dy_p = new_dx * 0.5, new_dy * 0.5
    else:
        new_dx_p, new_dy_p = new_dx, new_dy
    delta_old = np.array([[1.0, 0.0, old_dx], [0.0, 1.0, old_dy]], dtype=np.float32)
    delta_new = np.array([[1.0, 0.0, new_dx_p], [0.0, 1.0, new_dy_p]], dtype=np.float32)
    replay_old = apply_face_local_warp(real, delta_old, roi, feather=24)
    replay_new = apply_face_local_warp(real, delta_new, roi, feather=24)
    x0, y0, x1, y1 = roi
    pad = 40
    crops = []
    for img, lab in ((real, "IN"), (replay_old, f"OLD dx={old_dx:.1f}"), (replay_new, f"NEW dx={new_dx_p:.1f}")):
        crop = img[max(0, y0 - pad) : y1 + pad, max(0, x0 - pad) : x1 + pad]
        bgr = c.to_bgr(crop)
        color = (0, 255, 0) if ("NEW" in lab or lab == "IN") else (0, 0, 255)
        cv2.putText(bgr, lab, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        crops.append(bgr)
    # side-by-side
    hmax = max(im.shape[0] for im in crops)
    wsum = sum(im.shape[1] for im in crops) + 16 * 2
    canvas = np.zeros((hmax, wsum, 3), dtype=np.uint8)
    x = 0
    for im in crops:
        canvas[: im.shape[0], x : x + im.shape[1]] = im
        x += im.shape[1] + 16
    sbs_path = CTRL / "sbs_old_vs_new_delta_face.png"
    cv2.imwrite(str(sbs_path), canvas)
    cv2.imwrite(str(VIS / "sbs_old_vs_new_delta_face.png"), canvas)

    # forehead-eye check: new dy should be >=0 (downward), not large negative
    forehead_ok = new_dy >= 0 and new_dx > -24
    results["forehead_eye_check"] = {
        "extract_dx": new_dx,
        "extract_dy": new_dy,
        "ok": forehead_ok,
        "note": "dy>=0 and dx>-24 => not forehead-eye shift",
    }
    results["cyan_collar_note"] = "see vis cyan_collar_score in summary; controls do not synthesize cyan"

    passes = [r.get("pass", r.get("ok", False)) for r in results["controls"]]
    # control_tx_extract_bug returns dict with pass key
    all_pass = all(bool(p) for p in passes) and forehead_ok
    results["verdict"] = "CONTROLS_PASS_READY_FOR_ZENKO" if all_pass else "CONTROLS_FAIL"
    results["passes"] = passes
    (CTRL / "control_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (VIS / "control_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": results["verdict"], "passes": passes, "forehead_ok": forehead_ok, "extract": (new_dx, new_dy), "micro_accepted": micro.get("accepted")}, indent=2))

if __name__ == "__main__":
    main()
