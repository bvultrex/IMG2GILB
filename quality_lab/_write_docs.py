from pathlib import Path
import json, hashlib
from datetime import datetime

# Face iso result MD
face_sum = json.loads(Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_face_iso\face_iso_summary.json").read_text(encoding="utf-8"))
ranger_sum = json.loads(Path(r"D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833\quality_jump_second_fixture\ranger_hybrid_summary.json").read_text(encoding="utf-8"))

face_md = f"""# QUALITY_JUMP_FACE_ISO_RESULT

Created: 2026-10-02 ~21:05 (Europe/Warsaw)

## Scope
Isolated face correction on Hybrid path per Zenko Phase2b scorecard (5959135207 / 5959293815) + Danny go-ahead:
- **Freeze P2 torso/back** (P2 incidence — NOT Phase2b steeper falloff)
- Coherent face source: landmark gate → project-all OR paint-all (no mid-face eye/mouth mix)
- NEW sidecars only; P2 / P2B / jawblend / A0 untouched
- `production_accepted=false` — no Studio default flip

## Code
`quality_lab/project_hybrid_a3.py` — new `--face-iso` (mirrored `D:\\SF3D_QualityLab\\project_hybrid_a3.py`)

## Artifacts (David `5e81ac79…`)

| Artifact | Path | SHA256 |
|----------|------|--------|
| Color GLB | `…/quality_jump_face_iso/textured_hybrid_face_iso_color.glb` | `{face_sum['sha256']['face_iso_color']}` |
| PBR MR-retain | `…/textured_hybrid_face_iso_pbr_mr_retain.glb` | `{face_sum['sha256']['face_iso_pbr']}` |
| Atlas | `…/hybrid_work/albedo_atlas_hybrid_a3_2K.png` | `{face_sum['sha256']['face_iso_atlas']}` |

Vis: `C:\\Users\\Shadow\\Documents\\ComfyUI\\_vis_export\\quality_jump_face_iso\\`
- `sbs_face.png`, `sbs_chest_cross.png`, `sbs_back_emblem.png`, `sbs_collar_necklace.png`
- `sbs_angle_{{front,back,p35,m35}}_A0_P2_face_iso.png`

## Front micro
- chosen: `{face_sum['front_micro'].get('chosen')}`
- project_face: `{face_sum['front_micro'].get('project_face')}`
- weight_map: `{face_sum['front_micro'].get('weight_map')}`
- landmark residual median/p90: see report micro.landmark_quality

## Laplacian (mean abs) A0 / P2 / face_iso
| Crop | A0 | P2 | face_iso |
|------|-----|-----|----------|
| face | {face_sum['laplacian']['face']['A0']:.2f} | {face_sum['laplacian']['face']['P2']:.2f} | {face_sum['laplacian']['face']['face_iso']:.2f} |
| chest_cross | {face_sum['laplacian']['chest_cross']['A0']:.2f} | {face_sum['laplacian']['chest_cross']['P2']:.2f} | {face_sum['laplacian']['chest_cross']['face_iso']:.2f} |
| back_emblem | {face_sum['laplacian']['back_emblem']['A0']:.2f} | {face_sum['laplacian']['back_emblem']['P2']:.2f} | {face_sum['laplacian']['back_emblem']['face_iso']:.2f} |
| collar_necklace | {face_sum['laplacian']['collar_necklace']['A0']:.2f} | {face_sum['laplacian']['collar_necklace']['P2']:.2f} | {face_sum['laplacian']['collar_necklace']['face_iso']:.2f} |

**Back emblem energy == P2** (logo not weakened by steeper incidence). Chest held with P2.

## Baseline integrity
- P2 `{face_sum['sha256']['p2'][:12]}…` unchanged
- A0 atlas `{face_sum['sha256']['a0a'][:12]}…` unchanged
- P2B `{face_sum['sha256']['p2b'][:12]}…` unchanged

## Gates
- `production_accepted=false`
- Awaiting Zenko visual on face_iso SBS (esp. face identity vs P2 + emblem tip)
- No Meshy parity claim
"""
Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\QUALITY_JUMP_FACE_ISO_RESULT.md").write_text(face_md, encoding="utf-8")
Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\quality_jump_face_iso\QUALITY_JUMP_FACE_ISO_RESULT.md").write_text(face_md, encoding="utf-8")

gate = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\QUALITY_JUMP_SECOND_FIXTURE_GATE.md")
gate.write_text("""# Quality Jump — Second fixture gate (checklist)

**Purpose:** Promote texture/hybrid changes past the single David job only after hard multi-fixture proof.
**Studio defaults:** do not flip until this gate passes.
**production_accepted=false** until all criteria below pass Zenko visual + Danny.

## Gate criteria (all required)

1. **Second clothed character** (not David `5e81ac79…`) — same hybrid settings as accepted David arm; visual paint/A0 vs hybrid SBS (face / jaw / chest / back emblem or equivalent).
2. **Mechanical bust or hard-surface object** — texture + optional shape sanity; no Meshy-parity claim.
3. **Two consecutive auto Studio jobs** — must exercise the **candidate texture path** (see § Auto Studio tests), not legacy paint-only defaults; both finish without manual atlas surgery; Finalize GLB import/preview OK.
4. **Real GLB import/preview** — Studio preview + at least one external viewer (Blender or Windows 3D Viewer) on Finalize/color+PBR sidecars.
5. **MR invariant** — hybrid PBR `metallicRoughnessTexture` RGBA hash matches that job’s A0/source bake (`QUALITY_JUMP_MR_RETAIN.md`).
6. **No baseline overwrite** — A0 / Phase1 / prior hybrid color GLBs stay untouched; new names or sidecars only.

## Auto Studio tests (mandatory texture-path check)

Danny / Zenko clarification (Issue #1 5959293815): *“Two automatic jobs must exercise the actual candidate texture path, not merely unchanged defaults, or they cannot validate promotion.”*

For gate criterion 3, each auto job **MUST**:

| Requirement | How |
|-------------|-----|
| Enable hybrid / new texture stage | Studio settings: `hybrid_a3=true` (stage runs `quality_lab/project_hybrid_a3.py` after bake) |
| Not legacy front-only paint finalize | Job must produce `textured_hybrid_a3_color.glb` + `hybrid_a3/report.json` (or explicit sidecar under `quality_jump_*`) in addition to paint |
| Optional face experiment | Only if that arm is under test: pass `--face-iso` via hybrid script override / lab runner — do **not** silently change Studio default |
| Settings frozen across the two consecutive jobs | Same `paint_multiref` / `texture_sr` / `hybrid_a3` / remesh flags |
| Fail the gate if | Jobs complete with `hybrid_a3=false` and only `textured_color.glb` / `output.glb` from paint — that proves the **old** path only |

Suggested smoke (Shadow):

```bat
REM Example: two consecutive Studio jobs with hybrid_a3 ON (opt-in), textures ON
REM Verify each job dir contains hybrid_a3\\report.json and textured_hybrid_a3_color.glb
```

CPU assert after each job:

```bat
python -c "from pathlib import Path; j=Path(r'JOB'); assert (j/'hybrid_a3'/'report.json').exists(); assert (j/'textured_hybrid_a3_color.glb').exists(); print('texture_path_ok')"
```

## Candidate paths (Shadow PC)

### Clothed character A — Ranger (SF3D ortho) — **IN PROGRESS / first hybrid run done**

- Job: `D:\\SF3D_QualityLab\\app_jobs\\4abf740c34c9487ba818455efe460833\\` (`ranger_ortho_v1`)
- Orthos: `D:\\SF3D_QualityLab\\ranger_validation\\` + repo `fixtures\\ranger_ortho_v1`
- Hybrid sidecar (2026-10-02): `…\\quality_jump_second_fixture\\textured_hybrid_ranger_color.glb`
  - SHA `{ranger_sum['sha256']['hybrid_color']}`
  - Vis: `C:\\Users\\Shadow\\Documents\\ComfyUI\\_vis_export\\quality_jump_ranger_hybrid\\`
  - All four views projected (IoU≥0.89); paint baselines untouched
- Still needed for full gate: Zenko visual scorecard + second auto Studio job with `hybrid_a3=true` + bust + external GLB preview

### Clothed character B — Female anime — **NOT a clothed gate candidate**

- Zenko 5959293815: female orange-hair fixture must **not** satisfy the clothed second-fixture gate.
- Job `2a3235bc…` may still be used for unrelated texture experiments; do not tick criterion 1 with it.

### Clothed character C — Male anime (optional third)

- Jobs: `b66c77f5…`, replay `1cce72cd…`
- Verify distinct character (not David replay) before counting.

### Mechanical bust / object

- `D:\\SF3D_QualityLab\\bust_validation\\`
- Prefer texture A/B on existing textured bust; full shape re-run only with explicit approval.

### Current control (do not count as “second”)

- David Cyberpunk: `D:\\SF3D_QualityLab\\app_jobs\\5e81ac7963f84af2a403fb659cea7513\\`
- Phase1 A0–A3, Phase2/2b, face-iso, MR-retain under `quality_jump_*`

## Suggested order

1. ~~Zenko Phase2b scorecard~~ — DONE: Phase2b rejected; **P2 remains baseline** (5959135207).
2. ~~MR-retain~~ — DONE for P2/P2B sidecars; new hybrids use `--source-pbr`.
3. ~~Isolated face correction (David)~~ — delivered `--face-iso` sidecars; awaiting Zenko visual.
4. ~~Ranger hybrid texture-only~~ — first run done (see above); Zenko scorecard next.
5. Bust texture sanity from `bust_validation`.
6. **Two consecutive Studio auto jobs with `hybrid_a3=true`** + external GLB preview.
7. Only then discuss Studio default / Finalize promotion.

## Ownership sketch

| Role | Focus |
|------|--------|
| Grok | Hybrid writer / MR retain / GPU texture arms / face-iso |
| Zenko | Visual scorecards, invariant audits, gate pass/fail |
| Danny | Approves default flip / long GPU outside routine texture-only |

## Explicit non-goals

- No Meshy/Tripo weight copy
- No claiming geometry parity from texture hybrid
- No overwriting `textured_*.glb` production outputs during experiments
- No counting female-anime / paint-only auto jobs as clothed+texture-path gate passes
""", encoding="utf-8")

# Ranger short result
ranger_md = f"""# QUALITY_JUMP_RANGER_HYBRID_RESULT

Created: 2026-10-02 ~21:10 (Europe/Warsaw)

## Scope
Second clothed fixture through **new texture/hybrid path** (Paint fill + ortho projection), not legacy front-only paint finalize.

## Job
`D:\\SF3D_QualityLab\\app_jobs\\4abf740c34c9487ba818455efe460833` (ranger_ortho_v1)

## Artifacts
| Artifact | SHA256 |
|----------|--------|
| Hybrid color | `{ranger_sum['sha256']['hybrid_color']}` |
| Hybrid PBR MR-retain | `{ranger_sum['sha256']['hybrid_pbr_mr_retain']}` |
| Paint color (untouched) | `{ranger_sum['sha256']['paint_color_untouched']}` |

Paths under `…\\quality_jump_second_fixture\\`
Vis: `C:\\Users\\Shadow\\Documents\\ComfyUI\\_vis_export\\quality_jump_ranger_hybrid\\`

## Views
All four orthos projected (no skip): front/back/left/right IoU ≈ 0.90–0.93.

## Laplacian paint → hybrid
| Crop | paint | hybrid |
|------|-------|--------|
| face | {ranger_sum['laplacian']['face']['paint']:.2f} | {ranger_sum['laplacian']['face']['hybrid']:.2f} |
| chest | {ranger_sum['laplacian']['chest']['paint']:.2f} | {ranger_sum['laplacian']['chest']['hybrid']:.2f} |
| back_logo | {ranger_sum['laplacian']['back_logo']['paint']:.2f} | {ranger_sum['laplacian']['back_logo']['hybrid']:.2f} |

## Gates
- `production_accepted=false`
- Studio defaults unchanged
- No Meshy parity claim
- Gate criterion 1 (Ranger hybrid) ready for Zenko visual; auto Studio×2 with `hybrid_a3=true` still open
"""
Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\QUALITY_JUMP_RANGER_HYBRID_RESULT.md").write_text(ranger_md, encoding="utf-8")
Path(r"D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833\quality_jump_second_fixture\QUALITY_JUMP_RANGER_HYBRID_RESULT.md").write_text(ranger_md, encoding="utf-8")
print("docs written")
