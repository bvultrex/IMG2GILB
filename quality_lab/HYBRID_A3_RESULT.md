# Hybrid A3 A/B — David job 5e81ac7963f84af2a403fb659cea7513

Date: 2026-09-28 (Europe/Warsaw). `production_accepted=false`. No Meshy/Tripo parity claims.

## Ran
- Script: `quality_lab/project_hybrid_a3.py` (= `D:\SF3D_QualityLab\project_hybrid_a3.py`)
- Job: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513` (frozen shape+UV+Paint 2.1 @768→2K)
- Mode: texture-only; ~28s; no neural re-paint
- Alignment: bbox + IoU refine; no landmarks for this job
- Final policy: project front/back (IoU≈0.91); **skip** left/right (IoU 0.64 / 0.55) to avoid wrap bleed

## Outputs (sidecars; originals untouched)
- `.../textured_hybrid_a3_color.glb`
- `.../textured_hybrid_a3_pbr.glb` (reuses Paint MR atlas)
- `.../hybrid_a3/` atlas, confidence, alignment overlays, A0/A3 flats, `report.json`
- Vis: `IMG2GILB\_vis_export\texture_a3_hybrid\5e81ac7963f84af2a403fb659cea7513\` (`sbs_*.png`, `a0_*.png`, `a3_*.png`)

Original SHA256 prefixes unchanged: textured_color `fab4adf75ffbbf26`, textured_pbr `27cec97d349bce6d`, output `5364898362cc65f1`, paint atlas `d47102edc7b60357`.

## Visual verdict
- **Chest / insignia / jacket lines:** A3 clearly beats A0 — quilt pattern + cross necklace recovered from orthos.
- **Face identity:** A3 recovers anime eyes/features vs muddy A0, but residual forehead smudge / stretch from silhouette-only front align (not semantic landmarks).
- **Sides:** auto-align blocked; Paint fill retained there.

## Blockers
1. Left/right auto-align IoU below 0.72 → projection skipped (`auto_align_low_iou_skipped`).
2. Front/back IoU high (~0.91) but not feature-accurate (eyes/hairline) — needs landmarks or sparse correspondence, same lesson as seed42 REFERENCE_PROJECTION_RESULTS.
3. Baked photo/ortho lighting remains in projected regions.

## Studio wiring (done, default off)
- `desktop/pipeline.py`: optional stage `hybrid_a3` when `settings.hybrid_a3=true`, after bake, before face.
- Writes sidecars only; finalize still uses bake/face path.
- Protocol: `quality_lab/HYBRID_A3_PROTOCOL.md`; bat: `D:\SF3D_QualityLab\Run_Hybrid_A3.bat`

## Next step
1. Keep A3 opt-in; do not promote to finalize yet.
2. Improve auto-align: region-limited face landmarks or edge/feature match on front before trusting full-body transfer; then revisit sides.
3. Optional A/B arm: front+back-only hybrid is the current recommended offline default for this character class.
