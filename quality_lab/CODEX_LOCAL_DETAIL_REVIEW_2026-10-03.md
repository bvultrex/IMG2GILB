# Independent local-detail review — 2026-10-03

## Ownership
The user temporarily assigned full project ownership to Codex. Codex may now run
GPU work and edit desktop/hybrid components as well as perform independent audits.
Earlier Grok/Codex file ownership does not block this authorization. Preserve
existing work and baselines; the existing visual, second-fixture and export gates
still apply. Production defaults remain off.

## Verified finding
An independent Blender 5.2 import and full-bounds clay render of the existing
TRELLIS head probe shows one large lens and two smaller stacked lenses, both at
0 and +35 degrees. The earlier head-probe face render cropped away the relevant
geometry and must not be used to reject this candidate.

Model SHA256: e191f9b8e3f0b874c2a92ba92f7ca1b68bd4d4ef393c7a7a165e64829cfd3783.
94,887 triangles; 41,230 vertices. Source remained unchanged during import.
Local evidence: `../quality_runs/trellis_headprobe_full_clay/`, including
`import_report.json`, `front_clay.png`, `angle_35_0_clay.png`.

This supports a local-detail reconstruction strategy for this fixture. It does
not prove automatic ROI generalization or a usable complete model. Hoses and
surrounding surfaces still show substantial defects. Whole-object Hunyuan and
reviewed whole-object TRELLIS variants lose the three-lens arrangement.

## Existing integration evidence
Reviewed the existing `detail_dry_splice_v5_autoroiv3_ab.json` before scheduling
duplicate generation. Its automatic-ROI arm reports:

| Seam metric | Patch to base | Base to patch | Required |
| --- | ---: | ---: | ---: |
| p90 distance, mm | 4.400 | 4.015 | <= 3 |
| maximum distance, mm | 7.926 | 6.148 | <= 5 |
| coverage within 3 mm | 0.835 | 0.785 | >= 0.90 |

These are reported measurements, not newly independently recomputed distances.
Both directions fail. The rejection-reasons list omits the failing reverse
coverage check; any successor evaluator must include all bidirectional gates.
One protected vertex was present on the seam before exclusion. Excluding it
from measurement is not proof that the proposed cut avoids protected geometry.
No topology fusion or production acceptance is justified by this report.

## Next work package
1. Independently review the whole-bust dry splice and recompute seam metrics,
   including reverse coverage and protected vertices before filtering.
2. Replace fragmented seam selection with a coherent boundary proposal; retain
   a protected detail interior. Do not simply widen thresholds or increase snaps.
3. Only after whole-object and seam gates pass, attempt topology integration,
   then UV/textures, scale, independent GLB reload, and a second fixture.
4. Keep texture correspondence and face corrections separate from geometry
   experiments so improvements and regressions remain attributable.

No Meshy-parity claim, new installation, or production promotion.

## Independent topology follow-up
Executed codex_splice_boundary_audit.py on unchanged original TRELLIS base and exported automatic-ROI v5 scene. Positional topology (7-decimal rounding) shows base_cut 25,820 boundary edges / 545 nonmanifold edges; detail_patch 1,454 boundary edges / 2,417 nonmanifold edges and 445 boundary components (only 9 simple loops). Original base already has 25,395 boundary edges / 557 nonmanifold edges. Counts include preexisting defects and do not measure only new seam defects; rounding may collapse degenerate geometry. Closed-box and open-triangle controls passed. Saved report: ../quality_runs/splice_boundary_audit.json. Existing full-bust three-quarter contrast render independently inspected: visible overlapping fragmented hood/face surfaces; whole-object visual gate fails. Prioritize coherent patch extraction/topology before any welding; no distance-threshold relaxation.

## Repair isolation executed
Source headprobe before cutting already has 5,789 indexed nonmanifold edges (5,796 after positional welding). Isolated CuMesh repair completed in existing Python3.11 rig runtime; lab Python is ABI-incompatible with cp311 CuMesh and was not modified. Repair splits vertices, as confirmed by installed source. It removes zero triangles, moves vertices zero distance, reduces indexed nonmanifold edges to zero but increases indexed boundary edges from 2,060 to 19,679. Positional topology is unchanged. This is NOT a geometric repair or stitch-ready candidate; do not promote. Added explicit indexed and positional counters to distinguish split-topology bookkeeping from surface cleanup. Artifacts: ../quality_runs/headprobe_postrepair/. Source hash unchanged. Next investigate pre-remesh/raw versus remesh/simplification topology rather than applying vertex-splitting repair to the seam. Existing whole-bust visual rejection remains valid.

