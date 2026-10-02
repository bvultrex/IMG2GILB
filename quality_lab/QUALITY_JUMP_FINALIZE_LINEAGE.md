# QUALITY_JUMP_FINALIZE_LINEAGE

Created: 2026-10-02 ~22:07 (Europe/Warsaw / UTC+2)
Updated: 2026-10-02 ~22:13 (Europe/Warsaw / UTC+2)

## Status
- **Opt-in** finalize lineage wired in desktop/stages.py (+ thin desktop/server.py pass-through).
- Default finalize path **unchanged**: shape → textured_pbr → face/Face_1_0.glb when face processed.
- `finalize_candidate` default **OFF** (absent / empty / false).
- `production_accepted=false`. **No Studio UI default flip.**
- Two-auto candidate gate: **CLOSED for lineage proof** (Ranger + Bust Job.run with finalize_candidate). Zenko visual accept of the hybrid candidate and external Blender viewer remain separate.

## Settings contract

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `finalize_candidate` | string (job-relative path) or absent | OFF | When set, finalize loads this GLB as output.glb source (overrides face/pbr). Must stay inside job dir (no `..`, no absolute). |
| `face_source` | string label or absent | auto | Recorded into `result.json`. When candidate set and label omitted → `finalize_candidate:<relpath>`. |
| `hybrid_a3` | bool | OFF / unset | Studio API + pipeline opt-in; runs hybrid after bake. |

`result.json` extra fields on finalize:
- `face_source`
- `finalize_candidate` (null when default path)
- `finalize_source` (resolved absolute path used)
- `production_accepted`: false

## Auto script

`quality_lab/run_finalize_candidate_auto_gate.py`

- Clones fixture jobs (Ranger + Bust), sets **job-local** `hybrid_a3=true` + `finalize_candidate=textured_hybrid_a3_pbr.glb` + `face_source=hybrid_a3_pbr`.
- Seeds stage cache under the new fingerprint so prepare/shape/uv/paint/bake/hybrid(/face) reuse; **finalize** always re-runs via `pipeline.Job`.
- Asserts geom + albedo RGBA + MR RGBA lineage match; writes proofs under job + `_vis_export/quality_jump_finalize_auto_gate/`.
- Global Studio defaults and `production_accepted` stay false.

### Commands

```bat
D:\SF3D_QualityLab\venv\Scripts\python.exe ^
  C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\run_finalize_candidate_auto_gate.py
```

Summary: `D:\SF3D_QualityLab\app_jobs\_gate_finalize_candidate_auto_summary.json`

## Two consecutive auto jobs (2026-10-02 ~22:12)

| # | Fixture | Job ID | Candidate | output.glb content lineage | Studio /model |
|---|---------|--------|-----------|----------------------------|---------------|
| 1 | Ranger (clothed) | `8fb2487ba66a4421a12a4dcc59038f64` | `textured_hybrid_a3_pbr.glb` SHA `7cff6684…` | geom+albedo+MR **match** | 200 bytes=9833588 |
| 2 | Bust (mechanical) | `777f4adb6a6740cc9e59bf5ed8fde9af` | `textured_hybrid_a3_pbr.glb` SHA `4363d496…` | geom+albedo+MR **match** | 200 bytes=9571584 |

Cloned from prior hybrid_a3 gate jobs `4abf740c…` / `9c9d771b…` (inputs + texture path preserved; paint baselines untouched).

### result.json (Ranger excerpt)

```json
{
  "face_source": "hybrid_a3_pbr",
  "finalize_candidate": "textured_hybrid_a3_pbr.glb",
  "finalize_source": "D:\\SF3D_QualityLab\\app_jobs\\8fb2487ba66a4421a12a4dcc59038f64\\textured_hybrid_a3_pbr.glb",
  "production_accepted": false,
  "face_status": "processed",
  "bytes": 9833588,
  "texture_size": 2048
}
```

### Studio preview evidence

Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_finalize_auto_gate\`

- `studio_load_8fb2487ba66a4421a12a4dcc59038f64.txt` — /model 200 + /color 200
- `studio_load_777f4adb6a6740cc9e59bf5ed8fde9af.txt` — /model 200 + /color 200
- `ranger_proof.json` / `bust_proof.json` / `summary.json`

Studio briefly on :8190 for GET; stopped after proof.

## Prior manual E2E proof (Ranger hybrid MR-retain sidecar)

Job: `D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833` — stages.py finalize replay with `quality_jump_second_fixture/textured_hybrid_ranger_pbr_mr_retain.glb` (see earlier section / `finalize_lineage_proof.json`). Superseded for **auto gate** by the Job.run pair above using Studio-path `textured_hybrid_a3_pbr.glb`.

## Code touch

- `desktop/stages.py` — opt-in candidate resolve + metadata (commit 3c606cb)
- `desktop/server.py` — accepts optional `finalize_candidate` / `face_source` / `hybrid_a3` / `paint_multiref` / `texture_sr` on job create (**not** UI defaults)
- `desktop/pipeline.py` — remesh / multiref / hybrid_a3 / texture_sr stages (opt-in; hybrid default false)
- `quality_lab/run_finalize_candidate_auto_gate.py` — two-auto runner
- No `app.js` / checkbox changes in this gate commit
- IoU gate for face_iso **not** relaxed

## What still blocks production / default flip

1. ~~Auto jobs must set `finalize_candidate`~~ — **DONE** via auto script + server opt-in.
2. ~~Two consecutive full automatic jobs with final output.glb lineage = candidate~~ — **DONE** (Ranger + Bust).
3. Zenko visual accept of the hybrid candidate that auto jobs select (Ranger face_iso v2 = conservative fallback only; hybrid still under review).
4. External/third-party GLB import (Blender / Windows 3D Viewer) still nice-to-have.
5. `production_accepted` / Studio default flip remain **forbidden** until Zenko + Danny pass.

## Next (not this turn)

- Landmark reprojection residuals + boundary continuity for further face alignment.
- Zenko scorecard on finalize-consumed hybrid output.glb (not only sidecars).
