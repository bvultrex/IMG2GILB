# ChatGPT task queue (Grok-maintained)

Live handoffs still go in [Issue #1](https://github.com/bvultrex/IMG2GILB/issues/1).
This file is the durable backlog so ChatGPT can pick work without waiting for a chat ping.

Rules:

- Claim with `WORKING ON` in Issue #1 before editing overlapping areas.
- New files preferred over editing Grok-owned `*_v2` / `*_v5` / `stitch_*` / `ranger_trellis_*`.
- `production_accepted=false` until stated gates pass; no Meshy-parity claims.
- Mark items `DONE` / `RELEASED` in Issue #1 and update status here when finished.

---

## ACTIVE (do next)

### T1 — Texture sharpness diagnostic + controlled refine

**Status:** ASSIGNED (Issue #1, Grok comment after Auto-ROI general accept)

**Goal:** Measure and optionally improve texture sharpness on existing painted jobs without hiding failed geometry.

**Deliverables:**

1. `quality_lab/texture_sharpness_v1.py` (+ `Run_*.bat`)
2. Reversible refine experiment (keep originals)
3. `quality_lab/TEXTURE_SHARPNESS_V1_RESULT.md` + staged PNGs under `_vis_export/texture_v1/`
4. Notes tying to `LOCAL_DETAIL_ACCEPTANCE_GATES.md` §6

**Inputs:** existing SF3D app_jobs (e.g. `b66c77f5fb844cefae8ec485d8bab8af`); ranger SF3D only if Grok job finished.

**GPU:** Prefer light analysis; avoid long exclusive GPU runs while Grok SF3D 4-view ranger is active.

---

## BACKLOG (pick after T1, in order unless blocked)

### T2 — Freeze ranger Auto-ROI evaluation crop

After Danny qualitatively reviews `auto_roi_general_v1_fullbody_overlay.png`, document a **human-reviewed evaluation-only** reference crop for ranger fullbody (not used as inference input). Update protocol + RESULT; keep provisional → frozen gate language clear.

### T3 — Auto-ROI `object` mode third fixture

Add one non-character / object fixture (or reuse a small lab object if present), run `auto_roi_general_v1.py --mode object`, define provisional gates, prove no bust/fullbody regression.

### T4 — Studio mode routing sketch

Short design note: how Studio should choose `bust | fullbody | object` (and later texture/face refine) from inputs without exposing backend knobs. File e.g. `quality_lab/STUDIO_MODE_ROUTING_V1.md`. No UI promotion.

### T5 — Paint/UV failure taxonomy

From real app_jobs: classify soft/blurry textures vs UV stretch vs bake seams vs undersampled maps. Checklist for operators/agents. Feeds T1 metrics.

### T6 — Bust seam collaboration (only if Grok asks)

Alternative cut/bridge strategy as **new** files only. Do not weaken stitch gates. Do not edit Grok dry-splice/stitch scripts unless reservation released.

---

## DONE (recent)

| ID | Task | Result commit / note |
|----|------|----------------------|
| D1 | Auto-ROI bust v1/v2 + acceptance gates | v2 pass; v1 rejected control |
| D2 | Auto-ROI → densified registration gap (v3) | `baab4b7` interchangeable on bust |
| D3 | Second-fixture Auto-ROI general (ranger) | `51fc81b` provisional pass + bust no-regression |

---

## Grok currently owns (do not edit)

- Bust seam/register/dry-splice/stitch: `register_bust_detail_v2.py`, `dry_splice_bust_detail_v{2,3,4,5}*.py`, `stitch_bust_detail_v1.py`, `register_bust_detail_v3_autoroiv2.py`
- Ranger TRELLIS / SF3D shape runs under `ranger_validation/` and `quality_lab/ranger_*`
- SF3D Studio 4-view ranger job (in progress as of 2026-09-28)

## ChatGPT currently owns when claimed

- `auto_roi_*`, `AUTO_ROI_*`, `LOCAL_DETAIL_ACCEPTANCE_GATES.md` (coordinate before large rewrites)
- New `texture_sharpness_*` / Studio routing docs from this queue
