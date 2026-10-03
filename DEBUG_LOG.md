
## 2026-09-28 ~20:20 CEST Grok � Studio interim
- Packaged D:\SF3D_QualityLab\studio_interim + desktop\dist
- server reveal/open_jobs; web preset+folder+open buttons
- Smoke: service health OK, reveal 200, EXE launch OK, screenshots staged


## 2026-10-02 Codex takeover / Blender verification
- Fresh inputs-only sequential Ranger/Bust runner started; first job 4a80e4f55d0145408fc1921effe276b5 in ../quality_runs. BRIA/shape/UV passed; Paint running at this checkpoint. No seeded stage caches.
- Blender 5.2 imported and CPU-rendered both prior cached-finalize output.glb files. Ranger height 1.700000m / 99998 triangles; bust 0.400000m / 99990 triangles; embedded 2K albedo/MR decoded; source unchanged.
- External import/base-color preview passes; PBR lighting, rigging and fresh full run remain open. See codex_blender_import_check.py and CODEX_TAKEOVER_2026-10-02.md.

## 2026-10-02 fresh Ranger validation
Full original-input pipeline completed (910.8s), output 18bc53c88fed4641f0072fef9358fcb3708bba42fb9eef44b02870e17c3b534d. Independent Blender PBR import/render, size and decoded textures passed. Mesh/UV/MR invariants passed. Bust fresh run 341179b171fe48918a231032f4f5b82c automatically executing next. Production acceptance false; face/rig off, watertight false. Fixed audit renderer relative output resolution; rerender confirmed expected absolute output location. Neutral PBR visual inspected; soft detail remains, not a Meshy-parity claim.

## 2026-10-02 texture cache integrity
Fixed missing hybrid PBR output hash and missing active hybrid/multiref code fingerprints. Added behavioral CPU regression tests; 6 tests passed with existing contracts. No GPU restart or baseline modification. Live bust run still uses already-loaded orchestrator.

## 2026-10-02 independent matched Ranger review
Added configurable azimuths/resolution to Blender audit, rendered baseline and hybrid at 0/+35/-35/180, 1024px. Front and +35 hybrid reveal double/offset facial features despite clothing improvements. Identified execution gap: desktop invokes old default hybrid, not --face-iso tested sidecars. Next is isolated face_iso comparison after live bust GPU completion. No defaults promoted.

## 2026-10-02 serialized face-ISO run
Queued isolated fresh Ranger face-ISO after terminal successful fresh bust, session 55807. Existing fresh sequence session 36111 live. New runner retains output.glb and writes separate candidates plus provenance manifest. Compare results before integrating mode.

## 2026-10-02 two fresh jobs pass; quality verdict remains partial
Original-input Ranger+bust sequence completed, Blender and invariant audit on bust passed. Face ISO sidecar completed with baseline preservation; frontal double features gone via paint fallback, not restored reference identity. Separate quality gates remain open. See takeover checkpoint for IDs/hashes and local renders.

## 2026-10-02 face transform consistency
Measured actual applied translation vs fitted similarity on saved diagnostics: median5.105 vs1.561px (1024px canvas, 28 detector correspondences). Isolated bounded full-similarity experiment launched, session94854; existing IoU gate unchanged. Not yet accepted.

## 2026-10-02 interior RGB alignment experiment
Full-affine silhouette warp rejected; bounded interior RGB-only sidecar completed with identical alpha and silhouette IoU. Feature projection now used, but post-warp vertical center discrepancy remains ~10px at2048. Independent Blender three-angle render pending session71369; no acceptance/default changes.

## 2026-10-02 Ranger interior visual pass limited to facial doubling
Inspected front and ±35 independent Blender images plus prepared front reference. Double eye/brow issue improved, reference likeness better than paint fallback, but neck/collar seams persist. Geometry/UV/MR preserved. Second clothed fixture David isolated experiment running session53306, outputs on C. Defaults unchanged.

## 2026-10-02 ECC forward/inverse correction
Synthetic image registration confirmed ECC sampling transform must be inverted before default warpAffine. Added helper/test and corrected local hybrid function, preserving original script backup. Desktop cache hashes new helper. Seven relevant tests passed. Separate David re-run session71668; no production promotion.

## 2026-10-02 actual anime landmark schema
Inspected vendor landmarks.jpg and README. Corrected guessed jaw/chin indices used as eye/nose features to actual eye/nose/mouth indices11..27 for28-point model. Two math/schema tests pass. Isolated David run73006 active; no thresholds relaxed. Patch file preserves local untracked hybrid edits for handoff.

## 2026-10-02 semantic candidate visual rejection
David generated reference-face variant with corrected schema but double eye/brow features in independent GLB render. Post-warp quality also fails. Reject despite improved numeric direct position residuals. Ranger corrected-schema experiment42426 remains running. Need post-warp acceptance and source-mixing isolation.

