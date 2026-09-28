# Auto ROI General v1 — Ranger Second-Fixture Result

Date: 2026-09-28

Status: **second-fixture provisional gate passed**.

Production acceptance remains **false**.

## Fixture

Second unrelated fixture:

`fixtures/ranger_ortho_v1/front.png`

Mode:

`fullbody`

No golden crop was used as an inference input.

## Ranger automatic ROI

Proposal:

`[0.3813075506, 0.0837966160, 0.5790976059, 0.4449154006]`

Foreground source:

`border_rgb_distance`

Detected object bbox:

`[0.0055248619, 0.0614640884, 0.9944751381, 0.9212707182]`

## Ranger provisional evaluation

Measured:

- sensitivity stability IoU: **0.9885861561**
- central-upper-silhouette coverage: **0.6803419695**
- proposal area / object bbox area: **0.0842550836**
- proposal top offset: **0.0257028112** object heights
- proposal bottom position: **0.4465863454** object heights
- general fixture gate: **PASS**

Configured provisional gates:

- sensitivity stability IoU >= **0.80**
- central-upper-silhouette coverage >= **0.60**
- proposal area / object bbox area in **[0.04, 0.35]**
- proposal top offset <= **0.08** object heights
- proposal bottom position <= **0.50** object heights

All provisional gates pass.

The result is deterministic across foreground sensitivity 0.85 / 1.0 / 1.15.

## Bust no-regression check

The same runner re-executed the accepted mechanical-bust path.

Bust ROI v3:

- bbox IoU: **0.8831064614**
- known-crop coverage: **1.0**
- min alpha-threshold stability IoU: **0.9891601242**
- fixture gate: **PASS**

Bust densified registration:

Automatic ROI v3:

- held-out median: **1.3954802835 mm**
- held-out p90: **2.7721246841 mm**
- optimizer converged: **yes**
- near scale bound: **false**
- near rotation bound: **false**
- near translation bound: **false**
- geometric gate: **PASS**
- `automatic_interchangeable_with_fixed_crop=true`

Therefore the second-fixture implementation did **not** regress the previously
accepted bust ROI/registration behavior.

## Interpretation

This run demonstrates that the general ROI framework can operate on a second,
unrelated full-body orthographic fixture without relying on the bust-specific
golden crop.

The ranger result uses a provisional evaluation protocol based on stability,
central upper-body silhouette coverage, ROI scale, and ROI vertical placement.
It is not yet a frozen human-reviewed golden crop.

Passing this result does **not** establish:

- ranger detail-registration quality
- ranger splice/stitch readiness
- generic object-mode validation
- UI readiness
- production acceptance
- Meshy parity

## Artifacts

Expected local artifacts:

- `D:\SF3D_QualityLab\ranger_validation\ortho_v1\auto_roi_general_v1_fullbody.json`
- `D:\SF3D_QualityLab\ranger_validation\ortho_v1\auto_roi_general_v1_fullbody_overlay.png`

Relevant implementation commits:

- `fcdcd29` general automatic ROI proposer
- `c771841` second-fixture evaluation protocol
- `4f7c10e` ranger + bust-regression runner
