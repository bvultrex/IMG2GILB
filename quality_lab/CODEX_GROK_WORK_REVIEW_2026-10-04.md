# Review of resumed Grok work — 2026-10-04

Scope: fetched origin/main (ceefe19), read Issue #1 through comment 5979916627, inspected local scripts/reports and existing renders, independently decoded GLB JSON headers. No inference, model replacement, production promotion or asset upload performed. No Python inference/Blender worker appeared in the process snapshot; Studio and ComfyUI servers were running.

## Findings

- Native no-remesh rejection is useful and now committed. Subsequent experiments are mainly local quality_runs artifacts and untracked scripts, not integrated product improvements.
- Coherent patch and tighter seam reports both fail existing gates. Tighter seam increases reported flips from 274 to 305 and does not improve bidirectional coverage. Stop this lineage rather than widening thresholds.
- AutoPartGen really produced a combined mesh: header independently reports 531,221 vertices / 1,062,840 triangles, vertex colors, no texture images. Existing frontal render looks coarse; part generation alone has not established better reference fidelity. No matched-camera quantitative ranking performed here.
- TripoSG 8192-token report records 2,372,912 triangles, 211.7s, 5.44 GiB allocated peak. Inspected pedestal crop remains a rounded medallion. More tokens did not establish the desired skull detail on this fixture. This is not evidence that the model cannot reconstruct skulls generally.
- TRELLIS 1536 cascade is the most promising new detail result. Existing front/pedestal renders show eye-socket/nasal relief and ribbed hoses. However the face still has two dominant symmetric lenses instead of the reference's asymmetric three-lens arrangement. The bright custom raster renders also show substantial surface artifacts; these need independent shaded inspection before attributing every streak to mesh damage.
- Independently read 1536 GLB: 448,346,496 bytes, 12,496,642 vertices, 24,865,502 triangles, POSITION only, zero images. Container declared length matches disk. This is not a textured or Quest-ready result, and header inspection is not a full import validation.
- Independently read reduced 512 GLB: 4,483,732 bytes, 103,584 vertices, 269,998 triangles, POSITION only, zero images. It was reduced from the 512 output, NOT the promising 1536 output. It therefore does not prove that the high-resolution gain survives reduction. The filename's 100k means approximate vertices; do not confuse it with our previous 100k-triangle benchmark.
- The 1536 report still says GLB export MemoryError although a later GLB exists. Preserve the original failure but add a separate successful export manifest with lineage/hash. Texture-model presence check uses a checkpoint stem `.exists()` rather than checking its actual weight/config files; absence needs a correct inventory before any download decision.
- A failed tight skull crop does not establish 'missing prior'. Input framing, foreground mask, context and extraction must be controlled before drawing an architectural conclusion.

## Recommended next package

1. Freeze/hash the existing 1536 source and record generation versus later export lineage. Preserve originals. Reuse it; do not resample or install more generators yet.
2. Run independent front, +/-35 and rear inspection with neutral, consistent shading. Score whole silhouette, the three lenses, pedestal skull and hoses separately. High resolution may improve small relief while leaving semantic structure wrong.
3. Derive a reduced sidecar FROM 1536 with an explicit triangle budget (100k benchmark; a higher-budget comparison only if the first visibly loses detail). Measure retained detail, topology, memory and render cost. Avoid another patch-fusion loop.
4. On that same reduced geometry, UV unwrap and compare the existing texture baseline with controlled reference projection. Preserve visibility and uncertain-region fallback; do not blend misregistered side views blindly. Test normal-map baking from high resolution for surface relief; it cannot recover missing silhouettes or correct the wrong lens arrangement.
5. Only after visual improvement survives final textured GLB save/reload, integrate an opt-in Studio route and repeat on a clothed character. Keep defaults and production acceptance off until the established gates pass.

Decision: worthwhile diagnostic work and a credible high-resolution lead, but no demonstrated end-to-end quality breakthrough yet. Concentrate on carrying one promising result through reduction, texturing and independent preview rather than accumulating more raw model outputs. Private references/models stay local.

## Execution checkpoint

Independent Blender 5.2 import/render completed at 0, +/-35 and 180 degrees, 1024px, neutral clay. Source GLB SHA256 5b747371d50fd74f9e8e864642115209eda48601b2faa449d59530c70b2b84ae unchanged. Imported 24,865,502 triangles; height 0.399999976m. Results under ../quality_runs/trellis1536_independent_review. Front confirms pedestal relief and hose ribs but incorrect two-lens mask; rear exposes large open/incomplete surfaces in backpack. Reject production geometry pending reconstruction/extraction diagnosis. Do not spend a full texture pass on this damaged geometry merely because the front has improved detail.

CPU reduction started from original 1536 PLY (SHA256 f9bcace89c4fff1a856d6a76f78704f17b863876cc07745170b2a68470df5cac), explicit 100,000-triangle target, isolated ../quality_runs/trellis1536_reduce100k_v2. Runner quality_lab/codex_reduce_highres.py writes loading/reducing/exporting/complete checkpoints. Initial empty-directory attempt failed on Python 3.10 hashlib.file_digest availability; fixed with streaming hash, no source mutation. At this checkpoint reduction is RUNNING, not validated. Check report.json and live processes before any duplicate work. Next render resulting candidate with identical cameras; source render comparison remains diagnostic, not texture/production acceptance.
