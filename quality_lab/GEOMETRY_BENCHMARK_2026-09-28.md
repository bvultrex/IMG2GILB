# Mechanical bust: geometry benchmark, 2026-09-28

## Decision

No tested whole-object variant is accepted as a fidelity breakthrough or a production replacement. The reference and Meshy geometry have one large lens and two vertically stacked small lenses. Whole-object Hunyuan2mv, Hunyuan Shape2.1, TRELLIS.2 and TripoSG experiments all simplify this to two main lenses.

A TRELLIS head-only crop recovers the asymmetric three-lens arrangement, although the upper small lens remains malformed and the mesh is rough/open. This is a useful **diagnostic finding**, not a finished whole-bust solution. It motivates spatially localized detail reconstruction. Concatenating whole-image and crop feature tokens did NOT preserve the arrangement in the whole-object test; do not enable this experimental conditioning by default.

## Controlled observations

- The existing job uses Hunyuan3D-2mv for shape. Having Paint2.1 installed did not mean Shape2.1 was active.
- Original and prepared front inputs visibly contain all three lenses. Existing BRIA masking retained them.
- No explicit mirroring operation was found in the current shape stage. Symmetric-looking results are not evidence of a mirror-code bug.
- Front-only and front+back controls still lose the third lens. Inconsistent side references are therefore not the sole cause.
- Higher TRELLIS grid resolution and bypassing the 512 cascade did not fix the lens arrangement.
- Continuous CFG over [0,1], replacing the default [0.6,1], did not improve fidelity and degraded some mask details.
- Meshy's three lenses and hose corrugation survive a welded, geometry-only reduction to 99,999 triangles. Final polygon budget alone does not explain our gap.
- These observations concern this single fixture and seed, not a general ranking of these models.

## Runs

All use seed 42. Times exclude initial model loading and downstream rendering. VRAM values are peak Torch allocated GiB, **not total GPU usage or a universal minimum requirement**. Different model families have different default schedules; same seed does not make their random samples equivalent.

| Variant | Raw triangles | Generation seconds | Torch peak GiB | Visual outcome |
|---|---:|---:|---:|---|
| Hunyuan2mv front | 1,065,608 | 92.05 | 5.57 | Two main lenses |
| Hunyuan2mv front+back | 1,176,796 | 104.88 | 5.58 | Two main lenses |
| Hunyuan Shape2.1 front | 1,172,900 | 120.52 | 7.63 | Two main lenses |
| TRELLIS.2 512 | 2,809,162 | 83.64 | 2.65 | Two lenses; more mechanical detail |
| TRELLIS.2 1024 cascade | 11,131,202 | 152.20 | 6.01 | Two lenses; raw surface artifacts |
| TRELLIS.2 1024 direct | 10,575,038 | 79.75 | 5.75 | Two lenses |
| TRELLIS.2 direct, full CFG interval | 9,446,762 | 84.81 | 5.29 | Two lenses; some detail degraded |
| TRELLIS.2 direct, head-only crop | 12,496,548 | 122.83 | 6.81 | Three-lens arrangement partly recovered; upper lens rough |
| TRELLIS.2 direct, global+crop tokens | 10,222,004 | 89.16 | 5.65 | Two lenses; rejected |
| TripoSG front | 2,127,972 | 37.95 | 5.34 | Two main lenses; distorted rings |

Hunyuan runs: 50 steps, octree384, guidance5. TRELLIS runs: 12 steps per shape stage, guidance7.5, official rescaling defaults. TripoSG: 50 steps, guidance7, official non-flash hierarchical extraction, dense depth7 to final depth9. No TripoSG commercial-service parity is implied.

## Artifacts and rendering

Fixture/output root: `D:/SF3D_QualityLab/bust_validation/shape_ablation`.
Each generation has GLB and JSON metadata. TRELLIS and TripoSG latent checkpoints allow decoder recovery without repeating denoising. Original Meshy GLB and baseline Studio jobs are unchanged.

Blender renders use the same 40cm normalization, orthographic camera and Workbench clay shading for whole-object comparisons. Clay excludes textures and material normal maps. The head-only probe is separately normalized to 40cm and must NOT be compared as a physically scaled whole bust.

