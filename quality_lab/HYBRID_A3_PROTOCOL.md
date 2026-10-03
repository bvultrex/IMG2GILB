# Hybrid A3 — Paint fill + ortho projection

Status: experimental lab path. `production_accepted=false`. No Meshy/Tripo parity claims.
Date: 2026-09-28 (Europe/Warsaw).

## What it does
- Keeps Paint 2.1 albedo atlas as fill where projection confidence is low.
- Projects prepared front/back/left/right orthos into UV via Hunyuan MeshRender `back_project`.
- Weights: source alpha edge feather × raster visibility × smoothstep incidence; front/back boosted vs sides.
- Writes sidecar GLBs only (`textured_hybrid_a3_color.glb`, optional `_pbr.glb`); never overwrites `textured_*.glb` / `output.glb`.

## Alignment
- Default: letterbox-pad prepared RGBA to 2048, bbox match to rendered silhouette, IoU refine (scale/translate grid).
- Left/right azim chosen by better bbox IoU among {90,270}.
- Optional: seed42-style `projection_landmarks.json` piecewise affine if present next to job.
- Low IoU (<0.72) recorded as `auto_align_low_iou` blocker in report; projection still runs gated.

## Studio wiring
- Optional stage `hybrid_a3` in `desktop/pipeline.py` when `project.json` settings include `"hybrid_a3": true`.
- Default off. Sidecar only; finalize still uses bake/face outputs unless you promote manually.
- Script resolution: `runtime.json` key `hybrid_a3_script`, else `quality_lab/project_hybrid_a3.py`, else lab copy.

## Offline run
`Run_Hybrid_A3.bat [job_dir]` or:
```
D:\SF3D_QualityLab\venv\Scripts\python.exe D:\SF3D_QualityLab\project_hybrid_a3.py --job <job> --out <job>\hybrid_a3 --vis <IMG2GILB>\_vis_export\texture_a3_hybrid\<jobid>
```

## A/B arms
- A0 = current `paint/albedo_atlas_2K.png` / textured GLB
- A3 = hybrid atlas + `textured_hybrid_a3_color.glb`
- Crops: `_vis_export/texture_a3_hybrid/<jobid>/sbs_*.png`

## Skip policy (post first David run)
- Sides with silhouette IoU < 0.72 are **not** projected (Paint fill kept) unless landmarks provided.
- Front/back require IoU >= 0.80 to project without landmarks.
- See `HYBRID_A3_RESULT.md` for the David job A/B.

## Front micro-align (2026-09-28 meshy_like_v1)
- After bbox+IoU: anime-face bbox (or tight head ROI) -> clamped translation; **face-local** soft warp; soft face weight boost on projection alpha.
- Full-body affine from face kps rejected (IoU regression). Sides still IoU-gated.
- Vis A/B: _vis_export\meshy_like_v1\
