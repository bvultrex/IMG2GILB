# QUALITY_JUMP_FACE_ISO_TRANSFORM_DIAG

Created: 2026-10-02 ~21:45 (Europe/Warsaw / UTC+2)

## Status
- Zenko REJECT face_iso (Issue #1 comment 5959940728) — mapping corruption, not softness.
- Grok ACK 5959948593.
- `production_accepted=false`. Studio defaults unchanged. Failed artifact KEEP.
- `--face-iso` NOT propagated to Ranger/bust.
- Baseline remains **P2 MR-retain**.

## Symptoms (Zenko / sbs_face.png)
- Extra eye in forehead/hair
- Displaced facial fragments (collage)
- Cyan collar texture on cheek/jaw

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso\sbs_face.png`

## Transform path trace (`quality_lab/project_hybrid_a3.py`)

### Order (front, `--face-iso`)
1. **Body align** `bbox_matrix` + `refine_alignment` → full-frame 2×3 affine on ortho RGBA (`warp_rgba` / `cv2.warpAffine`, pixel coords, size typically 2048 during project). RGB **and** alpha share this matrix.
2. **`micro_align_front(..., face_iso=True)`**
   - ROI from anime-face **dst** bbox +28px pad (fallback: silhouette head). Pixel coords, image space (not normalized).
   - `face_center_translation` (capped) may set an initial `delta`.
   - **`face_landmark_quality`**: `estimateAffinePartial2D(src_kps → dst_kps)` on dense anime landmarks (subset idxs). Gate: residual med≤6, p90≤12, **|dx|,|dy|≤96**, scale∈[0.90,1.12].
   - If gate ok: **override** prior delta. If |rot| small → **strip to pure translation `(tx,ty)` from the scaled similarity**, then clamp so max(|dx|,|dy|)≤48 (`clamp_scale`).
   - `apply_face_local_warp(rgba, delta, roi)`:
     - `full = warpAffine(rgba, delta)` on **entire** RGBA (image+mask same transform) ✓
     - Soft rectangular ROI mask (Gaussian feather) in **unwarped** destination space
     - `out = (1-m)*original + m*full` → interior shifted, exterior frozen → **ghost/duplicate features at ROI rim**
3. **Weights** `face_iso_weight_map` on post-warp mask; `project_face=True` boosts projection in elliptical face ROI (`body_scale=1.0` — P2 torso freeze).

### Coordinate notes
- All micro deltas are **pixel** 2×3 affines (OpenCV: maps src→dst).
- No explicit crop-offset remapping inside `apply_face_local_warp` (ROI is absolute pixel box on full frame).
- Saved `hybrid_work/front_aligned.png` / `front_baseline.png` are **1024² previews**; live micro used full project resolution (landmark bboxes ~900–1100 ⇒ ~2048 space). Controls that touch previews must scale ROI/delta ×0.5.

## Failed-run numbers (KEEP artifact)
Job: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_face_iso\`

| Field | Value |
|-------|-------|
| chosen | `face_iso_landmark_translation_clamped` |
| landmark scale | **1.0936** |
| landmark dx, dy | **-65.15, -64.53** |
| clamp_scale | 0.737 |
| **applied delta** | **≈ (-48.0, -47.5) px** |
| face_center dx, dy (same call) | **(+17.0, +28.1)** |
| project_face / weight_map | true / `face_iso_project` |
| IoU before → after | 0.912 → 0.895 (accepted anyway) |

**Contradiction:** face centers already nearly aligned (+17,+28), yet landmark path applied ~48px **opposite** up-left translation. That alone explains eye→forehead and collar→cheek (content from ~48px below pulled into jaw ROI).

### Root cause (coordinate bug, not softness)
When landmark partial-affine has **scale≠1** but small rotation, code does:

```python
delta = [[1, 0, tx], [0, 1, ty]]  # drops scale; tx,ty are similarity translation terms
```

For scale≈1.09, `tx,ty` are **not** a pure face shift. They absorb `-(s-1)*position` style terms. Stripping scale invents a large bogus translation; clamp to 48px still wrecks a ~260px-tall face ROI. Soft ROI blend then composites warped face against unwarped body → duplicate eye fragments + cyan collar patch.

Secondary contributors:
- Gate `|dx|,|dy|≤96` too loose vs face_center (~24px) policy.
- IoU accept allows 4%+ regression for face-local warp.
- Landmark index subset `[0,1,2,3,4,11,…]` may be semantically weak (not proven primary here).

## Controls (NEW only under `…/quality_jump_face_iso/controls/`)

Script: `quality_lab/run_face_iso_transform_controls.py`

| Control | Result | Notes |
|---------|--------|-------|
| synthetic_identity | **PASS** | full_maxabs≤1; alpha unchanged |
| synthetic_known_translation (16,-12) | FAIL* | interior↔full MAE 0.19 OK; blue marker peak false-fail on checker (err 12px); alpha_interior MAE 0 |
| tx_extract_from_scaled_similarity (s=1.09) | **FAIL (bug demo)** | full affine err≈0; stripped translation median err **20.6px**; invented tx/ty |
| front_aligned_identity | **PASS** | |
| front_aligned_known_translation (16,0) | **PASS** | interior matches full warp; outside≈original; **RGB+A share delta** |

\*Mechanical warp path is OK; synthetic marker metric noisy. Verdict: **warp machinery trustworthy; delta construction is the bug.**

Artifacts:
- `…/controls/control_results.json`
- `…/controls/sbs_replay_failed_delta_face_1024space.png` (scaled replay of applied −24/−24 on 1024 preview)
- Vis mirror: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso\controls\`

## Proposed minimal fix arm (NOT implemented this turn)
Only because identity + known-translation on real front_aligned **PASS**:

1. **Never strip scale from landmark `Mq` into pure translation.** Prefer:
   - use **face_center translation only** when `|scale-1|>0.02`, OR
   - apply full partial affine **inside** `apply_face_local_warp` with tight caps (scale∈[0.97,1.03], |t|≤16), OR
   - convert similarity → translation via **bbox/landmark center delta** (not raw `M[:,2]`).
2. Tighten face_iso gate: require landmark `|dx|,|dy|≤24` **or** agreement with face_center within 12px; else `project_face=False` / no micro (paint-all coherent).
3. Reject micro if IoU drops (already almost — make stricter for face_iso).
4. Re-run David **new sidecar only**; keep failed face_iso tree.

Do **not** enable `--face-iso` on Ranger/bust until David control+visual pass.

## Auto gate OPEN (Studio E2E lineage)

`desktop/stages.py` **finalize** still picks:

```text
textured_pbr.glb  →  (optional) face/Face_1_0.glb  →  output.glb
```

It does **not** read `textured_hybrid_a3_color.glb` / `hybrid_a3/`.  
`desktop/pipeline.py` can run opt-in stage `hybrid_a3` (settings `hybrid_a3=true`) writing:

- `{job}/hybrid_a3/report.json`
- `{job}/textured_hybrid_a3_color.glb` (+ PBR via script)

…but **finalize does not promote hybrid → output.glb**. Therefore Auto gate for “Studio download = hybrid texture” remains **OPEN**. Do not claim closed.

### Commands / logs needed for full Studio E2E lineage proof
1. Start job with settings including `"hybrid_a3": true` (and existing paint_multiref / texture_sr freeze).
2. Confirm stage list in job status / pipeline log contains `hybrid_a3` before `finalize`.
3. Assert artifacts:
   ```bat
   python -c "from pathlib import Path; j=Path(r'JOB'); assert (j/'hybrid_a3'/'report.json').exists(); assert (j/'textured_hybrid_a3_color.glb').exists()"
   ```
4. Show finalize source in `stages.py` log / `result.json` still documents textured_pbr|face unless/until promote wired.
5. Optional explicit copy test (manual, not default): hash `textured_hybrid_a3_color.glb` vs any promoted output — only after product decision.
6. Keep `QUALITY_JUMP_AUTO_HYBRID_A3_GATE_RESULT.md` / `QUALITY_JUMP_SECOND_FIXTURE_GATE.md` checklist; Zenko visual still pending for Ranger/bust.

## Non-goals this turn
- No Studio default flip
- No `--face-iso` on Ranger/bust
- No overwrite of failed face_iso GLB/atlas
- No production_accepted=true

## Fix implemented (2026-10-02 ~22:10 UTC+2)
See `QUALITY_JUMP_FACE_ISO_V2_RESULT.md` + Issue #1 comment 5960147657.
v2 sidecar: `quality_jump_face_iso_v2/`; controls PASS; awaiting Zenko visual. v1 KEEP.
