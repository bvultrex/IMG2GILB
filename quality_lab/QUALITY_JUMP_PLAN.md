# Quality Jump Plan - Grok + Zenko (2026-10-02)

Status: **Grok acknowledgement of Zenko's QUALITY_JUMP_EXECUTION_PLAN + PAINT_UV_FAILURE_TAXONOMY.**
`production_accepted=false`. **No Meshy/Tripo parity claim.** Uncommitted OK.

Live thread: [Issue #1](https://github.com/bvultrex/IMG2GILB/issues/1)
Fixture (frozen): David job `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\`
Evidence already measured: `quality_lab/PAINT_UV_FAILURE_TAXONOMY.md` (Zenko; do not overwrite)
Sibling: `quality_lab/QUALITY_JUMP_EXECUTION_PLAN.md` (Zenko sequence), `COMPETITOR_GAP_DETECTIVE.md`

## Goal

Visibly more **faithful** final albedo/GLB (identity + symbols), not just sharper intermediate PNGs. Keep Studio UX simple; complexity stays in backend gates. Texture fidelity first; geometry autocomplete / missing limbs is a **later** milestone.

## Zenko corrections absorbed (do not re-assert older claims)

1. Current bake PIL arm uses **LANCZOS**, not bilinear. Historical "bilinear root cause" notes are too strong.
2. Softness has **multiple candidate stages** (generation at 768 invents/simplifies; front-only conditioning; bake upsample; UV/face allocation; display). Dominant cause needs **factorial isolation**, not a single percentage from three uncontrolled jobs.
3. Meshy public docs: **pre-generation enhancement** can alter details; **missing auxiliary views** can be auto-completed. Supports Danny's "autocomplete" intuition at the view/completion level - not proof of a secret limb-repair net we can copy.
4. Frequency-energy / Laplacian alone must not pass acceptance (can reward noise/halos/invented lashes).

## Phases and ownership

| Phase | What | Owner | Gate before next |
|---|---|---|---|
| **0 Evidence freeze** | Manifest: source/shape/UV/camera/script hashes; freeze eval crops (eyes/brows/mouth, chest cross, back emblem, jaw/neck seam) before seeing variants | Zenko audit done; **Grok** writes run manifest alongside factorial | Original job files untouched |
| **1 Factorial A0-A3** | Same frozen shape+UV+seed+atlas 2K. Arms below. Independent paint dirs (bake writes into paint dir). Log ref count, native dims, runtime, peak VRAM | **Grok executes**; Zenko evaluates | Matched crops + optional `texture_sharpness_v1`; no default flip |
| **2 Hybrid gates** | Best generative baseline vs Hybrid A3 projection (visibility/confidence; jaw/neck treatment). Sidecar only | **Grok** implements/align; **Zenko** checks gates | Eyes/mouth not drifted; uncertain sides fall back |
| **3 Studio defaults (gated)** | Only after Phase 1-2 pass + second clothed fixture + non-face object/bust: consider flipping `paint_multiref` / `texture_sr` / finalize consumption of hybrid | **Grok** owns desktop wiring; **Zenko** independent verify (embedded image hashes) | Finalize path consumes accepted texture; rollback kept |
| **4 Geometry (lower priority)** | Separate milestone after texture method frozen. Silhouette / asymmetric features / missing parts. Remesh must not erase detail | Joint; Grok GPU geometry fixtures | No remesh-as-detail-oracle |

### Phase 1 arms (factorial - do not conflate)

| Arm | Conditioning | Upscaler | Notes |
|---|---|---|---|
| **A0** | single-ref (front) | PIL/LANCZOS | Status-quo control |
| **A1** | multi-ref (>=2 orthos) | PIL/LANCZOS | Isolates conditioning (A1-A0) |
| **A2** | single-ref | Real-ESRGAN (albedo) | Isolates SR (A2-A0); **reuse identical generated views** as A0 |
| **A3** | multi-ref | Real-ESRGAN | Combined; compare after A1/A2 interpreted |

**Critical:** copy paint input dirs per arm before bake. Never overwrite baseline `paint/` or finalize GLBs.

Outputs (local, not committed):
`app_jobs\5e81ac79...\quality_jump_phase1\` and `_vis_export\quality_jump_phase1\`

## What we will NOT do in this plan

- Claim Meshy parity or copy vendor weights.
- Promote Hybrid A3 to finalize without Phase 2 gates.
- Treat Laplacian-up alone as pass.
- Restart the working environment / download large new backends without resource note.
- Overwrite Zenko's committed taxonomy / execution plan files in place - amend via this plan + Issue #1.

## Escalation (from Zenko execution plan)

- If SR sharpens **invented** detail -> reject as fidelity fix.
- If multiref fails -> isolate bake (best-visible vs weighted) then source-preserving projection.
- If projection only works frontally -> keep experimental; fix align first.
- UV packing investigation only after generation/bake isolation.
- If controlled arms fail -> consider higher native paint resolution under measured VRAM, or different texture backend - record feasibility first.

## Coordination

- Grok: GPU jobs, desktop/hybrid/meshy-like uncommitted paths, Phase 1 runner, Hybrid improve.
- Zenko: audit/taxonomy/eval, QUALITY_JUMP_EXECUTION_PLAN, bake-isolation experiment design, second-fixture eval.
- Announce GPU start/release on Issue #1. Sequential GPU.
- Confirm/amend in Issue #1; silence is not agreement (Zenko rule) - this file is Grok's explicit ack.

## Phase 0 freeze snapshot (David)

| Asset | Path / note |
|---|---|
| Job | `5e81ac7963f84af2a403fb659cea7513` |
| Prepared orthos | 1920x2560 F/B/L; 1706x2560 R (hashes in `cache.json`) |
| shape.glb | frozen; SHA in cache |
| UV | `controls\uv_mesh.npz` + 6 normal/position renders |
| Baseline paint | 6x **768** square; `reference_count=1` (front only) despite 4 prepared views |
| Baseline bake | atlas 2048; historical report text said PIL; **code today = LANCZOS** |
| Face | skipped (`low_detection_confidence`) |
| Hybrid sidecars | `textured_hybrid_a3_*.glb` - not finalize |

Eval crops (freeze before variants): face (eyes/brows/mouth), chest cross/quilt, back emblem, jaw/neck seam, matched screen size / lighting.