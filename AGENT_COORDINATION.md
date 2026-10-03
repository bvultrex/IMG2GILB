# Agent Coordination

Permanent coordination entry point for agents working on IMG2GILB.

**Live coordination thread:** GitHub Issue #1  
https://github.com/bvultrex/IMG2GILB/issues/1

**ChatGPT durable task queue:** [`quality_lab/CHATGPT_TASK_QUEUE.md`](quality_lab/CHATGPT_TASK_QUEUE.md)  
(Grok maintains ACTIVE + BACKLOG; ChatGPT claims via Issue #1.)

## Agents

- **ChatGPT / Zenko**: active repository contributor and technical reviewer
- **Grok Bot**: active repository contributor
- **Codex**: may contribute when available
- Additional agents should identify themselves in the issue before overlapping work

## Required workflow

Before starting substantial work:

1. Pull/read the latest `main`.
2. Read the latest comments in Issue #1 and `quality_lab/CHATGPT_TASK_QUEUE.md` if you are ChatGPT.
3. Check recent commits touching the files you plan to edit.
4. Post a short claim when working in an area another agent may also touch.

After finishing:

1. Commit with a descriptive message.
2. Run the relevant tests/diagnostics.
3. Post commit SHA, result, tests, and remaining blockers in Issue #1.
4. Update durable project documentation when a result changes project status.
5. If ChatGPT: mark the queue item DONE in Issue #1 (Grok will sync the queue file).

## Message format

```text
[CHATGPT|GROK|CODEX|OTHER]
WORKING ON:
FILES/AREA:
LAST COMMIT:
RESULT:
TESTS:
BLOCKERS / QUESTION:
NEXT:
```

Keep messages concise. Use commits and documentation for full details.

## Conflict rules

- Do not silently overwrite another agent's active work.
- If two approaches are useful, put the alternative in a separate new file/branch rather than replacing the active experiment.
- Experimental results remain experimental until their stated acceptance gate passes.
- Do not promote a backend/model to the simple Studio UI until its validation criteria pass.
- Never commit user reference images, generated private assets, model weights, caches, virtual environments, or large generated GLBs unless explicitly approved.

## Current technical focus

Product constraint: Studio must handle **full bodies, objects, and busts** with the same pipeline family (gates/ROI/register/splice must generalize).

Parallel tracks (2026-09-28):

- **Bust local detail:** Auto-ROI v3 interchangeable with fixed crop for densified registration; dry-splice still fails stitch gates (~4 mm p90). Grok owns seam scripts.
- **Ranger second fixture:** Auto-ROI general fullbody provisional pass; TRELLIS 512/1024 baselines done; SF3D Studio 4-view in progress for belt/pouch quality.
- **Texture:** ChatGPT assigned sharpness diagnostic (see task queue T1).

Active diagnostic areas:

- `quality_lab/auto_roi_*`, `AUTO_ROI_*`, `LOCAL_DETAIL_ACCEPTANCE_GATES.md`
- Grok-owned bust seam/register/dry-splice/stitch `*_v2+` (do not overwrite without claim)
- `quality_lab/CHATGPT_TASK_QUEUE.md`


## Quality jump (2026-10-02)

Joint Grok + Zenko texture-fidelity milestone (no Meshy parity):
- Plan: [`quality_lab/QUALITY_JUMP_PLAN.md`](quality_lab/QUALITY_JUMP_PLAN.md) (Grok ack of Zenko sequence)
- Zenko execution + taxonomy: `QUALITY_JUMP_EXECUTION_PLAN.md`, `PAINT_UV_FAILURE_TAXONOMY.md`
- Detective living note: `COMPETITOR_GAP_DETECTIVE.md`
- Phase 1 factorial A0-A3 on frozen David job - Grok GPU; results under lab `_vis_export\quality_jump_phase1\`
## Product north star

The final user experience remains intentionally simple:

1. Start one Windows EXE.
2. Upload one image or named multipose/multiview references.
3. Set only meaningful controls such as quality/poly target, texture, height, and optional rigging.
4. Click **Modell erstellen**.
5. See stage/progress information.
6. Inspect a rotatable 3D/PBR preview.
7. Save a validated GLB.

Backend model routing, Python environments, CUDA details, ports, UV tools, and diagnostic experiments stay hidden from the normal user.

### Grok Bot — 2026-09-28 ~19:50 Europe/Warsaw
- Anime SF3D 4-view replay job 1cce72cd (b66c77f5 inputs, same settings as ranger). shape bit-identical to original; _vis_export\anime_sf3d.


### Grok Bot — 2026-09-28 ~20:13 Europe/Warsaw
- Female anime SF3D 4-view job 2a3235bc from anime_test; shape watertight; _vis_export\anime_female_sf3d.



## 2026-09-28 20:20 CEST — Grok: Studio interim packaged
- Launch: D:\SF3D_QualityLab\studio_interim\Start_IMG2GILB_Studio.bat
- Patches: desktop/server.py reveal+open_jobs; web preset/folder/open buttons
- Screenshots: _vis_export\studio_interim\
- Issue draft: quality_lab\ISSUE1_DRAFT_STUDIO_INTERIM.md

## 2026-09-28 ~23:30 CEST — Grok: Meshy-like pipeline v1 (texture)
- Plan: quality_lab/MESHY_LIKE_PIPELINE_PLAN.md (no parity claims)
- Wired: paint_multiref, texture_sr=pil|realesrgan, remesh(opt), hybrid_a3 opt-in
- A3 front micro-align (face-local) on David 5e81ac79; vis _vis_export\meshy_like_v1\
- A3 still >> A0 on chest; face better than A0, jaw smear residual
- Uncommitted. Result: quality_lab/MESHY_LIKE_V1_RESULT.md

## 2026-10-02 — Joint detective (Grok + Zenko)
- Living doc: [quality_lab/COMPETITOR_GAP_DETECTIVE.md](quality_lab/COMPETITOR_GAP_DETECTIVE.md)
- Goal: find knackpunkt for mushy textures + coherent meshes vs Meshy/Tripo *public stages* (no parity claims).
- Ownership split + A/Bs inside that file. Claim work in Issue #1 before overlapping hybrid/desktop or GPU.
