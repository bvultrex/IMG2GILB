# TERMINAL: technical pass, visual gate fail

All named sessions completed. Final result and review: ../quality_runs/bust_texture1024_20261009/visual_review.json. Full final GLB imported/rendered successfully; duplicate shoulder emblem prevents quality acceptance. Do not rerun commands below against existing directories.

# Second motif: 1024 Paint

Current session: **56055**, run directory (relative to repository)
`../quality_runs/bust_texture1024_20261009/sequential_ff_chunk`.

The earlier `sequential_fresh` attempt is terminal: CUDA OOM inside
FeedForward/GEGLU. Do not resume it without a completed checkpoint.

The replacement uses opt-in `--ff-chunk`: 64 modules confirmed activated,
batch dimension split into one-item chunks. Attention still sees all six views.
Seed0,15steps,guidance3,1024 native maps. At last observation,2/15 completed;
coordinator handle confirmed live. PowerShell temporarily crashed under memory
pressure; lightweight cmd.exe log reads work. Do not launch a second GPU job.

Actual installed FeedForward/helper CPU equivalence test: max absolute error0.
This is not proof of full FP16 image equivalence. Two existing runner unit tests
passed after the opt-in change.

After session56055 exits successfully and sequential_report.json says passed:

```powershell
& 'D:/SF3D_QualityLab/venv/Scripts/python.exe' IMG2GILB/quality_lab/finish_paint_albedo_candidate.py --job quality_runs/341179b171fe48918a231032f4f5b82c --paint quality_runs/bust_texture1024_20261009/sequential_ff_chunk --out quality_runs/bust_texture1024_20261009/export_ff_chunk
```

Run from ComfyUI workspace. The finish helper verifies all12 map hashes/sizes and
control hashes before baking. It preserves baseline MR and geometry using exact
albedo replacement and exercises the real finalize stage. Not executed yet.
Then independently import finalized/output.glb and render against baseline.
Existing bust baseline uses seed42: do not attribute differences to resolution
alone. This test is fixed-geometry second-motif validation, not fresh E2E.

Ranger viewer and production defaults remain unchanged. Overall goal incomplete.
