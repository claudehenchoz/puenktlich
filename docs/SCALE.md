# Scale

Adopted from Timberwolf's Trains (`development_notes.md`), which is designed for this GoRender canvas.

| Axis | Canvas | Scale | Notes |
|---|---|---|---|
| x (length) | 256 | 10 vox/m | 256 vox = one 8/8 vehicle = 25.6 m |
| y (width) | 42 | ≈15 vox/m (exaggerated) | car bodies 40 wide (y 1..40), centre line between y 20 and 21 |
| z (height) | 72 | ≈12–15 vox/m (exaggerated) | z 0 = rail head; floor ≈ 15; roof ≈ 50; pantograph head ≤ 68 (tilt headroom) |

- **OpenTTD length** = `round(length_m / 3.2)`, clamped to 1..8. For example, Re 460 at 18.5 m gives 6/8. Vehicles longer than 25.6 m need articulation (roadmap).
- **Front** = high x. GoRender angle `a` corresponds to OpenTTD direction `a/45` (N, NE, E, SE, S, SW, W, NW).
- **Wheels**: diameter in length scale (1.1 m → 11 vox). Wheel faces at y 7..9 and 32..34, so they sit on OpenTTD's broad-looking rails.
- **Buffers** add ~6 vox per end (0.6 m), included in length over buffers.
- Sprite offsets: `render.sprite_layout()`, ported from `temporarily_late`. Tests pin every length 3–8, both zoom levels and all five sheet kinds (normal, turn_1, turn_2, up, down) to Timberwolf's generated templates.
- **Articulation** (`render.PARTS`): front/middle/rear part lengths. Only the middle part draws the vehicle, with offsets computed for the middle length.

  | Length | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|
  | Parts | 1-1-1 | 1-1-2 | 2-1-2 | 2-2-2 | 2-3-2 | 2-4-2 |

- **Headroom**: keep models at z ≤ 68 (a raised pantograph head ≈ 67). Hill sprites tilt the model by 10°, which lifts the ends by up to ~16 voxels. Cargopositor enlarges the canvas, so nothing is clipped, but very tall models would render oversized.

Reference model for proportions: Timberwolf's `brel_class_90.vox` (18.7 m Bo'Bo' electric).

## Metre gauge
- Body ≈ 2.65–2.8 m wide: `half_width` 17–18 (instead of 19.5). Roofs are lower (Ge 4/4 III: z 46).
- Wheels: `bogie(..., gauge="metre")`, faces at y 11..13 and 28..30 (`running_gear.GAUGES`). That is the standard spacing scaled by 1000/1435.
- Rails in the companion track GRF: half-gauge = 0.765 × 1000/1435 ≈ 0.53 world units (`tracks/raster.py`). Standard OpenTTD rails sit ≈ 1.53 units apart.
- Rack (NRAN/NRAE): a central bar 0.44 units wide with lighter teeth every ~0.55 units, on every piece, slope, bridge and tunnel sprite.
