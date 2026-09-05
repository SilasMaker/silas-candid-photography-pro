# Natural performance: a motivated moment, not a pose label

Read before planning any portrait. Keep user locks, identity, wardrobe, setting and tone; vary only what the request leaves open. This method applies to any supplied subject, clothing and plausible location, not a preset woman, home, outfit or ten-action checklist.

## Author the performance before the camera

Build one still-image beat as **trigger → body response → attention target → visible expression → physical consequence**. It is a frozen instant, not several consecutive actions or incompatible emotional states.

- `action`: state what is happening and why, the head's comfortable orientation, shoulder/torso relationship, the hands' different jobs, and visible support or weight transfer. Add one consequence such as a compressed cushion, resisting lid, shifting hem or displaced strand. Describe the mechanics relevant to the framing; do not demand visible feet in a headshot.
- `expression`: state a specific gaze target and its position relative to the face, then visible brow/eyelid/cheek/mouth behavior and intensity. Head orientation and eye direction are related but not identical: a small sideways glance is plausible; eyes looking upward while the head hangs sharply down is not a default recipe.
- Choose the scene and prop placement so the target is physically where the prompt says it is. A phone at lap height causes downward gaze; if the beat needs level attention, locate the phone near eye level without covering the face. Let a turning chest lead a comfortable head turn, rather than twisting only the neck.
- Use the actual wardrobe's mobility and coverage to choose an achievable action. A request for yoga does not unlock an outfit. Prefer a suitable gentle supported or standing movement over contortions; do not introduce exercise clothes, increased exposure, a new body shape or implausible fabric behavior.

Avoid isolated labels such as “自然微笑、整理发梢、自然抓拍” as finished performances. Those labels can seed ideation, but do not specify attention, support or emotion. Positive causal details do the work; a long list of “not stiff” negatives cannot replace them.

## Vary attention and energy, not just backgrounds

Before the composer, audit the whole batch by meaning, including batches assembled in several calls. A new lens or room, or a synonym for the same gesture, does not make the performance new.

For a freely varied batch of 10, aim for:

- at least 4 action families, such as thinking/pausing, handling/resisting an object, reacting/interacting, reaching/balancing/stretching, and moving/transitioning;
- at least 4 attention relationships: a nearby hand-held object, a level off-camera person/object, something above eye level, a distant point, a brief lens interaction, or restful closed eyes when the action motivates it;
- at least 3 expression/energy states; quiet concentration, curiosity, exertion, amusement and relief can coexist without turning every shot into a grin;
- no more than 2 near-identical head–gaze–expression combinations and no majority of passive lowered-head/downcast-eye shots.

These are editorial targets, not fixed quotas that override the brief. For smaller batches, vary proportionally. If the user locks a downcast pose, an all-quiet mood, a task requiring downward attention, or an exact movement sequence, preserve it and vary remaining open details. A quiet series can differentiate concentration, anticipation and relief with subtle faces; it need not include laughter, yoga or looking at the camera. A truly repeated locked pose is intentional, not a reason to secretly invent motion.

## Map to the composer

Submit one ordered `shots` array with exactly `count` objects. Each object requires `action` and `expression`; use rich, coordinated descriptions above. It accepts the same visual keys as `locks` (no new pseudo-model parameters). Author all scene/camera/foreground/light fields needed for a coherent scene; use top-level locks/reference controls for shared constraints. Include mobility and coverage constraints in the actual wardrobe value.

Precedence is **shared user locks → shared reference controls → authored shot → sampled defaults**. Per-shot details are protected from automatic repairs, but they do not grant permission to alter a shared constraint. The composer reports a conflicting draft so you can correct it before rendering. Do not put a generic shared action like “生活动作” in `locks` when you intend ten different actions; put the actual per-shot performances in `shots` and preserve broader requirements while designing them.

Minimal API illustration (not complete final prompts):

```json
{
  "count": 2,
  "seed": 42,
  "locks": {"scene": "同一个靠窗书房", "wardrobe": "用户指定的原有穿搭"},
  "shots": [
    {
      "action": "思路中断，左肘支桌托腮，右手笔尖停在纸上；头略向右倾，下巴轻抬，肩膀放松",
      "expression": "看向左上方窗外，眉心轻收、嘴唇微抿，正在思考"
    },
    {
      "action": "收到好笑的消息，右手把手机举到眼睛右前方，左手按腹，上身轻靠椅背，头随笑声轻偏",
      "expression": "看着眼睛高度的手机，眼角弯起、面颊上提、张口露齿笑"
    }
  ]
}
```

With `shots`, the script preserves order and checks identical final action/expression pairs instead of requiring four changed photographic dimensions. Different performances at the same fixed camera are valid. It does not understand synonyms, gaze geometry, anatomy or emotion; perform the semantic audit yourself. Without `shots`, the legacy random sampler remains available for exploration and backward compatibility, not as a finished natural-performance prompt.

If a warning is caused only by your authored draft, revise the conflicting unrequested detail and rerun before rendering. If actual user locks or reference roles conflict, ask the smallest necessary question. Intentionally repeated poses explicitly requested by the user count as acceptance of performance duplicates; preserve them without claiming diversity. Always recheck the final returned fields: a repair to scene, prop or framing can invalidate an earlier attention target.

## Reference and identity boundaries

Identity is stable anatomy, not a frozen facial performance. “Same person” does not mean same chin angle, gaze, eyelids or mouth. Preserve feature proportions while allowing natural expression-dependent changes, including visible effort and open-mouth laughter when appropriate. High identity consistency is not a universal neutral-face requirement.

Only an explicitly assigned pose/expression reference or user lock carries the source's downcast eyes, head tilt or smile into every shot. Identity, wardrobe and style references do not. Keep the eyes and useful facial anchors readable; let the whole body support a comfortable angle rather than forcing an extreme profile to manufacture variety.

## Before delivery and after generation

Check every intended beat: What triggered it? Where is attention directed? Does the head comfortably agree with that target? What are the hands doing? What supports the body or object? Does the visible expression arise from that event? Can the frame show the action's essential evidence? Does the clothing still obey the lock?

For actual generated images, inspect the whole batch as well as individual frames. Report unintended repetitions and failed head/gaze/body relationships from visible evidence; apply the existing rubric and bounded repair rules. A passing script or well-written prompt does not prove the rendered person looks natural. Do not promise zero stiffness or perfect identity on every render, and do not generate additional images without authorization.
