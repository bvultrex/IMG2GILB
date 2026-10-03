# Meshy-like pipeline plan (open stack)

Status: implementation plan + wiring guide. `production_accepted=false`.  
**No Meshy/Tripo parity marketing claims.** We mirror their *public stage structure* with our tools only.  
Date: 2026-09-28 (Europe/Warsaw). Author: Grok Bot for Danny.  
Uncommitted. See also: `MESHY_TRIPO_PIPELINE_INSIGHTS.md`, `TEXTURE_METHODS_SURVEY.md`, `HYBRID_A3_*.md`.

---

## 0. Intent

Danny: A3 looks much better → "copy the Meshy pipeline" meaning **stage order and knobs**, not their models or marketing.

We already own pieces of that graph. This plan maps **ours vs Meshy public stages**, names Studio settings, sets safe defaults, and lists non-goals.

---

## 1. Stage map (Meshy-inspired → IMG2GILB open stack)

| # | Meshy public stage (docs) | Our tool | Status | Studio setting |
|---|---|---|---|---|
| 0 | Image enhance / matte | BRIA prepare | keep | always when textures |
| 1 | Multiview geometry → white model | Hunyuan3D-2mv (`stages.shape`) | **keep** | `textures` implies shape |
| 2 | Remesh / topology cleanup (export hygiene; does **not** invent forms) | Optional pymeshlab cleanup before UV | **new flag** | `remesh=true` (default **false**) |
| 3 | Unwrap UV | `mesh_uv_wrap` + 2K control renders | keep; must run **after** remesh when enabled | automatic |
| 4 | Multiview AI texturing | Hunyuan Paint 2.1 | wire **multi-ref** preferred path | `paint_multiref=true` (default **true** when ≥2 prepared views; safe) |
| 5 | Back-projection | `project_hybrid_a3.py` after bake | wired; opt-in | `hybrid_a3=true` (default **false** until face landmark align better) |
| 6 | Super-resolution | Real-ESRGAN on paint views before bake (replace PIL-only) | wire | `texture_sr=realesrgan\|pil` (default **`pil`** until A/B; prefer realesrgan in plan once verified) |
| 7 | Optional face / region heal | Face 1.0 after hybrid albedo | keep; after hybrid when both on | `face=true` |

### Target order when all flags on

```
prepare → shape → [remesh] → uv → paint(multiref?) → bake(texture_sr) → [hybrid_a3] → [face] → finalize
```

Geometry and texture remain separately gateable: freeze `shape.glb` + `uv_mesh.npz` for texture A/B (David job already does).

---

## 2. Settings / flags (names for `project.json` settings)

| Key | Type | Default (safe) | Proposed staged default | Effect |
|---|---|---|---|---|
| `paint_multiref` | bool | **true** if ≥2 prepared views else false | true | Prefer `run_paint_multiref.py` over front-only `run_paint21.py` |
| `hybrid_a3` | bool | **false** | false until face micro-align validated; then opt-in | After bake: ortho back-projection sidecar GLBs |
| `texture_sr` | `"pil"` \| `"realesrgan"` | **`pil`** | switch to `realesrgan` after David A/B | Bake upsample path |
| `remesh` | bool | **false** | false | Light topology cleanup before UV (export quality only) |
| `face` | bool | existing UI | after hybrid when hybrid on | Face 1.0 on albedo |
| `quality` | fast\|standard | existing | standard → Paint@768 | unchanged |

Fingerprint must include new scripts when flags change (pipeline hash already covers `pipeline.py` + paint/bake).

### Sidecar vs finalize

- `hybrid_a3` writes **sidecars only** (`textured_hybrid_a3_*.glb`, `hybrid_a3/`). Finalize still uses bake/face path until Danny promotes.
- Do not overwrite `textured_*.glb` / `output.glb` from hybrid.

---

## 3. Defaults rationale (staged)

1. **Multiref ON (safe):** lab script exists; improves back/side consistency; no finalize coupling. Prefer when 2–4 orthos present.
2. **Hybrid A3 OFF until face align:** chest/insignia already win; residual face forehead smudge needs micro-align / face-region limit before default-on.
3. **texture_sr=pil initially:** keep A0 comparable; flip to realesrgan after one frozen-mesh A/B.
4. **remesh OFF:** shape already decimates to `triangles`; remesh is export hygiene, not detail recovery (bust lens lesson).

---

## 4. Non-goals (explicit)

- No "Meshy-comparable" / "Tripo-comparable" / parity marketing.
- No racing 8K atlas while generative paint is still 512/768.
- Remesh does **not** restore missing geometry (lenses, fingers, hair volume).
- No cloud Meshy/Tripo API dependency.
- No promoting hybrid/ESRGAN/multiref into simple Studio UI until acceptance gates pass.
- No overwriting production GLBs with experimental sidecars.
- GPU jobs only on claimed fixtures; leave uncommitted until Danny asks.

---

## 5. Implementation checklist (this pass)

| ID | Task | Done? |
|---|---|---|
| A | This plan file | yes |
| B1 | Wire `paint_multiref` in `desktop/pipeline.py` | this pass |
| B2 | Wire `texture_sr` into bake path | this pass |
| B3 | Optional `remesh` before UV (light pymeshlab cleanup) | this pass if cheap |
| B4 | Keep `hybrid_a3` opt-in (already wired) | yes |
| C1 | Improve A3 front align (ECC / feature / face-region) | this pass |
| C2 | Re-run David texture-only A/B → `_vis_export\meshy_like_v1\` | this pass |
| D | Optional multi-ref paint re-bake on frozen shape+UV | if GPU time |
| E | Update `AGENT_COORDINATION.md` + Issue#1 draft note | this pass |

---

## 6. David job A/B protocol (texture-only)

- Job: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\`
- Freeze: `shape.glb`, `controls/uv_mesh.npz`, prepared orthos.
- Arms:
  - **A0** — existing Paint@768 → PIL bake (current `textured_*` / atlas)
  - **A3** — prior hybrid (front/back project; sides skipped)
  - **A3v2 / meshy_like_v1** — improved front micro-align + same skip policy for low-IoU sides
  - **A2** (optional) — multiref paint re-bake on frozen UV, then hybrid
- Vis: `IMG2GILB\_vis_export\meshy_like_v1\`
- Metrics: visual SBS (face/chest/full); report.json IoU + align mode; no Meshy screenshot ranking.

---

## 7. German-friendly one-liners for parent

- Wir kopieren die **öffentliche Stufenstruktur** (Remesh→UV→Multi-Ref-Paint→Back-Projection→SR), nicht Meshy-Gewichte.
- Keine Parity-Claims.
- Multiref bevorzugt; Hybrid A3 weiter opt-in bis Face-Align besser; ESRGAN als `texture_sr` schaltbar.
- Remesh nur Topologie/Export — erfindet keine fehlenden Formen.