## Cleanup stage replay with exact input
Executed codex_remesh_stage_audit.py using existing cp311 runtime, isolated output ../quality_runs/headprobe_stage_audit. Indexed topology: raw 12,496,548 faces / 550,240 boundary / 257,708 nonmanifold; split-repaired 1,333,672 boundary / 0 nonmanifold; remesh512 6,082,436 faces / 0 boundary / 39,883 nonmanifold; simplified 96,522 faces / 0 boundary / 6,405 nonmanifold; final duplicate removal/orientation 94,211 faces / 2,169 boundary / 5,840 nonmanifold. Thus remeshing reintroduces nonmanifold connectivity, and final cleanup exposes boundaries; simplification alone is not the source. Output counts differ from historical replay: do not claim byte deterministic CuMesh behavior. Source unchanged verified. Candidate remains rejected for integration. Need a topology-preserving reconstruction/meshing alternative, not seam welding over this input.

## Blender voxel alternative tested
Executed codex_blender_voxel_probe.py at384 longest-axis samples on existing headprobe; no new model inference. Output ../quality_runs/headprobe_blender_voxel384. Voxel mesh2,388,100triangles, positional boundary0/nonmanifold5; decimated99,851triangles, boundary447/nonmanifold8. Export warning invalid mesh confirmed as149 triangular boundary loops after reduction. Independent Blender reload completed0/+35, source unchanged; front inspected: three-lens layout retained but grille details visibly softened and small hole on large lens. Improved topology counts do NOT pass quality gate. Candidate SHA4f5756f5494eeeef19a2410854e6555adc81109c85668ab0c9c16564dc42e00d. Need isolate pre-decimation detail fidelity (same cameras) and address reduction-generated triangular holes before further integration; no production promotion.

## Before-decimation visual isolation
Independent Blender pre-decimation384 render completed and source unchanged. Front grille openings are already largely filled in the 2.388M-triangle voxel output; not solely a100k budget issue. Pre/post normals differ (flat versus smooth), so shading is not a fidelity metric. Reduced boundary-edge lengths: median0.334mm/p900.838mm/max4.887mm; consistent winding, zero degenerate faces. Started resolution768 with same source and100k budget, isolated headprobe_blender_voxel768. This tests voxel resolution, no promotion until final shape and topology inspection.

## Voxel768 complete and inspected
Same source/budget: 10,324,168 voxel triangles ->99,679 reduced. Candidate SHA5c6fc52d26f3dfec49c5b72662fe4ae08701b0c132e0e66facafd19ce9233650. Independent Blender import0/+35 completed, source unchanged; front inspected and grille slots visibly return compared with384 while three lenses remain. Positional/indexed topology963 boundary edges in321 triangular loops,6 nonmanifold edges. Thus resolution improves detail but does not solve reduction/export defects; retain experimental only. Next inspect tiny-loop provenance and reduction/export validity before any patch insertion. Added future progress checkpoints to voxel probe (syntax checked); executed768 run used earlier script without checkpoints. All sessions terminal, no new inference running.

## Triangle fill falsified by independent Blender reload
Diagnostic fill added321faces without changing input faces/vertices; trimesh reported100000faces/zero boundaries. Blender reload instead had99679faces. Investigated: ALL321added faces are unordered duplicates of existing faces. These boundary loops are isolated triangle sheets, not holes; prior wording '321 holes' is corrected. Candidate4c7b7dadf848e79a21ff115f7257da884938479d6a6017e3bd0899adfaaff02c REJECTED. Filling artificially improves edge-count topology, does not repair surfaces. Added duplicate-face check to future probe reports. Next identify isolated components and quantify their contribution before removing debris; don't globally fill triangular loops. Nonmanifold6 still unresolved. No source/default change.

