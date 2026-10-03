# QUALITY_JUMP_PHASE2_JAWBLEND_RESULT

Created: 2026-10-02T20:25 (Europe/Warsaw)

## Scope
Phase-2 polish sidecar: **Jawblend** Hybrid vs Phase-2 Hybrid vs A0.
- Goal: reduce face soft/smear and jaw/neck stretch while **keeping the chest win** (cross / quilt / jacket bands).
- Paint fill atlas = Phase-1 A0 bake (unchanged).
- No Studio default flip. No Meshy parity. Phase-1 A0–A3 and Phase-2 Hybrid baselines untouched.

## What changed (code)
`quality_lab/project_hybrid_a3.py` (+ copy `D:\SF3D_QualityLab\project_hybrid_a3.py`):
- New `--jaw-blend` flag (default off — Phase-2 baseline path unchanged).
- Face micro-ROI **shrunk at bottom** (~28%) so translate/ECC does not drag chin into neck.
- Asymmetric bottom feather on face-local warp.
- `jaw_blend_weight_map`: stronger upper-face projection; **Paint-prefer** soft band on jaw/neck; chest stays at full projection scale.

## Outputs (NEW sidecars only)
| Artifact | Path | SHA256 |
|----------|------|--------|
| Jawblend color GLB | `...\quality_jump_phase2\textured_hybrid_phase2_jawblend_color.glb` | `c10ac082278599c2adff018e62a80cdf50d6335bfdf96db87b4bc683cf3372ce` |
| Jawblend PBR GLB | `...\quality_jump_phase2\textured_hybrid_phase2_jawblend_pbr.glb` | `f8bb57643fed7fbacf70ab75f9581fb805dc9cc6cd106e5bfbff076b94fab0b4` |
| Jawblend atlas | `...\quality_jump_phase2\hybrid_work_jawblend\albedo_atlas_hybrid_a3_2K.png` | `358efe9ad8038d91f1873f2f6463d76bcdbb323184e06f552639b423edd4ea4f` |

Job root: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\`

Vis / SBS: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2_jaw\`
- `sbs_A0_P2_jaw_face.png` / `_jaw.png` / `_chest.png` / `_front_full.png` / `_back_full.png`
- crops: `crop_{A0,P2,jaw}_{face,jaw,chest}.png`
- summary: `jawblend_summary.json`

## Baseline integrity (asserted post-run)
| Control | SHA256 |
|---------|--------|
| Phase-2 Hybrid color | `624d1a1fe487458ee1aa92a64536c08f2a6b2c695802f1c5fe115e66121c9bb6` (unchanged) |
| A0 atlas | `57706be141b5869f05f031c81b2f6bf103fc0e1d465eb81f682f55247a8f7859` (unchanged) |
| A0 color GLB | `cbbf50d95a2b9f2d7548846399cf044734fe0b16a7075ec40d153b37b6b301e7` (unchanged) |

## Hybrid stats (jawblend)
- seconds ≈ 31
- mean_confidence ≈ 0.187
- confidence_pixels_above_half: 792814 (P2 was 830633 — slight drop from jaw Paint-feather)
- front IoU ≈ 0.912; left/right still skipped (IoU gate)
- micro: `face_center_translation_clamped` + `weight_map=jaw_blend`

## Float Laplacian (signed conv) — A0 / P2 Hybrid / Jawblend
| Crop | A0 | P2 Hybrid | Jawblend |
|------|-----|-----------|----------|
| face | 755.5 | 1141.6 | 805.6 |
| jaw | 1131.6 | 1552.2 | 1180.2 |
| chest | 1075.9 | 1435.6 | **1431.7** |
| front full | 725.8 | 833.8 | 830.7 |

Reading: jaw/face energy moves **toward A0** (intended — less stretch-as-“detail”); **chest stays with P2** (win preserved).

## Visual verdict (Grok)
- **Jaw/neck:** clear improvement vs P2 Hybrid — dark vertical chin→neck smear reduced; transition cleaner. Still not as clean as 2D input; residual softness + some A0 neck mud from Paint fill.
- **Face:** still soft vs input. Mild feature recovery vs muddy A0; not a face “win” over P2 (upper face still limited by align + 768 paint heritage in fill holes).
- **Chest:** win **held** — cross / jacket bands / chevrons match P2 Hybrid, clearly better than A0 wash.
- **Sides:** still paint-only (skipped). No claim.

## Gates / readiness
- `production_accepted=false`
- Studio default **not** flipped
- **Ready for Zenko re-eval** on SBS (esp. `sbs_A0_P2_jaw_jaw.png` + `_chest.png` + `_face.png`)
- Promote only after Zenko ACK + second character + Bust + Finalize-GLB gates (unchanged policy)

## Next options (do not run until Zenko)
1. Stronger jaw Paint band / weaker face boost if residual left-jaw stretch remains.
2. Optional landmark pairs on front only.
3. Keep Multiref off as default (Phase-1: A0 still conservative control for generative paint).
