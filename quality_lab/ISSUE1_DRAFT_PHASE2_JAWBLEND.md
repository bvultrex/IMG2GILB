## [GROK] Phase-2 polish: Jawblend Hybrid sidecar (vs A0 + P2 Hybrid)

Zenko: Phase-2 post still unanswered — proceeding with jaw/neck polish as planned. No default flip.

### Change
`--jaw-blend` on Hybrid A3 (opt-in):
- Shrink face micro-ROI bottom + asymmetric bottom feather (less chin→neck warp drag)
- Paint-prefer weight band on jaw/neck; upper-face boost; **chest projection scale unchanged**

### Artifacts (NEW only)
- Color GLB: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2\textured_hybrid_phase2_jawblend_color.glb`
  - SHA `c10ac082278599c2adff018e62a80cdf50d6335bfdf96db87b4bc683cf3372ce`
- Vis/SBS: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2_jaw\`
  - `sbs_A0_P2_jaw_face.png` / `sbs_A0_P2_jaw_jaw.png` / `sbs_A0_P2_jaw_chest.png`
- Doc: `quality_lab/QUALITY_JUMP_PHASE2_JAWBLEND_RESULT.md`

### Baselines preserved
- P2 Hybrid color `624d1a1fe487…9bb6`
- A0 atlas `57706be1…7859` / A0 GLB `cbbf50d9…01e7`
- Phase-1 A0–A3 untouched

### Laplacian (face / jaw / chest)
| | A0 | P2 | Jawblend |
|--|----|----|----------|
| face | 756 | 1142 | 806 |
| jaw | 1132 | 1552 | 1180 |
| chest | 1076 | 1436 | **1432** |

### Grok visual read
- Jaw/neck smear vs P2: **improved** (dark stretch reduced)
- Chest symbols: **win held**
- Face: still soft; not a promotion trigger alone
- `production_accepted=false`

Please visual-eval the three SBS. I will not flip Studio defaults.
