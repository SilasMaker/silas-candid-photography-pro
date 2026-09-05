# Reference-image responsibilities

Assign every supplied image one or more explicit roles before planning. Refer to sources by the user's labels or attachment order, and copy only the evidence allowed by that role. Convert each concrete role fact needed in the result into `reference_controls` before calling the composer; never wait until rendering to overlay it.

| Role | Controls | Does not establish |
|---|---|---|
| `identity` | face shape and features, hair and hairline, body proportions, stable accessories or marks | pose, environment, lighting, or wardrobe unless separately assigned |
| `wardrobe` | garment silhouette, construction, material, coverage, color, and styling relationship | person identity or body shape |
| `companion` | identity and stable appearance of a dog, other companion, prop, or product | main-subject identity or scene composition |
| `composition` | subject placement, framing, shot distance, viewing direction, and spatial relationships | the depicted person's identity or garment identity |
| `environment` | architecture, layout, surface materials, fixtures, and scene objects | subject identity or lighting unless separately assigned |
| `lighting` | source direction, softness, contrast, exposure relationship, and motivated reflections | identity, garment structure, or object identity |
| `style` | medium, grain, tonal response, color treatment, and finish | subject identity, wardrobe structure, or composition |

## Normalize controls before composition

Map concrete reference evidence to the closest final-plan field: `identity` → `identity_anchors`; `wardrobe` → `wardrobe`; `composition` → `composition`, `shot_distance`, or `camera_angle`; `environment` → `scene`; `lighting` → `lighting`; and `style` → `color_scheme` or `photography_state`. `companion` details belong in the relevant subject/action wording only when the plan schema represents them explicitly; do not smuggle them into another field.

Pass these values as the top-level `reference_controls` object together with `references`, which retains source labels and role assignments. The composer copies every non-conflicting control into every returned final plan. A user lock on the same field wins; the original control remains visible in `normalized_request.reference_controls`, and the conflict appears in `warnings`. Bounded compatibility convergence and the final invariant check treat both locks and reference controls as protected. Resolve any warning before rendering instead of silently rewriting the reference assignment.

## Conflict precedence

Within safety and tool boundaries, apply: explicit user locks → `identity` anchors for the person → `companion` anchors for the companion/product → `wardrobe` structure → `composition` relationships → `environment` structure → `lighting` → `style`. An explicit role assignment is a boundary, not permission to blend other visual facts from that image. This precedence must be resolved in the normalized request/composer response, not in a model adapter.

Examples of required separation:

- A composition source can place the main subject at frame right but cannot replace their face.
- A style source can contribute muted warm-gray rendering but cannot recolor a locked white cardigan.
- An environment source can supply a bus interior but cannot make the person from that image the subject.
- When two same-role references conflict, preserve any user lock and ask one decisive question only if the conflict affects the requested result; otherwise use the more specifically assigned source and state the choice when explanation is allowed.

## Identity policy

For `high` identity consistency, explicitly preserve face shape, feature proportions, hairline, signature accessories, and body proportions from the `identity` source. Keep these anchors visible and stable across the batch. Do not use heavy facial obstruction, extreme facial perspective distortion, strong motion blur over the face, radical profile rotations unsupported by the source, or style treatment that changes recognizable anatomy. Composition, lighting, and candid imperfections adapt around those anchors.

For `balanced`, preserve stable identity while allowing ordinary pose, expression, and viewpoint variation. No policy permits a non-identity reference to overwrite identity.

## Image availability

Textual role descriptions are sufficient for prompt-only output: name the intended role and phrase the prompt without claiming the image was inspected. Image editing or generation that depends on a reference requires that exact image to be locally available to the image tool. If any required local image is missing, do not call the tool: suspend Generate mode, request the attachment, and clearly downgrade to prompt-only output when the textual role description is sufficient.
