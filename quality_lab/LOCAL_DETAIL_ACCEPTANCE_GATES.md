# Local Detail ROI and Acceptance Gates

Status: **experimental quality-lab policy**, not a production feature.

This document defines when a locally reconstructed detail region may advance from
ROI proposal to registration, dry splice, topology stitching, and finally UI
consideration.  It is intentionally conservative because the current mechanical
bust baseline is already non-watertight and because a successful head-only
reconstruction does not prove a safe whole-object replacement.

## 1. Automatic ROI proposal gate

Reference fixture crop used only for evaluation:

`[0.32, 0.015, 0.675, 0.36]` in normalized `x0,y0,x1,y1` image coordinates.

`auto_roi_bust_v1.py` proposes a hood/lens ROI from the prepared front image's
BRIA alpha silhouette.  The known crop is not read by the inference logic.

For the mechanical-bust fixture the proposal may advance only if all are true:

- bounding-box IoU against the known fixture crop: **>= 0.60**
- known-crop coverage by the proposal: **>= 0.75**
- minimum IoU of proposals at alpha thresholds 0.35 / 0.50 / 0.65 against the
  threshold-0.50 proposal: **>= 0.90**
- overlay review shows the ROI covers the hood/lens assembly without swallowing
  most of the shoulders/robe

These thresholds validate only this fixture.  A second unrelated fixture is
required before any generic automatic-ROI claim.

## 2. Registration gate

A local reconstruction may advance to splice-readiness tests only if:

- held-out support-surface p90 distance: **<= 3.0 mm**
- held-out median distance: **<= 2.0 mm**
- optimizer reports successful convergence
- scale, rotation, and translation are not pinned to configured parameter bounds
- the protected semantic detail remains visibly intact

The Grok v2 dense-surface experiment reports held-out p90 **2.1232 mm**, so the
registration-distance gate can pass for this fixture.  That does not authorize
stitching by itself.

## 3. Whole-bust visual gate

Before topology mutation, clay/contrast renders of the disconnected dry splice
must show:

- all **three distinct lenses** on the complete bust in the front view
- the three-lens arrangement remains coherent in a 3/4 view
- no obvious duplicate hood, floating shell, or gross depth inversion
- whole-bust outer silhouette remains stable outside the local ROI
- hose/grille/mechanical detail outside the replacement ROI is not degraded

A head-only render is insufficient.  This gate is explicitly a whole-bust gate.

## 4. Seam / stitch-readiness gate

Topology stitching remains forbidden unless all are true on the **new seam loop
only**, excluding pre-existing robe/scrap openings:

- seam nearest-neighbour p90: **<= 3.0 mm**
- seam nearest-neighbour maximum: **<= 5.0 mm**
- bidirectional coverage within 3 mm: **>= 0.90**
- protected-lens vertices/samples on the seam: **0**
- no protected lens vertex is moved by seam preparation
- no newly flipped face normals in the accepted seam band
- no new disconnected component is introduced by the stitch preparation

Current ROI-aware v2 measurements reported by Grok are approximately
7.40 mm / 7.17 mm p90 and 11.99 mm / 11.67 mm max in the two directions.
The stitch-readiness dry-run also reports coverage@3mm **0.2436** and 47 protected
AABB vertices on seam samples.  Therefore the current fixture is correctly
**REJECTED** for welding/stitch insertion.

The 3 mm / 5 mm limits are project acceptance thresholds for this 40 cm fixture,
not universal manufacturing tolerances.

## 5. Post-stitch geometry gate

If a future seam passes the readiness gate and a topology stitch is attempted,
acceptance additionally requires:

- no new non-manifold boundary attributable to the local replacement
- no self-intersection visible in the seam QA pass
- no face-normal flips introduced by the stitch
- protected three-lens geometry remains present after any cleanup/remesh
- outer silhouette remains stable outside the ROI
- target mesh-budget reduction does not collapse the recovered third lens

Because the baseline source mesh is not watertight, "must be watertight" is not a
valid fixture gate.  Instead compare topology against the unchanged baseline and
reject newly introduced defects.

## 6. Texture/export gate

Only after geometry passes:

- regenerate/validate UV and PBR outputs as needed
- verify Blender import
- verify requested physical scale
- verify texture maps remain embedded and assigned correctly
- if rigging is enabled, rerun rig structural/deformation validation after the
  geometry change

Texture sharpness must not be used to hide failed geometry.

## 7. UI-promotion gate

The localized-detail path stays out of the normal Studio UI until:

- this mechanical-bust fixture passes all relevant gates
- at least **one unrelated second fixture** passes the same automatic selection,
  registration, seam, and whole-object checks
- failure/rejection returns the untouched successful base model rather than a
  malformed replacement
- deterministic rerun produces materially equivalent ROI/gate decisions
- cancellation/retry preserves valid intermediate results

Until then it remains a `quality_lab` experiment.

## 8. Claims boundary

Do **not** claim Meshy parity from this work.

Allowed statement: the local-detail path is being tested against specific
geometric details that the current whole-object reconstruction misses.

Not allowed without broader evidence: "same quality as Meshy", "better than
Meshy", or a general ranking of reconstruction systems.

## Current evidence paths

Local reports/renders referenced by the current investigation:

- `D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_registration.json`
- `D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_dry_splice_roiv2.json`
- `D:\SF3D_QualityLab\bust_validation\shape_ablation\detail_stitch_v1.json`
- dry-splice clay/contrast renders in the same fixture directory

These local generated artifacts are evidence, not repository source files.
