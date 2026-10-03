# Meshy / Tripo pipeline insights vs IMG2GILB

Status: research note only. `production_accepted=false`.  
**No Meshy/Tripo parity marketing claims.** Honest gap analysis of *learnable public structure*.  
Date: 2026-09-28 (Europe/Warsaw). Author: Grok Bot research pass for Danny.  
Uncommitted lab note. Do not treat as product copy.

Sources (public only): Meshy docs/blogs (Multiview Upgrade, Image-to-3D guide, Remesh/UV/AI Texturing APIs, 8K Texture blog, Meshy 7 ~Aug 2026); Tripo OpenAPI v3 (multiview-to-model, models/texture, mesh/decimate); TripoSR research page; existing IMG2GILB lab notes (`TEXTURE_METHODS_SURVEY.md`, `GEOMETRY_BENCHMARK_2026-09-28.md`, `run_paint_multiref.py`).

---

## 0. Bottom line for Danny

Yes — we can still learn from Meshy/Tripo **pipeline structure**, even without their weights.  
The empirical gap Danny sees (washed textures + geometry quality wall) is **not mysterious**:

| Symptom | Mostly our bug / settings? | Mostly model ceiling? |
|---|---|---|
| Washed / soft textures | **Yes — dominant.** Production Paint @512/768 + PIL bilinear upsample to 2K; front-only generative paint; **no ortho photo projection** in Studio.Job | Residual: Paint invents HF detail; even native 2K generative paint will not match photo-pixel fidelity without projection or stronger image conditioning |
| Geometry quality wall (bust ~4 mm local detail, missing lenses, TRELLIS holes) | Partly settings/post: no remesh/retopo stage; backend choice (Hunyuan2mv vs SF3D vs TRELLIS) | **Mostly model-limited** for fine local forms on whole-object runs — lab bust benchmark already showed whole-object backends simplify 3-lens → 2-lens; remesh cannot invent missing geometry |

**Do not claim** "we can match Meshy/Tripo." Claim: "their public stage graph shows several controls we under-use; several are already half-built in quality_lab."

---

## 1. What Meshy publicly does (Meshy 7 / 2026)

Staged, not monolithic. Public docs describe **geometry and texture as separate products**, with remesh/UV as explicit bridges.

### 1.1 Stage graph (reconstructed from docs)

```
input image(s)
  → [optional] Image Enhancement
  → [optional] Generate Multi-view (synth L/B/R if missing)
  → Multiview Geometry  →  untextured "white model"
  → Remesh (target polycount / quad|tri / adaptive)   ← destroys UVs
  → Unwrap UV  (API hard ceiling ~40k faces → remesh first)
  → Multiview / AI Texturing:
       UV + multi-view diffusion + back-projection + super-resolution
       native texture res 2K / 4K / 8K (Meshy claims 8K is native, not upscale)
       delight / Remove Lighting
       optional PBR (albedo, normal, metallic, roughness)
  → Retexture-only / Texture Edit (region heal) without re-running geometry
```

Key public statements:

- **Multiview Geometry ≠ Multiview Texture** — two stages; texture can run on any imported untextured mesh.
- Multiview inputs: Main + Left + Back + Right; missing aux views auto-filled (completion / inference).
- Texture tutorial explicitly lists: **UV unwrapping → multi-view diffusion → back-projection → super-resolution**.
- Remesh is a first-class topology product (API `target_polycount` 100–300k; quad/triangle; adaptive modes). Docs warn: remesh invalidates UVs → unwrap + retexture after.
- UV Unwrap API: ≤40k faces; remesh first if denser.
- 8K blog: explicitly contrasts **"native Multiview Diffusion @ 8192" vs upscaler-from-low-res** (pores/scratches smear when upscaled). This is the closest public analog to our washed-texture failure mode.
- Multiview Texture (new): base color at native 2K/4K/8K; **PBR not yet** on that multiview texture path (standard AI Texturing still offers PBR + delight).

### 1.2 What we can *test*, not their secret sauce

Learnable / testable:

1. Separate geometry approval before spending texture budget.
2. Remesh → UV → texture order (topology quality before paint).
3. Multi-view refs for **both** shape and texture.
4. Back-projection of view colors into UV (hybrid of generative + projected).
5. Native high-res texture generation vs post-hoc upsample.
6. Explicit delight before albedo bake.
7. Retexture without reshaping.

Not learnable from public docs (do not reverse-engineer / claim):

- Exact diffusion architecture, training data, proprietary consistency losses.
- Internal face-refinement nets beyond marketing "Texture Edit / heal".
- Why their remesh looks good on a given asset class.

