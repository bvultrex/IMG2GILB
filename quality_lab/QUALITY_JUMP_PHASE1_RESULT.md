# Quality Jump Phase 1 Result — Factorial A0–A3 (David)

Status: **executed 2026-10-02 Europe/Warsaw**. `production_accepted=false`. Experimental only. **No Meshy parity. Hybrid not promoted to finalize.**

Plan: `QUALITY_JUMP_PLAN.md` · Zenko taxonomy: `PAINT_UV_FAILURE_TAXONOMY.md` (untouched)

## Fixture

- Job: `D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513\` (Cyberpunk David)
- Frozen shape + `controls\uv_mesh.npz` + cameras reused
- Original `paint/` views + `output.glb` **byte-intact** vs `cache.json` after experiment
- Outputs: `...\quality_jump_phase1\` and `Documents\ComfyUI\_vis_export\quality_jump_phase1\`
- Manifest: `...\quality_jump_phase1\manifest.json`

## Arms

| Arm | Conditioning | Upscaler | Ref count | Native | Bake s | Paint gen s | Paint peak MiB | color SHA256 (12) | Atlas Lap.var |
|---|---|---|---|---|---|---|---|---|---|
| A0 | single | PIL/LANCZOS | 1 | 768 | 192.7 | 140.0 | 14673 | cbbf50d95a2b | 99.7 |
| A1 | multi | PIL/LANCZOS | 4 | 768 | 202.0 | 174.7 | 14086 | 3f7bc3eb936a | 80.5 |
| A2 | single | Real-ESRGAN | 1 | 768 | 225.4 | (same views as A0) | 14673 | 18ffab7ab94d | 172.9 |
| A3 | multi | Real-ESRGAN | 4 | 768 | 215.7 | (same views as A1) | 14086 | 825e47f4c44e | 129.1 |

Notes:
- A0/A2 share **identical** generated single-ref views (copied from original `paint/`).
- A1/A3 share **identical** multiref generation under `quality_jump_phase1\multiref_gen\` (`reference_count=4` confirmed in report).
- Bake writes into per-arm paint copies only.
- PIL = **LANCZOS** (Zenko correction).
- Laplacian/HF on full atlas is a **proxy only** — must not pass alone (can reward ESRGAN noise). Visual crops required for Zenko eval.

## Visual staging

`C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase1\`
- Per arm: `front_face.png`, `front_chest.png`, `view2_*`, atlas windows, full `albedo_atlas_2K.png`
- Sheets: `sheet_front_face.png`, `sheet_front_chest.png`, `sheet_atlas_mid.png`

GLBs (color):
- `...\A0_single_pil\textured_A0_single_pil_color.glb`
- `...\A1_multi_pil\textured_A1_multi_pil_color.glb`
- `...\A2_single_esrgan\textured_A2_single_esrgan_color.glb`
- `...\A3_multi_esrgan\textured_A3_multi_esrgan_color.glb`

## Preliminary read (Grok — not acceptance)

- **SR effect (A2−A0 / A3−A1):** atlas energy ↑ as expected (ESRGAN). Check whether chest emblems/face look *crisper true detail* or *sharpened invention* on sheets.
- **Multiref effect (A1−A0 / A3−A2):** atlas Lap.var slightly ↓ vs single; may mean smoother multi-view consensus rather than "worse". Judge on back/side identity and symbol fidelity, not energy.
- **Do not** flip Studio defaults from this run alone. Phase 2 Hybrid gates + Zenko visual eval + second fixture still required.

## GPU

Sequential claim on Shadow A4500; released after A3. Peak during multiref paint ~14 GB used.

## Next

1. Zenko: visual eval on frozen crops (face/chest/back/seam) + optional T1 sharpness on GLBs.
2. Phase 2 Hybrid only after choosing generative baseline (likely best of A0–A3).
3. No finalize / default flips yet.