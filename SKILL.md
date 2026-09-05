---
name: silas-candid-photography-pro
description: Use when users request candid photography prompts, realistic lifestyle portraits, unusual camera angles, batch portrait concepts, reference-image identity consistency, or direct generation with image-quality review.
---

# Silas Candid Photography Pro

Produce reproducible, plausible candid photography while preserving explicit choices. Default to 10 numbered Chinese prompts featuring a Korean INS-style adult woman; a supplied subject or identity reference replaces it.

## Resolve the request

Parse `count`, `mode`, `subject`, `aspect_ratio`, `model`, `seed`, `locks`, `biases`, `references`, `reference_controls`, and `identity_policy`. “Must,” “only,” and exact values are locks; preferences are biases. `reference_controls` is a concrete mapping from a reference assignment to a plan field (for example, `composition`, `lighting`, or `identity_anchors`), not a second plan to overlay later.

Apply this priority order:

1. Safety and tool boundaries
2. Explicit user locks
3. Explicit reference-image roles
4. User biases
5. Default subject
6. Random variables
7. Aesthetic preferences

Locks survive every stage. On a hard conflict, name the smallest conflicting set and ask one decisive question. If locks limit diversity, retain them and use the warning gate. Reference controls are protected below locks: pass both values to the composer so it returns the lock, records the reference conflict, and never hides the disagreement.

## Choose the mode

Before rendering any plan, run `python scripts/compose_plan.py --request-json '<JSON object>'` here. It validates count/weights, applies locks and concrete reference controls, repeatedly repairs only unprotected incompatible fields until stable within a fixed bound, checks final compatibility invariants, and returns `normalized_request`, final `plans`, `repairs`, `seed`, `version`, and `warnings`. Any protected, non-convergent, or otherwise remaining final conflict is an explicit warning. That returned record is the sole source of truth. Do not merge sampled values back into an earlier draft and do not apply a reference, aesthetic, or renderer overlay afterward.

- **Prompt** (default): render numbered natural-language prompts without an image tool.
- **Generate**: requires an explicit image-creation request. Assign reference roles, use an available image tool, audit each result, and allow at most two repairs. Generation does not authorize sharing.

Without an image tool, explicitly downgrade to Prompt mode, state that no image was generated, and provide the adapted prompts. If generation depends on a required local reference that is unavailable, do not call the tool: suspend Generate mode, request that image, and provide a clearly labeled prompt fallback when its textual role description is sufficient. Never claim to have inspected an unavailable image.

### Warning gate

Stop before prompt rendering on an unresolved compatibility or lock/reference-control warning and ask one decisive question. On a diversity warning without explicit acceptance of best-effort duplicates, ask whether to accept duplicates with protected controls retained. Never append warnings to a nominal successful batch. After acceptance, render without claiming the warned condition was resolved; “only prompts” still outputs only prompts after the gate is resolved.

## Build the result

1. Read [the aesthetic system](references/aesthetic-system.md) to render natural language.
2. For supplied images or identity consistency, read [reference-image responsibilities](references/reference-images.md).
3. For a named renderer or generation, read [model adapters](references/model-adapters.md); phrase only the final returned plan values.
4. In Generate mode, read [the quality rubric](references/quality-rubric.md) before generation.
5. Read [the example](references/examples.md) only for three-reference or targeted-repair ambiguity.

Require visible final-prompt slots for subject, every lock, any identity anchors, expression, wardrobe, scene, in-progress action, shot distance, lens, camera position/angle, composition, foreground, lighting, 3–4 dominant colors, photography state, and reference roles. Each slot must phrase its value from the returned final plan; no adapter may silently substitute a “more suitable” value.

## Output contract

Unless the user requests a structured plan, render each prompt as:

```markdown
### 01

完整提示词
```

Use the user's count and language. Prompt mode returns only numbered entries unless asked for a plan or explanation; resolve conflicts and warning gates first. “Only prompts” excludes seed, notes, scores, audit, warnings, and generation claims. Include `actual_seed` only when requested and allowed by that lock. Generate mode shows the image and only necessary audit or unresolved criteria.
