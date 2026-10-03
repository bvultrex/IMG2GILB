# Texture Methods Survey — IMG2GILB Studio

Status: research note only. `production_accepted=false`. No Meshy/Tripo parity claims.
Date: 2026-09-28 (Europe/Warsaw). Author: Grok Bot research pass for Danny / bvultrex.

## 1. Current Studio texturing path (code-backed)

Orchestrator: `desktop/pipeline.py` → stages `prepare → shape → uv → paint → bake → [face] → finalize`.

| Stage | What it does today | Key paths |
|---|---|---|
| prepare | BRIA matting per uploaded view | ComfyUI BRIA nodes |
| shape | Hunyuan3D-2mv DiT from 1–4 ortho views | `desktop/stages.py` shape |
| uv | `mesh_uv_wrap` + MeshRender normals/positions for 6 cameras (0/90/180/270/top/bottom), render/texture size 2048 | `desktop/stages.py` uv → `controls/uv_mesh.npz`, `render_*_multiview_*.png` |
| paint | **Hunyuan Paint 2.1** (`run_paint21.py`): DINO features + 2.5D UNet; **only `prepared/front.png`**; 6 generated albedo+MR views at **512 (fast) or 768 (standard)** | `D:\SF3D_QualityLab\run_paint21.py` |
| bake | Resize painted views **PIL bilinear → 2048**, cosine-weighted `fast_bake_texture`, Python `texture_inpaint`, export color + PBR GLB | `D:\SF3D_QualityLab\bake_paint21.py` |
| face | Optional anime face warp + multiband blend + UV reproject (albedo only) | `face_refining/` + `FACE_TEXTURES_1_0.md` |
| finalize | If `texture_size != 2048`, LANCZOS resize embedded maps | `desktop/stages.py` finalize |

Softness levers already visible in this path:

1. Native diffusion resolution is 512/768; bake upscales with plain PIL resize (`bake_paint21.py` report note: `upscaler='PIL resize only'`).
2. Studio paint uses **one** reference even when 2–4 ortho images exist (`pipeline.py` paint action). Lab has `quality_lab/run_paint_multiref.py` and `D:\SF3D_QualityLab` multiref experiments, but they are **not** wired into Studio.Job.
3. Paint invents appearance (logos/tattoos/eyes) under geometry conditioning; it does not project the user's ortho photos.
4. Speculative MR maps are already generated; sharpness pain is primarily **albedo fidelity**, not missing speculative PBR.

Planned work (not a full method change): ChatGPT queue **T1** — `quality_lab/CHATGPT_TASK_QUEUE.md` + `TEXTURE_SHARPNESS_V1_PROTOCOL.md` — CPU diagnostic + reversible unsharp on embedded baseColor. Useful as a metric harness; **not** a root-cause fix (`LOCAL_DETAIL_ACCEPTANCE_GATES.md` §6).

## 2. Lab evidence already on disk

| Experiment | Outcome for sharpness / fidelity | Paths |
|---|---|---|
| Paint 2.1 @ 6×768 vs older 2.0 | Clearer face/tattoo outlines; still invented text; VRAM OK with offload on ~20 GB | `D:\SF3D_QualityLab\PAINT21_RESULTS.md`, HANDOFF |
| Real-ESRGAN / RealESRNet on generated views before bake | Moderate edge gain; can amplify wrong invented detail; ESRGAN preferred over ESRNet for crispness | `D:\SF3D_QualityLab\UPSCALE_REVIEW.md` |
| Manual landmark ortho projection into Paint atlas | **Best fidelity gain** for face/text/tattoo in trusted regions; blend/registration artifacts remain; lighting baked from photos | `D:\SF3D_QualityLab\REFERENCE_PROJECTION_RESULTS.md`, `project_references.py` |
| Face Textures 1.0 | Moderate anime face improvement; preserves atlas outside mask | `FACE_TEXTURES_1_0.md` |
| T1 unsharp refine | Assigned diagnostic; RESULT.md not present yet at survey time | `quality_lab/texture_sharpness_v1.py` |

