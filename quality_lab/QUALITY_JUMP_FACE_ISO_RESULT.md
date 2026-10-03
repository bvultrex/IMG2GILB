# QUALITY_JUMP_FACE_ISO_RESULT

Created: 2026-10-02 ~21:05 (Europe/Warsaw)

## Scope
Isolated face correction on Hybrid path per Zenko Phase2b scorecard (5959135207 / 5959293815) + Danny go-ahead:
- **Freeze P2 torso/back** (P2 incidence — NOT Phase2b steeper falloff)
- Coherent face source: landmark gate → project-all OR paint-all (no mid-face eye/mouth mix)
- NEW sidecars only; P2 / P2B / jawblend / A0 untouched
- `production_accepted=false` — no Studio default flip

## Code
`quality_lab/project_hybrid_a3.py` — new `--face-iso` (mirrored `D:\SF3D_QualityLab\project_hybrid_a3.py`)

## Artifacts (David `5e81ac79…`)

| Artifact | Path | SHA256 |
|----------|------|--------|
| Color GLB | `…/quality_jump_face_iso/textured_hybrid_face_iso_color.glb` | `734742db9fec559f53f3a26882e683f7d4a0f3e52a8410535450d2f4e6f63715` |
| PBR MR-retain | `…/textured_hybrid_face_iso_pbr_mr_retain.glb` | `b0a3c9fe8c90c6f6648c8329e47271d84dd8c420313ddb10754eb67aa1d4abaa` |
| Atlas | `…/hybrid_work/albedo_atlas_hybrid_a3_2K.png` | `8a7ca2e30e40e7d825bd7b225401d263baf3f0d944eff4bb5af790d5f8e4c67f` |

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso\`
- `sbs_face.png`, `sbs_chest_cross.png`, `sbs_back_emblem.png`, `sbs_collar_necklace.png`
- `sbs_angle_{front,back,p35,m35}_A0_P2_face_iso.png`

## Front micro
- chosen: `face_iso_landmark_translation_clamped`
- project_face: `True`
- weight_map: `face_iso_project`
- landmark residual median/p90: see report micro.landmark_quality

## Laplacian (mean abs) A0 / P2 / face_iso
| Crop | A0 | P2 | face_iso |
|------|-----|-----|----------|
| face | 12.46 | 16.00 | 17.36 |
| chest_cross | 15.18 | 18.54 | 20.36 |
| back_emblem | 9.41 | 13.72 | 13.72 |
| collar_necklace | 15.45 | 19.91 | 21.31 |

**Back emblem energy == P2** (logo not weakened by steeper incidence). Chest held with P2.

## Baseline integrity
- P2 `624d1a1fe487…` unchanged
- A0 atlas `57706be141b5…` unchanged
- P2B `7829d786fe13…` unchanged

## Gates
- `production_accepted=false`
- Awaiting Zenko visual on face_iso SBS (esp. face identity vs P2 + emblem tip)
- No Meshy parity claim
