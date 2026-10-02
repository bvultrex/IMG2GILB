# Quality Jump - Second fixture gate (checklist)

**Purpose:** Promote texture/hybrid changes past the single David job only after hard multi-fixture proof.
**Studio defaults:** do not flip until this gate passes.
**production_accepted=false** until all criteria below pass Zenko visual + Danny.

Updated: 2026-10-02 ~21:12 (Europe/Warsaw) — Grok auto hybrid_a3 jobs + bust texture path.

## Gate criteria (all required)

1. **Second clothed character** (not David 5e81ac79…) — same hybrid settings as accepted David arm; visual paint/A0 vs hybrid SBS (face / jaw / chest / back emblem or equivalent).
   - [x] Ranger hybrid texture path delivered (lab sidecar + **Studio auto** hybrid_a3)
   - [ ] Zenko visual scorecard on Ranger (pending)
2. **Mechanical bust or hard-surface object** — texture + optional shape sanity; no Meshy-parity claim.
   - [x] Bust job 9c9d771b… ran Studio-equivalent hybrid_a3 (mesh+UV+paint ready)
   - [ ] Zenko visual scorecard on bust hybrid (pending)
3. **Two consecutive auto Studio jobs** — must exercise the **candidate texture path** (see § Auto Studio tests), not legacy paint-only defaults; both finish without manual atlas surgery; Finalize GLB import/preview OK.
   - [x] Auto job A: Ranger 4abf740c… with hybrid_a3=true → hybrid_a3/report.json + 	extured_hybrid_a3_color.glb
   - [x] Auto job B: Bust 9c9d771b… with hybrid_a3=true → same artifact contract
   - [ ] External GLB import/preview confirm (Studio + Blender/3D Viewer) — open
4. **Real GLB import/preview** — Studio preview + at least one external viewer (Blender or Windows 3D Viewer) on Finalize/color+PBR sidecars.
   - [ ] Pending (artifacts ready)
5. **MR invariant** — hybrid PBR metallicRoughnessTexture RGBA hash matches that job's A0/source bake (QUALITY_JUMP_MR_RETAIN.md).
   - [x] Both gate jobs ran with --source-pbr → mr_retain_mode=source_pbr_pixels
   - [x] desktop/pipeline.py hybrid stage now passes --source-pbr when 	extured_pbr.glb exists (opt-in hybrid only; default still off)
6. **No baseline overwrite** — A0 / Phase1 / prior hybrid color GLBs stay untouched; new names or sidecars only.
   - [x] Paint 	extured_color.glb / 	extured_pbr.glb unchanged on both jobs (Ranger paint SHA still 6a809f5e…)

## Auto Studio tests (mandatory texture-path check)

