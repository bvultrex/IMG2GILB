# Texture Sharpness v1 — protocol and acceptance notes

Status: **experimental**, CPU-only, `production_accepted=false`.

## Purpose

Measure whether an existing painted GLB's base-color atlas is soft and test one
controlled, reversible sharpening pass without re-running shape or Paint.

This task deliberately avoids long GPU work while the ranger 4-view job is active.

## Diagnostic metrics

The v1 script reports:

- **Laplacian variance**: local edge/detail response.
- **High-frequency RMS**: energy removed by a small Gaussian low-pass.
- **Gradient p90 / p99**: upper distribution of local luminance gradients.
- **near-black/white channel fraction**: crude clipping/contrast sanity metric.

These are **proxies**, not general perceptual-quality scores. Higher is not
automatically better.

## Controlled refine

Only the embedded **base-color/albedo** image is modified.

Default knobs:

- Gaussian radius: **1.0 px**
- unsharp amount: **0.60**
- activation threshold: **2 / 255**
- maximum per-pass delta: **14 / 255**

The refined image is written separately and, by default, embedded into a new
`output_texture_refine_v1.glb`.

The source GLB is never overwritten. Alpha is preserved exactly. Other embedded
images are SHA-checked byte-for-byte after the GLB rewrite.

## Preview artifacts

The runner stages:

- `albedo_before.png`
- `albedo_after.png`
- `detail_before.png`
- `detail_after.png`

under:

`C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1\`

The detail crop is selected deterministically from the highest high-frequency
atlas region, so before/after use the exact same pixel window.

## Acceptance boundary

A texture-refine experiment is worth keeping for review only if:

1. the source GLB remains untouched;
2. alpha is unchanged;
3. non-albedo embedded maps remain byte-identical;
4. sharpness proxies increase modestly rather than explosively;
5. newly clipped channels remain near zero;
6. visual review does not show halos, crunchy outlines, or amplified bake noise.

There is intentionally no automatic `production_accepted=true` path in v1.

## Geometry warning — LOCAL_DETAIL_ACCEPTANCE_GATES §6

Sharper texture must **never** be treated as a substitute for failed geometry.

Reject or ignore the texture gain when:

- missing forms are geometric rather than albedo detail;
- silhouette is wrong;
- seams/gaps/non-manifold geometry are the actual defect;
- UV stretching is responsible for blur;
- bake seams or wrong projections are being sharpened;
- sharpening makes a malformed feature merely look higher-contrast.

Geometry gates run first. Texture work may only improve an already acceptable
surface representation.

## Reproduction

```powershell
.\quality_lab\Run_Texture_Sharpness_v1.bat
```

Optional explicit job:

```powershell
& 'D:\SF3D_QualityLab\venv\Scripts\python.exe' quality_lab\texture_sharpness_v1.py --job 'D:\SF3D_QualityLab\app_jobs\<JOB_ID>'
```
