# Texture detective: measured lineage and promotion gates

2026-10-02, Codex / Zenko. Experimental; no production defaults changed.

## What was actually measured

`codex_texture_audit.py` inspected saved PNG pixels, embedded GLB images and cached UV triangles on CPU. No generation, image resampling or asset writes. Full audit JSON remains in the local lab `research/` directory; private references and GLBs are not published.

| Saved job | Paint views / actual dimensions | Recorded reference count | Sum of UV triangle areas | UV triangles below 1e-12 area |
|---|---|---|---|---|
| David `5e81ac7963f84af2a403fb659cea7513` | 6 / 768 square | 1 | 0.488294 | 89 / 99,996 |
| `22282dae660c4cd98bd9b9d20275f3c2` | 6 / 768 square | 1 | 0.482831 | 39 / 99,998 |
| `1cce72cdf2d5450385658f480cc4e8b6` | 6 / 768 square | 1 | 0.478717 | 83 / 99,996 |

All three contain 2048-square albedo atlases. UV area sum is NOT rasterized occupancy: overlap, padding and thin triangles must be checked separately. These values motivate a packing investigation; they do not prove that half the atlas can safely be recovered. The few degenerate UV triangles do not explain global softness by themselves.

**David has a decisive negative finding:** decoded RGBA pixels in `paint/albedo_atlas_2K.png`, `textured_color.glb`, `textured_pbr.glb`, `output.glb` and `preview_color.glb` are identical. Thus this run's final export introduced no albedo pixel blur. Its hybrid sidecar differs and is not the final albedo. The `22282…` final GLB also matches its atlas. No equivalent final-image identity conclusion is made for `1cce…`.

David prepared references are 1920x2560 (front/back/left) and 1706x2560 (right), but its saved paint reference and each generated view are 768x768. Its report records one reference although the project lists four views. Visual inspection of saved `albedo_0.png` already shows changed facial expression and simplified jacket/necklace detail before baking. This is evidence of pre-bake fidelity loss, not a quantitative allocation of all final blur to generation.

Current lab bake code uses **LANCZOS**, not bilinear, for the PIL arm. The historical report only says PIL resize; today's code cannot prove the historical filter. Earlier notes asserting a confirmed dominant bilinear root cause are too strong.

## Failure taxonomy

| Symptom | First discriminating check | What cannot fix it by itself |
|---|---|---|
| Missing or invented logo, different mouth | Inspect native generated view against prepared reference before baking | Sharpening or larger export dimensions |
| Native view sharp, atlas/render doubled | Freeze cameras/UV; compare single best visible view to weighted blending | Extra references without checking consistency |
| Small face remains undersampled | Measure face UV pixel allocation and projected native-view footprint | Global 2K label or more triangles |
| Crisp atlas but soft display | Compare flat/unlit render at equal screen footprint; inspect mipmaps, filtering, render resolution | Regenerating geometry blindly |
| Dark/muddy relit surface | Compare unlit albedo with neutral-lit PBR; inspect baked lighting and MR channel/color-space handling | Contrast boost alone |
| Seam after reference projection | Visibility, camera fit, color mismatch, island padding; inspect oblique views | Blending across misregistered eyes/mouth |

Do not assign a percentage of mush to a stage from three uncontrolled historical jobs. Frequency-energy gains can reward noise, halos and invented eyelashes.

## Three controlled experiments

Freeze source hashes, geometry, UVs, cameras, seed, atlas dimensions and viewer settings. Use separate output directories: current bake writes atlas PNGs into its input paint directory, so copy paint inputs for each arm. Never overwrite the baseline.

1. **Grok: reference use and upscaler factorial.** A0 single-reference/PIL, A1 multireference/PIL, A2 single-reference/ESRGAN, A3 multireference/ESRGAN. Compare A1-A0 for conditioning and A2-A0 for upscaler effect; do not conflate both with one combined run. Reuse identical generated views for each upscaler pair. Confirm report reference count and actual image dimensions. Check face, chest emblem, back and seam regions at matched screen size.
2. **Bake isolation.** Same generated views, two bake arms: current weighted combination versus highest-confidence visible source per texel with seam-only blending. Keep occlusion and camera mapping fixed. Begin with a known synthetic pattern rendered through the same cameras to establish a ground-truth round trip; then David. Measure edge displacement, duplicate edges and seam error. A clean single-view control with blurred blended output implicates view disagreement/blending; failure in both points toward sampling/mapping. This experiment is specified, not yet executed.
3. **Reference-preserving hybrid.** Fixed A0 geometry/UV and paint; change only trusted-region reference projection. Use visibility and alignment confidence; decline uncertain side views. Score both detail retention and new distortion, especially jaw/eyes/neck. After acceptance, separately test UV packing/face allocation with rebaking, rather than mixing it into this trial.

## Promotion gates (proposed, not passed)

- Preserve mesh, UV, non-target material maps and input hashes for texture-only trials; report runtime and peak memory.
- Freeze evaluation masks/landmarks before comparison. Check eye whites, eyebrow width, mouth location, chest cross/stripes, back emblem, silhouette and oblique seams. More edge energy alone never passes.
- At equal screen size: no added double contours, halos, changed symbols or face drift; measured landmark error and seam discontinuity must not worsen beyond baseline measurement repeatability. Record visual assessment separately from automatic metrics.
- Require a second unseen, fully clothed character plus a non-face object/bust test. Reject face processing on a mechanical mask instead of forcing a human-face prior.
- Hybrid must be explicitly consumed by finalize and verified through embedded-image hashes; creating a good sidecar is not an end-to-end pass.
- Only then consider production defaults. Keep the UI simple: backend confidence/fallback logic should remain internal.

## Public evidence relevant to the hypothesis

- [Meshy Multiview Upgrade](https://www.meshy.ai/blog/multiview-upgrade): separate geometry/texture stages and automatically generated missing auxiliary views. This supports completion at the view level, not proof of a particular limb-repair network.
- [Meshy Image Enhancement](https://help.meshy.ai/en/articles/13880941-what-does-the-image-enhancement-toggle-do): preprocessing can simplify or alter details. A changed mouth could therefore originate before geometry; that attribution remains an inference for Danny's specific example.
- [Tripo Texture API](https://developers.tripo3d.ai/en/docs/models-texture): original-image versus geometry alignment, multiview conditioning, and quality choices with identical output dimensions. Texture size alone is not quality; delight is version-specific.
- [Meshy PBR tutorial](https://www.meshy.ai/tutorials/pbr-texturing-with-meshy): UV handling, projection, lighting removal and healing are documented capabilities. This does not establish that every product version automatically runs every stage or disclose the internal denoising resolution.

Our generators already infer unseen content. The actionable gap is controlling where inference is useful and where visible reference details must survive. A new autocomplete add-on alone is not an established solution.

## Reproduce

```powershell
python quality_lab/codex_texture_audit.py <saved-job-directory> --out <new-report.json>
```

Dependencies: Pillow and numpy. CPU only. Existing output report paths are refused. Source GLBs are decoded, never re-exported. External GLB image URIs are recorded as unsupported rather than fetched.