## 2026-10-02 source mixing isolation
Found face_iso still mixes Paint via incidence-weighted confidence, despite coherent-source intent. Added opt-in exclusive front-face atlas diagnostic, no default change; David run22640 active. Known post-warp gate failure remains disqualifying. Ranger corrected-schema front render retains improvement.

## 2026-10-02 alpha quantization root cause in experiment
Double eyes already present in aligned 2D image. Original prepared alpha mostly254; strict>=254 experimental overlap fragmented after interpolation to253. Corrected to existing projection foreground criterion>250. New candidate85580 active; production unchanged, prior mixed-source diagnosis alone insufficient.

## 2026-10-02 David double features resolved in isolated GLB
Alpha-consistent interior candidate verified front and ±35 Blender views: no double eyes/brows. Post-warp fit passes; mesh/UV/MR unchanged. Hairline/neck/body defects remain. Added near-opaque interpolation regression (3 math tests pass). Replay identical settings on Ranger active; defaults unchanged.

2026-10-02: Ranger final face settings visually reviewed at 0/+35/-35; mesh/UV/MR invariant pass. Added fail-closed post-warp face gate to isolated experiment; 4 CPU tests pass. Same workflow rerun ranger_postgate_verified started, results pending. Defaults unchanged; neck/body quality and normal pipeline integration remain open.
2026-10-02: Post-gate Ranger full replay passed; final candidate byte-identical to reviewed render input. Started mechanical-bust negative control (bust_postgate_check), no defaults changed.
2026-10-02: Bust negative control failed automatic face-skip requirement (no detections but ECC and upper-region Paint weighting). Patched isolated runner to skip both-negative detections, 5 tests pass; same bust rerun bust_face_skip_verified active.
2026-10-02: Bust skip replay confirms no detected face => no face-specific warp/weights; mesh/UV/MR checks pass. Independent Blender render session58001 active. Added future-run provenance hashing (not retrospective evidence).
2026-10-02: Matched clay isolates geometry cavities and wrong lenses from texture artifacts. Shape/bake welded topology identical:0 boundary,13 nonmanifold edges. Added independent --clay audit; no blind hole fill or defaults change.
2026-10-02: Found side projection tests only90/270 despite oblique bust references. Started optional oblique-camera search on frozen mesh, session75511; defaults unchanged, semantic/visual validation pending.
2026-10-02: Oblique-angle candidate rejected after independent0/+35/180 render review: better silhouette score but worse shoulder/base text ghosts. Invariants pass. Do not promote camera-search defaults.
2026-10-02: Started frozen-camera best-reference-versus-average ablation, session76225. Existing confidence/Paint contribution kept identical; only reference color selection changes. Result and seams pending review.
2026-10-02: Best-source candidate still ghosts pedestal text at+35; reject as complete fix. Invariants pass; camera exact; confidence exact check failed by at most1byte, documented quantitatively. No defaults changed.
2026-10-02: Frozen rasterization exported three mixing arms; invariants all pass. Independent+35 comparison batch76511 running. No production promotion.
2026-10-02: Front/back-only control inspected+35: side plaque ghost and hood lens contamination disappear; front details preserved vs generated baseline. Side registration identified as cause, not solved; multiview remains required. Invariants pass.
2026-10-02: CPU SIFT correspondence audit failed semantic plausibility (5right/7left mutual matches, many wrong parts). No warp applied. Local DINOv3 directory exists; next runtime/feature feasibility check.
2026-10-02: DINOv3 offline512 completes89/86matches, coarse association improves but fine semantics unproven. Started1024resolution audit, no warp.
2026-10-02: DINO1024 audit completed253/233matches; cross-scale consistent70/91, coverage recorded. Repeated motif/surface ambiguity remains; no production warp or default change.
2026-10-02: Stable DINO matches still cause12/19local foldovers. Geometry audit+identity/reflection controls pass; blind warp rejected, assets untouched.
2026-10-03: Filtered local2Dwarp probe rejected visually for doubled contours/broken transitions. No GLB mutation. Need upstream pose/surface alignment, not promotion of patch blend.
2026-10-03: Semantic-camera GLB rejected after independent+35 review, persistent doubled symbols/text. Invariants pass; no default change. Global pose ranking insufficient.
2026-10-03: Raw1.18Mtriangle clay confirms form defects precede decimation. Started front-only conditioning ablation on same model/seed/settings to test inconsistent multiview inputs.

2026-10-03 Codex: independent headprobe clay import passed, source unchanged; three-lens asymmetry visible at 0/+35. Existing v5 auto seam still fails both distance and coverage gates; reverse coverage missing in rejection reasons. Findings and next package in quality_lab/CODEX_LOCAL_DETAIL_REVIEW_2026-10-03.md. No production promotion.

