# Temporary autonomous takeover

User explicitly assigned full temporary ownership to Codex/Zenko. Grok was notified in Issue #1 to pause overlapping edits/runs. Preserve the existing dirty tree; no blanket reset, pull or staging.

## Active execution

`codex_fresh_pipeline_gate.py` launches Ranger then bust sequentially through normal Job.run. Only original input PNGs are copied. No prepared data, meshes, paint, hybrid, face outputs or cache entries are copied. A failed first job stops the sequence.

Settings: standard, 100k triangles, 2K, seed42, single-reference paint control, hybrid_a3 on, MR-retain, finalize_candidate hybrid PBR; separate face stage and rig off for isolation. This validates the texture pipeline, not rigging or overall production quality.

First job: `4a80e4f55d0145408fc1921effe276b5`. Local outputs and manifest are in sibling `../quality_runs/`, on C because D had only about 4GB free. Existing runtime/models stay in place. Inspect fresh_gate_*.json, state.json and job.log before starting another GPU process. Initial unified exec session: 36111.

Heartbeat now continues autonomous implementation/testing every 30 minutes rather than delegating work to Grok. Defaults remain unchanged. Next: resolve first real pipeline failure if any; independently import/render final GLBs; complete second sequential run; report test scope honestly. Existing cached-finalize tests remain useful but are not full fresh runs.

## Fresh Ranger checkpoint — 2026-10-02 22:38 local

Ranger 4a80e4f55d0145408fc1921effe276b5 completed all seven stages from original inputs in 910.8 seconds. Independent Blender 5.2 import and neutral PBR render passed: 99,998 triangles, 63,762 vertices, 1.700000 m height, two embedded 2048px maps. Final SHA256: 18bc53c88fed4641f0072fef9358fcb3708bba42fb9eef44b02870e17c3b534d. CPU invariants confirm mesh arrays, UV and MR retained against pre-hybrid baseline. Face/rig deliberately off. Mesh is not watertight; no production acceptance. Frontal render still shows soft detail; no quality-parity claim.

Second fresh job (bust) automatically started: 341179b171fe48918a231032f4f5b82c, currently shape. Runner session 36111 remains active. Do not start a competing GPU job. Studio server session 8273 serves existing D-drive jobs; C-drive fresh results are not yet UI-validated. Local evidence: sibling quality_runs/ranger_fresh_invariants.json and quality_runs/blender_ranger_fresh_pbr/. Blender audit now supports neutral PBR lighting and resolves output paths before rendering to avoid Blender-relative path ambiguity.

## Texture cache correction
The hybrid cache previously omitted textured_hybrid_a3_pbr.glb; missing/corrupt final PBR could therefore be reused. It now verifies that output too. Active hybrid/multireference implementation content and resolved paths contribute to the fingerprint, using the same script resolver as execution. Existing cache entries naturally invalidate. Six CPU tests passed (test_texture_cache plus test_contracts), including unchanged cache reuse, deleted/modified PBR regeneration and implementation-change invalidation. The already-running fresh bust process retains its originally loaded orchestrator; this change is for subsequent processes, with no running-service restart.

## Studio selection race
Guarded render against responses whose job ID is no longer selected. Previously a late poll could overwrite a newly selected project's preview and download URL. Node regression executes actual render code and confirms stale complete/running responses cannot change preview, download or busy state. JS syntax passes. Browser tested rapid bust-to-Ranger switch plus color preview: correct Ranger model and download link remained, no console warnings/errors. This checks cached-final Ranger 8fb2487ba66a4421a12a4dcc59038f64, not yet C-drive fresh job. Pre-existing Grok app.js helper edits preserved unstaged.

## Serialized face-ISO experiment queued
Runner quality_lab/codex_fresh_face_iso.py started in session 55807. It waits up to 30 minutes for fresh bust 341179b171fe48918a231032f4f5b82c to reach complete, aborts for failure/cancellation, then runs the fresh Ranger with --face-iso and exact source PBR. Separate codex_face_iso directory/GLBs; execution manifest records command, implementation hash and original output hash preservation. No --vis Hunyuan renders requested; use independent matched Blender views afterwards. Do not launch duplicate face-ISO or another GPU job while this runner is pending. Fresh sequence session 36111 still live, currently MR bake. Completion of this experiment is not visual acceptance.

## Fresh sequence completed; face ISO fallback verified
Fresh Ranger and bust both completed with original inputs only; no seeded intermediate caches. Bust output SHA256 de171dc6e0c6618c8c1cf5b3775086ac43b8a08215e229a54756fc4e0fc9fbac, Blender import passed: 99,990 triangles, 69,423 vertices, 0.400000m and two 2048 maps. Mesh/UV/MR invariant audit passed. Independent baseline/hybrid matched Blender renders at 0/35/180 written under sibling quality_runs/bust_matched_*; frontal inspection shows more faithful lettering and mask texture but underlying symmetric lens geometry remains wrong. No geometry acceptance.

Face ISO runner session 55807 completed after sequence session 36111 exited successfully. Original Ranger output hash unchanged. Report reproduces iou_regression rejection (0.90310961 -> 0.90090890); coherent paint fallback, project_face=false. Front Blender render removes doubled eye/brow projection but restores generated identity. This is coherence protection, NOT a reference-fidelity breakthrough. Matched four-angle renders under quality_runs/ranger_matched_face_iso; front inspected, other angles still to inspect. GPU experiments now completed; do not poll ended sessions. Next investigate local alignment rejection and reference-to-geometry mapping before integration. Defaults remain unchanged.
