# Multiview feasibility audit

Evidence read: official TencentARC/Pixal3D README/inference_mv.py/requirements.txt and LocalMesh source c30fb47f8a57f1c68650697a7b99bc2c2399be23, especially multivue/chemin.py, cameras.py, traits.py, forme.py, champ/layers/attentions.py and docs/WEIGHTS.md. Source-only clones are sibling folders pixal3d-source-audit and localmesh-source-audit. No external source executed or installed.

## Decision

Worth an isolated test: official Pixal3D has released a genuinely trained multiview path, separate *_mv weights. This is not a supported switch on the existing single-image TRELLIS weights and cannot be reproduced by averaging four image encodings. The high-frequency NAF features are also required by the intended architecture; omitting them would test a different system.

## Measured local compatibility

- Existing rig/TRELLIS interpreter: Python 3.11.16, torch 2.7.0+cu128; importlib finds no natten.
- LocalMesh package declares Python >=3.12,<3.13, torch2.8.0/torchvision0.23.0 and transformers5. Installing it into the existing runtime would violate its ABI pins. Do not upgrade the working runtime in place.
- Official Pixal3D requirements instead pin transformers4.57.3 and diffusers0.37.1. Do not assume these two distributions have interchangeable requirements.
- Free disk measured C20,130,140,160 bytes and D3,789,160,448 bytes. D unsuitable for the proposed new weights alone. Separate runtime/model-cache/output budgets must fit C before download.
- Existing DINOv3 and TRELLIS decoder can potentially be reused, but model API and checkpoint equivalence require smoke tests. Reuse is not yet proven.

## Weight/source scope

LocalMesh documents approximately4.27GB for three quantized multiview flow weights,2.7MB NAF, optionally544MB DA3. Its whole bundle is13.1GB excluding gated DINOv3; do not download all when only multiview is under test. These are documented sizes, not an independently downloaded inventory. FP8 is a lossy conversion; pin revision and verify source metadata before treating it as an official-weight control.

## Camera constraint

Official inference_mv.py consumes original framing plus camera-to-world matrices and horizontal FOV; it does not automatically crop/rescale input views. Its shipped90-degree camera rig is only suitable for matching views. The bust's oblique sides cannot silently use90-degree labels. LocalMesh supports measured azimuth adjustments but keeps elevation/FOV/distance nominal; this is not full calibration and does not resolve inconsistent reference geometry.

## Next implementation order

1. Resolve an isolated NATTEN/torch-compatible runtime or verified process-local integration before downloading flows. No global pip upgrades.
2. Pin the small multiview architecture descriptors and weight inventory, share existing approved assets only where compatible.
3. Start with a fully clothed four-view character and explicit camera/framing assumptions; log those assumptions. Bust side-angle ambiguity is a separate control, not hidden behind nominal cameras.
4. Sequential single-view/multiview comparison at identical output resolution and seed; inspect raw geometry before any cleanup, then final textured GLB. Score asymmetry, back structure and identity, not triangle count alone.

No inference result, quality improvement, installation success or production acceptance claimed by this audit.

Sources: https://github.com/TencentARC/Pixal3D ; https://github.com/Quentincls/localmesh-engine

## Isolated runtime implementation

Created sibling IMG2GILB-multiview-runtime, Python 3.12.10 from the official python NuGet package, with its own venv. Torch2.8.0+cu128/torchvision0.23.0 installation is in progress (exec session55491); do not launch a duplicate installer. Working runtimes were not altered.
Four Windows cp312 extension wheels downloaded from LocalMesh wheels-cp312-cu128; every SHA256 matched the GitHub release digest. Inventory: sibling runtime/release-assets.json. These are third-party binary builds, not official NATTEN binaries.
Added codex_natten_smoke.py: executes cutlass-fna on GPU at dilations1,2,4 and checks finite output plus constant-value attention invariance. Not yet executed. Successful imports alone will not count as passing.
Pinned remote weight inventory at Qtn-Cls/LocalMeshEngine revision6d52086dfb308dcd9db4a9a76d19f74d774d4625. Only inventory downloaded, no flow weights. Official Pixal source revision f7cf38429b0bd264f1995f0f8743a88b1c728b94.

### Runtime result (supersedes in-progress note)
Torch and all four wheels installed successfully; sessions55491 and85257 are terminal. Actual NATTEN CUDA computation FAILED: `no kernel image is available for execution on the device`. GPU independently measured NVIDIA RTX A4500, compute capability8.6. `HAS_LIBNATTEN=True` is insufficient evidence. No smoke success report exists. Need an SM86 build or independently validated supported backend before inference. C free after installation12,087,164,928 bytes; retain budget for4.28GB flows and outputs. Do not download full bundle. Official build documentation supports NATTEN_CUDA_ARCH=8.6; inspect existing portable CUDA toolkit before attempting build. No existing runtime or production defaults changed.