## 3. Ranked alternatives (fit for 4-ortho Studio)

Scoring axes: (a) 4-ortho character/object/bust fit, (b) sharpness/seam upside, (c) local Windows/CUDA installability, (d) IMG2GILB integration effort, (e) license/risk. Scale 1–5; higher better except risk.

### Option A — Hybrid: Paint fill + ortho reference projection (classic bake blend)
**Scores:** a5 b5 c5 d3 e4

- Project prepared ortho RGB into existing UV with visibility + incidence weights; keep Paint where confidence low.
- Pros: Matches user pain (soft vs crisp reference detail); lab prototype already proves visual upside; works for fullbody/objects/busts; albedo-first (no speculative PBR chase); offline.
- Cons: Needs **automatic** alignment (manual landmarks do not scale); photo lighting / incomplete alpha still bleed; geometry errors stay geometry errors.
- License: own lab code + existing Hunyuan renderer (already in use).

### Option B — Wire multi-reference Paint 2.1 into Studio
**Scores:** a4 b3 c5 d4 e4

- Use all uploaded prepared views in `HunyuanPaintPipeline` (lab: `run_paint_multiref.py`).
- Pros: Already installed; small Studio change; better back/side consistency than front-only.
- Cons: Still generative at 512/768; does not guarantee reference-pixel crispness; memory rises with ref count.
- License: Hunyuan3D-2.1 / MaterialMVP+RomanTex stack (already accepted locally).

### Option C — In-pipeline SR of Paint views before bake (Real-ESRGAN)
**Scores:** a4 b3 c5 d4 e5

- Already tested; optional stage after paint, before bake.
- Pros: Tiny integration; measurable Laplacian/HF gain; reversible A/B.
- Cons: Sharpens invented pixels; weak vs true projection; not a fidelity transfer.
- License: Real-ESRGAN (BSD-style); weights already downloaded in lab.

### Option D — Native paint ≥768 always + stop soft upsample path
**Scores:** a4 b3 c5 d5 e5

- Standard quality already uses 768; ensure bake uses ESRGAN or Paint-native higher res rather than PIL; avoid finalize downscale→viewer upscale confusion.
- Pros: Almost free config discipline.
- Cons: Limited ceiling vs projection; 768 still far from 2K reference detail.

### Option E — MV-Adapter image-to-texture / MVPaint / SyncMVD
**Scores:** a3 b4 c2 d2 e3

- Strong multi-view consistency research (MVPaint UV SR + seam smooth; SyncMVD UV sync; MV-Adapter i2tex).
- Pros: Better seam literature; image-conditioned texturing exists (MV-Adapter).
- Cons: Windows friction (PyTorch3D / CV-CUDA); mostly **generation** not ortho photo transfer; high integration cost; sequential GPU contention with current Studio.
- License: research repos; check each before bundling.

### Option F — TRELLIS.2 / Unique3D / InstantMesh texture stages
**Scores:** a2 b3 c2 d1 e2

- Different full generators, not drop-in texture stages for Hunyuan/SF3D meshes.
- Pros: Interesting long-term geometry+material families.
- Cons: Gated DINOv3 / VRAM / Windows packaging; wrong abstraction for "upgrade texture on existing Studio mesh"; Unique3D/InstantMesh bake their own reconstruction.
- Do not chase for near-term Studio.Job texture sharpness.

### Explicitly lower priority
- Post-hoc unsharp-only (T1) as production quality fix.
- Inventing sharper roughness/metal to "look crisp".
- DiffTex (architectural SfM proxies, not character ortho).
- TEXTure / Paint3D as primary (older T2T, UV-fragile) unless used as fill ideas only.
- Meshy/Tripo cloud parity racing.

## 4. #1 recommendation

**Pursue Option A as the primary upgrade path**, with **B+C as cheap control arms** in the same A/B matrix.

Why A wins: the user's 4-ortho Studio inputs are already calibrated appearance references. Paint 2.1 is a strong hole-filler and view synthesizer, but the softness complaint is largely **lost high-frequency reference detail** after generative 768→PIL→2K bake. The lab's landmark projection already showed the fidelity direction without claiming Meshy parity. Automating alignment (silhouette/IoU + optional sparse correspondences, region-limited transfer) is the smallest strategically correct step that matches fullbody + objects + busts.

