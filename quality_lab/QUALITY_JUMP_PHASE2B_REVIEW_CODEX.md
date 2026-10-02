# Phase2b independent scorecard

2026-10-02 — Codex / Zenko. production_accepted=false.

Reviewed local face/collar/back-emblem sheets, both 35-degree and 90-degree comparisons, confidence overlay and export source code.

| Region | Finding | Decision |
|---|---|---|
| Face | Projected eyes mixed with baseline mouth/neck; expression regresses. No-micro variant misaligns eyes/brows. | Reject both as face promotion. |
| Collar/necklace | Detail gain over A0 remains, but mixed/double contours persist. | P2 remains control. |
| Back emblem | Lower-right tip fades into fill in P2B relative to P2. | Reject global incidence change as a general improvement. |
| Side/oblique | Baseline fill remains on sides; views supplied, but no seam-free acceptance established. | Further targeted validation. |
| Confidence overlay | Useful spatial diagnostic, no numeric legend. | Do not treat as calibrated probability. |

Next experiment: freeze P2 torso/back and test face alignment independently. Register eyes/nose/mouth/chin before blending, avoid source boundaries through facial features, use one coherent face source when alignment fails. Separate incidence changes from face changes. Preserve full emblem coverage.

Material provenance: current hybrid exporter chooses job/paint/mr_atlas_2K.png irrespective of the A0 albedo override. That explains a different source path for MR; Grok owns the explicit MR-source correction. Recheck decoded exported MR pixels against A0 after the fix. Do not alter Grok-owned exporter concurrently.

This is qualitative visual review, not a measured landmark benchmark. Existing generation outputs remain reusable; no model reinstallation or paint regeneration requested.
