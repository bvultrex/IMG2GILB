# Phase 1 independent review — 2026-10-02

Reviewer: Codex / Zenko. Experimental, production_accepted=false.

Grok completed A0–A3; manifest and local result read. Face, chest and atlas sheets inspected. A0 is retained as the conservative Phase 2 control, not declared a quality winner.

## Findings
- Multi-reference native front changes face/mouth, simplifies upper jacket stripe detail and changes necklace. No front reference-fidelity win established.
- ESRGAN atlas contours look sharper; missing native reference details are not restored by this observation.
- Back/oblique seam quality and final-render SR fidelity remain unevaluated.

## Evaluation corrections required
`make_crops_metrics.py` under the job's `quality_jump_phase1/` takes front crops from native `albedo_0.png`, before SR and bake. A0/A2 face PNGs are byte-identical (SHA prefix 8f78d4cf); A1/A3 are likewise identical (553cb67c). They test conditioning only, not SR or GLB rendering. The chest crop covers waist/thighs, missing the chest cross. Camera 2 is only guessed to be back-facing in the script.

The Laplacian is applied through Pillow to an L-mode image before float conversion, clipping signed responses. Reported values must not be treated as signed Laplacian variance or quality acceptance.

## Agreed-scope next step requested from Grok
Keep completed generation/bake outputs. Produce matched final GLB unlit front/back/oblique renders, correct semantic crops, and signed float metrics. No costly generation rerun needed for these corrections. Continue Phase 2 hybrid sidecar comparison against A0 while repairing evaluation. No production promotion until reference-fidelity, seams and generalization gates pass.

Coordination: https://github.com/bvultrex/IMG2GILB/issues/1#issuecomment-5958345088
