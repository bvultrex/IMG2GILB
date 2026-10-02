# QUALITY_JUMP_FINALIZE_AUTO_GATE_RESULT

Created: 2026-10-02 ~22:13 (Europe/Warsaw)

## Scope
Two consecutive `pipeline.Job` runs with **job-local** `hybrid_a3=true` and `finalize_candidate=textured_hybrid_a3_pbr.glb` so final `output.glb` lineage is the hybrid PBR sidecar (not face/paint default).

Studio **defaults unchanged**. `production_accepted=false`. IoU / face_iso unchanged.

## Jobs
1. Ranger `8fb2487ba66a4421a12a4dcc59038f64` (clone of `4abf740c…`)
2. Bust `777f4adb6a6740cc9e59bf5ed8fde9af` (clone of `9c9d771b…`)

## Proof
- `result.json`: `finalize_candidate`, `finalize_source`, `face_source=hybrid_a3_pbr`, `production_accepted=false`
- Content lineage: geom + albedo RGBA + MR RGBA match candidate (trimesh rewrite → container SHA differs)
- Studio `/api/jobs/<id>/model` → 200; `/color` → 200

## Commands
```bat
D:\SF3D_QualityLab\venv\Scripts\python.exe quality_lab\run_finalize_candidate_auto_gate.py
```

## Artifacts
- Summary: `D:\SF3D_QualityLab\app_jobs\_gate_finalize_candidate_auto_summary.json`
- Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_finalize_auto_gate\`
- Doc: `quality_lab/QUALITY_JUMP_FINALIZE_LINEAGE.md`

## Still open
- Zenko visual accept of finalize-consumed hybrid
- External Blender / 3D Viewer
- Studio default flip (forbidden)
