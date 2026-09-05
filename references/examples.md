# Complete example: normalized controls, final plan, and one targeted repair

**Request:** “Use image A only for the same adult woman's identity—oval face, straight hairline, shoulder-length dark hair, and silver hoop earrings. Use image B only for composition—the woman at frame right, photographed through a bus window. Use image C only for dusk backlight and a low-saturation warm-gray palette. She must wear a white knit cardigan. Create one 4:5 candid image of her reaching for the stop-request button, using Seedream. Keep identity consistency high.”

## Composer response: sole source of truth

The role-specific facts are normalized into `reference_controls` before composition. The returned `plans[0]` already contains every lock and reference-controlled visual value; no reference or adapter overlay follows.

```json
{
  "version": "3",
  "seed": 918273645,
  "normalized_request": {
    "count": 1,
    "mode": "generate",
    "subject": "same adult woman as image A",
    "aspect_ratio": "4:5 vertical",
    "model": "seedream",
    "seed": 918273645,
    "locks": {
      "wardrobe": "white knit cardigan, relaxed silhouette, visible ribbed texture",
      "scene": "an ordinary city bus nearing a stop",
      "action": "reaching for the stop-request button while the bus is still moving",
      "shot_distance": "medium shot",
      "lens": "50mm standard perspective",
      "camera_angle": "eye level from outside/alongside the window",
      "foreground": "a soft reflection entering from the lower-left edge of the window",
      "photography_state": "documentary grain, slight motion only in the passing exterior"
    },
    "biases": {},
    "references": {
      "A": ["identity"],
      "B": ["composition"],
      "C": ["lighting", "style"]
    },
    "reference_controls": {
      "identity_anchors": "oval face, straight hairline, shoulder-length dark hair, silver hoop earrings",
      "composition": "subject on the right third with aisle space opening left, photographed through bus-window glass",
      "lighting": "dusk backlight outlining hair, with dim bus interior fill",
      "color_scheme": "warm gray glass, cream-white cardigan, muted amber rim light, charcoal interior"
    },
    "identity_policy": "high"
  },
  "plans": [
    {
      "subject": "same adult woman as image A",
      "identity_anchors": "oval face, straight hairline, shoulder-length dark hair, silver hoop earrings",
      "identity_policy": "high",
      "expression": "自然微笑",
      "wardrobe": "white knit cardigan, relaxed silhouette, visible ribbed texture",
      "scene": "an ordinary city bus nearing a stop",
      "action": "reaching for the stop-request button while the bus is still moving",
      "shot_distance": "medium shot",
      "lens": "50mm standard perspective",
      "camera_angle": "eye level from outside/alongside the window",
      "composition": "subject on the right third with aisle space opening left, photographed through bus-window glass",
      "foreground": "a soft reflection entering from the lower-left edge of the window",
      "lighting": "dusk backlight outlining hair, with dim bus interior fill",
      "color_scheme": "warm gray glass, cream-white cardigan, muted amber rim light, charcoal interior",
      "photography_state": "documentary grain, slight motion only in the passing exterior"
    }
  ],
  "repairs": [],
  "warnings": []
}
```

## Seedream-adapted prompt

This adapter only phrases the values above:

4:5竖幅，人物身份仅参考图A：保持同一成年女性的椭圆脸型、平直发际线、齐肩深色头发与银色圈形耳环，面部清晰；自然微笑，白色罗纹针织开衫。构图仅参考图B：人物位于画面右侧三分之一，隔着公交车窗玻璃拍摄，左侧留出车厢纵深。她在车辆行进中伸手按下车按钮，中景，50mm平视。左下角一小片柔和玻璃反光进入前景但不遮脸。光线与色调仅参考图C：傍晚逆光与暗车厢补光，暖灰玻璃、奶油白、暗琥珀、炭灰四个主色块。纪实颗粒，运动感只留在窗外。

## Hypothetical audit and repair

Initial audit: locks 25/25, identity 19/20, candid action 9/10, camera/composition/depth 11/15, foreground 2/10, light/color 9/10, photographic texture 8/10; **83/100**. Locks and identity pass, but the total is two points short. Foreground has the largest adjustable deficit (8 points), which alone can recover the shortfall, so it is the only selected repair target. The other deductions are not independent pass failures.

Round-1 repair instruction, changing only the selected foreground target:

> 保持图A的人物身份、白色针织开衫、人物位于画面右侧且隔窗拍摄、傍晚逆光、暖灰低饱和色调，以及动作、50mm中景平视和其他未选中内容不变。仅加强前景：让一条半透明暖灰车窗反光从左下角进入约画面宽度的12%，形成清晰前—中—后景层次；反光不得覆盖脸、发际线或银色圈形耳环。

Second audit: locks 25/25, identity 19/20, action 9/10, camera/composition/depth 14/15, foreground 8/10, light/color 9/10, texture 9/10; **93/100**. All locks hold, identity is at least 16, and total is at least 85: pass and stop. The audit does not impose separate floors on foreground or any other non-identity quality dimension.
