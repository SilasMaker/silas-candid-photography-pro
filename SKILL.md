---
name: silas-candid-photography-pro
description: Use when users request candid photography prompts, realistic lifestyle portraits, unusual camera angles, batch portrait concepts, reference-image identity consistency, or direct generation with image-quality review.
---

# Silas Candid Photography Pro

Produce reproducible, plausible candid photography while preserving explicit choices. Default to 10 numbered Chinese prompts featuring a Korean INS-style adult woman; a supplied subject or identity reference replaces it.

## Resolve the request

Parse `count`, `mode`, `subject`, `aspect_ratio`, `model`, `seed`, `locks`, `biases`, `references`, `reference_controls`, `identity_policy`, and ordered `shots`. “Must,” “only,” and exact values are locks; preferences are biases. `reference_controls` is a concrete mapping from a reference assignment to a plan field (for example, `composition`, `lighting`, or `identity_anchors`), not a second plan to overlay later.

Apply this priority order:

1. Safety and tool boundaries
2. Explicit user locks
3. Explicit reference-image roles
4. User biases
5. Default subject
6. Random variables
7. Aesthetic preferences

Locks survive every stage. On a hard conflict, name the smallest conflicting set and ask one decisive question. If locks limit diversity, retain them and use the warning gate. Reference controls are protected below locks: pass both values to the composer so it returns the lock, records the reference conflict, and never hides the disagreement.

## Plan a natural performance

Before composition, read [natural performance](references/natural-performance.md). Design each shot as one motivated instant: a trigger, coordinated head/shoulders/body and hands, a specific gaze target, visible expression, and a physical consequence. Put body mechanics and head orientation in `action`, and gaze target plus facial behavior in `expression`. Preserve identity and wardrobe without freezing the reference's pose or face.

Submit these paired descriptions in one `shots` array of exactly `count` entries; include the other photographic fields needed to make each moment coherent. Audit action families, head/gaze combinations and emotional energy across the complete batch, not merely room or lens changes. Respect explicitly quiet, downcast or fixed-pose requests. The legacy random action/expression labels are brainstorming seeds, not finished prompts.

## Choose the mode

Before rendering any plan, run `python scripts/compose_plan.py --request-json '<JSON object>'` here. It validates count/weights, applies locks and concrete reference controls, repeatedly repairs only unprotected incompatible fields until stable within a fixed bound, checks final compatibility invariants, and returns `normalized_request`, final `plans`, `repairs`, `seed`, `version`, and `warnings`. Any protected, non-convergent, or otherwise remaining final conflict is an explicit warning. That returned record is the sole source of truth. Do not merge sampled values back into an earlier draft and do not apply a reference, aesthetic, or renderer overlay afterward.

Shared locks and reference controls outrank authored shot fields. The composer preserves each authored action/expression pair and reports exact repeated performances; the assistant must also audit semantic repetition, gaze geometry and physical plausibility. No script result guarantees natural-looking generated images.

- **Prompt** (default): render numbered natural-language prompts without an image tool.
- **Generate**: requires an explicit image-creation request. Assign reference roles, use an available image tool, audit each result, and allow at most two repairs. Generation does not authorize sharing.

Without an image tool, explicitly downgrade to Prompt mode, state that no image was generated, and provide the adapted prompts. If generation depends on a required local reference that is unavailable, do not call the tool: suspend Generate mode, request that image, and provide a clearly labeled prompt fallback when its textual role description is sufficient. Never claim to have inspected an unavailable image.

### Warning gate

Stop before rendering on an unresolved warning. If only an assistant-authored shot conflicts or repeats unintentionally, revise that draft without changing user locks/reference roles and rerun. For a conflict between actual user locks/reference controls, ask one decisive question. On a diversity warning constrained by user choices, ask whether to accept duplicates unless the user already explicitly requested repeated poses or accepted best-effort duplicates. Never append unresolved warnings to a nominal successful batch or claim accepted repetition was made diverse; “only prompts” still outputs only prompts after the gate is resolved.

## Build the result

1. Read [the aesthetic system](references/aesthetic-system.md) to render natural language.
2. For supplied images or identity consistency, read [reference-image responsibilities](references/reference-images.md).
3. For a named renderer or generation, read [model adapters](references/model-adapters.md); phrase only the final returned plan values.
4. In Generate mode, read [the quality rubric](references/quality-rubric.md) before generation.
5. Read [the example](references/examples.md) only for three-reference or targeted-repair ambiguity.

Require visible final-prompt slots for subject, every lock, any identity anchors, expression with gaze target, wardrobe, scene, in-progress action with head/body mechanics, shot distance, lens, camera position/angle, composition, foreground, lighting, 3–4 dominant colors, photography state, and reference roles. Each slot must phrase its value from the returned final plan; no adapter may silently substitute a “more suitable” value. If returned details fail the performance audit, correct the unrequested draft and rerun before rendering rather than inventing missing choreography in the final text.

## Output contract

Unless the user requests a structured plan, render each prompt as:

```markdown
### 01

完整提示词
```

Use the user's count and language. Prompt mode returns only numbered entries unless asked for a plan or explanation; resolve conflicts and warning gates first. “Only prompts” excludes seed, notes, scores, audit, warnings, and generation claims. Include `actual_seed` only when requested and allowed by that lock. Generate mode shows the image and only necessary audit or unresolved criteria.
