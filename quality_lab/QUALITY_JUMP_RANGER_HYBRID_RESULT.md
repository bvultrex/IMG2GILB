# QUALITY_JUMP_RANGER_HYBRID_RESULT

Created: 2026-10-02 ~21:10 (Europe/Warsaw)

## Scope
Second clothed fixture through **new texture/hybrid path** (Paint fill + ortho projection), not legacy front-only paint finalize.

## Job
`D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833` (ranger_ortho_v1)

## Artifacts
| Artifact | SHA256 |
|----------|--------|
| Hybrid color | `ee70297722412b4461257f555d57343fc8182602dd6489546532bcee59bb9847` |
| Hybrid PBR MR-retain | `92fd78c9e6562fe1290663ceed8c37b9b14d76d3028dd82265d7aaf88717d66b` |
| Paint color (untouched) | `6a809f5e2181aa03cd314e86544fbb0c1b6a70f5960cc9c036ab99f6dda2a833` |

Paths under `…\quality_jump_second_fixture\`
Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_hybrid\`

## Views
All four orthos projected (no skip): front/back/left/right IoU ≈ 0.90–0.93.

## Laplacian paint → hybrid
| Crop | paint | hybrid |
|------|-------|--------|
| face | 5.78 | 10.23 |
| chest | 6.73 | 10.09 |
| back_logo | 6.16 | 10.76 |

## Gates
- `production_accepted=false`
- Studio defaults unchanged
- No Meshy parity claim
- Gate criterion 1 (Ranger hybrid) ready for Zenko visual; auto Studio×2 with `hybrid_a3=true` still open
