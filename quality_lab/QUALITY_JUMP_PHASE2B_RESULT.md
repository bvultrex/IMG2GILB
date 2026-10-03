# QUALITY_JUMP_PHASE2B_RESULT

Created: 2026-10-02 20:37 (Europe/Warsaw)

## Scope
Phase2b Hybrid sidecar per Zenko 5958649808 / 5958774240:
- Face/jaw/neck: hard Paint-prefer on **tight** jaw only (stops before collar/necklace)
- Steeper confidence falloff front/back -> side (incidence), **no global blur**
- Explicit **fallback_no_micro** compare
- Matched renders: front, back, +/-35deg, +/-90deg + confidence/coverage masks
- Correct **collar_necklace** + **chest_cross** + **back_emblem** crops (not waist)
- Hybrid baseline remains **P2** (`624d1a1f...`); jawblend unaccepted; A0 control
- `production_accepted=false` — no Studio default flip — no A0-A3 regen

## Code
`quality_lab/project_hybrid_a3.py` (opt-in flags; P2/jawblend paths unchanged):
- `--phase2b`: jaw ROI + steeper incidence + anime-face align attempt + hard jaw Paint (tight) + +/-35/90 renders
- `--no-face-micro`: explicit region-specific fallback (weight map only)
- `--jaw-blend`: prior Phase2 polish (kept; not promoted)

## Artifacts (NEW under quality_jump_phase2b/ only)

| Artifact | Path | SHA256 |
|----------|------|--------|
| P2B color GLB | `.../textured_hybrid_phase2b_color.glb` | `7829d786fe135fa70ca3995ea4f8ab5e55c2d12ac84331da7c38f4eb7e33e8c1` |
| P2B PBR GLB | `.../textured_hybrid_phase2b_pbr.glb` | `81ca2e7e361a5e4ea3f1bef4ad32bce29b107d96006c195bb1e270ae234d647c` |
| P2B atlas | `.../hybrid_work/albedo_atlas_hybrid_a3_2K.png` | `1629a48641430a521fba8ad35a9f5cf21cec2bc4314339f8b4420d820b5fe723` |
| Fallback color GLB | `.../textured_hybrid_phase2b_fallback_no_micro_color.glb` | `b1ff3eeb1612c3bc8d7c48c7ab03710b9076586c94853bfea076b655d0d3ee77` |
| Confidence atlas | `.../hybrid_work/confidence_atlas.png` | `6febae8873db9a10b4fbd8602c99f49bb349d5d7f1f3acf61db3e3e114e9b346` |

Job: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513`

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase2b`
- Angles: `sbs_angle_{front,back,p35,m35,p90,m90}_A0_P2_P2B.png`
- Fallback: `sbs_angle_*_P2_P2B_fallback.png`
- Crops: `sbs_{face,jaw,collar_necklace,chest_cross,back_emblem}.png` + crop guides
- Masks: `confidence_atlas.png` / `_heatmap.png` / `P2B_front_confidence_overlay.png` / `*_coverage.png`

## Baseline integrity (post-run)
| Control | SHA12 | Status |
|---------|-------|--------|
| P2 Hybrid color | `624d1a1fe487` | unchanged |
| Jawblend color | `c10ac0822785` | unchanged |
| A0 atlas | `57706be141b5` | unchanged |

## Stats
- P2B mean_confidence ≈ 0.1413 (steeper than P2/jaw; intentional side falloff)
- confidence_pixels_above_half: 603061
- front micro chosen: `face_center_translation_clamped` / weight `phase2b_hard_jaw_paint`
- sides skipped: ['left', 'right']
- fallback mode: `bbox_iou_refine+forced_no_micro`

## Laplacian (mean abs lap) — A0 / P2 / jaw / P2B / fallback
| Crop | A0 | P2 | jaw | P2B | fb |
|------|-----|-----|-----|-----|-----|
| face | 19.5 | 25.7 | 20.9 | 22.1 | 22.1 |
| jaw | 21.1 | 26.3 | 21.6 | 24.6 | 24.6 |
| collar_necklace | 19.5 | 25.2 | 21.4 | 24.2 | 24.2 |
| chest_cross | 19.2 | 23.5 | 24.3 | 24.8 | 24.8 |
| back_emblem | 10.1 | 16.3 | 16.3 | 15.4 | 15.4 |

Reading (metric only — Zenko visual is authoritative):
- **chest_cross / collar_necklace**: P2B ≈ P2 (torso win aimed preserved; tight jaw no longer eats necklace)
- **back_emblem**: slight energy dip vs P2 from steeper incidence — check SBS visually
- **face/jaw**: between A0 and P2 (less stretch-as-detail than raw P2; not a face win claim)

## Grok visual notes (not acceptance)
- No global blur applied
- Double-contour risk reduced vs jawblend by hard source-select on tight jaw
- Face still soft vs 2K ortho input; micro = face-center clamp (anime bbox ROI)
- Oblique +/-35deg should show cleaner front->side fade; +/-90deg still mostly Paint
- `production_accepted=false`

## Gates / next
1. Zenko visual scorecard on Phase2b SBS (collar_necklace, chest_cross, back_emblem, face/jaw, +/-35)
2. Compare P2B vs fallback_no_micro if face looks wrong
3. Later: second clothed + bust + real GLB import gate before finalize
4. No Studio default flip

## Limitations
- Auto-align still silhouette/face-bbox, not full semantic landmarks
- Left/right ortho projection still skipped (low IoU)
- Geometry unchanged; no Meshy/Tripo parity
