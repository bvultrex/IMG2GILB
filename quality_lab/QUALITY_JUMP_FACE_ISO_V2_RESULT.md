# QUALITY_JUMP_FACE_ISO_V2 (transform fix)

Created: 2026-10-02 ~22:10 (Europe/Warsaw / UTC+2)

## Status
- Root cause fix from `QUALITY_JUMP_FACE_ISO_TRANSFORM_DIAG.md` **implemented**
- NEW sidecar only: `quality_jump_face_iso_v2/` — failed v1 **KEEP**
- Controls: **PASS** (`CONTROLS_PASS_READY_FOR_ZENKO`)
- `production_accepted=false` — no Studio default / stages.py finalize flip
- **Not** propagated to Ranger/bust
- Baseline remains **P2 MR-retain**

## Fix (`quality_lab/project_hybrid_a3.py`, mirrored `D:\SF3D_QualityLab\project_hybrid_a3.py`)
1. **`face_iso_extract_micro_delta`**: never strip scaled similarity `M[:,2]` into pure translation when `|scale-1|>0.02`. Prefer face_center / bbox-center delta; clamp applied `|t|≤24`.
2. **`face_landmark_quality`**: gate translation on **bbox center** (≤48) not raw `M[:,2]`; report `center_dx/dy`.
3. **`apply_face_local_warp`**: warp soft ROI with same delta; `mask = max(mask, warp(mask))` to cover vacated+landing (less ghosting).
4. Stricter face_iso IoU accept: `iou + 0.002 >= base_iou` (no 4% regression).

## Failed v1 → fixed v2 (David `5e81ac79…`)

| | v1 (KEEP) | v2 |
|--|-----------|-----|
| chosen | `face_iso_landmark_translation_clamped` | `face_iso_face_center_vs_scaled_sim_clamped` |
| raw landmark tx/ty | −65.15, −64.53 | same (ignored) |
| scale | 1.0936 | 1.0936 |
| **applied delta** | **≈(−48, −47.5)** forehead | **≈(+14.5, +24)** face_center |
| IoU before→after | 0.912→0.895 | 0.912→0.911 |

## Artifacts

| Artifact | Path | SHA256 |
|----------|------|--------|
| Color GLB | `…/quality_jump_face_iso_v2/textured_hybrid_face_iso_v2_color.glb` | `e5484e63e8082b4c7698be9035c1097b66c02538a32702efae33db5b8a34159f` |
| PBR MR-retain | `…/textured_hybrid_face_iso_v2_pbr_mr_retain.glb` | `044f435bd1ed97799b385efd17f186f02ca53fc13bd28c9c479358e83d53aceb` |
| Atlas | `…/hybrid_work/albedo_atlas_hybrid_a3_2K.png` | (see summary) |

MR RGBA matches A0: `f08811e3313e46bbd9a842e3d240b8328750352582df71c6675606dfdad0c393`

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso_v2\`
- `sbs_face.png` (A0|P2|v1 FAIL|v2)
- `sbs_collar_necklace.png`, `sbs_chest_cross.png`, `sbs_back_emblem.png`
- `controls/sbs_old_vs_new_delta_face.png`

## Controls
Script: `quality_lab/run_face_iso_v2_controls.py` → `…/quality_jump_face_iso_v2/controls/control_results.json`

| Control | Result |
|---------|--------|
| front_aligned_v2_identity | PASS |
| front_aligned_v2_known_translation | PASS |
| tx_extract_from_scaled_similarity (fixed extractor) | **PASS** |
| no forehead-eye delta (dy>0) | PASS |

## Laplacian (mean abs)

| Crop | A0 | P2 | v1 | v2 |
|------|-----|-----|-----|-----|
| face | 12.46 | 16.00 | 17.36 | 16.30 |
| chest_cross | 15.18 | 18.54 | 20.36 | 20.36 |
| back_emblem | 9.41 | 13.72 | 13.72 | **13.72** (=P2) |
| collar_necklace | 15.45 | 19.91 | 21.31 | 21.31 |

## Baseline integrity
- P2 `624d1a1fe487…` unchanged
- A0 atlas `57706be141b5…` unchanged
- P2B `7829d786fe13…` unchanged
- face_iso v1 color/pbr unchanged

## Gates
- `production_accepted=false`
- Awaiting Zenko visual on face_iso_v2 SBS (face identity vs P2; no forehead-eye; emblem tip)
- No Ranger/bust propagation yet
- No Meshy parity claim
