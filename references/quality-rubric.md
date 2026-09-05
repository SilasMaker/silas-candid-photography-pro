# Image-quality rubric and repair loop

Use this only after an explicitly authorized image-generation attempt. Audit what is visible in the actual image; do not award points for prompt text that the image failed to realize.

## 100-point audit

| Dimension | Points | Full-credit evidence |
|---|---:|---|
| User locks | 25 | Every locked subject, garment, scene, camera, composition, and other condition is visibly satisfied. |
| Subject / identity consistency | 20 | Face shape, feature proportions, hairline, signature accessories, and body proportions follow the identity policy and references. |
| Natural action and candidness | 10 | Motivated head/shoulder/body coordination (3), eyes attending to the planned target with coherent facial response (3), plausible hand/support/weight relationships (2), and a mid-flow physical consequence (2). Judge only evidence relevant to the framing. |
| Camera, composition, and spatial depth | 15 | Shot distance, lens character, photographer position, unusual composition, and depth relationships read clearly. |
| Foreground obstruction | 10 | The named intrusion enters plausibly, creates depth, and preserves protected identity anchors. |
| Lighting and color | 10 | Sources, direction, contrast, exposure, and 3–4 dominant colors match the plan. |
| Real photographic texture | 10 | Skin, fabric, surfaces, grain/blur, and incidental imperfection look camera-made rather than synthetic or studio-perfect. |

The complete pass rule is exactly:

1. every hard lock is satisfied (`25/25` for User locks);
2. total score is at least `85/100`; and
3. identity is at least `16/20`.

There are no mandatory floors for action, camera/composition/depth, foreground, lighting/color, or texture. For example, foreground `6/10` does not prevent a pass when all locks hold, identity is at least 16, and the total is at least 85. Record points and concrete visible evidence for every dimension, but do not turn descriptive expectations into additional pass gates.

For batches, also inspect a contact-sheet view or compare all outputs: did varied planned performances collapse into the same chin tilt, downward gaze or small smile? Record the observed repetitions, not merely the prompt's intended variety. Explicit user requirements for varied performances belong to User locks; missed gaze/action values that were explicitly locked are also lock misses. Otherwise score the visible failure in action/candidness and follow the existing pass and bounded-repair rules. Do not manufacture a new numerical pass gate or call a stiff result natural merely because its background changed. Preserve intentionally quiet or repeated poses requested by the user.

## Select repair targets

1. Always target any visibly missed hard lock. The locked value itself remains invariant; repair its realization rather than relaxing it.
2. Always target identity when it is below `16/20`.
3. If the total is below 85, compute the shortfall `85 - total`. For each dimension with an adjustable, unlocked aspect, compute its point deficit from full credit. Order candidates by largest deficit, breaking ties in rubric-table order, and select only as many as are needed for the selected deficits to cover the shortfall. Mandatory lock/identity targets remain selected regardless; count any realistically recoverable deficit from them toward the shortfall before adding more candidates.
4. If total is at least 85 and locks/identity pass, pass immediately even when another dimension has a low score. If the total is low but no additional point deficit is adjustable without changing a lock or reference control, stop and report the constraint instead of rewriting protected values.

If an exact identity reference required for comparison is unavailable during audit, record **0/20 (unverifiable)** rather than inventing likeness evidence; the result cannot pass. Before generation, that missing local reference blocks generation instead. A textual identity description can earn points only for its visible stated anchors, never for unseen exact likeness.

## Bounded targeted repair

Keep the original plan and locks as the invariant source of truth.

1. **Initial audit:** score all seven dimensions, apply the exact pass rule, and select targets with the rules above. If it passes, stop.
2. **Repair round 1:** rewrite only the selected targets. Express the missing visible evidence positively—for example, “a translucent leaf enters the lower-left 12% of frame while the entire face and earrings remain clear.” Preserve all untargeted dimensions, reference controls, and locks verbatim in the repair instruction. Generate once and audit again.
3. **Repair round 2:** if it still fails, rescore and select targets again. Rewrite those targets and, only when necessary, replace variables that are both unlocked and directly related to them. Record each replacement. Generate once and audit again.
4. **Stop:** after two repair rounds, do not generate again. Keep the highest-scoring result that preserves all hard locks; report its score and the still-unmet criteria. If no result preserves all hard locks, say so rather than calling one best.

Identity below 16/20 is always a repair target, even when total score is high. A hard-lock miss stays locked during every repair; never “fix” it by relaxing the requirement. A point deduction alone is not a repair target when the result already passes, and the shortfall algorithm never authorizes rewriting more dimensions than needed to reach 85.

If the image tool itself fails, allow at most one tool-level retry. A tool retry is not a quality-repair round because no image was available to audit. After that retry, stop generation, provide the adapted prompt when useful, and report the tool failure.
