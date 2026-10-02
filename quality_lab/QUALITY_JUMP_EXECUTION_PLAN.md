# Quality jump execution plan — 2026-10-02

Status: proposed by Zenko within the existing Grok/Zenko ownership split; awaiting Grok's explicit acknowledgement of this sequence. No quality improvement claimed yet.

## Objective and decision
Deliver a visibly more faithful final GLB, not merely sharper intermediate images. Preserve visible reference details, avoid new seams and facial distortion, and keep the normal Studio flow automatic. Texture fidelity is the first milestone; missing geometry is a separate second milestone.

## Order and owners
1. **Freeze evidence (Zenko audit; Grok run manifest).** Use David job 5e81ac7963f84af2a403fb659cea7513. Record source, shape, UV, camera and script hashes plus dependency/model versions. Freeze evaluation crops before seeing variants: eyes/brows/mouth, chest cross/stripes, back emblem, jaw/neck seams. Use matched cameras, lighting and screen size. Preserve original files.
2. **Texture conditioning and SR (Grok executes; Zenko evaluates).** Run single-reference/PIL, multi-reference/PIL, single-reference/ESRGAN, multi-reference/ESRGAN. Same generated views within each upscaler pair; same geometry/UV/seed/resolution across conditioning arms. Use independent directories because bake writes back into the paint directory. Log actual reference count and image dimensions, runtime and peak VRAM. GPU jobs sequential; announce start/release in Issue #1.
3. **Reference projection (Grok implements; Zenko checks).** Compare accepted generative baseline against hybrid projection with visibility/confidence gating and jaw/neck seam treatment. Preserve eyes and mouth alignment; uncertain regions fall back to baseline. If misregistration remains, stop blending fixes and resolve camera/shape alignment first.
4. **Integration (Grok owns desktop files; Zenko independently verifies).** Wire the accepted texture into finalize only after visual gates pass. Check embedded GLB image hashes, material channels, preview and save/reload. Sidecar-only improvement is not completion. Keep old output available as rollback.
5. **Generalization (joint).** Repeat on a second fully clothed character and mechanical bust/object with frozen references. Face processing must skip non-human masks. Require two consecutive successful jobs without manual texture edits or repair.
6. **Geometry milestone (separate subsequent experiment).** Freeze the accepted texture method. Score silhouette, asymmetric features and missing parts on the bust/clothed character. Compare whole-object and local-detail reconstruction before any remeshing. Smoothing/remeshing must not erase lenses, fingers or emblems; poly count alone is not the score.

## Acceptance and escalation
- Primary: visible identity and symbol fidelity improve in preselected regions at equal display size; no new double contours, lost eye whites, heavier eyebrows, halos or mouth drift.
- Seam discontinuity and landmark error must not worsen beyond baseline measurement repeatability. Report actual measurements and visual findings separately; no invented numeric pass thresholds after seeing results.
- Preserve mesh/UV/non-target maps in texture-only arms. More high-frequency energy alone cannot pass.
- If upscaling sharpens invented detail: reject as a fidelity fix.
- If multireference conditioning fails: isolate baking with fixed views (best visible source versus weighted blend), then test source-preserving projection. Do not stack more changes blindly.
- If projection succeeds only frontally: retain it as experimental; improve alignment/visibility before integration.
- Investigate UV allocation only after isolating generation/bake loss; area sum near 0.48 is not a proven packing bug.
- If these controlled arms fail, compare a different texture backend or genuinely higher generation resolution under the measured VRAM budget. Record resource feasibility before installing/downloading. Do not restart the working environment.
- No guaranteed Meshy parity. A milestone passes only with final GLB evidence and the second-fixture checks.

## Required result bundle
Run IDs; manifest and hashes; exact settings; before/after matched renders and detail crops; final GLB path; stage lineage audit; time/VRAM; pass/fail and remaining defects. Private images and GLBs stay local. Public repo receives scripts, findings and sanitized manifests.

## Coordination
Grok retains ownership of desktop/hybrid changes and GPU experiments. Zenko owns audit/evaluation and this new plan file. No overlapping edits. Confirm or amend this plan in [Issue #1](https://github.com/bvultrex/IMG2GILB/issues/1); absence of a reply is not agreement.

Evidence: [measured texture taxonomy and gates](PAINT_UV_FAILURE_TAXONOMY.md).
