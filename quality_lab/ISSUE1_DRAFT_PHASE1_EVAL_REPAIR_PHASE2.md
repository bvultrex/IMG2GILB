## [GROK] Phase-1 eval repair + Phase-2 Hybrid sidecar (A0 control)

ACK Zenko review (comment 5958345088): A0 = conservative Phase-2 control; no default flip.

### 1) Eval repair (no paint regen)
- Script: `quality_lab/eval_repair_phase1_final_glb.py` (new; does **not** mutate `make_crops_metrics.py`)
- Staging: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase1_evalfix\`
- Doc: `QUALITY_JUMP_PHASE1_EVAL_REPAIR.md` (same folder + `quality_lab/`)
- Unlit front/back/oblique from each arm?s **bake atlas** (color-GLB content) via shared UV mesh
- Face+chest crops retargeted on 1024 (chest = jacket/necklace/reflective bands, not waist/thighs)
- Laplacian = float64 signed convolution (`ndimage`), not PIL L-mode
- Sanity: A0 vs A2 face crop **no longer identical**
  - Face crop SHAs / metrics: `quality_jump_phase1_evalfix/eval_repair_report.json` ? `sanity`

Phase-1 color GLB SHAs (unchanged):
- A0 `cbbf50d95a2b9f2d7548846399cf044734fe0b16a7075ec40d153b37b6b301e7`
- A1 `3f7bc3eb936a488cad3263719a2f87501572a24270a917c6fef858f7bce3e046`
- A2 `18ffab7ab94da9654137287a43d0f4f2f0dad821558fe4e618f0598471aab01e`
- A3 `825e47f4c44e452465e53846a9601e631f01bc81a99b510bda15cf820ed14ded`

### 2) Phase-2 Hybrid sidecar vs A0
- Fill atlas: Phase-1 A0 bake `57706be141b5869f05f031c81b2f6bf103fc0e1d465eb81f682f55247a8f7859`
- Out GLB: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2\textured_hybrid_phase2_vs_A0_color.glb`
  - SHA `624d1a1fe487458ee1aa92a64536c08f2a6b2c695802f1c5fe115e66121c9bb6`
- Vis/SBS: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2\`
  - `sbs_matched_face.png`, `sbs_matched_chest.png`, `sbs_matched_front_full.png`, `sbs_matched_back_full.png`
- Doc: `quality_lab/QUALITY_JUMP_PHASE2_RESULT.md`
- Left/right projection skipped (IoU gate); front/back projected
- `production_accepted=false`, Studio default **unchanged**

Please visual-eval SBS (esp. jaw/neck + chest symbols). I will not flip defaults.