Keep Face 1.0 as a character-only post-pass after the hybrid albedo is stable.

## 5. Suggested A/B after the current 2K ortho pre-upscale probe

**Fixture:** Ranger (better than chaotic bust for texture spotting). Freeze the same shape.glb + `uv_mesh.npz` from one completed job so geometry is held constant.

| Arm | Pipeline change | Goal |
|---|---|---|
| A0 | Current Studio: single-ref Paint @ resolution used by probe → PIL bake 2K | Baseline |
| A1 | Same Paint views → Real-ESRGAN x4plus → bake 2K | In-pipeline SR vs pre-upscaled inputs |
| A2 | Multi-ref Paint 2.1 (front+back[+side] prepared) @ 768 → bake | Reference-count effect |
| A3 | A0 or A2 albedo atlas + **automatic** ortho projection blend (visibility/incidence; Paint fill where weight low) | Fidelity / sharpness candidate |
| A4 (optional) | A3 + Face 1.0 if character | Face-only delta |

**Inputs:** same prepared 4-view set; record whether probe pre-upscaled inputs to 2K *before* shape/paint or only for texture.

**Metrics:**
- Visual: fixed Ranger crops (face/insignia/fabric edges), front/back/side flat renders, seam strips.
- Quantitative: reuse `texture_sharpness_v1.py` proxies (Laplacian variance, HF RMS, grad p90/p99) on albedo; report ratios vs A0; also `near_black_or_white_channel_fraction` for clip risk.
- Integrity: source GLB untouched; non-albedo maps byte-identical when only albedo changes; Blender import + height gate.
- Reject gain if UV stretch / bake seams / wrong silhouette are the real defect (`LOCAL_DETAIL_ACCEPTANCE_GATES.md` §6).

**Stop rule:** if A3 does not beat A1 on *reference-detail visual* review (not only Laplacian), debug alignment before installing new painters.

## 6. What NOT to chase yet

- Full MVPaint/SyncMVD Windows ports.
- TRELLIS.2 texturing while DINOv3 gate / VRAM packaging unresolved.
- Replacing Paint 2.1 wholesale without A/B against hybrid projection.
- Production UI promotion of texture refine or projection.
- Any Meshy/Tripo quality ranking language.
- Using T1 unsharp as the main quality story.

## 7. Cited paths / URLs

### Local / repo
- `https://github.com/bvultrex/IMG2GILB` — `desktop/pipeline.py`, `desktop/stages.py`, `desktop/replace_albedo.py`, `face_refining/`, `quality_lab/CHATGPT_TASK_QUEUE.md`, `TEXTURE_SHARPNESS_V1_PROTOCOL.md`, `texture_sharpness_v1.py`, `run_paint_multiref.py`, `LOCAL_DETAIL_ACCEPTANCE_GATES.md`, `FACE_TEXTURES_1_0.md`, `HANDOFF.md`
- `D:\SF3D_QualityLab\run_paint21.py`, `bake_paint21.py`, `project_references.py`, `UPSCALE_REVIEW.md`, `PAINT21_RESULTS.md`, `REFERENCE_PROJECTION_RESULTS.md`, `QUALITY_STRATEGY_AUDIT.md`

### External
- Hunyuan3D-2 / Paint bake: https://github.com/Tencent-Hunyuan/Hunyuan3D-2 , https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- MaterialMVP: https://github.com/ZebinHe/MaterialMVP
- RomanTex (inside Paint 2.1): https://oakshy.github.io/RomanTex/ , arXiv 2503.19011
- MVPaint: https://github.com/3DTopia/MVPaint
- SyncMVD: https://github.com/LIU-Yuxin/SyncMVD
- Paint3D: https://github.com/OpenTexture/Paint3D
- MV-Adapter: https://github.com/huanngzh/MV-Adapter
- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN
- TRELLIS.2: https://github.com/microsoft/TRELLIS.2
