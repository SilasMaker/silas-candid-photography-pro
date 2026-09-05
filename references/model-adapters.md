# Model adapters

The composer response is the sole source of truth. For each output, an adapter receives one returned final plan plus nonvisual delivery metadata from `normalized_request` such as aspect ratio, model, mode, and reference labels. Locks and concrete reference controls are already resolved into that plan. An adapter changes ordering, density, and phrasing only: it must not resample, repair, merge an earlier draft, reread a reference for extra visual facts, or replace a returned field with a supposedly better value.

Every adapted prompt must visibly phrase the returned subject, identity anchors when present, expression, wardrobe, scene, action, shot distance, lens, camera position, composition, foreground, lighting, color scheme, and photography state. Reference-role language may identify where a returned value came from, but it cannot overlay a different value. If the composer returns an unresolved warning, resolve the warning gate before adapting rather than hiding the conflict in prose.

Within `action` and `expression`, retain the causal beat, comfortable head/body relationship, hands/support, specific gaze target and visible facial response. Never compress these back to “自然微笑、自然抓拍” or add habitual downcast eyes to a returned level/upward gaze. Identity-preservation wording protects anatomy, not a frozen pose. Remove repeated mood adjectives before cutting these relationships.

Do not claim cross-model pixel equivalence. Do not invent support for seeds, reference weights, negative-prompt fields, edit masks, quality switches, or any other parameter. Pass attachments and settings only through controls actually exposed by the available tool.

## Prompt budgets

These are editorial budgets, not claimed API limits. Locked facts and core spatial relationships never get cut; compress optional modifiers first.

| Adapter | Soft budget | Compression rule |
|---|---:|---|
| Generic | 180–320 Chinese characters or equivalent | One coherent paragraph plus a short necessary-avoidance clause |
| OpenAI ImageGen | 220–420 Chinese characters or equivalent | Separate reference roles, preserve/change boundary, then the requested moment |
| Gemini / Nano Banana | 200–380 Chinese characters or equivalent | Lead with identity consistency and exact edit boundary; keep unchanged facts explicit |
| Seedream | 120–240 Chinese characters or equivalent | Short clauses; subject and composition first; remove repeated style synonyms |
| Midjourney | 60–140 words or equivalent | Dense visual noun phrases; retain relationships, not explanatory prose |

## Generic

Render the natural-language assembly in full. End with only the negative constraints needed to protect locks, identity, candidness, and physical plausibility. Use this adapter for an unknown model and say it is the Generic fallback when explanation is allowed.

## OpenAI ImageGen

For reference-guided work, identify each image's already-normalized role, state the preserve/change boundary, and phrase the final plan's exact scene/composition relationship. Do not extract or substitute any new value at this stage. For prompt-only output, phrase these as instructions without claiming a tool-specific feature. For direct generation, use only attachment and generation controls visible in the available image tool.

## Gemini / Nano Banana

Use concise edit-oriented language: identify the returned subject and stable identity anchors, state each normalized source role, define the permitted change, and list protected returned facts. Repeat a protected fact only when needed to make the edit boundary unambiguous; otherwise keep one occurrence. Do not add model-specific syntax, parameters, or visual facts.

## Seedream

Use short, image-forward clauses. Put the returned subject/identity, wardrobe, composition, and camera relationship before atmosphere. Follow with the returned action, scene, lens/angle, foreground, light, 3–4 colors, and candid texture. Compress duplicate adjectives and long explanations, never structural slots or their values.

## Midjourney

Convert the returned plan into compact visual noun phrases while keeping verbs and spatial prepositions clear. If `normalized_request.aspect_ratio` is specified and the active Midjourney interface supports the standard aspect-ratio parameter, append `--ar W:H` (for example, `--ar 4:5`); otherwise leave the ratio in prose. Add no version, style, seed, image-weight, quality, or stylization parameter unless the user requested it and the active interface verifiably supports it.

## Adapter check

Compare the adapted text field-by-field against the returned final plan before returning it, then confirm its reference labels and aspect ratio against `normalized_request`. Every plan field must have a visible counterpart with the same value and relationship. If prompt budget and completeness conflict, remove redundant aesthetic adjectives, never a returned value or required slot.
