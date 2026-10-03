# QUALITY_JUMP_PHASE1_EVAL_REPAIR

Created: 2026-10-02 (Europe/Warsaw)

## Purpose
Repair Phase-1 evaluation bugs flagged by Zenko (Issue #1 comment 5958345088).
No paint regeneration. Baselines A0?A3 bake/GLB preserved.

## Bugs fixed
1. Crops from **unlit renders of final bake atlases** (color GLB content), not native `albedo_0` pre-SR.
2. Face + chest semantic boxes on 1024 unlit front; chest retargeted to jacket/necklace/reflective bands (not waist/thighs).
3. Laplacian = **float64 signed convolution** / `ndimage.laplace` (no PIL L-mode clip).
4. Cameras explicit: front azim=0, back azim=180, oblique elev=8 azim=35.

## Staging
- Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase1_evalfix`
- Report JSON: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase1_evalfix\eval_repair_report.json`
- Script: `quality_lab/eval_repair_phase1_final_glb.py` (+ lab copy under D:\SF3D_QualityLab)


## Sanity (A0 vs A2 after repair)
- Face identical? **False**
- Chest identical? **False**
- A0 face: `4aac5f5ff9ff1b033ecfbd1bf9ecc473620dd3db38ed1971d79a6f4b98471d73`
- A2 face: `a7265519457eac43bab6d48285d5db7604738b86a4ee7f5e864530ed528fb5b5`
- A0 chest: `77cad74406fdd5336d9317720fd06c315e20317fff2459bf9315aeee59880337`
- A2 chest: `f3d41930382f63cd01535ef2526bf383329fb9eb88a4d187644ca489a9eb2680`


## Crop boxes (1024)
- face: `[360, 20, 664, 300]`
- chest: `[320, 200, 704, 460]`


## Per-arm hashes + metrics

| Arm | Atlas SHA256 | Color GLB SHA256 | Atlas lap_var | Unlit front lap_var | Face SHA |
|-----|--------------|------------------|---------------|---------------------|----------|
| A0_single_pil | `57706be141b5869f?` | `cbbf50d95a2b9f2d?` | 163.70 | 1374.75 | `4aac5f5ff9ff1b03?` |
| A1_multi_pil | `1c7633fb9c16ff78?` | `3f7bc3eb936a488c?` | 108.88 | 990.88 | `de8c790aaace578c?` |
| A2_single_esrgan | `e9a9efefd2e2865f?` | `18ffab7ab94da965?` | 313.25 | 2264.29 | `a7265519457eac43?` |
| A3_multi_esrgan | `c98939cdd4f9fd51?` | `825e47f4c44e4524?` | 203.10 | 1443.77 | `9bbc8034c025a8d0?` |

## Sheets
- sheet_unlit_front/back/oblique.png
- sheet_front_face/chest.png
- sheet_atlas_mid.png


## Notes
- A0 = conservative Phase-2 Hybrid control (not quality winner).
- No Studio default flip. No Meshy parity.
- Prior `make_crops_metrics.py` left untouched.
