# Fresh Ranger matched-render review

2026-10-02. Fresh job 4a80e4f55d0145408fc1921effe276b5, original inputs only; all seven stages completed. This is a texture evaluation, not overall completion.

Independent Blender 5.2 CPU emission renders at 1024px, identical orthographic camera framing, azimuths 0, +35, -35, 180. Baseline and hybrid imported world extents match exactly. Files remain local under sibling quality_runs/ranger_matched_baseline and ranger_matched_hybrid. Renderer emits source hashes and camera settings in import_report.json. Visually inspected front, +35 and rear hybrid and baseline front this turn; remaining pairs not yet scored.

## Findings

- Hybrid recovers finer clothing trim, straps and boot detail compared with the generated baseline front. This is a visible improvement in detail, not proof of full reference fidelity.
- Front hybrid has doubled/offset eye and brow features, continuing into the +35 view. Cannot pass face or seam gates.
- Rear hybrid is coherent at whole-model scale, but small-symbol fidelity needs the matched reference check.
- Surface shape and hand silhouettes are unchanged. No geometry breakthrough claimed.

## Concrete integration gap

The desktop hybrid command invokes project_hybrid_a3.py without --face-iso or --phase2b. The independently tested face_iso v2 fallback is therefore NOT what these fresh jobs exercise. Prior sidecar acceptance cannot establish the normal pipeline's face quality. Current finalization correctly exports its selected hybrid, but that hybrid still uses the earlier default projection behavior.

Next controlled experiment: same fresh Ranger geometry, paint and MR; run --face-iso into separate sidecar GLBs and a separate output/report directory after the sequential bust run releases GPU. Compare the same four Blender views. Preserve baseline/final output and defaults. Only wire a selected mode into the orchestrator after its actual final result passes face and body gates; document paint fallback honestly as coherence protection rather than identity improvement.
