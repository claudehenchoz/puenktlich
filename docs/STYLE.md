# Style guide

Goal: the best-looking Swiss trains that still sit naturally next to OpenTTD's base graphics.

## Colour
- Voxels store **TTD palette indices**. Use the named constants and ramps in `src/puenktlich/voxel/palette.py`.
- **CC1 (198–205)** is the main livery colour. Fixed liveries map it with `palette_2cc(cc1, cc2)`: SBB red = `RED`, BLS = `GREEN`, RhB = `RED`, etc.
- **CC2 (80–87)** is the secondary colour: stripes, logos, doors.
- Paint flat surfaces with a mid-ramp index (`P.ramp(P.CC1, 0.6)`). GoRender does the shading.
- Glass = mauve window ramp (`P.GLASS`), always **inset by one voxel** (`Model.inset`) so it catches shadow.
- Use the darker CC1 index (`ramp(CC1, 0.25)`) for seams and door outlines, again inset.
- Roof equipment, bogies and underframe use greys (`DARK_GREY`/`MID_GREY`/`LIGHT_GREY`). Avoid pure black except for small details.
- Never use 253–255 (Cargopositor mask) or the animated ranges (227–254) unless intended.

## Shape
- Exaggerate what makes the class recognisable at 1× zoom (noses, window bands, pantographs). Underplay noise such as rivets and small grilles.
- Recurring shapes belong in `voxel/parts/`. Recipes describe a vehicle, not geometry.
- Symmetric vehicles: model one end via `front=True/False` loops.

## Review checklist (contact sheet `pk preview <id>`)
- [ ] Recognisable at **1×** (the 1× row, scaled ×4 in the preview)
- [ ] No holes, floating parts or stray voxels in any of the 8 views
- [ ] CC1/CC2 mask covers exactly the livery areas (mask row)
- [ ] Windows read as windows, not as dark blobs
- [ ] Proportions match reference photos (length, height, nose rake)
- [ ] In-game (OpenTTD 15+): sits on the rails in all directions and couples without gaps
