# Resume audit 2026-10-09

- Local HEAD and freshly fetched origin/main e23f04d. Recovery commit preserves previous scripts. No tracked edits before audit. Issue1 page2 latest comment5979916627 (2026-10-04); no new coordination found there.
- No live Python/Blender processes on initial and final process checks. No GPU inference launched this audit.
- Previously undocumented later local artifacts exist: pixal_mv_bust_trial1, pixal_mv_ranger_trial12, front_only_trial1, front_back_trial1, pixal_mv_fourview_trial1, pixal_mv_fourview_600k/clean/coherent1. Must inspect before duplicating experiments.
- pixal_mv_fourview_trial1_textured/report.json says running, but there is no live Python process and its directory contains only report.json and run_texture.py: no generated texture or GLB. Treat as interrupted/unverified, not a verified wait. Original manifest preserved.
- coherent1 reports complete geometry but explicitly admits front/back arms extended versus side arms down. Its name does NOT establish coherent inputs or quality. No production acceptance.
- New independent split-edge diagnostic: starting cleaned Ranger465143faces, indexed nonmanifold8214 ->0 after CuMesh repair_non_manifold_edges; indexed boundaries1371 ->28839. Positional nonmanifold8216 and boundaries1349 unchanged. Vertex splitting hides indexed connectivity errors without repairing geometric surface; do not use indexed zero as acceptance. No new production geometry exported. Report quality_runs/pixal_mv_ranger_surface_clean/split_edge_audit.json.
- Existing stage audit confirms nonmanifold15796 already after DC remesh, before simplification. Duplicate cleanup alone insufficient.

Next: reconcile later fourview geometry/texture experiments and input pose compatibility, then resume actual texture run only on a documented candidate. Preserve all baselines and foreign reports. Full goal remains open.
