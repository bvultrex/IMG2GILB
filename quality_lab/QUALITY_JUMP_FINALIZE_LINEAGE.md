# QUALITY_JUMP_FINALIZE_LINEAGE

Created: 2026-10-02 ~22:07 (Europe/Warsaw / UTC+2)

## Status
- **Opt-in** finalize lineage wired in desktop/stages.py (+ thin desktop/server.py pass-through).
- Default finalize path **unchanged**: shape → 	extured_pbr → ace/Face_1_0.glb when face processed.
- inalize_candidate default **OFF** (absent / empty / false).
- production_accepted=false. **No Studio UI default flip.**
- Two-auto candidate gate remains **OPEN** (see blockers).

## Settings contract

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| inalize_candidate | string (job-relative path) or absent | OFF | When set, finalize loads this GLB as output.glb source (overrides face/pbr). Must stay inside job dir (no .., no absolute). |
| ace_source | string label or absent | auto | Recorded into 
esult.json. When candidate set and label omitted → inalize_candidate:<relpath>. |


esult.json extra fields on finalize:
- ace_source
- inalize_candidate (null when default path)
- inalize_source (resolved absolute path used)
- production_accepted: false

## E2E proof (Ranger hybrid MR-retain)

Job: D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833

### Commands

`at
REM Backup prior Studio finalize (face path)
copy output.glb output_pre_finalize_lineage.glb
copy result.json result_pre_finalize_lineage.json
copy preview_color.glb preview_color_pre_finalize_lineage.glb

REM project.json settings (job-local):
REM   "finalize_candidate": "quality_jump_second_fixture/textured_hybrid_ranger_pbr_mr_retain.glb"
REM   "face_source": "hybrid_a3_mr_retain"

D:\SF3D_QualityLab\venv\Scripts\python.exe ^
  C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\stages.py ^
  finalize ^
  D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833 ^
  C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\runtime.json
`

Log: inalize_lineage_proof.log + stdout JSON (also mirrored under vis).

### Lineage SHAs

| Artifact | SHA256 | Bytes |
|----------|--------|-------|
| Candidate quality_jump_second_fixture/textured_hybrid_ranger_pbr_mr_retain.glb | 92fd78c9e6562fe1290663ceed8c37b9b14d76d3028dd82265d7aaf88717d66b | 9833516 |
| Final output.glb (trimesh re-export) | ed1d3e77b9e72b206e4ad1d33d3b710781fbdfaf8639751ae56eacd260a51100 | 9833620 |
| Pre-proof output_pre_finalize_lineage.glb (old face path) | 35590c23e803602107cacbbd8bf2f0b3f159559a2ac757dc107bbe7b92114072 | 9283864 |

Container SHA of output.glb ≠ candidate (trimesh rewrite) — **content lineage** matches:

| Check | Match |
|-------|-------|
| Geometry (verts/faces/uv) | **true** (0f1d6f431ad37532…) |
| Albedo RGBA | **true** (829e707732dff501…) |
| MetallicRoughness RGBA | **true** (e148150e36709224…) |

Default path (opt-in removed) would still resolve to: D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833\face\Face_1_0.glb (ace_source=face_processed).

### Import / preview evidence

Vis: C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_finalize_lineage\

- sbs_candidate_vs_output_albedo.png — candidate vs output.glb albedo (diff≈0)
- import_preview_card.png — stats card + atlas thumb
- output_albedo_atlas_512.png
- studio_load_log.txt:
`
Studio load OK status=200 bytes=9833620 content-type=model/gltf-binary job=4abf740c34c9487ba818455efe460833 time=2026-10-02 22:07:35 Europe/Warsaw
Studio color preview OK status=200 bytes=7037124
`
- Proof JSON: inalize_lineage_proof.json (job + vis)

Studio briefly started on :8190 for the GET; stopped after proof. /api/jobs/.../model → 200, bytes=9833620 (model/gltf-binary); /color → 200.

### result.json excerpt

`json
{
  "face_source": "hybrid_a3_mr_retain",
  "finalize_candidate": "quality_jump_second_fixture/textured_hybrid_ranger_pbr_mr_retain.glb",
  "finalize_source": "D:\\SF3D_QualityLab\\app_jobs\\4abf740c34c9487ba818455efe460833\\quality_jump_second_fixture\\textured_hybrid_ranger_pbr_mr_retain.glb",
  "production_accepted": false,
  "face_status": "processed",
  "bytes": 9833620,
  "texture_size": 2048
}
`

## Code touch

- desktop/stages.py — opt-in candidate resolve + metadata
- desktop/server.py — accepts optional inalize_candidate / ace_source on job create (not UI defaults)
- No pp.js / checkbox changes
- IoU gate for face_iso **not** relaxed

## What still blocks two-auto gate close

1. Auto jobs must set inalize_candidate to the hybrid/face_iso artifact they want consumed (today hybrid_a3 stage writes sidecars; finalize only picks them up with this opt-in).
2. Need **two consecutive** full automatic jobs where the **final** output.glb lineage is the selected candidate (not only sidecar presence) — this Ranger run is a **manual finalize replay** on an existing job, not a fresh end-to-end Studio auto pair.
3. Zenko visual accept of the candidate that auto jobs would select (Ranger face_iso v2 = conservative fallback only; hybrid still under review).
4. External/third-party GLB import beyond Studio+trimesh still nice-to-have.
5. production_accepted / Studio default flip remain **forbidden** until the above pass.

## Next (not this turn)

- Landmark reprojection residuals + boundary continuity for further face alignment.
- Wire auto-job scripts to set inalize_candidate after hybrid_a3 (still default false globally).