## Component-aware debris cleanup verified
Runtime briefly exited with Windows native error before printing; runtime smoke and same read-only analysis subsequently passed without installation. Source768 has339 edge-adjacency components,321singletons (area9.17249e-6m2 / total1.673807m2). codex_isolated_triangle_cleanup.py removes only faces with all three edges incident to no other face; no threshold on detail size. Retained faces/vertices exact. Output99,358triangles,zero boundary edges,six nonmanifold edges; all six involve faces in the main adjacency component, so simply separating disconnected objects cannot resolve them. Independent Blender reload confirms99,358faces (no loss unlike fill), source unchanged; front render reviewed. Candidate SHA59b43ed1f99a9b2a442d02c391035302607557e3b8292df49516217184eb79e0. Experimental only, detailed local edge topology next before integration. All jobs terminal.

## Cleanup shading regression fixed
Previous cleanup export omitted NORMAL attribute, causing flat Blender appearance. Capture input vertex normals before filtering and explicitly export them; reload checks faces and used-vertex normals(atol1e-6). Unused963vertex normals excluded from comparison because trimesh normalizes them tozero after removing their faces. Independent Blender import/render terminal success:99,358faces, smooth front appearance restored, three lenses/grille retained. Candidate025c364fb6e17edc1d37ca1f91e93cb63178d3cf4249131f28c9b827612f1871, local headprobe_voxel768_cleanup_normals_verified. Geometry still has6nonmanifold edges, no promotion. Source unchanged. No process active.

## Local sheet connectivity probe
Measured6valence4edges, lengths0.639..2.519mm. Tested orientation-consistent normal-paired halfedges and corner union, preserving all triangle positions and normals with no surface removal. Output headprobe_sheet_connectivity:99,358triangles,zero indexed boundaries,4indexed nonmanifold edges(down from6); positional contacts remain6. Therefore reject as complete repair; counts alone cannot qualify. Source hash025c364fb6e17edc1d37ca1f91e93cb63178d3cf4249131f28c9b827612f1871 unchanged. All work terminal. Next inspect whether remaining contacts lie outside the actual replacement patch and build a coherent crop from the improved head, rather than making global head manifoldness a substitute for the local integration objective. No production promotion.

## Registered crop contact localization
Transferred historical affine registration by least-squares matching identical-index original/registered meshes; max reconstruction error8.27e-9m. Applied to improved head, no refit. Four of6indexed contacts outside historical box;2inside including one at(-.0200,.1517,.0566)m in protected lens box. Cannot simply ignore contacts. Box-only crop(no surface-distance perforation) yields19,394triangles,17boundary components,2nonmanifold edges,4branched boundary vertices. Not a coherent single seam. Blender front import/render terminal success, SHA d0ed1398db395509360feb3d5942cdccccd996430db056894fcc784345598c3a. Whole-head positional counter changes6to8 after affine due1e-7rounding; indexed remains6, avoid false new-defect claim. Source hashes unchanged. No fusion. Next surface-connected ROI/boundary selection must protect both lens geometry and create a coherent seam; box alone insufficient.

## Installed MeshLab local repair controls
MeshLab Split Vertices plus vertex repair(displacement0) leaves6nonmanifold edges unchanged. Remove Faces removes12triangles and creates6simple quadrilateral holes, zero nonmanifold edges. Standard close_holes adds12faces but reintroduces5nonmanifold edges; rejected. Custom quadrilateral fill forbids already-occupied diagonals to prevent this failure; aborts because both diagonals are already occupied for at least one loop. No successful quad candidate exported, source unchanged. This identifies need for larger local retriangulation or an inserted interior vertex rather than existing-diagonal closure; do not rerun same hole filler as repair. Artifacts headprobe_meshlab_local_repair/report.json. All processes terminal, no production edits.

## Six local edge contacts repaired with interior fans
--fan-repair replaces12removed triangles with24fan triangles and6new centroid vertices.99,370faces;zero indexed/positional boundary or nonmanifold edges,zero duplicate/degenerate faces,consistent winding. New vertices nearest old vertex max1.126mm (NOT surface displacement). Independent Blender reload/render confirms99,370faces and preserves visible three lenses/grille. SHA71daa21ec3f021c97c1832c06fcce3719457c4207c1ef13619501b0ca687714d. MeshLab self-intersection selection flags303faces before and303after;none of24new faces selected. Equal count is not proof of identical affected sets, no intersection-free claim. Existing intersections still need localization to replacement region. Model remains experimental, no whole-bust fusion or UI promotion. All processes terminal.

