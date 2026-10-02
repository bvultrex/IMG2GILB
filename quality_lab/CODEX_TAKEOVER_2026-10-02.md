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

## Full-similarity diagnostic and isolated experiment
CPU landmark audit on saved 1024px diagnostics (28 correspondences): median residual unchanged10.383px, applied center translation5.105px, fitted similarity1.561px. These are detector correspondences, not ground truth. Existing gate scores a similarity but extraction applies only translation, so scored transform differs from actual transform. New isolated codex_face_similarity_experiment.py keeps the existing IoU and quality gates, allows full fitted similarity only for scale0.98–1.02, rotation<=2deg and center shift<=24px. Outputs separate codex_face_similarity, preserves production GLB. Process session94854 currently live; log sibling quality_runs/ranger_similarity.log. Inspect report accepted/reject and independent renders before any integration. No threshold relaxed, no defaults changed.

## Similarity gate result and interior-only follow-up
Full similarity experiment exited successfully but micro alignment rejected: IoU 0.90310961 -> 0.89859607, so result remains paint fallback. This does not justify loosening the silhouette threshold.

Isolated --interior experiment now running in session92223, log sibling quality_runs/ranger_similarity_interior.log, output fresh Ranger/codex_face_similarity_interior. Only RGB inside valid opaque source/candidate overlap can move, feathered 12px from coverage boundary; alpha is asserted identical. Existing IoU gate retained (structurally unchanged coverage), and post-warp landmark-quality metadata added. Semantic/visual validation is essential because fixed alpha alone cannot prove correct features. No defaults or production hybrid changed. Follow-up: compare actual detected landmark positions and independent GLB renders; reject if face edges/identity regress.

Interior experiment completed successfully (session92223 ended). Report accepted=true/project_face=true and identical silhouette IoU/alpha, but post-warp detected center remains dy=-10.05px at2048, so alignment is not established by that acceptance flag. Independent three-angle Blender render running session71369, outputs quality_runs/ranger_matched_interior. Inspect visually next; do not treat quality detector refit residual as actual placement residual.

## Ranger interior candidate visual review
Independent Blender front/+35/-35 renders inspected; conspicuous doubled eyes/brows from default hybrid are absent, and face resembles prepared reference more closely than paint fallback. Remaining hard neck/collar transitions prevent whole-texture approval. Frontal source reference inspected directly. Mesh/faces/UV/MR invariant comparison passed; candidate SHA256 5ec676c4989ec47580cda9ab0a5a4395a76d0edc2ca1ddd45cbb50f69b77c45c. This is a promising fixture-specific result, not production/generalization acceptance.

Second clothed fixture David 5e81ac7963f84af2a403fb659cea7513 now running the same --interior experiment, session53306. Explicit output C sibling quality_runs/david_similarity_interior avoids D capacity pressure. Log quality_runs/david_similarity_interior.log. Added --out to experiment runner; default behavior preserved. Existing job assets untouched. Next inspect acceptance metadata, matched Blender views and compare against existing David control before considering integration.
David experiment session53306 completed; separate candidate generated. Independent three-angle Blender render now session30651. No GPU experiment remains active.
David metadata: accepted=true but project_face=false, chosen=ecc_translation. Thus accepted flag does not mean reference-face projection; candidate still requires fallback-specific review.

## ECC direction bug confirmed and patched
David interior run had project_face=false (scale1.144 exceeds1.12 gate). ECC then returned (-5.38,-18.47), treated incorrectly as a forward warp. Synthetic known-translation test confirms findTransformECC returns template-to-input sampling transform, whereas downstream warpAffine without WARP_INVERSE_MAP needs its inverse. Added face_transform_math.ecc_to_forward, patched project_hybrid_a3.py to convert once and log sampling/forward direction. Existing untracked hybrid source preserved as .bak_codex_ecc_direction. No scale/IoU threshold relaxed. CPU synthetic test passed; six desktop contracts passed. Helper contributes to hybrid cache fingerprint.

David isolated rerun session71668 currently live, out quality_runs/david_interior_ecc_fixed and matching .log. Original outputs preserved. Need inspect post-warp metrics and independent views; this fixes math, not proof of identity fidelity. Source project_hybrid_a3.py remains pre-existing untracked file with this small local patch; don't blanket-stage all Grok work.

## Verified landmark schema correction
ECC-fixed rerun session71668 completed: correction now (+5.38,+18.47); post detected center improves from (21.78,42.55) to (15.06,8.10), but reference projection still rejected. Stronger root cause found in local authoritative anime-face-detector assets/landmarks.jpg: indices0..4 are contour/chin, NOT eyes/nose as hybrid's guessed subset claimed. Actual eyes11..22, nose23, mouth24..27. Corrected quality subset to those17 indices for28-point detector; unknown counts retain all rather than guessing. Existing residual/scale thresholds unchanged. Added schema regression test, 2 math tests pass. Untracked project_hybrid_a3.py changes captured reproducibly in CODEX_HYBRID_MATH_FIX.patch relative to preserved pre-ECC source; helper committed separately.

New isolated David run session73006 currently live: quality_runs/david_semantic_landmarks, log same-name.log. Review gate outcome and actual independent render before accepting. Ranger needs rerun with corrected schema too; previous successful interior candidate remains preserved.

## David semantic-index candidate rejected visually
Session73006 completed. Pre-warp fit now passes (17 actual feature points, scale1.068), but post-warp quality fails (p90=24.55px at2048). Independent front GLB render clearly has double eyes/brows. Reject candidate; no promotion. Direct saved-image position audit (no refit, 1024px) shows median5.33/p907.63 versus previous wrong-ECC aligned image11.56/20.37; this numerical improvement is explicitly NOT visual acceptance and comparison baseline is experimental, not ground truth. Added codex_face_position_audit.py to distinguish actual placement from fit residual.

Ranger with corrected semantic schema currently running session42426, output quality_runs/ranger_semantic_landmarks. David Blender session63758 and CPU position audit96323 finished. Next ensure post-warp gate controls projection acceptance and investigate face texel source mixing; existing experimental acceptance flag is too weak. Preserve old stable outputs. No defaults changed.
