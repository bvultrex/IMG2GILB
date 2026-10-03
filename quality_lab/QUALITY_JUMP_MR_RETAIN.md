# Quality Jump — MR retain (albedo-only PBR control)

**Status:** fixed in hybrid writer + CPU rebake of P2/P2b PBR sidecars  
**Studio defaults:** unchanged (`hybrid_a3` still opt-in; no Finalize flip)  
**Baselines:** A0 / old hybrid `*_pbr.glb` preserved

## Zenko invariant (Issue #1 comment 5958798088)

Hybrid PBR GLBs must keep the **same** `metallicRoughnessTexture` RGBA hash as the A0 (source bake) PBR.
Verts / faces / UVs already matched; only albedo/`baseColorTexture` may change.

## Root cause

`project_hybrid_a3.py` packed MR from `job/paint/mr_atlas_2K.png` on every hybrid export.

Phase-1 A0 bake uses a **different** MR atlas:

| Source | RGBA sha256 (packed MR as in GLB) |
|--------|-----------------------------------|
| A0 `quality_jump_phase1/A0_single_pil/mr_atlas_2K.png` → A0 PBR | `f08811e3313e46bbd9a842e3d240b8328750352582df71c6675606dfdad0c393` |
| `job/paint/mr_atlas_2K.png` → old hybrid PBR | `843b862cf6935c1bdddbcfe26fb55ed00a58dbbf0bce188b87840c9ab77256e2` |

Same pack formula (`[255, G, R]`); wrong input atlas → invariant break.

## Fix

In `quality_lab/project_hybrid_a3.py` (mirrored `D:\SF3D_QualityLab\project_hybrid_a3.py`):

1. `--source-pbr <A0_pbr.glb>` → copy MR **pixels** + metallic/roughness factors from that GLB (preferred).
2. Else if `--atlas` has sibling `mr_atlas_2K.png` → pack that (matches A0 when atlas is Phase1 A0).
3. Else `--mr-atlas` → pack explicitly.
4. Else fallback `job/paint/...` with an explicit report blocker warning.

CPU helper (no GPU): `quality_lab/rebake_hybrid_pbr_retain_mr.py`

```bat
D:\SF3D_QualityLab\venv\Scripts\python.exe ^
  C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\rebake_hybrid_pbr_retain_mr.py ^
  --source-pbr ...\A0_single_pil\textured_A0_single_pil_pbr.glb ^
  --hybrid-color ...\textured_hybrid_phase2b_color.glb ^
  --report ...\mr_retain_rebake_report.json
```

## Re-emitted artifacts (NEW names; old `*_pbr.glb` kept)

Job `5e81ac7963f84af2a403fb659cea7513`:

- `quality_jump_phase2b\textured_hybrid_phase2b_pbr_mr_retain.glb`
- `quality_jump_phase2b\textured_hybrid_phase2b_fallback_no_micro_pbr_mr_retain.glb`
- `quality_jump_phase2\textured_hybrid_phase2_vs_A0_pbr_mr_retain.glb`
- `quality_jump_phase2\textured_hybrid_phase2_jawblend_pbr_mr_retain.glb`

All four: `mr_rgba_sha256 == A0` (`f08811e3…`), albedo hashes unchanged vs prior color GLBs.

Verify:

```bat
python quality_lab\codex_glb_invariants.py A0_pbr.glb hybrid_pbr_mr_retain.glb --out mr_retain_invariants.json
```

Expect: `matches_baseline.metallicRoughnessTexture == true` (and verts/faces/uv true). Old hybrid `*_pbr.glb` still fails MR match (intentional before/after).

## Phase2b note

Still awaiting Zenko visual scorecard. MR fix is orthogonal to jaw/face visual gates — no Studio default flip.

## Limitations

- Does not change Paint MR generation; only which MR is **attached** to hybrid PBR sidecars.
- Color-only GLBs never carried MR (unchanged).
- No Meshy/Tripo parity claim.
