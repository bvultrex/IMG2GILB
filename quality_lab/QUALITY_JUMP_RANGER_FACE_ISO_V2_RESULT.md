# QUALITY_JUMP_RANGER_FACE_ISO_V2

Created: 2026-10-02 ~21:55 (Europe/Warsaw / UTC+2)

## Status
- face_iso **v2 transform fix** exercised on Ranger (second clothed fixture)
- NEW sidecar only: `quality_jump_ranger_face_iso_v2/` — prior hybrid + paint **KEEP**
- Extract path: `prefer_center_not_raw_tx` → `face_iso_face_center_vs_scaled_sim` **dx=+6.82 dy=+11.65** (no forehead-eye)
- Micro warp **REJECTED** (`iou_regression` 0.90311→0.90084); landed as `face_iso_paint_no_micro`
- Controls: **PASS** (`CONTROLS_PASS_READY_FOR_ZENKO`)
- `production_accepted=false` — no Studio default / stages.py finalize flip
- Full export/preview gate: **OPEN**

## Job
`D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833` (ranger_ortho_v1)

## Artifacts

| Artifact | Path | SHA256 |
|----------|------|--------|
| Color GLB | `…/quality_jump_ranger_face_iso_v2/textured_hybrid_ranger_face_iso_v2_color.glb` | `b2b44d33e26b325e…` (full in summary) |
| PBR MR-retain | `…/textured_hybrid_ranger_face_iso_v2_pbr_mr_retain.glb` | `25b32ab0ec1db287…` |
| Atlas | `…/albedo_atlas_hybrid_a3_2K.png` | `3f73ff8f6ddc…` |

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_face_iso_v2\`
- `sbs_face.png`, `sbs_jaw.png`, `sbs_chest.png`, `sbs_back_logo.png`
- `sbs_angle_{front,back,p35,m35,p90,m90}.png`
- `sbs_face_angle_*.png`, `sbs_jaw_angle_*.png`
- `controls/sbs_old_vs_new_delta_face.png`

## Micro extract (v2 fix)

| Field | Value |
|-------|-------|
| scale | 1.044 |
| raw landmark tx/ty | −39.85, −3.77 (**ignored**) |
| chosen | `face_iso_face_center_vs_scaled_sim` |
| applied candidate | **(+6.82, +11.65)** |
| accepted | **false** (`iou_regression`) |
| weight_map | `face_iso_paint_no_micro` |

## Laplacian (mean abs)

| Crop | paint | prior hybrid | face_iso_v2 |
|------|-------|--------------|-------------|
| face | 5.78 | 10.23 | 9.97 |
| jaw | 7.83 | 11.88 | 12.70 |
| chest | 6.73 | 10.09 | 11.21 |
| back_logo | 6.16 | 10.76 | **10.76** (=hybrid) |

Cyan-collar score ≈ 0 (paint/hybrid/face_iso).

## Controls
Script: `quality_lab/run_ranger_face_iso_v2_controls.py`

| Control | Result |
|---------|--------|
| ranger_front_aligned_v2_identity | PASS |
| ranger_front_aligned_v2_known_translation | PASS |
| tx_extract_from_scaled_similarity (fixed) | PASS |
| no forehead-eye delta (dy>0) | PASS |

## Baseline integrity
- paint color/pbr unchanged
- prior hybrid color/pbr (`quality_jump_second_fixture`) unchanged
- David face_iso_v2 **not** overwritten

## Gates
- `production_accepted=false`
- Studio defaults OFF
- Full export/preview test **OPEN**
- Awaiting Zenko visual on Ranger angled SBS (face/jaw ±35/±90; no forehead-eye; no cyan collar)
- No Meshy parity claim
