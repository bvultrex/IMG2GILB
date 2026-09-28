# Texture Sharpness v1 — Result

Date: 2026-09-28

Status: **T1 diagnostic/refine experiment completed on one existing painted SF3D job**.

`production_accepted=false`.

## Source

Existing painted GLB:

`D:\SF3D_QualityLab\app_jobs\b66c77f5fb844cefae8ec485d8bab8af\output.glb`

Input texture:

- base-color image index: **0**
- source format: **PNG**
- resolution: **2048×2048**

No shape generation or Paint rerun was performed.

## Controlled refine

The experiment modified only a copy of the embedded base-color texture.

Knobs:

- radius: **1.0 px**
- amount: **0.60**
- activation threshold: **2 / 255**
- maximum delta: **14 / 255**

Measured pixel impact:

- active pixels: **26.0039%**
- RGB MAE: **0.8297 / 255**
- RGB p99 delta: **10.7580 / 255**
- newly clipped channel fraction: **0.0011973**
- alpha preserved exactly: **true**

## Sharpness proxy metrics

| Metric | Before | After | Ratio |
| --- | ---: | ---: | ---: |
| Laplacian variance | 0.0025609676 | 0.0047251345 | **1.8451×** |
| High-frequency RMS | 0.0154307474 | 0.0199633908 | **1.2937×** |
| Gradient p90 | 0.0563888872 | 0.0600715566 | **1.0653×** |
| Gradient p99 | 0.1765947544 | 0.2023971952 | 1.1461× |

Mean luminance remained effectively unchanged:

- before: **0.4512912009**
- after: **0.4512723283**

Near-black/white channel fraction:

- before: **0.0038391749**
- after: **0.0053374767**

Interpretation: the pass increases local high-frequency/edge response measurably while keeping the average color/luminance shift small. These numbers are diagnostic proxies, not a perceptual-quality score.

## GLB integrity

Corrected integrity rerun:

- source GLB SHA before = source GLB SHA after
- source unchanged: **true**
- requested refined base-color SHA equals embedded refined base-color SHA
- embedded refined base-color MIME: **image/png**
- other embedded image index 1 before/after SHA identical: **true**
- all non-target embedded images identical: **true**
- overall integrity: **PASS**

Acceptance flags:

- diagnostic completed: **true**
- original preserved: **true**
- refine reversible: **true**
- controlled-refine integrity passed: **true**
- geometry validated by this test: **false**
- production accepted: **false**

## Artifacts

Original extracted albedo:

`D:\SF3D_QualityLab\texture_validation\texture_v1\albedo_original.png`

Refined experimental albedo:

`D:\SF3D_QualityLab\texture_validation\texture_v1\albedo_refined_v1.png`

Refined experimental GLB:

`D:\SF3D_QualityLab\texture_validation\texture_v1\output_texture_refine_v1.glb`

Staged previews:

- `C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1\albedo_before.png`
- `C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1\albedo_after.png`
- `C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1\detail_before.png`
- `C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1\detail_after.png`

Deterministic detail crop:

`[480, 864, 864, 1248]`

## Acceptance boundary / geometry warning

This result is **texture-only**.

Sharper texture must not be used to disguise or compensate for:

- wrong silhouette or missing geometric forms,
- open seams or non-manifold geometry,
- UV stretch,
- bake seams,
- projection errors,
- malformed geometric detail.

This is consistent with `LOCAL_DETAIL_ACCEPTANCE_GATES.md` §6: geometry/export validity remains upstream of any texture-quality claim.

The refined output remains experimental until visual review confirms that the added high-frequency response does not produce halos, crunchy outlines, or amplified bake noise.

No Meshy-parity or production-quality claim is made.

## Relevant commits

- `6a8cf13` texture sharpness diagnostic/refine
- `f3fc865` texture acceptance protocol
- `0840192` runner
- `974cbe8` embedded image MIME consistency
- `998655f` corrected integrity verification
- `203f07a` acceptance bound to integrity check
