# QUALITY_JUMP_PHASE2_RESULT

Created: 2026-10-02T20:14:30 (Europe/Warsaw)

## Scope
Phase-2 Hybrid A3 **sidecar** vs Phase-1 **A0** conservative control (Zenko ACK).
- Paint fill = A0 bake atlas (`albedo_atlas_2K.png` from `A0_single_pil`)
- Ortho projection from prepared front/back (left/right skipped: IoU < 0.72)
- No Studio default flip. No Meshy parity. Phase-1 A0?A3 GLBs untouched.

## Outputs
| Artifact | Path | SHA256 |
|----------|------|--------|
| Hybrid color GLB | `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2\textured_hybrid_phase2_vs_A0_color.glb` | `624d1a1fe487458ee1aa92a64536c08f2a6b2c695802f1c5fe115e66121c9bb6` |
| Hybrid PBR GLB | `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2\textured_hybrid_phase2_vs_A0_pbr.glb` | `e894872742874b5b7138ac4da21989aeb31fb05a2a0ecd0b2a4af50664e696fc` |
| Hybrid atlas | `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase2\hybrid_work\albedo_atlas_hybrid_a3_2K.png` | `6360eaaa2f83e79fa7d9b22a13306ee39e5f53372f344fc5ada1ab31b78155ff` |
| A0 control atlas | `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase1\A0_single_pil\albedo_atlas_2K.png` | `57706be141b5869f05f031c81b2f6bf103fc0e1d465eb81f682f55247a8f7859` |
| A0 control GLB | `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_phase1\A0_single_pil\textured_A0_single_pil_color.glb` | `cbbf50d95a2b9f2d7548846399cf044734fe0b16a7075ec40d153b37b6b301e7` |

Vis / SBS: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2`
- `sbs_matched_face.png` / `sbs_matched_chest.png` / `sbs_matched_front_full.png` / `sbs_matched_back_full.png`
- also prior hybrid labels: `sbs_front_face.png`, `sbs_front_chest.png`, ?

## Hybrid stats
- seconds: 32.54700000000048
- mean_confidence: 0.18345850706100464
- confidence_pixels_above_half: 830633
- blockers: left/right auto_align_low_iou_skipped (same class as prior hybrid)

## Float Laplacian (signed conv) ? A0 render vs Hybrid
| View/crop | A0 lap_var | Hybrid lap_var |
|-----------|------------|----------------|
| front | 467.7 | 543.5 |
| back | 402.0 | 478.7 |
| crop face | 747.7 | 1136.8 |
| crop chest | 1211.6 | 1690.3 |

## Visual expectation (for Zenko)
- Chest jacket stripes / necklace: hybrid should retain ortho detail vs soft paint fill where projection confidence is high.
- Face: check jaw/neck smear; prior hybrid risk remains.
- Sides: paint-only (skipped) ? no claim.

## Baselines preserved
- phase1 A0?A3 color GLB SHAs unchanged
- job `paint/albedo_atlas_2K.png` untouched
- job-root `textured_hybrid_a3_color.glb` untouched (Phase2 wrote under `quality_jump_phase2/`)

## Next
Zenko visual-eval of SBS ? decide jaw micro-align vs promote hybrid opt-in only after second character + Bust + Finalize-GLB gates.
