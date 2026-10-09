
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
`n2026-10-04: Completed TRELLIS1536 direct QEM and Blender voxel768 reduction controls. Both independently rendered and rejected. 3383 duplicate triangles explain direct-export Blender count discrepancy; dedup does not fix visual damage. Originals unchanged, no active run from package. See quality_lab/TRELLIS1536_REDUCTION_REVIEW_2026-10-04.md. Next: upstream native-unit whole-bust surface export control before UV/texturing.

2026-10-04: Native whole-bust export control running from saved latent; session66767/PID3076. No new sampling; no baseline edits. See TRELLIS1536_REDUCTION_REVIEW_2026-10-04.md for live checkpoint.

2026-10-04: Native1536 export completed; independent Blender views complete. Better coherent surface than QEM, but lost hose detail, visible defects,3396 positional nonmanifold edges. Not accepted. See TRELLIS1536_REDUCTION_REVIEW_2026-10-04.md.

2026-10-04: Stage isolation complete. Fill/remesh retain hose ribs;100k simplification loses them.500k control recovers visible ribs, independently Blender-rendered. Existing holes/lens errors remain, no production acceptance. See TRELLIS1536_REDUCTION_REVIEW_2026-10-04.md.

2026-10-04: Index-only GLB sanitation verified by independent Blender:476164 stored/imported triangles match, source unchanged.1662 duplicates+106 exact zero-area faces removed. Remaining topology defects not fixed; experimental only.

2026-10-04: Full-stage indexed topology audit confirms nonmanifold edges before simplification. Rejected tiled-extractor fix as inapplicable to active non-tiled path. LocalMesh source-only audit opened for trained Pixal3D multiview feasibility; no runtime changes.

2026-10-04 Codex: isolated cp312 torch2.8 multiview runtime installed; checksum-verified NATTEN wheel imports but actual CUTLASS CUDA smoke fails on RTX A4500 SM86 (no kernel image). No model inference/quality gain claimed. See PIXAL3D_MULTIVIEW_PREFLIGHT_2026-10-04.md and codex_natten_smoke.py. Next: SM86-specific build using existing toolkit, then repeat same smoke.

2026-10-04 Codex: NATTEN GPU blocker resolved with existing visualbruno Torch280 wheel. CUTLASS-FNA real GPU smoke passes on A4500 at dilation1/2/4. Isolated LocalMesh dependencies and SHA-verified MV weights being installed; production remains unchanged. Model inference still pending.

2026-10-04 Codex: isolated MV dependency installation and verified weight downloads completed. Real offline Ranger DINO+NAF conditioning passes (10.13s). Existing FP16 sparse/shape decoder strict state_dict audits pass with zero meta leftovers; decoder forward and full MV generation pending. Reports under IMG2GILB-multiview-runtime; no production changes.

2026-10-04 Codex: first trained MV geometry trial running (session55393); four-view encodings and structure/first shape sampling passed. Outputs/report under quality_runs/pixal_mv_ranger_trial1. Camera/background limitations explicit; no quality claim.

2026-10-04 Codex: independent MV clay renders completed; Z-up export corrected in viewer only. Recognizable Ranger but widespread holes; indexed topology fails. Same-seed non-tiled extraction control running session17682; no production acceptance.

2026-10-04 Codex: tiled/non-tiled MV meshes canonical-identical, ruling out tiling for Ranger holes. Native fill/DC1024 surface control visually reduces pitting, but8408 nonmanifold edges and28zero-area faces remain; rejected production. Blender three-angle renders verified, all sessions terminal.

2026-10-09 resume: no live inference; remote/main e23f04d. Later local fourview artifacts found. Texture manifest running is stale (no process/output); preserved and flagged in RESUME_AUDIT_2026-10-09.md. Independent edge-split control fixes indexed count only, positional defects unchanged; rejected as geometric repair.

2026-10-09 user-requested current-state review: inspected Grok local reports/renders and texture runner; documented factual reference-count/pose/orientation problems and bounded next delivery in RESTART_DECISION_2026-10-09.md. Handoff updated. No GPU jobs launched.

2026-10-09 user authorized start: ACTIVE_TARGET_PROMPT.md created. Ranger native1024 texture candidate launched session79487 on fixed baseline geometry/UV/cameras (six views); no new installation or production change. Log: quality_runs/ranger_texture1024_20261009/generation.log. Must finish bake/GLB and visual comparison before claiming gain.

2026-10-09: 1024 sampling completed15/15 but native c10.dll access violation0xc0000005 before image writes, session79487 terminal. Decode stage suspected, not proven. Isolated runner now persists VAE decode input before invoking native decode; original runner/defaults unchanged. One diagnostic retry to preserve expensive sampler output.

2026-10-09: diagnostic session36905 confirmed live, GPU18080MiB/100%. Added isolated per-view checkpoint decoder and exact-binary albedo-only GLB append/repoint exporter (syntax checked). Export preserves original BIN bytes and all document fields except explicit albedo image/texture addition. Candidate not yet exported or visually accepted.

2026-10-09: checkpoint retry reached15/15 and saved1.57MB VAE input, then native fault in accelerate offload model.to during VAE decode entry. Windows additionally confirmed1455/pagefile too small. After all generator processes exited, isolated per-view VAE decoded12x1024 maps successfully (session41736 exit0). Bake session47170 active on unchanged UV; Blender CPU baseline renders produced. No inference retry needed.

2026-10-09: native1024 candidate exported candidate_albedo_only.glb, independent Blender four-angle import/render complete, exact geometry/UV/MR invariants passed. Clothing locally clearer, dark chin marking already present in generated side view; reference fidelity gate not passed. Full result and next correction in quality_lab/RANGER_1024_RESULT_2026-10-09.md. Bake and decoder terminal.

2026-10-09: reference correction completed session72226; corrected GLB independent four-angle Blender renders and geometry/UV/MR invariants passed. Not visually accepted: ghosting/double belts persist; no significant gain over prior hybrid. comparison.html added. Checkpoint runner now supports --checkpoint-only to cleanly separate generation/decode on future authorized runs (no new generation launched).

2026-10-09: isolated source-ownership control completed. Four views cause bright torso patches from wrong projection; front/back-only control improves front/oblique clothing clarity and preserves face reference. Four Blender views inspected; invariants pass. Candidate remains experimental; side registration/fallback, PBR and generalization pending. comparison.html includes new candidate. No production defaults changed.

2026-10-09: Ranger PBR six-angle comparison completed. Second-fixture ownership run revealed unguarded ECC face operation on mechanical bust. Added detector-pair guard only to experimental ownership runner; guarded rerun confirms both-negative skip without face weights. Candidate generated, visual validation/positive Ranger guard control pending; defaults untouched.

2026-10-09: detector guard positive control passed: Ranger output byte-identical to reviewed candidate; bust negative skip confirmed. Real Studio finalize executed sequentially for both isolated candidates without cache spoofing; output GLB mesh/UV/albedo/MR equality and physical heights passed. UI/full fresh pipeline and bust visual gates remain open. All jobs terminal.

2026-10-09: PBR concern investigated. MR channel transfer exact, factors1/1, no coat/normal map. Added transient matte and individual material-channel rendering; matte/PBR looks similar under identical lights. material_comparison.html and pbr_audit.json saved. Physical material assignment and albedo/MR alignment remain unverified; no non-target material mutations.

2026-10-09: actual static Studio color preview was still lit PBR (metallic0 roughness0.8). Added color_preview.py using KHR_materials_unlit, preserving BIN chunks and animation/mesh metadata; finalize uses it for preview only. Standard PBR output SHA remains20f4af0ae148d79271ca6b3346ede518de65550f3d9db6312bd66daaf8261057. One binary/metadata preservation test and2cache tests pass; helper included in fingerprint. Blender imports/renders new preview. Existing saved previews/rig walk preview not migrated; browser UI validation remains pending.

2026-10-09: PBR user review: static color-preview export now truly unlit; matched matte/PBR comparison shows material differentiation remains unresolved. Existing MR preserved, production defaults unchanged. Browser UI verification pending. See quality_lab/RANGER_1024_RESULT_2026-10-09.md.
2026-10-09: Rendered final Ranger metallic channel independently in Blender: buckles detected brighter, nonzero contour contamination elsewhere. Added material_channels.html; GLB unchanged. Material semantics still not accepted. Renderer report scope corrected for channel audits.
2026-10-09: Local three-way Ranger GLB comparison delivered on127.0.0.1:8192. Download hashes and true-unlit material declarations verified over HTTP. Codex browser open queued; WebGL still unverified. No production changes/GPU job.
2026-10-09: Corrected side-patch diagnosis after inspecting input views: light panels already in references; source design differences contribute in addition to registration. One anchor-agreement side-addition experiment rejected after35/90 Blender views (new trouser transitions, no meaningful gain). Fixed geometry/UV/MR verified. Best local candidate unchanged; do not sweep blend thresholds.
2026-10-09: Sequential Paint runner implemented; unit tests pass; real checkpoint replay reproduces all12 PNGs. Fresh1024 reliability run active under sequential_fresh/session32096; no other generation should start until terminal. Defaults unchanged.
2026-10-09: Fresh sequential1024 sampling+decode passed without manual recovery. Tiny pixel differences from previous sampling, not byte-identical; details in sequential_fresh/pixel_difference.json. No active generation. Blank viewer addressed with direct matched Blender comparison images (12HTTPimages decoded). Complete handoff: quality_lab/HANDOFF_2026-10-09_TEXTURE_RESTART.md. Server17300 active8192; browservisualcheck remains open.
2026-10-09: Sequential Paint integration opt-in only; shared paint/bake resolution, code fingerprints and checksum-verified attempt promotion.7CPUregressions pass, including nestedWindowsguards. Existing defaults unchanged. FullStudiochain notrerun. Fullrestart handoff updated.
2026-10-09: Reproduced and fixed untextured finalize regression caused by mandatory unlit materials. Real finalize subprocess and existing color-preview test pass. Default hybrid candidate selection intentionally unchanged pending visual gates. Fullhandoff updated.
2026-10-09: Isolated existing QwenImageEdit runtime on8193/session37414. One side-reference material-consistency experiment queued e0d807a2-8ff5-4401-b53d-af5195750cbe; no downloads, no GLB mutation. Poll samejob; fullhandoff contains provenance/settings.

## Authoritative handoff update: Qwen attempt terminated with memory error
The previous lowvram prompt e0d807a2-8ff5-4401-b53d-af5195750cbe was intentionally interrupted after verifying it was our sole queued job. LOW_VRAM forces the text encoder to CPU in the installed core. Old server session37414 was stopped; isolated server restarted with --normalvram, session49827, port8193.
Replacement prompt62e092d2-2481-49d0-9e0f-4af02ee0908b is now TERMINAL ERROR, not active. Text encoder successfully loaded on CUDA (~7910MB), but UNETLoader failed in safetensors.safe_open with Windows os error1455 (paging file too small) before sampling. No new image or GLB was produced. Full history saved at ../quality_runs/ranger_qwen_reference_20261009/history_normalvram.json; submission_normalvram.json is the authoritative submission. Queue running/pending both empty. Requested unload_models/free_memory via local /free after confirming empty queue.
Measured Windows memory: physical total29340088KiB, free17794192KiB; virtual total33280828KiB, free10077688KiB. Pagefile allocated3848MB. C: free2882347008bytes (~2.68GiB). Do NOT blindly grow pagefile, download models, or retry identical workflow with this disk headroom. No disk cleanup or system pagefile change performed. Resolve commit/disk budget or use a genuinely smaller/sequential model strategy before another Qwen trial. This is a resource failure, not evidence against reference-consistency hypothesis.
Viewer8192 still respondsHTTP200. Static comparison PNG routes were validated previously; browser visual/WebGL acceptance remains open. This handoff supersedes the ACTIVE Qwen statements above. Current experiment is stopped, no GPU generation queued; session49827 is only the idle isolated server. Baselines, MR maps and Studio defaults unchanged.

### Follow-up: existing read-only loader succeeds (CPU-only evidence)
Revalidated current loader implementation in installed comfy/utils.py: default safetensors.safe_open failed with1455, while existing load_safetensors uses mmap.ACCESS_READ and torch.frombuffer. Executed that existing helper in an isolated .venv CPU subprocess against the same20.43GB Qwen UNET. It returned1933tensor entries in0.027seconds and exited0. This only proves mapping/header/tensor-view creation, NOT full tensor access, inference or successful GPU allocation. No model files or installed core edited. Existing cli_args enables this path via --fast dynamic_vram (when not highvram/gpu_only); model_management also changes loading thread behavior, so evaluate that mode in the isolated8193 server before relying on it. No new generation submitted this follow-up. Next justified test: same workflow/seed on isolated server using built-in dynamic_vram, with queue/process exclusivity verified. Do not treat disk/memory limitation as resolved globally. Production defaults unchanged.

### Active isolated DynamicVRAM trial (supersedes idle server state)
Verified queue empty and Python processes: only comparison server and isolated8193 core; stopped only8193 processes. Restarted same base with --normalvram --fast dynamic_vram, toolsession39938. Startup confirms DynamicVRAM enabled on RTX A4500; allocator warns experimental/unsupported. No installation, model edits or production setting changes. Same workflow_api.json submitted once; authoritative submission_dynamicvram.json, prompt c800ba48-2e85-4d2e-8e01-1b5f241ab087. Poll same prompt/session, do not duplicate. Current state RUNNING/queued, generation success unknown. Existing readonly-loader mapping test is not full inference validation. Only this GPU trial permitted.

### DynamicVRAM initial trial terminal failure
Prompt c800ba48-2e85-4d2e-8e01-1b5f241ab087 failed before first completed sampler step, after86.54s. Readonly mapping bypassed1455 but comfy/pinned_memory.py:15 torch.empty failed allocating9440256bytes. Full history_dynamicvram.json preserved. Existing --disable-pinned-memory returns before that allocation (verified source), so next isolated trial disables pinned RAM buffers, same workflow. Queue verified empty before stopping only8193 server. Replacement server session84584, same arguments plus --disable-pinned-memory; awaiting submission. This is targeted memory-path correction, not quality parameter sweep. Production defaults unchanged.
Verified progress: DynamicVRAM + disabled pinned buffers completed model initialization and sampler step1/20. Session84584/prompt399cd60a-674d-42b3-b856-4be5e4962776 still RUNNING. This passed both prior memory failure locations; output/quality unproven. Keep polling same run.

## Latest terminal result: local Qwen edit SUCCESS, image-only gate
Prompt399cd60a-674d-42b3-b856-4be5e4962776 finished20/20 plus VAE decode in278.84s. API status success/completed=true. history_dynamic_no_pinned.json preserved. Output ranger_qwen_reference_20261009/output/ranger_left_material_edit_00001_.png, SHA e72aa8030d7f579263e3fb9d1c3f3a16819e9951f1d1f9440fcd43713280a1fa. Both input/output1024square. Simple foreground maxRGB>20 mask IoU0.985718; this is NOT semantic alignment proof. image_gate.json records metric and limitations.
Visual inspection: intended pale torso/lower coat panels now brown leather; pose/face/belt/pouch broadly retained. Non-target trouser seams/edges also changed; generated outline halo visible. Thus do NOT blindly replace full source image or claim a final GLB gain. Next: restrict any use to verified target clothing regions with existing source geometry/camera correspondence, inspect seams, then matched GLB renders. Original alpha/source outside target must remain intact. Need second side consistency before four-view promotion. No new GLB has been generated from Qwen yet.
Working launch flags: --normalvram --fast dynamic_vram --disable-pinned-memory in isolated8193 core. No install/download/system changes. Queue empty after success; /free requested to release models. Server84584 remains idle; viewer17300/8192 still serves earlier candidate. Main active objective remains incomplete. This section supersedes prior RUNNING statuses.

## Qwen-to-GLB diagnostic: completed, visual gate REJECTED
New lab tool project_local_reference_edit.py projects only a fixture-specific pale-garment ROI from edited aligned left image (azimuth270) onto fixed UVs. It is explicitly NOT automatic material segmentation. garment_roi.json + reference_edit_mask.png document the limitation. Starting atlas: previous front/back ownership candidate. Source GLB: generative baseline, preserving original9385592BINbytes, all document fields except append/repoint albedo. Changed76285atlastexels; outside projected mask exact. Output projected_left/candidate.glb SHA c20e92faff2fde9c370f075d9c8bcf23e2cdd1413ed96092bd8e5a8e064744eb.
Independent Blender5.2 CPU import and matched1024unlit renders at0,-35,-90 completed:63762vertices,99998triangles,1.700000m,embedded2048albedo/MR. Report projected_left/renders/import_report.json. Original file hash unchanged. Visual review vs prior front/back ownership: side garment color more consistent, but lower skirt has additional shifted/doubled boundaries at-35/-90. Reject overallquality gate; DO NOT promote to viewer/defaults or generate second side merely to repeat this. Earliest remaining failure is local image-to-surface garment registration/shape disagreement; global silhouette IoU and canonical colors are insufficient. Next substantive correction must resolve correspondence (or respect existing surface boundaries), not another resolution/colorblend sweep. Face/hose edits from generatedimage were excluded by explicit mask.
Isolated Qwen8193 server was stopped after verifying empty queue to release memory before projection. Projection session7320 and Blender65212 both exit0; no active generation. Viewer8192 remains previouscandidate. User-facing image is experimental, not accepted final output. Handoff preserved complete states and sources.

## Continuation after user reset usage limit
Codex continues ownership; Grok handoff is saved context, not evidence Grok received control. Local DIS bidirectional registration experiment completed (projected_left_registered): only1455/15837targetpixels reliable at2pxcycle/24pxdisplacementgate; mediancycle7.25px. Generated GLB029c85879de2eec06a00a5c77b08b97f8451b3a4f0b2c0b54ab12c266d8782de NOT accepted; no independentBlenderaudit yet because correspondence gate alreadyfailed. Images show reference garmentcut differsfromcurrentmesh. No threshold sweep.
Next justified hypothesis: enhance the actual current model render, preserving its panel layout, instead of projecting an incompatible reference silhouette. workflow_modelspace.json uses model_left_source.png copiedfromregistration_target.png, same20stepQwen settings, prompt onlyrestoreexistingbrownleatherdetail and preserveallgeometry/panelboundaries. Isolated8193 server restarted withpreviousworkingflags, session58036. No productionpromotion. Poll authoritative submission/history oncequeued; no parallelGPU jobs.

## Model-space whole-image refinement: terminal, no quality promotion
Qwen prompt66a68cc9-40be-4d6e-bd53-baf6df2ec941 completed in275.66s, history_modelspace.json. Output output/ranger_modelspace_leather_00001_.png SHA30f46e105f1cfa2e787a979017142a856707274d2b40a6a5dd100b7c5e55e370. Inputactualmodelrender; silhouetteIoU.99641 atmaxRGB>20. Visualreview: layoutpreserved, mainlycontrast/colorchange, existing blurred/smearedleatherstructure persists. modelspace_image_gate.json rejects substantialqualitygain; NO projection/newGLB fromthisimage. Do not treat successfulinference asbreakthrough.
Both directreferenceprojection and genericwholemodelrefinement nowhaveboundednegativeevidence. Next justified work must address limitedlocalpixelallocation: garment occupies roughly175x260boundingROI in1024wholebodyimage, actualvisibleareasmaller. A future single region-specific model-space refinement can supply a larger clothingcrop while preserving existing boundary/coordinate transform and originaloutsidepixels. This is an untested hypothesis, NOT an instruction to run a prompt/parameter sweep. First inspect crop detail and define edge/reference acceptance. Existing changes must remain lab-only. No productiondefault or comparisoncandidate changed.
Stopped isolated8193 server onlyafteremptyqueueverified; session58036no longeractive. Onlycomparisonserver remains. live_status.json updated. Full objective remains unmet; no blocker status asserted.

## Local-resolution hypothesis: crop refinement trial
Wholeimage modelspace refinement preserved shape but failed detailgain. Single next controlledtest keeps sameQwenweights/seed20steps/prompt and changes only framing: ImageCrop x320,y160,width384,height512 from1024 model_left_source.png, ImageScaleLanczos768x1024. Positive/negativeconditioningandVAE input alluse resizedcrop. Exact inverse isdownscale2thenpaste at320,160; use existingmodelvisibility forprojection, not silhouettefit. workflow_modelspace_crop.json persisted. This crop includes torso/garment context; eventual editsmustbe constrained toclothing andpreserve outsidepixels. Noqualityclaim/noGLByet. Server48993 startingat8193, previousserverstopped; processesbeforelaunch onlyviewer. Validate nodeschemas/queuebeforeonesubmission.

## Crop refinement terminal result – route stop
Prompt2f08fa5d-d31f-4193-8e08-282d481a96a6 completed20steps/VAE in253.29s, history_modelspace_crop.json. Output output/ranger_modelspace_leather_crop_00001_.png visibly has dense engraving/contour-line artifacts, not natural leather detail. REJECTED before projection, no newGLB. modelspace_crop_gate.json holds outputhash/decision. No further Qwen crop/prompt sweep for thisfixture justified. Wholeimage failed detailgain; localizedupscaledcrop produced artifacts. These bounded failures do not prove all refinement impossible, but this genericQwenroute has not mettexturegoal. Keep priorbestFrontBack candidate and baselines; no production/default changes.
Server48993 stoppedonlyafteremptyqueue; no activeGPUjob. Next work should return to the actualUV/texturegenerationpipeline and inspect source/detailpreservation or modelconditioning, rather than more genericimage-edit attempts. Any newroute requires a concrete mechanism/evidence, not another cosmeticparameterchange. Fullgoal remainsopen; no successorblockingclaim.

## Scoped source correction: Paint body + reference head candidate
AuditofactualPaintPNG versusHybridrenders shows clothingdoubleboundaries introducedbywholebodyreferenceprojection; generatedbody cleaner. Newlabscript combine_paint_body_reference_head.py preserves1024Paintbody exactly andtakesheadfrompreviousFrontBackownershipatlas. Initialheightgate.86-.895 crossedchin andmixedoldchinmarks; oneobservedcorrection movedtransitionbelowjaw,.825-.85. TheseRangerheightvalues areNOTgeneralautomaticheadsegmentation.
Finalcandidate paint_body_reference_head_neck/candidate.glb SHA83200f7e12df5aafa88fdf09043609dc2fdcba621160473c1e4ab72635ec83e7. OriginalbaselineBIN9385592bytespreserved;79221texelschangedversus1024Paint,bodyoutsidemaskexact. IndependentBlender0,±35,±90,180renders completed:63762vertices,99998triangles,1.7m,2Kembeddedmaps. ActualFinalizein finalized/ passedvertices/faces/UV/albedo/MR invariants; output.glb SHA4882a6e106e49827bb087048cf5b4d8ecbb92bd338f64b218852b76f15d712f7. Finalize-only,notfreshend-to-end.
Visualassessment: cleanerclothingthanwholebodyHybrid andimprovedfrontfaceversusgenerativebaseline. Remainingnecktransition/hairregistrationandgeometryissues; nooverallproductionacceptance. Do notclaimthissolvesallseams or secondmotif. Thisisreviewablecombinedcandidate,notQwenoutput.
Comparisonserverrestarted, CURRENTsession86204 on8192; old17300stopped. Addshead_onlyfourthmodel/panel, retainsoldbaseline/hybrid/candidate. FourHTTPimagesdecode1024square, servedGLBhashmatchesfinalizedfile; browserWebGLnotverified. NoGPUjobactive. Nextwork: generalizeheadlocalization/transitionandindependentvisualgatebeforeintegration; do notreturntoQwensweeps. Handoffandprivateassetsremainlocal.

## UV-selection padding bug fixed; latest review candidate
Added --top-fraction camera framing to Blender audit; headcloseups (neck_audit/) revealed finecracks newlyintroducedbyzeroheightmaskoutsideUVrasterizedtriangles. combine_paint_body_reference_head.py nowextendsUVheightfield tonearestcoveredtexel with scipyEDT BEFOREselection blending. No textureblur/colorresampling, originalBINpreserved. Headcloseupbefore/after confirms addedfinecracksremoved. Coarsechin/hair/neckprojectionboundaries existedintheheadsource andremain; do NOTclaimallseamsfixed.
Latestcandidate paint_body_reference_head_padded/candidate.glb SHAe8d21bd363c4f3e2a55c60539659b3867771a5fa39326e64d339ceac54bf2d65. ActualFinalizeoutput finalized/output.glb SHAefd46ee6bd7cf530c313e6530258c4b10d4b1a8d24d419fec2d66a8c2f42d732; vertices/faces/UV/albedo/MR invariantsallpass. Blenderhead0/+35andfullbody0/±35/±90/180 completedCPU/importpass. NoGPUjobactive. Sixfullbodyrenders saved; closeupswerevisuallyinspected. Bodyoutsideheadselectionunchanged; fixtureheightgate notproductionsegmentation.
ComparisonCURRENTserver31926 on8192 (old86204stopped): head_onlynowpaddedcandidate; oldvariantsstillpreserved. Addedcollapsible detailbefore/after. FourPNG+twoheadPNG HTTPdecodepass,downloadSHAexact. Browservisual/WebGLstillnotverified. HandoffopeningparagraphupdatedtoremoveobsoleteQwenactiveinstructions. Nextmeaningfulwork: inheritedcoarseheadprojectionboundary/sourceconfidence; noQwenretry, nofurtherheadheightparameter sweep. Overallqualitygates/integration/secondmotifremainopen.


## Latest verified checkpoint: head depth-margin correction (2026-10-09)
- Candidate: ../quality_runs/ranger_texture1024_20261009/paint_body_head_no_depth_margin/finalized/output.glb. SHA256: 3212368de79eb2780a59d8618bf77533087a39646a535655a8ef5aeed21dcaf7.
- UV selection padding fixed fine cracks. Opt-in run_reference_ownership.py --no-depth-margin disables depth-boundary dilation only inside the experimental renderer subclass; original visibility/depth rejection and angle gates remain. Production defaults untouched.
- Broad chin band visibly reduced in front and 35-degree closeups. Narrow chin patch, hair/reference misalignment and collar artifacts remain. No complete quality acceptance.
- Real finalize_candidate export passed invariants. Independent Blender import of source candidate c8618a73f89f6b320f8c762d4f894f46ef9090b0709b5b1c156dca98f8753c3e passed: 63,762 vertices, 99,998 triangles, 1.7m, two 2048 textures; six unlit renders completed. Not fresh end-to-end acceptance.
- Comparison server restarted: tool session22585, port8192. Four head_only images and both detail images decoded over HTTP; downloaded final GLB hash matches. Browser/WebGL still not verified.
- Next: inspect side/back regressions, replace fixture height-based head ownership with robust automatic selection before broader integration, then test second motif. Preserve MR, geometry, UV and baselines. Do not resume rejected Qwen sweeps.


Final-export verification: Independent Blender import of paint_body_head_no_depth_margin/finalized/output.glb completed. Front and +35 head renders compared against pre-finalize candidate; results in final_import/render_equivalence.json. Side views inspected: hair and collar limitations remain; no production acceptance.


## Automatic head gate audit (2026-10-09)
Implemented quality_lab/audit_detected_head_gate.py. Uses confirmed destination face bbox from projection report and exact front raster interpolation of normalized mesh height, not a guessed image-to-world scale. Ranger result: forehead 0.9525763, jaw 0.8488553; proposed blend gate [0.8125530, 0.8384832] vs fixed [.825,.85]. Evidence: ../quality_runs/ranger_texture1024_20261009/detected_head_gate.json, input report/mesh hashes included. Missing destination face yields explicit rejection and generated-texture fallback recommendation. No GLB changed by audit.
Next: compare this one face-derived transition against the verified candidate, then run audit on second fixture (must reject absent face). This remains a vertical-slab heuristic, not semantic head segmentation or production acceptance.


## Face-derived transition tested; not promoted (2026-10-09)
- combine_paint_body_reference_head.py accepts --gate-audit with exact mesh SHA binding and validates accepted/range; input atlas hashes now recorded.
- Candidate ../quality_runs/ranger_texture1024_20261009/paint_body_auto_head/candidate.glb SHA661d2b48380d6393b26137447a0f21123f6829f78e5fe136066758b04573b9e3. Original 9,385,592 BIN bytes preserved, body outside gate exact.
- Independent Blender front/+35 closeups complete. Face retained but lowered gate changes neck color and produces a faint horizontal boundary. visual_review.json says DO NOT PROMOTE. Viewer remains verified no-depth-margin fixed-gate candidate.
- Mechanical bust audit ../quality_runs/bust_ownership_guarded_20261009/detected_head_gate.json rejected: no confirmed destination face. This is a negative detection control, NOT successful second-motif quality acceptance.
- Root limitation: vertical slab includes skin/collar/hair together. Next ownership correction needs material/surface-aware region selection; do not sweep height thresholds.


## Region ownership diagnostic rejected before projection
Existing model filename scan found no dedicated face/skin parsing or SAM checkpoint in inspected models/research roots (not proof none exists elsewhere). CPU GrabCut seeded from confirmed face was evaluated once. First execution exposed diagnostic-image coordinates: report bbox is 2048, exported front_aligned.png is 1024; script now explicitly scales coordinates via --detection-resolution. Corrected run: ../quality_runs/ranger_texture1024_20261009/face_neck_region_scaled. Overlay inspected: selection includes hair, collar, cloak and ornament, not a usable skin/material segmentation. REJECTED before projection, no GLB/default/viewer changes. Do not tune GrabCut or height gates in a sweep. Current best remains fixed-gate no-depth-margin final GLB; automatic material-aware ownership remains unresolved.


## Second motif sequential Paint started
Buste fixed controls/reference: job341179b171fe48918a231032f4f5b82c. New run ../quality_runs/bust_texture1024_20261009/sequential_fresh, tool session47858. Six views,1024,seed0,15steps,guidance3; sampling exits before sequential VAE decode. Check same live session/process before any restart. Scope recorded experiment_scope.json: existing bust project seed42, so visual comparison is NOT resolution-only attribution. No concurrent GPU generation was observed before launch. Next: await twelve verified maps, bake into existing UV2048, replace albedo only to retain baseline MR, independently import and render. No production promotion.


## Bust OOM and targeted FF-memory correction
Session47858 terminated exit1: CUDA OOM in GEGLU/FeedForward, requested1.41GiB; Torch allocated12.86GiB +1.42GiB reserved. No completed decode checkpoint. PowerShell also emitted double-mapped-memory failure under pressure. After sampler exit GPU returned to ~614MiB used; no concurrent generation.
Installed Hunyuan modules already implement _chunked_feed_forward. Added opt-in --ff-chunk to checkpoint/sequential runners, sets module.set_chunk_feed_forward(chunk_size=1,dim=0), leaves attention/six views/seed0/15steps/guidance3 unchanged. Fingerprinted option in sequential_inputs. CPU test using actual FeedForward + installed chunk helper,18x128x64, maxabs0.0; this does NOT establish full FP16 image equivalence.
New isolated attempt ../quality_runs/bust_texture1024_20261009/sequential_ff_chunk, session56055. Poll exact handle before retry. Failed run preserved.
Prepared quality_lab/finish_paint_albedo_candidate.py: only accepts passed12map hashes and matching controls, bakes existing UV2K, appends albedo while retaining original BIN/MR, runs real finalize. Script compiled; full execution pending generation. No defaults changed.


## Second motif complete: technical pass, visual gate fail
Session56055 completed sampling+sequential decode, all12 maps1024/hash checks passed with --ff-chunk. Session20041 completed bake284.55s + albedo-only append + real finalize. Session55203 independently imported final output and rendered front,+35,-35,180 at1024.
Final GLB: ../quality_runs/bust_texture1024_20261009/export_ff_chunk/finalized/output.glb SHA64cd5664484d1a09a7b8d118d07cade47fcbd1e0f8fe3e2c57d093c70cf79e9f. Baseline binary9461896bytes preserved before finalize; vertices/faces/UV/albedo/MR pixel checks all true across finalize.
Visual finding: asymmetric facial lenses improved vs baseline. New duplicate shoulder skull visible at+35; invented lettering/symbols already in generated albedo_0; mesh defects persist. Technical success is not quality acceptance. Decision visual_review.json = technical_pass_visual_gate_fail. Do not promote production defaults. Next meaningful quality target is cross-view semantic consistency/source assignment, not another resolution/height/GrabCut sweep. Existing baseline seed42 vs newseed0 prevents pure resolution attribution.


## Earliest duplicate-emblem source found; one multireference correction started
Inspected decoded albedo_1 (azimuth90) and albedo_3(270): multiple shoulder emblems already exist inside each image BEFORE bake. Therefore bake-only source ownership cannot remove this within-view invention. Runner used front-only input despite available four references. Installed run_paint_multiref.py and HunyuanPaintPipeline explicitly support multiple image reference latents plus concatenated DINO features.
Added experimental --references to checkpoint/sequential runner following installed path; records ordered reference hashes and refuses duplicates/front mismatch. Original single-reference behavior remains. Existing2runner tests and compile passed; full multiref unverified. Studio guard still rejects multiref on experimental path; defaults untouched.
Exactly one controlled correction launched: ../quality_runs/bust_texture1024_20261009/sequential_multiref, session72747. Same seed0/15steps/guidance3/1024/sixcontrols/FFchunk, now front/back/left/right inputs. Compare against preceding sequential_ff_chunk (not old seed42 baseline) to isolate reference conditioning. No generation process was present before launch. Poll same handle; next decode then inspect raw shoulder images BEFORE baking. If duplicate emblems remain, reject without unnecessary bake.


## Multireference controlled trial terminal: reject before bake
Session72747 exit0, all12 native1024 maps passed. Four references confirmed in log/checkpoint. Front and side raw maps0,1,3 inspected against previous same-seed FFchunk single-reference trial. Repeated shoulder emblems persist on both side images; front lenses regress toward symmetry. Candidate rejected BEFORE bake: ../quality_runs/bust_texture1024_20261009/sequential_multiref/visual_review.json. No new final GLB created or promoted.
Conclusion is scoped: adding reference images through existing image/DINO conditioning does not enforce correct per-surface symbol placement for this fixture. Do not repeat reference-count/seed/step sweeps. Existing best Ranger GLB unchanged; bust single-reference GLB remains technically valid but visual-gate failure. Next substantive quality work must address explicit image-to-surface correspondence or generation conditioning, not atlas sharpness alone. No active GPU job remains from these trials.


## Integration of verified memory option; historical correspondence failures reconciled
Reviewed CODEX_TAKEOVER_2026-10-02.md: SIFT, DINO512/1024, cross-scale stable matching, triangle filtering/local warp, and semantic camera ranking already failed quality gates. Do NOT repeat these unmodified.
Integrated explicit experimental_paint_ff_chunk boolean into Studio sequential_paint dispatch. False/omitted preserves previous behavior; true adds --ff-chunk. Non-bool rejected. Existing full project settings/code fingerprint covers cache invalidation.5CPU tests pass (including explicit opt-in command dispatch and corrupt-map protection). No full Studio E2E claim. PAINT_SEQUENTIAL_RUNNER.md updated; no defaults changed and multiref guard remains.
Remaining quality barrier is reliable semantic correspondence, not missing mask threshold or absent DINO experiment. Existing Ranger gain remains partial; second motif has technical completion but failed visual gate.


## Review delivery updated
Local comparison server session32843 at127.0.0.1:8192. Ranger initial selection now latest verified head_only candidate (comparison UI only, no production-default change). /bust exposes matched baseline/new front,+35,-35,rear images and experimental final GLB; prominently labels visual-gate failure and seed confound. Eight PNGs decoded over HTTP and downloadable GLB SHA64cd5664484d1a09a7b8d118d07cade47fcbd1e0f8fe3e2c57d093c70cf79e9f verified. Browser/WebGL not claimed.
Abnahme remains incomplete: Ranger partial visible gain but unresolved hair/collar and automatic selection; bust technical pass but duplicate motifs; four-reference correction rejected. No further generation launched.

2026-10-10: User confirmed Ranger light side panels are intentional. reference_design_decision.json updated; no GLB or production defaults changed.

2026-10-10: Side-design audit: confirmed cream panels already absent in raw Ranger Paint side albedo_1, and both final side renders remain brown. Front-only generation provenance verified. Historical front/back color-agreement reconciliation conflicts with confirmed user intent. No production acceptance.

2026-10-10: Ranger multiref diagnostic final GLB exported and independently imported/rendered in Blender. Cream side gain survives bake; front/face regressions prevent acceptance. Handoff contains SHA and sessions.
