# Agent Coordination

Permanent coordination entry point for agents working on IMG2GILB.

**Live coordination thread:** GitHub Issue #undefined
https://github.com/bvultrex/IMG2GILB/issues/1

## Agents

- **ChatGPT / Zenko**: active repository contributor and technical reviewer
- **Grok Bot**: active repository contributor
- **Codex**: may contribute when available
- Additional agents should identify themselves in the issue before overlapping work

## Required workflow

Before starting substantial work:

1. Pull/read the latest `main`.
2. Read the latest comments in Issue #undefined.
3. Check recent commits touching the files you plan to edit.
4. Post a short claim when working in an area another agent may also touch.

After finishing:

1. Commit with a descriptive message.
2. Run the relevant tests/diagnostics.
3. Post commit SHA, result, tests, and remaining blockers in Issue #undefined.
4. Update durable project documentation when a result changes project status.

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

The current fidelity bottleneck is **local geometry preservation**, demonstrated by the mechanical bust fixture:

- whole-object Hunyuan/TRELLIS/TripoSG tests simplify the reference's three-lens arrangement;
- a TRELLIS head-only crop partially recovers the asymmetric three-lens arrangement;
- bounded global registration improves held-out support error but does not reach the registration gate;
- protected local warp improves support agreement while leaving the central lens region unchanged;
- the current next test is a **dry splice** that places the warped detail patch into the whole bust without welding it.

Active diagnostic files:

- `quality_lab/register_bust_detail.py`
- `quality_lab/deform_bust_detail.py`
- `quality_lab/dry_splice_bust_detail.py`
- `quality_lab/render_dry_splice.py`
- their `Run_*.bat` runners
- `quality_lab/GEOMETRY_BENCHMARK_2026-09-28.md`

Latest ChatGPT-side geometry commits at creation of this file:

- `3a297b4` test bounded rotational bust registration
- `c1542de` add protected local bust detail warp
- `0a3befc` add local bust warp runner
- `75aaa8a` add dry splice bust diagnostic
- `8fa410e` add dry splice diagnostic renders
- `66accaa` add dry splice runner

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
