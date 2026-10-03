"""face_iso_v2 transform controls + failed-delta contrast (NEW under quality_jump_face_iso_v2/controls)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
sys.path.insert(0, str(ROOT))
from project_hybrid_a3 import apply_face_local_warp, face_iso_extract_micro_delta  # noqa: E402
# Reuse helpers from the v1 control script
sys.path.insert(0, str(ROOT))
import run_face_iso_transform_controls as c  # noqa: E402

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513")
V2 = JOB / "quality_jump_face_iso_v2"
HW = V2 / "hybrid_work"
OUT = V2 / "controls"
OUT.mkdir(parents=True, exist_ok=True)
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso_v2\controls")
VIS.mkdir(parents=True, exist_ok=True)

# Monkeypatch module OUT/VIS so reused helpers write to v2
c.OUT = OUT
c.VIS = VIS
c.DOC_CTRL = ROOT / "_face_iso_controls_v2"
c.DOC_CTRL.mkdir(parents=True, exist_ok=True)
c.FACE_ISO = V2
c.HW = HW

def main():
    results = {"controls": [], "v2_micro": None}
    # Load v2 micro from report
    rep = json.loads((HW / "report.json").read_text(encoding="utf-8"))
    micro = rep["views"][0]["align"]["micro"]
    results["v2_micro"] = {
        "chosen": micro.get("chosen"),
        "extract": micro.get("extract"),
        "iou_before": micro.get("iou_before"),
        "iou_after": micro.get("iou_after"),
        "project_face": micro.get("project_face"),
        "roi": micro.get("roi"),
    }
    # Mechanical controls on v2 front_aligned
    fa = HW / "front_aligned.png"
    real = c.load_rgba_png(fa)
    roi = tuple(micro.get("roi") or [905, 206, 1152, 468])
    # Scale ROI if preview is 1024
    h, w = real.shape[:2]
    if max(h, w) <= 1024 and max(roi) > 1024:
        # shouldn't happen if roi matches preview; if live was 2048 and preview 1024:
        scale = 0.5
        roi = tuple(int(x * scale) for x in roi)
        results["roi_scaled_for_preview"] = True
    results["controls"].append(c.control_identity(real, roi, "front_aligned_v2"))
    results["controls"].append(c.control_known_translation(real, roi, dx=16.0, dy=0.0, tag="front_aligned_v2", markers=None))
    results["controls"].append(c.control_tx_extract_bug())

    # Replay OLD bad delta vs NEW good delta on v2 front_aligned for smoking-gun SBS
    old_dx, old_dy = -48.0, -47.5
    new_dx = float(micro["extract"]["dx"])
    new_dy = float(micro["extract"]["dy"])
    # If preview 1024 and deltas were in 2048 space, scale
    if max(h, w) <= 1024:
        old_dx, old_dy = old_dx * 0.5, old_dy * 0.5
        # extract dx was at full res during bake; preview is half
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
        cv2.putText(bgr, lab, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if "NEW" in lab or lab=="IN" else (0, 0, 255), 2)
        crops.append(bgr)
    sbs = np.concatenate(crops, axis=1)
    for p in (OUT, VIS, c.DOC_CTRL):
        cv2.imwrite(str(p / "sbs_old_vs_new_delta_face.png"), sbs)

    results["delta_contrast"] = {
        "old_dx_dy_preview": [old_dx, old_dy],
        "new_dx_dy_preview": [new_dx_p, new_dy_p],
        "new_dx_dy_fullres": [new_dx, new_dy],
        "artifact": str(OUT / "sbs_old_vs_new_delta_face.png"),
        "forehead_eye_risk_old": True,
        "forehead_eye_risk_new": bool(new_dy_p < 0 and abs(new_dy_p) > 10),
    }

    mech = [x for x in results["controls"] if x["name"] in ("front_aligned_v2_identity", "front_aligned_v2_known_translation")]
    tx = next(x for x in results["controls"] if x["name"] == "tx_extract_from_scaled_similarity")
    results["mechanical_warp_pass"] = all(x.get("pass") for x in mech)
    results["tx_extract_pass"] = bool(tx.get("pass"))
    results["no_forehead_eye_delta"] = not results["delta_contrast"]["forehead_eye_risk_new"]
    results["verdict"] = (
        "CONTROLS_PASS_READY_FOR_ZENKO"
        if results["mechanical_warp_pass"] and results["tx_extract_pass"] and results["no_forehead_eye_delta"]
        else "CONTROLS_FAIL"
    )
    out_json = OUT / "control_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (VIS / "control_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": results["verdict"], "chosen": micro.get("chosen"), "new_delta": [new_dx, new_dy], "out": str(out_json)}, indent=2))
    for x in results["controls"]:
        print(f"  [{'PASS' if x.get('pass') else 'FAIL':4s}] {x['name']}")

if __name__ == "__main__":
    main()