## NATTEN blocker resolved
Actual GPU smoke now PASSES all three dilations (1,2,4), constant-value max error0. Used already-present visualbruno/ComfyUI-Trellis2 wheels/Windows/Torch280/natten-0.21.6-cp312-cp312-win_amd64.whl, SHA2561ba8ca20697ffec8ab8e853971f166e72a1c3b6aa274eee59bfa61c096f84451. Installed only into isolated runtime. No source build needed. Report: sibling runtime/natten-smoke.json. Previous LocalMesh wheel was incompatible on this GPU despite successful import.
LocalMesh editable package install with triton-windows<3.5 in progress session19916. Pinned multiview weights download with LFS SHA verification in progress session71159. Re-poll these handles, do not duplicate. Existing DINO and TRELLIS1 sparse decoder can be referenced locally; shape decoder expected by LocalMesh is FP8 path, existing decoder is FP16. Must explicitly adapt loader to correct descriptor/state_dict or obtain matching decoder; never rename a FP16 checkpoint as FP8 without verification. No inference yet.

## Conditioning and decoder audits passed
Install session19916 and download71159 completed exit0. All three MV safetensors plus NAF verified against pinned LFS hashes. Runtime requirements frozen in requirements-resolved.txt. Existing approved DINO directory is shared by a directory junction; no copied/downloaded DINO weights.
`codex_multiview_encoder_smoke.py` passed offline on ranger_ortho_v1/front.png: DINO(1,1029,1024), NAF(1,256,512,512), finite,10.13s. Report runtime/encoder-smoke.json. This is one-image conditioning, not reconstruction.
`codex_multiview_decoder_audit.py` passed STRICT state_dict loading of existing FP16 sparse decoder(74keys) and shape decoder(292keys) into LocalMesh classes, no meta tensors remaining. Report runtime/decoder-audit.json. Forward/decode remains untested. Use explicit process-local path redirection to actual FP16 descriptors for the upcoming runner; do not relabel files FP8. Sparse module printed flash_attn despite environment flags, so explicitly inspect/set backend before inference. Existing shaders and baseline untouched. All sessions terminal; no GPU generation launched.
Next: prepare four-view calibrated inputs and process-local decoder mapping, set supported sparse attention backend, execute trained MV geometry cascade and independently render it. No quality acceptance yet.

Full MV trial launched via codex_multiview_trial.py, exec session55393, output quality_runs/pixal_mv_ranger_trial1. Observed completed four-view512 encoding, structure12steps, four-view1024 encoding, first shape6steps; now decoder stage. Existing FP16 decoder mapping process-local. Sparse config explicitly set sdpa after import. Inputs reuse previous prepared Ranger RGBs, padded square with backgrounds retained; nominal cameras uncalibrated. This is an integration experiment, not end-to-end acceptance. Recipe file says12shape steps but LocalMesh default override uses6; next controlled quality run should explicitly pass12 or document6. Do not restart while session55393/process16280 is live.

Session55393 subsequently completed exit0, including second shape stage and raw.ply export. No process pending. Next independent render and topology/geometry review required.

## First visual review, not accepted
Trial1 independently imported/rendered in Blender5.2. Raw1796196vertices/4010632triangles; SHA83c35ffa2e86a8b78fc2d2b5a530dc5fe0d89b11fb8e3a240110513496007b82 unchanged. Output is Z-up, not earlier diagnostic PLY Y-up; added explicit --ply-up to renderer. Correct renders in clay_zup. Front/back/35deg show coherent gross body/clothing, recognizable face/hair, but widespread small holes/pitting and jagged detail; not Meshy parity or production accepted. Indexed incidence audit:186130 boundary edges,422931 nonmanifold edges,max4. This is not a positional-welded/self-intersection audit.
Started controlled fresh rerun pixal_mv_ranger_untiled_control, session17682: identical input/seed/settings, only useTiled=False. Runner now records final shape latent before decoding for future same-latent controls. Preserve both raw outputs; compare surface quality and topology. Re-poll17682 before any new GPU launch. No texture run yet.

## Surface control result
Untiled run17682 completed47.03s. Canonical vertex positions AND unoriented face sets exactly equal trial1 despite different array ordering; same indexed edge counts. Tiling is not root cause on this fixture. Evidence canonical_comparison.json. Saved shape_latent.pt enables later decoder-only replay.
Native surface control codex_mv_surface_control.py completed9.76s: small-hole fill perimeter0.01 ->4036890faces; DC1024 band1 project_back0 ->4662948faces; target500k simplification ->466150storedfaces. Z-up raw rotated correctly to Y-upGLB. Blender imported465171faces,223404vertices; SHA57edaeb511cd3f0a941adb57b898d92e20adec0c95f80255cc23961b082ede6d. Renders surface_control/clay show pitting substantially reduced, retained major clothing/hair forms, but visible chest defect remains and fine details soften. Shading also changes from flat raw to smooth normals, so visual smoothness is not solely geometric improvement.
Indexed final audit:0boundary,8408nonmanifold,28zero-area faces; Blender/storage discrepancy979faces. NOT accepted; zero boundary is not valid-manifold proof. All sessions terminal (61465,67111,32014). Next isolate topology before/after simplification, remove duplicates without altering normals, evaluate thin/small feature retention, then texture on verified surface. No Meshy parity claim.
