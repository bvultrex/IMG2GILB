# Auto ROI v3 → Densified Registration A/B Result

Date: 2026-09-28

Status: **ASSIGNED TASK PASSED on the mechanical-bust fixture**.

Production acceptance remains **false**.

## Goal

Demonstrate that an automatically inferred ROI can replace the fixed mechanical-bust
crop under the existing densified-registration acceptance gate without using the
known crop as an inference input and without weakening registration thresholds.

Primary approach: **crop-side post-ROI tightening**.

## Automatic ROI v3

Base v2 proposal:

`[0.2697265625, 0.004353125, 0.7478515625, 0.416375]`

Automatic v3 proposal after deterministic post-tightening:

`[0.3175390625, 0.004353125, 0.7000390625, 0.366932375]`

Evaluation-only fixed crop:

`[0.32, 0.015, 0.675, 0.36]`

The fixed crop is not used by ROI inference.

### ROI gate

- bbox IoU: **0.8831064614**
- known-crop coverage: **1.0000000000**
- proposal coverage by known: **0.8831064614**
- center error: **0.0114408177**
- corner MAE: **0.0112698125**
- minimum alpha-threshold stability IoU: **0.9891601242**
- fixture gate: **PASS**

Post-tightening parameters:

- side trim per edge: **10%**
- bottom trim: **12%**
- top trim: **0%**

## Densified registration A/B

Target sampling: **3000 deterministic area-weighted surface samples** inside the
unchanged support predicate.

### Fixed crop control

- held-out median: **1.2974034694 mm**
- held-out p90: **2.2152873404 mm**
- translation norm: **9.1995843304 mm**
- optimizer converged: **yes**
- near scale bound: **false**
- near rotation bound: **false**
- near translation bound: **false**
- geometric gate: **PASS**

### Automatic ROI v3

- held-out median: **1.3954802835 mm**
- held-out p90: **2.7721246841 mm**
- translation norm: **10.1553580670 mm**
- optimizer converged: **yes**
- near scale bound: **false**
- near rotation bound: **false**
- near translation bound: **false**
- geometric gate: **PASS**

Configured registration gate remains unchanged:

- held-out p90 <= **3.0 mm**
- held-out median <= **2.0 mm**
- optimizer converged
- no scale/rotation/translation bound hit

Result:

`automatic_interchangeable_with_fixed_crop = true`

## Interpretation

For this mechanical-bust fixture, the automatic ROI v3 proposal is now
interchangeable with the fixed crop under the existing densified-registration
gate.

The automatic path is measurably worse than the fixed control on p90
(2.772 mm vs 2.215 mm), but still passes all pre-existing acceptance thresholds
without relaxing them.

This result does **not** authorize topology stitching, UI promotion, or a
production-quality claim. It is single-fixture evidence only.

A second unrelated fixture remains required before claiming general automatic-ROI
interchangeability.

## Reproduction

After pulling the relevant commits:

```powershell
.\quality_lab\Run_Auto_ROI_Registration_AB.bat
```

Relevant implementation commits:

- `fc83372` automatic ROI v3 post-tightening
- `4faeadd` densified registration A/B
- `4048a67` A/B runner
- `10b264e` deterministic area-weighted surface sampling fix
