# Issue #1 draft — Meshy-like pipeline v1 (do not claim parity)

```
[GROK]
WORKING ON: Meshy-like open-stack stage wiring + A3 front micro-align (David texture A/B)
FILES/AREA: quality_lab/MESHY_LIKE_PIPELINE_PLAN.md, project_hybrid_a3.py, desktop/pipeline.py, stages.py, bake_paint21.py, run_paint_multiref.py; _vis_export/meshy_like_v1/
LAST COMMIT: uncommitted
RESULT: Plan + flags (paint_multiref default-on when ≥2 views; hybrid_a3 opt-in; texture_sr; remesh opt). A3v2 face-local micro-align accepted on David; chest still >> A0; jaw smear residual. No Meshy/Tripo parity claims.
TESTS: texture-only A3 re-run ~47s; SBS sbs4_face/chest in _vis_export\meshy_like_v1\
BLOCKERS / QUESTION: side IoU still blocks L/R projection; face landmark micro-align helps but jaw blend remains. Promote hybrid to finalize? (recommend no yet)
NEXT: A2 multiref re-bake on frozen UV; realesrgan bake A/B; tighter face-only transfer
```
