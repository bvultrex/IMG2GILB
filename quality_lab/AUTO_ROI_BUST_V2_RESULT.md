# Auto ROI Bust v2 Result

Date: 2026-09-28

Status: **fixture gate passed**, production acceptance remains **false**.

## Input

Prepared front reference:

`D:\SF3D_QualityLab\app_jobs\9c9d771bfdf844cefae8ec485d8bab8af\prepared\front.png`

Known fixture crop used for evaluation only:

`[0.32, 0.015, 0.675, 0.36]`

The known crop is not an inference input.

## Proposal

Automatic v2 ROI:

`[0.2697265625, 0.004353125, 0.7478515625, 0.416375]`

## Acceptance metrics

- Bounding-box IoU: **0.6217069488**
- Known-crop coverage: **1.0000000000**
- Proposal coverage by known crop: **0.6217069488**
- Center error, normalized: **0.0254991821**
- Corner MAE, normalized: **0.04753671875**
- Minimum alpha-threshold stability IoU: **0.9896731711**

Configured fixture gates:

- bbox IoU >= **0.60**
- known-crop coverage >= **0.75**
- alpha-threshold stability IoU >= **0.90**

Result: **PASS**

## Threshold stability

- alpha 0.35: `[0.2685546875, 0.0043484375, 0.7490234375, 0.416703125]`
- alpha 0.50: `[0.2697265625, 0.004353125, 0.7478515625, 0.416375]`
- alpha 0.65: `[0.27099609375, 0.0051390625, 0.74560546875, 0.416828125]`

## Method

The v2 proposal uses:

- the largest BRIA-alpha connected foreground component,
- an eroded upper-foreground region,
- luminance Sobel/detail energy,
- weighted horizontal detail-energy quantiles,
- a weighted vertical detail-energy lower bound,
- broad task-level sanity constraints.

The fixed fixture crop is used only after inference to score the proposal.

## Interpretation

V1 was a valid negative control: it was highly stable across alpha thresholds but selected too much of the upper body, producing IoU 0.41747.

V2 narrows the region enough to pass the defined fixture gate while retaining full coverage of the known hood/lens crop.

This establishes only that the current automatic ROI heuristic is viable on this mechanical-bust fixture. It does **not** establish semantic lens detection, safe seam topology, production stitching, UI readiness, or generalization to unrelated objects.

A second unrelated fixture remains mandatory before any generic automatic-ROI or UI-promotion claim.
