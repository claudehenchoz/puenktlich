# Style guide

Goal: the best-looking Swiss trains that still sit naturally next to OpenTTD's base graphics.

## Colour
- Voxels store **TTD palette indices**. Use the named constants and ramps in `src/puenktlich/voxel/palette.py`.
- **CC1 (198–205)** is the main livery colour. Fixed liveries map it with `palette_2cc(cc1, cc2)`: SBB red = `RED`, BLS = `GREEN`, RhB = `RED`, etc.
- **CC2 (80–87)** is the secondary colour: stripes, logos, doors.
- Glass = mauve window ramp (`P.GLASS`), always **inset by one voxel** (`Model.inset`) so it catches shadow.
- Painted white (stripes, logos, lettering) is `P.OFF_WHITE`. `P.WHITE` is reserved for lit headlamps.
- Avoid pure black (`P.BLACK`) except for small details such as window frames, lamp housings and axles.

### Shade table
Flat surfaces get one shade from this table (`palette.py`); GoRender does the shading. Builders and recipes use the names, never their own `P.ramp(...)` value for one of these surfaces.

| Name | Ramp value | Use |
|---|---|---|
| `P.BODY_CC1` | CC1 0.6 | Livery colour on flat body surfaces, doors |
| `P.SEAM_CC1` | CC1 0.25 | Door seams and panel lines on CC1 surfaces, inset |
| `P.BODY_CC2` | CC2 0.75 | Large secondary-colour surfaces (white coach sides) |
| `P.STRIPE_CC2` | CC2 0.85 | Stripes, bands, logo panels |
| `P.DARK_CC2` | CC2 0.4 | Dark secondary-colour bands (skirts of regional units, RABe 511) |
| `P.ROOF` | grey 0.45 | Silver-grey roofs: locomotives, coaches |
| `P.ROOF_DARK` | grey 0.3 | Anthracite roofs of modern multiple units |
| `P.ROOF_LIGHT` | grey 0.7 | Bus roofs |
| `P.DARK` | grey 0.2 | Car ends, gangways, dark window bands |
| `P.UNDERFRAME` | dark grey | Bogie frames, skirts, underfloor equipment, buffers |

Roof equipment uses `MID_GREY`/`LIGHT_GREY` so it stands out from the roof.
- Never use 253–255 (Cargopositor mask) or the animated ranges (227–254) unless intended.

## Shape
- Exaggerate what makes the class recognisable at 1× zoom (noses, window bands, pantographs). Underplay noise such as rivets and small grilles.
- Recurring shapes belong in `voxel/parts/`. Recipes describe a vehicle, not geometry.
- Symmetric vehicles: model one end via `front=True/False` loops.

## Review checklist (contact sheet `pk preview <id>`)
- [ ] Recognisable at **1×** (the 1× row, scaled ×4 in the preview)
- [ ] No holes, floating parts or stray voxels in any of the 8 directions (the sheet has 24 views: each direction ± 15°)
- [ ] CC1/CC2 mask covers exactly the livery areas (mask row)
- [ ] Windows read as windows, not as dark blobs
- [ ] Proportions match reference photos (length, height, nose rake)
- [ ] `pk lint` passes: centred, symmetric, within the length and height limits, buffers at the coupling height (`checks.py`)
- [ ] In-game (OpenTTD 15+): sits on the rails in all directions and couples without gaps
