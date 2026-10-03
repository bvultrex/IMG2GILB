# Meshy-like v1 — David A/B result

Date: 2026-09-28 (Europe/Warsaw). `production_accepted=false`. **No Meshy/Tripo parity claims.**

## Job
`D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513` (David; frozen shape+UV+Paint@768)

## What landed this pass
1. Plan: `quality_lab/MESHY_LIKE_PIPELINE_PLAN.md`
2. Studio wiring (`desktop/pipeline.py`, `desktop/stages.py`, lab bake/multiref):
   - `paint_multiref` (default on when ≥2 prepared views)
   - `hybrid_a3` (still opt-in)
   - `texture_sr=pil|realesrgan` (default pil)
   - `remesh` optional before UV (topology cleanup only)
3. A3 front micro-align: anime-face bbox → clamped translation, **face-local** warp + soft face weight boost
4. Vis: `_vis_export\meshy_like_v1\` (incl. `sbs4_face.png`, `sbs4_chest.png`)

## A/B visual verdict
| Arm | Face | Chest/insignia | Notes |
|---|---|---|---|
| A0 paint | muddy / wrong style | washed; cross missing | baseline |
| A3 prev | anime eyes recovered; forehead/jaw smear | **clear win** vs A0 (cross, quilt, stripes) | sides skipped (IoU) |
| A3v2 micro | same class as A3; micro-align **accepted** (face_center_translation_clamped, IoU 0.912→0.911) | still clearly > A0 | face-local; residual jaw blend |

**Overall:** A3/A3v2 still much better than A0 on front landmarks. Micro-align is live but residual jaw/neck smear remains — not solved by silhouette IoU alone.

## Align report (front)
- mode: `bbox_iou_refine+face_center_translation_clamped`
- roi_source: `anime_face_bbox`
- accepted: true; face_local: true
- sides: still skipped (left IoU≈0.64, right≈0.55)

## Studio defaults (safe)
- paint_multiref: prefer on
- hybrid_a3: **opt-in** until face smear better
- texture_sr: pil (flip to realesrgan after A/B)
- remesh: off

## Next
1. Face-only transfer / multiband at jaw; optional manual landmarks for David
2. Finish A2 multiref paint→bake on frozen UV; then A2→hybrid
3. `texture_sr=realesrgan` A/B on same atlas
4. Do not promote hybrid to finalize yet

## Uncommitted paths
- `quality_lab/MESHY_LIKE_PIPELINE_PLAN.md`, `project_hybrid_a3.py`, `run_paint_multiref.py`
- `desktop/pipeline.py`, `desktop/stages.py`
- `D:\SF3D_QualityLab\bake_paint21.py`, `project_hybrid_a3.py`, `run_paint_multiref.py`
- `_vis_export\meshy_like_v1\`


## A2 multiref (attempted)
- Started then **stopped**: GPU contention with Studio paint on job 22282dae... (~20 GB VRAM). Duplicate python hosts also attached to same out dir.
- Partial: paint_a2_multiref/reference_*.png only; no albedo yet.
- Re-run when GPU free: same command logged in _vis_export\meshy_like_v1\run_a2_multiref.log.

