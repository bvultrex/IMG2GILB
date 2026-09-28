# Auto ROI General v1 — second-fixture evaluation protocol

Status: experimental only. `production_accepted=false`.

## Purpose

Validate that automatic local-detail ROI proposal is not specific to the
mechanical bust. The second fixture is the unrelated fantasy-ranger orthographic
front reference staged at:

`fixtures/ranger_ortho_v1/front.png`

The current test does **not** require a detail mesh or ranger registration. It
only evaluates automatic ROI proposal/generalization.

## Modes

`auto_roi_general_v1.py` accepts:

- `--mode bust`: delegates to the already accepted bust-v3 proposer.
- `--mode fullbody`: head/upper-torso detail proposal for humanoid full bodies.
- `--mode object`: central detail-rich proposal across an arbitrary foreground.

This mode split is explicit and is intended to be more product-relevant than
assuming every input is a bust.

## Foreground

The proposer first chooses a foreground source automatically:

1. informative alpha channel, if present;
2. otherwise color-distance from the image border background.

Only the largest connected foreground component is retained.

## Ranger evaluation without a golden crop

There is no pre-existing human-approved ranger detail crop. Therefore v1 does
not invent one and then train against it.

Instead, the first ranger acceptance uses:

- deterministic proposal stability across foreground sensitivity 0.85 / 1.0 / 1.15;
- coverage of the central upper-body silhouette;
- proposal area relative to the detected full-body bounding box;
- top and bottom position relative to the detected body height;
- qualitative overlay review.

For `fullbody`, the provisional gates are:

- minimum sensitivity-stability IoU >= **0.80**
- central-upper-silhouette coverage >= **0.60**
- proposal area / object-bbox area between **0.04 and 0.35**
- proposal top offset <= **0.08** object heights
- proposal bottom <= **0.50** object heights

The overlay renders three grayscale boxes:

- dark: detected object bbox
- mid-gray: evaluation-only central upper-silhouette proxy
- white: proposed detail ROI

Danny can later approve/freeze a human reference crop from this overlay. That
reference would be evaluation-only, not an inference input.

## Bust regression

The ranger experiment must not change accepted bust behavior.

The runner therefore also executes:

- `auto_roi_bust_v3.py`
- `auto_roi_registration_v1.py`

The mechanical-bust gates remain unchanged. Expected accepted state:

- bust ROI fixture gate = true
- automatic ROI registration geometric gate = true
- `automatic_interchangeable_with_fixed_crop=true`

## Claims boundary

Passing ranger v1 means only that the general ROI proposer behaves
deterministically and plausibly on a second unrelated fixture.

It does not establish:

- ranger detail-registration success
- topology splice readiness
- generic production readiness
- UI promotion readiness
- quality parity with Meshy or another commercial service