2026-10-03: Independent splice boundary audit and primitive controls completed. Exported detail patch has fragmented/nonmanifold positional topology; full-bust three-quarter visual fails. No model edits. See CODEX_LOCAL_DETAIL_REVIEW_2026-10-03.md.

2026-10-03: Post-remesh repair probe terminal success. CuMesh vertex splitting changes index topology only: 5789 to 0 indexed nonmanifold, boundary2060 to19679; no vertex movement or face removal. Rejected as geometric fix. Audit now distinguishes indexed/positional topology. No production changes.

2026-10-03: Full cleanup stage replay completed. Remesh512 introduces39883 indexed nonmanifold edges after repaired0; final cleanup creates2169 boundary edges. Source unchanged, output isolated. See headprobe_stage_audit/report.json. No production promotion.

2026-10-03 Blender voxel384 experiment completed plus independent reload. Three lenses retained; grille softened; decimation yields149 triangular holes. Topology substantially better but visual/mesh gate still fails. Local sidecars only.

2026-10-03: Pre-decimation384 clay confirms grille loss before reduction. Voxel768 test running: Blender process3812, tool session86611; high-density GLB exported, reduction still active, repeated session polls live. Do not restart; await same handle and then inspect candidate. No acceptance claimed.

2026-10-03: Voxel768 completed, Blender reload passed. Front grille slots better preserved than384;321 triangular holes and6 nonmanifold edges remain. Candidate not accepted. Detailed report in CODEX_LOCAL_DETAIL_REVIEW_2026-10-03.md.

2026-10-03: CRITICAL audit correction:321triangular loops are isolated triangle sheets. fill_holes added321duplicate reverse faces; Blender drops them. Candidate rejected, duplicate check added. Prior hole interpretation withdrawn. Next component-aware cleanup.

2026-10-03: Component-aware cleanup removes321 isolated triangle sheets, retains all other geometry exact. Blender reload99,358faces confirmed. No boundaries,6nonmanifold edges remain inside main component. No production promotion.

2026-10-03: Fixed isolated-triangle cleanup dropping GLB NORMAL attributes. Explicitly retains and exports normals; reload check verifies all used vertex normals within1e-6.963unused isolated vertices legitimately normalize tozero after removal. Verified candidate path headprobe_voxel768_cleanup_normals_verified. Blender visual check underway; source unchanged,6nonmanifold edges remain.

2026-10-03 Sheet connectivity probe completed:6to4indexed nonmanifold,6positional contacts unchanged, exact triangle coordinates. Rejected as full repair. Next coherent local crop/contact localization, not global topology bookkeeping.

2026-10-03 Registered improved detail crop tested and rendered.2of6contacts withinpatch,oneprotected. Box-onlycut17boundarycomponents cannot pass seamgate. No fusion/default change.

2026-10-03 MeshLab repair isolated:12faces removed,6quadholes. Standardfill recreates5nonmanifold. Occupied-diagonal safeguard rejects customquadfill. Need interior-vertex/localretriangulation; no promotion.

2026-10-03 Interior-fan local repair passes edge topology and independent Blender reload, zero boundary/nonmanifold edges. Existing303self-intersection flaggedfaces remain;new24faces notflagged. Three lenses/grille retained. See headprobe_fan_repair artifacts; no production promotion.

2026-10-03 Exact surface-set comparison:303flaggedfaces unchanged afterfanrepair.33touchcrop/23protectedbox. Existing intersection issue remains inside targetdetail; no blind deletion or promotion.

2026-10-03 Independent BlenderBVH95nonadjacent overlap pairs/153faces; red overlay rendered and reviewed. Includes smalllens region. Added source-hash-checked diagnostic overlay. No production change.

2026-10-03 Local bounded smoothing v2 tested3caps.0.25mm reduces303to127selected intersectingfaces, topologyedgechecks remainzero. Blender reload/render terminal success99,370faces; front details retained at reviewedresolution. Candidate9386578c4f17ad26799f558338c7766544722ce8de48913d2a263d4b512b41d6 experimental, remaining intersections unresolved.

2026-10-03 Orientation audit rejects previous127face arm(21flips). Guarded iterative run achieves168remaining,zero flips/degenerate/edge defects,totalcap0.25mm,rollback on plateau. Experimental only.

2026-10-03 Upstreamgeometrycontrol launched from savedlatent. First isolateddecode failed because decoder remained trainingmode; fixed explicit.eval() (normalpipeline does this). Firstsession29830terminal. Newsession28964 confirmedlive, outputheadprobe_native_standard_eval. No newdiffusion/install. Must inspect samehandle before restart.
