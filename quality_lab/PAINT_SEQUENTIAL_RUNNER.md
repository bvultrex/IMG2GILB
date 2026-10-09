# Separate sampling and decode processes

Experimental opt-in runner; Studio defaults are unchanged. Uses installed Lab dependencies and weights, without downloads. It produces six albedo and six MR images, not a baked GLB.

Run with the existing Lab Python:

```powershell
& 'D:/SF3D_QualityLab/venv/Scripts/python.exe' quality_lab/run_paint_sequential.py --input <front.png> --controls <controls-directory> --output <new-directory> --resolution 1024
```

Use absolute paths when starting outside the repository. The output directory must be new. Confirm that no other generation job is running before launch; this standalone runner does not acquire the Studio GPU lock. Sampling uses seed 0, 15 steps, guidance 3, six views. Control geometry remains supplied, so this is not a fresh image-to-geometry test.

The sampler writes the exact VAE input atomically, records its checksum, then exits. Only after that process exits does the coordinator start the decoder. The Windows process guard kills owned children if the coordinator terminates. The decoder processes one image at a time. The coordinator verifies all twelve output sizes and records their hashes.

If decoding fails after a valid checkpoint, repeat the same command with `--resume`. Input/control/code fingerprints must match. Resume refuses a missing, truncated or mismatched checkpoint; PNG presence alone is never evidence of success. A failure before a complete checkpoint requires a new run directory. Model weight files themselves are not fingerprinted; do not replace weights between sampling and resume.

Validation:

- `python -m unittest test_paint_sequential.py` from this directory checks corrupt checkpoint rejection and actual protected subprocess success/failure.
- Ranger checkpoint replay through the new process guard reproduced all twelve prior PNG hashes exactly (`sequential_decode_replay/replay_report.json`). This checks decode equivalence, not fresh sampling.
- Fresh combined-run status is recorded separately under `quality_runs/ranger_texture1024_20261009/sequential_fresh/sequential_report.json`. Consult that file before claiming full sampler-to-decode success.

No production promotion, material-map replacement, or new quality acceptance is implied.

## Optional FeedForward memory reduction

Standalone `--ff-chunk` invokes the installed transformer blocks' batch-wise
FeedForward chunking (size1,dimension0); all six attention views remain together.
This completed the bust1024 sampler and sequential decode after unchunked GEGLU
OOM, then completed bake/final export and independent Blender import. The bust
still fails visual fidelity gates; memory success is not quality acceptance.

Studio experimental jobs may explicitly set `experimental_paint_ff_chunk: true`
alongside `experimental_paint_sequential: true`, `paint_multiref: false`, and
`paint_resolution: 1024`. Default is false; strings are rejected. Full project
settings enter cache fingerprints. Five CPU integration tests pass, including
actual command dispatch with flag absent/present. Full Studio E2E with this flag
has not been run. Existing pipeline defaults are unchanged.

Standalone `--references` is also available, but remains a lab diagnostic only:
the four-reference bust control completed yet preserved duplicate side emblems
and worsened facial asymmetry. Do not promote it as a quality preset. Studio's
experimental sequential multireference guard intentionally remains in place.

## Studio pipeline opt-in (developer project settings only)
The pipeline now supports these explicit project.json settings:

```json
{"experimental_paint_sequential": true, "paint_resolution": 1024, "paint_multiref": false}
```

This does not add a UI default or a quality-approved preset. Existing jobs without the flag retain512/768 according to quality. Multi-reference sampling is deliberately rejected for this runner rather than silently dropping references; projection references later in the pipeline are separate.

Each uncached pipeline attempt gets a new paint_attempts/<uuid> directory. All12output checksums and completed report are verified before copying maps into the standard paint directory. Failed attempts remain for diagnosis/manual CLI resume; the Studio retry currently starts a fresh attempt, it does not auto-resume them. Sampling and bake share one validated resolution. Runner/checkpoint/decoder/process-guard code enters the texture cache signature.

CPU tests: desktop/test_sequential_paint.py covers defaults, incompatible settings, corrupt-output rejection, decoder-code invalidation and actual nested Windows process guards. With existing cache and unlit-preview tests:7tests passed. The standalone fresh sampling+decode run passed earlier; the newly wired full Studio image→GLB chain has NOT been rerun or accepted.