TRELLIS raw decoder meshes require orientation cleanup. Diagnostic CuMesh cleanup and optional narrow-band remesh512 were tested before reduction. Target100k yields approximately93–96k actual triangles after cleanup. Those probes remain non-watertight and visibly imperfect; they are neither print-ready nor final textured exports. A mesh with more triangles is not automatically a more faithful mesh.

Useful render files under the output root's `renders/`:
- `triposg_front_face_clay.png`
- `trellis1024_direct_100000_face_clay.png`
- `trellis1024_direct_headprobe_100000_remesh512_front_clay.png`
- `trellis1024_direct_detailcond_100000_remesh512_face_clay.png`

Meshy/baseline clay controls: `D:/SF3D_QualityLab/bust_validation/meshy_comparison/meshy100k_face_clay.png` and `ours_face_clay.png`.

## Reproduction and isolation

These scripts are local fixture experiments with explicit paths, not a portable installer or production UI feature. Run from the IMG2GILB repository. Do not run GPU benchmarks concurrently.

```powershell
& 'D:\SF3D_QualityLab\venv\Scripts\python.exe' quality_lab/bust_shape_ablation.py
& 'D:\SF3D_QualityLab\venv\Scripts\python.exe' quality_lab/bust_shape21.py
& 'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-rig-runtime\venv\Scripts\python.exe' quality_lab/test_trellis_attention.py
& 'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-rig-runtime\venv\Scripts\python.exe' quality_lab/bust_trellis_shape.py --resolution 1024 --direct
# Diagnostic crop, not an automatic detector:
& 'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-rig-runtime\venv\Scripts\python.exe' quality_lab/bust_trellis_shape.py --resolution 1024 --direct --head-probe
& 'D:\SF3D_QualityLab\venv\Scripts\python.exe' quality_lab/bust_triposg.py
```

Hunyuan2.1 adds timm1.0.15 only to `D:/SF3D_QualityLab/shape21_deps`. TRELLIS uses process-local dependencies in `IMG2GILB-trellis-runtime/deps` with the existing rig Python3.11/Torch2.7. Sparse SDPA compatibility patch is `trellis_sdpa.patch`; ragged CPU/CUDA self- and cross-attention match explicit attention. Missing checkpoint keys are rejected except constructor-generated deterministic `rope_phases`. Bundled Triton compiler/CUDA paths are process-local.

TripoSG uses existing lab Python3.10/Torch2.6 plus isolated `IMG2GILB-triposg-runtime/deps` packages jaxtyping0.3.3, typeguard4.4.4 and wadler-lindig0.1.7. `triposg_optional_diso.patch` makes DISO import local to the unused flash extractor; the tested official non-flash path uses scikit-image. Existing BRIA alpha is reused; no new BRIA model is downloaded.

Pinned sources/weights:
- Hunyuan2.1 source `82920d643c0dc2f7bfd7255f45f62d386edfe60c`; weights `0b94677654c57bb9a6b6845cd7b704ccf551d327`.
- TRELLIS.2 source `75fbf0183001ed9876c8dbb35de6b68552ee08bd`; weights `af44b45f2e35a493886929c6d786e563ec68364d`; sparse decoder repo revision `25e0d31ffbebe4b5a97464dd851910efc3002d96`.
- TripoSG source `fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c`; weights `2c1c516d22d58db486a058d98d31bb6177344e06`.

## Research and next acceptance gate

Primary sources: [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), [TripoSG](https://github.com/VAST-AI-Research/TripoSG). These are predictive/generative shape models already; the project is not merely projecting images onto a symmetric template. Meshy's internal architecture cannot be established from the supplied GLB.

The open [TRELLIS quality-settings question](https://github.com/microsoft/TRELLIS.2/issues/92) is a user's proposed configuration, not an official validated best-quality preset. [Hunyuan3D-Part](https://github.com/Tencent-Hunyuan/Hunyuan3D-Part) is a relevant part-segmentation/reconstruction research lead; it has NOT been installed, tested or shown to solve this fixture.

Next work should explicitly preserve spatial correspondence when refining a small region, with automatic region selection, registration, boundary handling and rejection of malformed replacements. Simply joining a generated head onto the bust or concatenating its image features is not a validated solution. Require all three lenses on the **whole** bust, stable silhouette and hose/grille detail at the target mesh budget, then run UV/texture/export and a second unrelated fixture before promoting anything to the simple UI.