---

## 2. What Tripo publicly does (API v3 / Studio)

Also staged. Commercial Tripo ≠ open TripoSR.

### 2.1 Stage graph (API-facing)

```
image | text | multiview images
  → [optional] image-to-multiview / edit-multiview
  → generation (image-to-model | multiview-to-model | text-to-model)
       geometry_quality: standard | detailed (Ultra)
       texture on/off; pbr on/off
       export_uv on/off (UV can be deferred to texturing)
  → POST /v3/models/texture  (regenerate / retexture)
       texture_quality: fast | standard | detailed | extreme (8K)
       texture_alignment: original_image | geometry
       texture_prompt: text | single image | images[front,left,back,right]
       delight (v3.5+ texture model)
  → POST /v3/mesh/decimate  (retopo)
       v2.0 smart retopology | v1.0 basic decimation
       optional bake textures onto low-poly
  → mesh/complete, mesh/segment, convert, animate…
```

Key public knobs:

- **Multiview-to-model** takes front(+left/back/right); improves geometry *and* texture coverage.
- Texture endpoint accepts **exactly 4** guidance images `[front, left, back, right]` — first-class multi-ref texture.
- `texture_alignment=original_image` prioritizes photo color fidelity; `geometry` prioritizes mesh consistency. Direct A/B idea for us.
- `delight` strips baked lighting from reference before texturing (v3.5-20260815).
- `extreme` = 8K textures (extra credits).
- Retopology is separate from generation; smart retopo rebuilds topology rather than only dumping faces.

### 2.2 TripoSR / "Hippo"

- **TripoSR**: open Stability/Tripo fast LRM-style single-image recon (~0.5 s draft on A100). Useful as a **baseline draft recon**, not a stand-in for commercial Tripo quality or for our production character/bust path.
- **Hippo**: no solid public pipeline docs found in this pass (name may be internal/research/marketing adjacent). Do not plan experiments around undocumented Hippo claims. Prefer Tripo API docs + TripoSR paper/code only.

---

## 3. Stage-by-stage vs IMG2GILB (verified Studio path)

Studio: `prepare → shape → uv → paint → bake → [face] → finalize`  
(see `TEXTURE_METHODS_SURVEY.md`).

