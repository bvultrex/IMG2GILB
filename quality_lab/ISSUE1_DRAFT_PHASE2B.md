[GROK]
WORKING ON: Phase2b Hybrid bundle **DONE** — awaiting Zenko visual scorecard
FILES/AREA: quality_lab/project_hybrid_a3.py (--phase2b / --no-face-micro); NEW sidecars quality_jump_phase2b/; vis _vis_export/quality_jump_phase2b/; QUALITY_JUMP_PHASE2B_RESULT.md
LAST COMMIT: uncommitted (OK)
RESULT:
ACK Zenko 5958649808 + 5958774240: jawblend unaccepted; **P2 Hybrid remains baseline**; A0 control.

### Delivered (NEW only; P2/jaw/A0-A3 untouched)
- Color GLB: D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2b\textured_hybrid_phase2b_color.glb
  - SHA 7829d786fe135fa70ca3995ea4f8ab5e55c2d12ac84331da7c38f4eb7e33e8c1
- Fallback no-micro GLB: ...\textured_hybrid_phase2b_fallback_no_micro_color.glb
  - SHA b1ff3eeb1612c3bc8d7c48c7ab03710b9076586c94853bfea076b655d0d3ee77
- Vis: C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2b\
  - Angles A0|P2|P2B: sbs_angle_{front,back,p35,m35,p90,m90}_A0_P2_P2B.png
  - Crops: sbs_collar_necklace.png, sbs_chest_cross.png, sbs_back_emblem.png, sbs_face.png, sbs_jaw.png (+ crop guides)
  - Masks: confidence_atlas_heatmap.png, P2B_front_confidence_overlay.png, per-angle coverage
- Doc: quality_lab/QUALITY_JUMP_PHASE2B_RESULT.md

### Changes vs P2 / rejected jawblend
- Steeper front/back->side incidence falloff (**no global blur**)
- Hard Paint-prefer on **tight jaw only** (stops before collar/necklace — addresses jawblend torso/double-contour issue)
- Explicit --no-face-micro fallback for region-specific compare
- Correct collar+necklace crop (not waist)

### Integrity
P2 624d1a1fe487... / jawblend c10ac082... / A0 atlas 57706be1... **unchanged**
production_accepted=false — no Studio default flip

### Please eval [CODEX/Zenko]
1. collar_necklace + chest_cross + back_emblem vs P2 (must not regress emblem/cross)
2. face/jaw vs P2 and vs fallback sheets
3. +/-35 deg transition cleanliness; +/-90 deg honesty (Paint sides)
4. CPU lineage check welcome

GPU free after this post. No A0-A3 regen.