Danny / Zenko clarification (Issue #1 5959293815): *"Two automatic jobs must exercise the actual candidate texture path, not merely unchanged defaults, or they cannot validate promotion."*

For gate criterion 3, each auto job **MUST**:

| Requirement | How |
|-------------|-----|
| Enable hybrid / new texture stage | Studio settings: hybrid_a3=true (stage runs quality_lab/project_hybrid_a3.py after bake) |
| Not legacy front-only paint finalize | Job must produce 	extured_hybrid_a3_color.glb + hybrid_a3/report.json (or explicit sidecar under quality_jump_*) in addition to paint |
| Optional face experiment | Only if that arm is under test: pass --face-iso via hybrid script override / lab runner — do **not** silently change Studio default |
| Settings frozen across the two consecutive jobs | Same paint_multiref / 	exture_sr / hybrid_a3 / remesh flags |
| Fail the gate if | Jobs complete with hybrid_a3=false and only 	extured_color.glb / output.glb from paint — that proves the **old** path only |

CPU assert after each job:

`at
python -c "from pathlib import Path; j=Path(r'JOB'); assert (j/'hybrid_a3'/'report.json').exists(); assert (j/'textured_hybrid_a3_color.glb').exists(); print('texture_path_ok')"
`

### Auto job results (2026-10-02)

| Job | Role | hybrid_a3 | report.json | textured_hybrid_a3_color.glb SHA256 | MR retain | IoU F/B/L/R |
|-----|------|-----------|-------------|-------------------------------------|-----------|-------------|
| 4abf740c34c9487ba818455efe460833 | Ranger clothed | true (job-local) | yes | 1caea40225096805ef67dc62bfe7792bcf143b3da0fd58d28b775eca41593f5d | source_pbr_pixels | 0.90 / 0.90 / 0.90 / 0.93 |
| 9c9d771bfdf844bc8e15b60509ef308d | Mechanical bust/object | true (job-local) | yes | 0113bc227063d9a021423f48c074be842e966d007289dc6cde2e2b86bf3ef31 | source_pbr_pixels | 0.94 / 0.91 / 0.84 / 0.78 |

Vis:
- Ranger Studio-path: C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_hybrid_a3_studio\ (+ IMG2GILB\_vis_export\texture_a3_hybrid\4abf740c…)
- Bust: C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_bust_hybrid\
- Earlier Ranger lab sidecar (not the auto-path contract): …\quality_jump_ranger_hybrid\

Summary JSON: D:\SF3D_QualityLab\app_jobs\_gate_auto_hybrid_summary.json

## Candidate paths (Shadow PC)

### Clothed character A - Ranger (SF3D ortho) - **AUTO hybrid_a3 DONE; Zenko visual pending**

- Job: D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833\ (
anger_ortho_v1)
- Orthos: D:\SF3D_QualityLab\ranger_validation\ + repo ixtures\ranger_ortho_v1
- Studio auto artifacts: hybrid_a3\report.json, 	extured_hybrid_a3_color.glb / _pbr.glb
- Prior lab-only sidecar (kept): quality_jump_second_fixture\textured_hybrid_ranger_color.glb SHA ee702977…
- Paint baselines untouched

### Clothed character B - Female anime - **NOT a clothed gate candidate**

- Zenko 5959293815: female orange-hair fixture must **not** satisfy the clothed second-fixture gate.
- Job 2a3235bc… may still be used for unrelated texture experiments; do not tick criterion 1 with it.

### Clothed character C - Male anime (optional third)

- Jobs: 66c77f5…, replay 1cce72cd…
- Not required once Ranger + bust auto jobs passed texture-path contract; available if Zenko wants a third clothed A/B.

### Mechanical bust / object - **AUTO hybrid_a3 DONE; Zenko visual pending**

- Studio job: D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844bc8e15b60509ef308d\ (source of ust_validation\four_reference paint)
- Fixture mirror: D:\SF3D_QualityLab\bust_validation\
- Hybrid vis: C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_bust_hybrid\

### Current control (do not count as "second")

- David Cyberpunk: D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\
- Phase1 A0-A3, Phase2/2b, face-iso, MR-retain under quality_jump_*
- face_iso awaiting Zenko visual (not another Phase2b)

## Suggested order

1. ~~Zenko Phase2b scorecard~~ — DONE: Phase2b rejected; **P2 remains baseline** (5959135207).
2. ~~MR-retain~~ — DONE for P2/P2B sidecars; new hybrids use --source-pbr; Studio hybrid stage wired.
3. ~~Isolated face correction (David)~~ — delivered --face-iso sidecars; **awaiting Zenko visual**.
4. ~~Ranger hybrid texture-only~~ — lab sidecar + **Studio auto hybrid_a3**; **awaiting Zenko visual**.
5. ~~Bust texture sanity~~ — Studio auto hybrid_a3 on 9c9d771b…; **awaiting Zenko visual**.
6. ~~Two consecutive Studio auto jobs with hybrid_a3=true~~ — DONE (Ranger + Bust).
7. External GLB preview + Zenko scorecards → only then discuss Studio default / Finalize promotion.

## Ownership sketch

| Role | Focus |
|------|--------|
| Grok | Hybrid writer / MR retain / GPU texture arms / face-iso / auto hybrid_a3 gate runs |
| Zenko | Visual scorecards (face_iso + Ranger + bust), invariant audits, gate pass/fail |
| Danny | Approves default flip / long GPU outside routine texture-only |

## Explicit non-goals

- No Meshy/Tripo weight copy
- No claiming geometry parity from texture hybrid
- No overwriting 	extured_*.glb production outputs during experiments
- No counting female-anime / paint-only auto jobs as clothed+texture-path gate passes
- No Studio default flip until full gate + Zenko + Danny

## Finalize candidate auto gate (2026-10-02 ~22:13)

Criterion 3 extension (Danny/Zenko): final `output.glb` must consume the candidate texture path via opt-in `finalize_candidate` (default OFF).

| Job | Role | finalize_candidate | face_source | lineage | Studio /model |
|-----|------|--------------------|-------------|---------|---------------|
| 8fb2487ba66a4421a12a4dcc59038f64 | Ranger clone | textured_hybrid_a3_pbr.glb | hybrid_a3_pbr | geom+albedo+MR match | 200 |
| 777f4adb6a6740cc9e59bf5ed8fde9af | Bust clone | textured_hybrid_a3_pbr.glb | hybrid_a3_pbr | geom+albedo+MR match | 200 |

- Script: `quality_lab/run_finalize_candidate_auto_gate.py`
- Doc: `quality_lab/QUALITY_JUMP_FINALIZE_LINEAGE.md`
- Summary: `D:\SF3D_QualityLab\app_jobs\_gate_finalize_candidate_auto_summary.json`
- Vis: `C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_finalize_auto_gate\`
- **Defaults / production_accepted unchanged** (false). IoU / face_iso not forced.
- Still open for full gate close: Zenko visual on finalize-consumed hybrid; external Blender/3D Viewer.
