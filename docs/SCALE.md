# Scale

Adopted from Timberwolf's Trains (`development_notes.md`), which is designed for this GoRender canvas.

| Axis | Canvas | Scale | Notes |
|---|---|---|---|
| x (length) | 256 | 10 vox/m | 256 vox = one 8/8 vehicle = 25.6 m |
| y (width) | 42 | ≈15 vox/m (exaggerated) | car bodies 40 wide (y 1..40), centre line between y 20 and 21 |
| z (height) | 72 | ≈12–15 vox/m (exaggerated) | z 0 = rail head; floor ≈ 15; roof ≈ 50; pantograph head ≤ 71 |

- **OpenTTD length** = `round(length_m / 3.2)`, clamped to 1..8. For example, Re 460 at 18.5 m gives 6/8. Vehicles longer than 25.6 m need articulation (roadmap).
- **Front** = high x. GoRender angle `a` corresponds to OpenTTD direction `a/45` (N, NE, E, SE, S, SW, W, NW).
- **Wheels**: diameter in length scale (1.1 m → 11 vox). Wheel faces at y 7..9 and 32..34, so they sit on OpenTTD's broad-looking rails.
- **Buffers** add ~6 vox per end (0.6 m), included in length over buffers.
- Sprite offsets: `render.sprite_layout()`, ported from `temporarily_late`. Its test pins it to Timberwolf's output.

Reference model for proportions: Timberwolf's `brel_class_90.vox` (18.7 m Bo'Bo' electric).