## Intersection surfaces compared exactly
Executed codex_intersection_localization.py: canonical exact triangle-coordinate sets confirm all303MeshLab-selected surfaces identical before/after fan repair (0new,0removed). After historical registration,33flagged triangles have any vertex insidebox,31fullyinside;23touch protected lensbox. Thus contact repair introduces no newly flagged surfaces under this checker, but existing intersections cannot be ignored as peripheral. Counts are selected faces, not intersection pairs; box membership is a fixture localization, not semantic proof. Next isolate the23protected flagged triangles and their counterpart faces before any geometry deletion or fusion. Report headprobe_fan_repair/intersection_localization.json; hashes recorded. No production acceptance.

## Independent Blender overlap pairs and visualization
Blender BVH epsilon0 reports215overlap pairs,120sharingvertex,95withoutsharedvertex. Excluding sharedvertex may omit adjacentfoldovers; not full validity certificate.153distinctfaces in95pairs highlighted red in independent transient render, verified sourcehash/trianglecount. Front visual inspected: visible red includes smalllens/uppermask plus peripheral lowerhead. Confirms problematic surfaces cannot all be dismissed as adjacency. New reusable --highlight-pairs audit option does not modify GLB. Evidence headprobe_fan_repair/blender_intersection_pairs.json and intersection_render/front_clay.png. Need paired local geometry inspection/repair, not global smoothing. All sessions terminal.

Visual localization correction: front overlay clearly shows red beneath the large lens and along lower/peripheral surfaces; this render alone does not establish a small-lens intersection. Use actual paired coordinates for exact localization.

## Bounded local intersection correction
Executed one-step uniform Laplacian on vertices incident to flagged faces, then capped each displacement independently. Initial inclusive=True transfer yielded0vertices/no-op; preserved invalid experiment headprobe_local_smoothing, corrected inclusive=False with nonempty assertion. Valid v2 selects467vertices; unselected coordinates unchanged assertion. Caps0.1/0.25/0.5mm yield193/127/120flaggedfaces vs303baseline. All keep99,370faces,zero boundary/nonmanifold edges. Chose0.25mm arm for visual check due diminishing returns at0.5; not a production threshold. Input hashunchanged. Remaining intersections unresolved; no intersection-free claim. Output headprobe_local_smoothing_v2.

## Orientation-guarded iterative correction
Additional normal-direction check rejects previous127face arm:21faces reversed relative to original although edge topology passes. No production promotion ever occurred. New codex_iterative_local_correction.py rolls back nonimproving steps, caps TOTAL original-relative movement0.25mm, freezes vertices incident to flips/degeneracy. Valid run303->179->169->168, fourthstep168rejected(noimprovement).426vertices moved,totalmax0.25mm;zero flipsvsoriginal,degenerate,boundary,nonmanifold. This supersedes the apparently better but invalid127arm. Remaining168flaggedfaces unresolved; report headprobe_iterative_orientation_guard/report.json. Preserves sourcehash71daa21ec3f021c97c1832c06fcce3719457c4207c1ef13619501b0ca687714d.

## Upstream export comparison and native-coordinate control
Read official Microsoft TRELLIS.2 o-voxel/o_voxel/postprocess.py online and installed source. No-remesh branch uses initialfill,3xtargetsimplification/cleanup,finaltargetcleanup; customclean_trellis_mesh differs. Existing bust_trellis_shape.py scales raw to0.4m before externalcleanup; original native scale not recorded. This is a potential confound for absolute cleanup thresholds, NOT proven cause. Started codex_native_export_control.py using existing savedlatent and shape decoder only (no diffusion/reference regeneration/install). It reconstructs native coordinates and replays official no-remesh geometry sequence, recordsbounds/scale, then exports0.4m. Tool session29830 confirmed live loadingdecoder. Output headprobe_native_standard; need wait samehandle,inspect firsterror or finalcandidate, topology and visual. Source: https://github.com/microsoft/TRELLIS.2/blob/main/o-voxel/o_voxel/postprocess.py . No production promotion.

Native control28964 now terminal success after explicit decoder.eval() fix (initial29830 failed in trainingbranch). Existing latent recovered nativebounds~[-.451,-.495,-.373]..[.452,.500,.390]. Official no-remesh geometry sequence produced96,348faces;17,700indexed boundaryedges/0indexed nonmanifold;positional17,470boundaries/50nonmanifold. Native_to_GL Bscale0.5251328074 recorded. Thus upstreamsequence alone does not provide cleanclosed result on thisfixture; visualcomparison pending. No process active, no newinference sampling performed. Earlier live-statuslog superseded by completion.
