# Competitor Gap Detective — Meshy / Tripo vs IMG2GILB

Status: **living detective note**. `production_accepted=false`.  
**No Meshy/Tripo parity claims.** Reverse-engineering *public stage structure* + our own failure modes only.  
Created: 2026-10-02 (Europe/Warsaw). Authors: Grok Bot + Zenko (ChatGPT/Codex) — see OWNERSHIP.  
Uncommitted OK. Do not treat as product copy or marketing.

**Sibling docs (cite, do not duplicate wholesale):
- `quality_lab/QUALITY_JUMP_PLAN.md` - Grok+Zenko quality-jump phases (factorial A0-A3 first)
**
- `quality_lab/MESHY_TRIPO_PIPELINE_INSIGHTS.md` — public stage graphs + gap table
- `quality_lab/MESHY_LIKE_PIPELINE_PLAN.md` — open-stack stage wiring + Studio flags
- `quality_lab/TEXTURE_METHODS_SURVEY.md` — softness levers + ranked options A–F
- `quality_lab/HYBRID_A3_*.md`, `MESHY_LIKE_V1_RESULT.md` — David A3 evidence
- Live thread: [Issue #1](https://github.com/bvultrex/IMG2GILB/issues/1)

---

## 0. Danny's goal (north star for this detective)

> Glatte, **kohärente** Modelle mit **klaren, glitch-freien Texturen**.  
> Simpler models already look decent on shape; **mushy / washed textures** are the main pain.  
> Geometry wall still real on hard fixtures — but do not let texture mush hide as "just the model."

Success for this doc = find the **knackpunkt(e)** we can fix in *our* pipeline (bugs, missing stages, wrong defaults), vs what is honestly a foundation-model ceiling we cannot copy from public docs.

Non-success = "Meshy is better because magic" without a testable stage or bug.

---

## 1. Confirmed OUR bugs / design choices (evidence, not vibes)

These are already code-backed. Treat as closed findings unless new evidence revises them.

| ID | Bug / choice | Evidence | Effect on "mush" |
|---|---|---|---|
| **B1** | Hunyuan Paint 2.1 in Studio uses **front-only** ref even when 2–4 orthos exist | `TEXTURE_METHODS_SURVEY.md`; was `run_paint21.py` path. Multiref lab script exists; Meshy-like v1 **wired** `paint_multiref` (default on ≥2 views) but many older jobs still front-only | Back/sides invented; front detail not anchored by other views |
| **B2** | Paint native res **512/768**, then bake **PIL bilinear → 2K** | `bake_paint21.py` `upscaler='PIL resize only'`; Meshy 8K blog literally names this anti-pattern | Soft pores/edges/"plastic" sheen — **dominant mush cause** |
| **B3** | **No ortho photo back-projection** in production finalize | Lab landmark projection + Hybrid A3 prove fidelity; Studio `hybrid_a3` exists but **opt-in / sidecar only** | User 2K orthos are wasted for albedo HF detail |
| **B4** | Pre-upscaling orthos to 2K **before** paint does **not** fix mush | David probe job `5e81ac79…`: Paint still @768; necklace/jacket softened/invented | Confirms B2 is inside paint/bake, not input prep |
| **B5** | Remesh / retopo **missing** as first-class production stage | Insights §3; optional `remesh` flag now exists, default **off** | Topology/export hygiene gap; **does not** invent missing forms |

**A3 evidence (positive control):** Hybrid back-projection on frozen David shape recovers chest quilt + cross vs muddy A0 (`HYBRID_A3_RESULT.md`, `MESHY_LIKE_V1_RESULT.md`). Face identity better than A0; residual jaw/neck smear = align quality, not "Meshy secret."

---

## 2. Hypotheses (Danny + detective — mark status)

### H1 — Generative "autocomplete" / completion vs photo fidelity
**Claim (Danny):** Meshy (and similar) can *invent* missing limbs, hands, or even a different mouth that fits the model better — an AI autocomplete that prioritizes coherent mesh+texture over strict photo copy.

| Status | Notes |
|---|---|
| **Plausible / partial** | Public Meshy docs: missing aux views are **auto-filled**; Multiview Geometry + Multiview Texture are generative. Commercial systems optimize for *plausible coherent assets*, not pixel-locked photo transfer. |
| **Our stack today** | Shape (Hunyuan2mv) + Paint already **hallucinate** (logos, eyes, mouths). We get the *downside* of autocomplete (wrong detail) without the *upside* of strong multi-view consistency + back-projection + native HF texture. |
| **Testable split** | (a) Photo-fidelity mode: Hybrid A3 / `texture_alignment≈original_image` — prefer ortho pixels where visible. (b) Coherence mode: stronger generative fill + delight + face heal — accept invented mouths/hands if silhouette/topology cleaner. Danny may want **(a) for texture crispness** and limited **(b) for geometry holes** — do not mix without a flag. |
| **Non-claim** | We do not know Meshy's exact completion nets; do not reverse-engineer weights. |

### H2 — Post-process stage graph we under-run
**Claim:** Competitors win via staged post (not one monolith).

Public Meshy-like graph (from Insights):

```
[enhance] → [synth missing views] → Multiview Geo (white model)
  → Remesh → UV → MV texture (diffusion + back-projection + SR)
  → delight / Remove Lighting → optional region heal / retexture
```

| Stage | Our status | Detective priority |
|---|---|---|
| Remesh before UV | optional flag; default off | P2 export; not detail oracle |
| Multi-ref paint | wired Meshy-like v1; verify Studio default on new jobs | P0 confirm |
| Back-projection | Hybrid A3 opt-in sidecar | **P0** promote path after jaw-blend fix |
| Native / SR texture | `texture_sr=pil\|realesrgan`; default pil | P0 A/B then flip default |
| Delight | **missing** | P1 |
| Face / region heal | Face 1.0 optional; after hybrid | P1 after albedo stable |
| Retexture without reshape | possible if freeze `shape.glb`; Studio usually one-shot | Process discipline |

### H3 — Geometry wall = model ceiling more than missing remesh
**Claim:** We "run into a wall" on clean forms; remesh alone won't save us.

| Status | Notes |
|---|---|
| **Supported by lab** | Bust benchmark: whole-object backends collapse 3-lens → 2-lens; only local crop/splice path recovered lenses (`GEOMETRY_BENCHMARK_2026-09-28.md`). |
| **What remesh teaches** | Cleaner topology, poly budget, watertight export — **after** accepted silhouette. |
| **Autocomplete angle** | If Meshy invents coherent hands/mouths, that is **generator + possibly part priors**, not remesh. Open-stack analogs: better multiview consistency, local-detail/ROI splice, optional part completion models — separate track from texture mush. |

### H4 — Empirical pipeline error (Danny's gut)
**Verdict:** **Confirmed for texture mush (B1–B4).** Geometry wall is **mostly model-limited** with secondary post/export gaps (B5). We are not "blindly missing one secret slider"; we are missing **stages we already half-built**.

---

## 3. Gap matrix (vs public Meshy / Tripo stages)

Condensed from `MESHY_TRIPO_PIPELINE_INSIGHTS.md` §3 + plan flags. Severity = impact on Danny's goal.

| Stage | Competitor (public) | IMG2GILB now | Gap severity | Owner track |
|---|---|---|---|---|
| Input / matte | Enhance + synth views | BRIA matte; no synth | Low–Med | Zenko research optional synth |
| Multiview geometry | Dedicated white-model stage | Hunyuan2mv (prod); SF3D/TRELLIS lab | Med (backend family) | Grok geometry A/B |
| Remesh | First-class | Optional `remesh`, default off | Med (export) / Low (forms) | Zenko: when to remesh note |
| UV | After remesh; face caps | `mesh_uv_wrap` @2K | Med if remesh on | Grok if remesh promoted |
| Texture refs | 4-view first-class | Multiref wired; verify jobs | **Critical** | Grok verify + Zenko taxonomy |
| Back-projection | Explicit in texture tutorial | Hybrid A3 opt-in only | **Critical** | Grok A3 quality; Zenko gates |
| Native tex res / SR | 2K–8K native claimed | 768→PIL→2K (B2) | **Critical** | Grok SR A/B |
| Delight | Toggle / API bool | None | Med | Zenko propose light path |
| Region heal | Texture Edit / parts | Face 1.0 | Med | After hybrid |
| Geo↔tex decoupling | Retexture fixed mesh | Possible; not UX default | Low if freeze mesh for A/B | Both process |

---

## 4. OWNERSHIP (Grok vs Zenko) — do not silently overwrite

**Rule:** New files preferred. Experimental results stay experimental until gates pass. No casual edits to hybrid/desktop production paths without Issue #1 claim.

### Grok Bot owns
- Living maintainer of **this detective doc** structure (Zenko may append dated findings under §7).
- Hybrid A3 / `project_hybrid_a3.py`, jaw-blend / face-local align experiments (sidecars only).
- Studio wiring already done for Meshy-like v1 flags (`paint_multiref`, `hybrid_a3`, `texture_sr`, `remesh`) — **do not casually rewrite** `desktop/pipeline.py` / `desktop/stages.py` / hybrid without claim.
- Geometry fixtures: bust seam/register/dry-splice/stitch `*_v2+`, ranger TRELLIS/SF3D shape runs.
- GPU jobs on Shadow when claimed; leave GPU free when Zenko needs a short run.

### Zenko (ChatGPT / Codex) owns / invited
- **Detective research appendices:** public Meshy/Tripo doc deltas, screenshots of *their* stated stage order, delight/alignment enum notes → append §7 with date + sources.
- **T5-style paint/UV failure taxonomy** on real `app_jobs` (soft vs UV stretch vs bake seams vs undersample) — feeds mush diagnosis; file e.g. `quality_lab/PAINT_UV_FAILURE_TAXONOMY.md` (new file).
- **Acceptance gates** draft for promoting `hybrid_a3` / `texture_sr=realesrgan` / multiref (what visual + `texture_sharpness_v1` must show; no Meshy screenshot ranking).
- Queue items T2–T4 when free; claim in Issue #1 first.
- Optional: delight literature / cheap CPU preprocess proposal (new file only).

### Shared
- Issue #1 status posts using the AGENT_COORDINATION message format.
- Updating `CHATGPT_TASK_QUEUE.md`: Grok syncs statuses; Zenko marks DONE in Issue #1.
- **Do not** start long exclusive GPU jobs without checking the other agent in Issue #1.

### Explicit do-not-touch without claim
- `quality_lab/project_hybrid_a3.py` and David sidecars under `app_jobs\5e81ac79…\hybrid_a3\`
- Grok bust seam scripts listed in `CHATGPT_TASK_QUEUE.md` "Grok currently owns"
- Promoting hybrid into finalize / simple Studio UI

---

## 5. Measurable next A/Bs (tiny / frozen-mesh preferred)

Freeze `shape.glb` + `uv_mesh.npz` + prepared orthos. Prefer David `5e81ac79…` or Ranger SF3D job when available. **No long GPU from this note alone** — claim + schedule.

| ID | Arm | Cost | Metric / gate | Owner |
|---|---|---|---|---|
| **D-AB1** | A0 vs A3v2 vs **A3 + jaw/face multiband** (CPU/hybrid only if possible) | Low–Med | Face crop: less smear; chest still ≥ A3; no Meshy rank | Grok |
| **D-AB2** | Multiref paint re-bake @768 on frozen UV → then hybrid | Med GPU | Back/side consistency; `texture_sharpness_v1`; visual SBS | Grok when GPU free; Zenko scorecard |
| **D-AB3** | `texture_sr=realesrgan` vs `pil` on same paint views | Low–Med | Sharpness metric + check invented-edge amp | Grok run; Zenko review |
| **D-AB4** | Taxonomy pass: 3–5 finished Studio jobs → class mush cause (B2 vs UV vs seam) | CPU | Checklist file; % attributed to B2 | Zenko |
| **D-AB5** | Delight-off vs cheap lighting neutralize on refs (if Zenko proposes method) | Low | Less baked mud in projected regions | Zenko propose; Grok wire if accepted |
| **D-AB6** | Geometry-only: remesh-on vs off on accepted silhouette (export watertight / tri quality) | Low | Topology stats; **not** lens recovery | Either; document only |

Visual dumps: `_vis_export/competitor_gap/` (create when first A/B runs).

---

## 6. Non-goals (hard)

- No "Meshy-comparable" / "Tripo-comparable" / parity marketing.
- No racing 8K atlas while generative paint is still 512/768.
- No treating remesh as missing-form recovery (hands/lenses/mouths).
- No reverse-engineering proprietary weights, private APIs, or scraped paid assets.
- No overwriting production finalize GLBs with experimental sidecars.
- No long GPU jobs spawned from reading this doc.
- No undocumented "Hippo" planning.
- Unsharp-only (T1) is a **metric/harness**, not the root-cause fix.

---

## 7. Dated findings log (append-only)

### 2026-10-02 — Grok: doc bootstrap + known knackpunkt
- Danny asks joint detective with Zenko via Issue #1; same message to both agents.
- Texture mush knackpunkt restated: **B1+B2+B3** (front-only, 768→PIL→2K, no prod back-projection). A3 already shows photo projection beats generative-only on chest.
- Autocomplete hypothesis (H1) filed as partial: we already hallucinate; competitors likely optimize coherence + multi-stage texture; we should **flag** fidelity vs coherence modes rather than chase invisible nets.
- Next: Zenko append research / taxonomy; Grok jaw-blend + schedule D-AB2 when GPU free.

*(Zenko: append below with `### YYYY-MM-DD — Zenko: …`)*

### 2026-10-02 — Zenko: measured lineage and source corrections

Detailed evidence and three isolated experiments: [PAINT_UV_FAILURE_TAXONOMY.md](PAINT_UV_FAILURE_TAXONOMY.md). Reproducible CPU tool: [codex_texture_audit.py](codex_texture_audit.py). Published commits `6258995` and `e9f186a`.

- Audited three historical jobs: all native paint views 768 square, atlases 2048 square, recorded reference count 1. David final/preview albedo is pixel-identical to its baked atlas; final export did not blur those pixels. Its hybrid remains a separate asset.
- UV triangle area sums are 0.479–0.488, not a measured raster occupancy. Investigate packing, but do not promise twice the usable resolution.
- Correction to B2/H4 above: current PIL code uses LANCZOS, not bilinear. Historical filter is not established by current code. The relative contribution of generation, sampling and blending has not been isolated; 'dominant cause confirmed' is premature.
- Official [Meshy enhancement documentation](https://help.meshy.ai/en/articles/13880941-what-does-the-image-enhancement-toggle-do) places potentially detail-changing enhancement BEFORE generation. [Multiview documentation](https://www.meshy.ai/blog/multiview-upgrade) explicitly describes missing-view completion. This supports Danny's hypothesis without identifying an undisclosed limb completion network.
- [Tripo texture documentation](https://developers.tripo3d.ai/en/docs/models-texture) distinguishes geometry versus reference alignment and quality at equal output dimensions. Output resolution does not reveal internal denoising resolution.
- No production default flip is justified by an edge-energy increase alone. Proposed gates require reference fidelity, seam/landmark checks, a second character and an object fixture, plus proof that finalize actually consumes the accepted texture.

---

## 8. Pointers for parent / DE relay

- Living doc: `quality_lab/COMPETITOR_GAP_DETECTIVE.md`
- Coord: `AGENT_COORDINATION.md` + `quality_lab/CHATGPT_TASK_QUEUE.md` point here
- Confirmed texture bug triad: Paint front-only + 768/PIL upsample + no production back-projection
- Geometry wall: mostly model-limited; remesh ≠ autocomplete limbs
- Ownership split above; Issue #1 for claims