| Stage | Meshy (public) | Tripo (public) | IMG2GILB today | Divergence severity |
|---|---|---|---|---|
| Input prep | Enhancement; multi-view synth | image-to-multiview / edit | BRIA matting per view | Low — we already matte; synth views optional |
| Geometry | Multiview Geometry (Meshy 7); white model first | multiview-to-model; geometry_quality Ultra | Hunyuan3D-2mv; TRELLIS/SF3D/TripoSG lab only | Medium — backend family differs; we *do* have multi-view shape inputs |
| Remesh / retopo | First-class Remesh before UV/texture | mesh/decimate smart/basic | **Missing in production** | **High for topology/watertight export**; low for missing-form recovery |
| UV | Explicit Unwrap after remesh; 40k ceiling | export_uv or unwrap at texture | mesh_uv_wrap + 2K control renders | Medium — we UV; we don't remesh-then-reUV |
| Texture refs | Main+L/B/R multiview texture | 1 image or **4** ordered images | **Paint 2.1 front-only** in Studio | **Critical** |
| Texture method | MV diffusion + **back-projection** + SR | generative texture + alignment + delight | Generative Paint only; **no ortho projection in prod** | **Critical** |
| Native tex res | 2K/4K/**8K native** (claimed) | detailed / **extreme 8K** | Paint **512/768** → PIL → 2K atlas | **Critical** (matches Meshy's "fake upscale" failure description) |
| Delight | Remove Lighting toggle | `delight` bool | None in paint/bake | Medium |
| Face / local | Texture Edit / region heal | part segmentation + part texture | Optional Face 1.0 warp (albedo) | Medium — different mechanism |
| Geometry↔texture coupling | Retexture without reshape | texture endpoint on fixed mesh | Can re-paint if mesh frozen; Studio.Job usually one-shot | Low if we freeze shape.glb for A/B |

### 3.1 Softness levers we already documented

From lab (not speculation):

1. Native diffusion 512/768; bake PIL bilinear → 2048 (`upscaler='PIL resize only'`).
2. Studio paint uses one ref even when 2–4 orthos exist; `run_paint_multiref.py` exists but **not wired**.
3. Paint invents appearance; does not project user orthos. Landmark projection in lab was **best fidelity gain**.
4. Real-ESRGAN helps edges but amplifies invented detail.

---

## 4. Washed texture: bug vs ceiling

### Verdict

**Mostly a known pipeline bug / design choice**, not a mysterious Meshy-only secret.

Evidence:

- Meshy's own 8K marketing defines our failure mode: generate low → upscale → soft pores/edges/"plastic" sheen.
- Our production path literally: Paint@768 → PIL upsample → 2K.
- Lab already proved sharper/crisper paths: multi-ref Paint, ESRGAN, especially **ortho reference projection**.

### What remains model ceiling

- Even at native higher res, a generative painter will hallucinate logos/text/eyes unless anchored by photo projection or strong multi-image conditioning.
- Closing 100% of the visual gap to commercial Meshy/Tripo albedo without their models is **not** a promised outcome. Closing the **washed** look relative to *our own* 2K orthos is.

### Practical split

| Fix class | Expected effect on "washed" | Cost |
|---|---|---|
| Always Paint@768 (no 512) | Small | Config |
| Multi-ref Paint (wire lab script) | Moderate consistency (back/sides) | Small Studio change |
| Real-ESRGAN before bake | Moderate sharpness; risk invent sharpen | Small |
| **Hybrid Paint fill + ortho projection** | **Largest fidelity** (lab already) | Medium (auto-align) |
| Native Paint >768 | Unknown / likely blocked by Hunyuan Paint 2.1 design (~512/768 public) | High / maybe impossible without different texture model |
| Delight pass on refs or atlas | Cleaner relight; less "baked mud" | Small–medium |

---

## 5. Geometry wall: model vs settings/post

### Verdict

**Mostly model-limited for fine local structure**; settings/post matter for cleanliness, not for inventing missing forms.

Lab (`GEOMETRY_BENCHMARK_2026-09-28.md`):

- Whole-object Hunyuan2mv / Shape2.1 / TRELLIS.2 / TripoSG all collapsed bust's three lenses → two.
- TRELLIS **head crop** recovered asymmetric 3-lens arrangement (diagnostic only; rough/open mesh).
- ~4 mm bust local-detail seam stuck — local splice/registration work ongoing; not a remesh slider fix.

What Meshy/Tripo remesh/retopo **can teach**:

- Remesh **after** a good high-detail draft improves topology / poly budget / watertight export (SF3D already better watertight on some fixtures).
- Remesh **cannot** restore forms the generator never produced — same as our experience.

What to A/B for geometry (honest):

1. Shape backend by fixture class (Hunyuan2mv vs SF3D multiview vs TRELLIS) — already started.
2. Multiview completeness / consistency of side refs (bad sides → bad structure).
3. Optional remesh/decimate **after** accepted silhouette (export hygiene), not as fidelity magic.
4. Localized crop reconstruction (TRELLIS head-probe class) + careful splice — only path that showed missing-lens recovery so far.
5. Do **not** expect Meshy-like remesh alone to beat the wall.

---

## 6. Prioritized empirical experiments (no parity claims)

Freeze `shape.glb` + `uv_mesh.npz` per fixture when testing texture. Do **not** start GPU jobs from this note.

### P0 — Texture (close washed gap vs our orthos)

| ID | Experiment | Why (Meshy/Tripo analog) | Lab status |
|---|---|---|---|
| T-P0a | Wire multi-ref Paint 2.1 into Studio (front+back[+sides]) @768 | Tripo `images[4]`; Meshy Multiview Texture | `run_paint_multiref.py` ready |
| T-P0b | Hybrid: Paint fill + **automatic** ortho projection blend (visibility/incidence) | Meshy "back-projection"; Tripo `texture_alignment=original_image` | Manual landmark projection proven; auto-align is the gap |
| T-P0c | Replace PIL bake upsample with Real-ESRGAN (or skip upsample if painting higher) | Meshy SR stage; their anti-pattern is our PIL path | ESRGAN already tested |

Acceptance: Ranger/insignia/face crops sharper vs A0 baseline; no claim vs Meshy screenshots.

### P1 — Texture controls

| ID | Experiment | Why |
|---|---|---|
| T-P1a | Delight / lighting-neutralize refs before Paint or after projection | Meshy Remove Lighting; Tripo `delight` |
| T-P1b | `texture_alignment`-style blend weight: favor photo vs favor geometry in overlap | Tripo alignment enum |
| T-P1c | Face 1.0 only after hybrid albedo stable | Avoid sharpening wrong geometry |

### P2 — Geometry (honest, fixture-scoped)

| ID | Experiment | Why |
|---|---|---|
| G-P2a | Fixture-class shape A/B: Hunyuan2mv vs SF3D-4view vs TRELLIS (holes noted) | Backend ceiling mapping |
| G-P2b | Post-accept remesh/decimate for topology only (quad/tri target poly) | Meshy Remesh; Tripo decimate — export hygiene |
| G-P2c | Continue local-detail / Auto-ROI splice (bust) | Only lab path that recovered missing lenses |
| G-P2d | Multiview-ref quality audit (side consistency) before blaming backend | Both vendors stress multi-view coverage |

### Explicit non-goals

- Marketing "Meshy-comparable" / "Tripo-comparable" quality.
- Racing 8K atlas for its own sake while albedo is still generative@768.
- Treating unsharp (T1) or speculative MR maps as root-cause fixes.
- Building on undocumented "Hippo" claims.
- GPU jobs from this research pass.

---

## 7. What we already know is *our* bug

1. **Production texture softness**: Paint@768 (or 512) + PIL→2K; front-only refs; no projection. Documented in `TEXTURE_METHODS_SURVEY.md`.
2. **Unused lab assets**: `run_paint_multiref.py`, `project_references.py`, Real-ESRGAN experiments, Face 1.0 — not the Studio.Job default path.
3. **Geometry wall misattribution risk**: remesh/UV tweaks will not fix missing bust lenses; that is generator + (maybe) localized recon territory.

---

## 8. What we can still learn (summary)

From Meshy/Tripo **public stage structure**, not from their black boxes:

1. Treat geometry and texture as separately gateable stages.
2. Multi-view for texture is as important as multi-view for shape.
3. Back-projection / photo-alignment is a first-class texture ingredient alongside generative fill.
4. Native high-res texture ≠ upscale; our bake path is the anti-pattern they advertise against.
5. Remesh → UV → texture order improves topology/seams; it is not a detail oracle.
6. Delight and texture-alignment knobs are cheap A/B dimensions.
7. Retexture-without-reshape enables fair texture ablations (freeze mesh).

Gaps that remain honest:

- Their foundation models (Meshy 7, Tripo v3.1 geometry + v3.5 texture) are not ours.
- Native 4K/8K generative texture is outside Hunyuan Paint 2.1's public resolution envelope.
- Whole-object fine geometry on hard fixtures remains an open research/engineering problem for open stacks; commercial results may still be better for reasons we cannot copy from docs alone.

---

## 9. Suggested parent summary (DE-ready bullets)

- Danny's Verdacht (empirischer Pipeline-Fehler) ist **teilweise bestätigt**: Texture-Wash ist vor allem **unser** Paint@768 + PIL-Upscale + Front-only + keine Ortho-Projektion — kein reines Modell-Schicksal.
- Geometrie-Wand ist **überwiegend modellbegrenzt** (Bust-Benchmark); Remesh wie bei Meshy/Tripo hilft Topologie/Export, nicht fehlende Formen.
- Meshy/Tripo lehren vor allem **Stufenstruktur**: Multi-Ref Texture, Back-Projection, natives High-Res statt Upscale, Delight, Remesh→UV→Texture, Retexture ohne Shape-Reset.
- Nächste Experiments (ohne Parity-Claims): multi-ref Paint verdrahten → Hybrid-Projektion → ESRGAN-Bake; Shape-A/B + lokales Detail getrennt halten.
- Keine GPU-Jobs aus diesem Note; Datei uncommitted unter `quality_lab/MESHY_TRIPO_PIPELINE_INSIGHTS.md`.

---

## 10. References (URLs)

- https://www.meshy.ai/blog/multiview-upgrade
- https://www.meshy.ai/tutorials/image-to-3d-model-complete-guide
- https://www.meshy.ai/blog/8k-texture
- https://docs.meshy.ai/en/webapp/guides/3d-model/ai-texturing
- https://docs.meshy.ai/en/webapp/guides/3d-model/unwrap-uv
- https://docs.meshy.ai/en/api/remesh
- https://docs.meshy.ai/en/api/uv-unwrap
- https://developers.tripo3d.ai/en/docs
- https://developers.tripo3d.ai/en/docs/models-texture
- https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard
- https://developers.tripo3d.ai/en/docs/mesh-decimate
- https://www.tripo3d.ai/research/triposr

Local: `quality_lab/TEXTURE_METHODS_SURVEY.md`, `quality_lab/GEOMETRY_BENCHMARK_2026-09-28.md`, `quality_lab/run_paint_multiref.py`.
