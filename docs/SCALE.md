# Scale

Adopted from Timberwolf's Trains (`development_notes.md`), which is designed for this GoRender canvas.

| Axis | Canvas | Scale | Notes |
|---|---|---|---|
| x (length) | 256 | 10 vox/m when modelling | 256 vox = one 8/8 vehicle = 25.6 m; **rendered at half length** (below) |
| y (width) | 42 | ≈15 vox/m (exaggerated) | car bodies 40 wide (y 1..40), centre line between y 20 and 21 |
| z (height) | 72 | ≈12–15 vox/m (exaggerated) | z 0 = rail head; floor ≈ 15; roof ≈ 50; pantograph head ≤ 68 (tilt headroom) |

- **Rendered length.** OpenTTD draws one 1/8 unit as 4 px at 1x in the 90° view. On this manifest (62 px for 256 voxels) that is 16 voxels, so an 8/8 vehicle has to render **128** voxels long. Recipes still model at 10 vox/m on the full canvas. `voxel/squash.py` halves every train grid along x before Cargopositor and GoRender. Width and height stay, which gives the usual compressed OpenTTD look. When two voxels merge, the colour that is rarer in the model wins, so one-voxel seams, pillars and lamps survive. A test checks every car: rendered length ≤ 16 × OpenTTD length (+2).
- **Rendered width (calibrated to aBase).** With Timberwolf's proportions a 40-voxel body is 7 px wide end-on at 1x. aBase draws its wagons about 11.5 px wide at the same length and height (measured from `abase_base.grf`, Passenger Carriage at 4x: 46 px end-on, 130×43 px side-on). `voxel/squash.py` therefore widens each body 1.5× onto a **64-voxel-wide** render canvas. In each x-column, the rows from the first body-wide row (≥ 30 voxels across) upward are stretched. Wheels, bogie frames and buffers below the body keep their gauge, so trains stay on the rails. The train manifests GoRender gets (`build/manifests/`) are derived from Timberwolf's (`render/manifests/`), with the same pixels per voxel in every view. The layout tests stay pinned to his originals. Result at 4x: EW IV 42 px end-on, 124×55 side-on.
- **Fit models to their OpenTTD length.** A model longer than `ottd_length × 3.2 m` overlaps its neighbours in trains and in the depot window. Compress such models to the OpenTTD length, e.g. EW IV 26.4 → 25.6 m, Eanos 14.04 → 12.8 m, Sgns 19.7 → 19.2 m.
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

## Road vehicles
Canvas **126 × 40 × 48** voxels (`render/manifests/road.json`, copied from Timberwolf's Road
Vehicles), not squashed. 10 voxels per metre along x. One 1/8 unit = 4 px = 14 voxels on this
manifest (126 voxels → 36 px), so 8/8 = 11.2 m and OpenTTD road length = round(length_m / 1.4).
Models are fitted to their length: the 12 m Citaro is modelled at 11.2 m (8/8), the 18 m Citaro G
as 8.4 + 5.6 m (6 + 4), with the bellows inside each part. For rendering, road models are widened
1.5× and raised 1.15× as a whole onto a 126 × 60 × 64 canvas (aBase's Leopard bus is ~1.6× wider
and ~1.3× taller than a bus on Timberwolf's road canvas; widening alone already adds some height). Body 34 voxels wide (y 2..37, centre 19.5),
floor at z ≈ 4 (low floor), roof at z ≈ 40, roof equipment up to z ≈ 44.

## Double-deck cars
FV-Dosto (4.59 m high, `voxel/parts/dosto.py`):

| Level | z |
|---|---|
| Lower-deck body bottom (between the bogies) | 3 |
| Intermediate levels over the bogies | 12 |
| Door bottom (platform height) | 6 |
| Black lower band top | 17 |
| Lower windows | 14–26 |
| Upper windows | 42–51 |
| Double-deck roof / cab roof | 56 / 53 |

A raised pantograph on the cab roof uses `raise_height=12` to stay within the z ≤ 68 tilt headroom.

