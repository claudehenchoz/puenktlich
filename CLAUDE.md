# Pünktlich — agent guide

Swiss trains & buses for OpenTTD. Vision: `docs/IDEA.md`. Architecture: `docs/ARCHITECTURE.md`.

## Pipeline (one line)
`data/vehicles/*.yaml` + `models/<op>/<id>/recipe.py` → `build/vox/<id>.vox` → GoRender (1×/2×/4×, 8bpp + 32bpp + mask) → `overrides/` → generated NML → `nmlc` → `build/puenktlich.grf`

## Commands
- `uv run pk list`: list vehicles
- `uv run pk preview <id>`: build the model, render it, and write the contact sheet `build/previews/<id>.png`. **Look at it** (Read the PNG) after every model change.
- `uv run pk build`: full build to `build/puenktlich.grf`
- `uv run pk ingame <id> [--zoom 4x]`: headless OpenTTD 15+ run (isolated profile in `build/ingame/`). It builds a test loop, runs the vehicle in all its liveries, and screenshots `build/ingame/<zoom>/…/screenshot/*.png`. Takes ~1 min per shot, so run it in the background. Read the screenshots.
- `uv run pk lint`, `make lint`, `make test`: always green before committing
- `uv run pk coverage`: completeness vs `data/reference/*.yaml`, writes `docs/COMPLETENESS.md`
- First-time setup: `make setup` (needs Go; builds gorender + cargopositor into `.tools/bin`)

## Rules that protect saved games (never break these)
- `grf_id` in vehicle YAML is permanent. Never change or reuse one. Pick the next free id (`pk list`).
- `liveries:` lists are **append-only**. Item id = `grf_id * 8 + livery index`.
- The GRFID (`PKCH`, in `src/puenktlich/nml/generate.py`) never changes.

## Modelling conventions (details: docs/SCALE.md, docs/STYLE.md)
- Canvas 256 × 42 × 72 voxels = one 8/8 vehicle. **x is length, and high x is the FRONT/cab 1.** y is width, z is height, and z=0 is the rail head.
- 10 voxels/m along x. Width and height are exaggerated: a body is 40 wide (y 1..40), the floor is at z≈15, and a roof is at z≈50.
- Centre the vehicle in x. OpenTTD length (1/8 units) = round(length_m / 3.2).
- Voxel values are **TTD palette indices**. Use `puenktlich.voxel.palette` names and ramps, never magic numbers.
  - The body colour that should follow the livery is **CC1 (198–205)**. Secondary/stripe colour is **CC2 (80–87)**.
  - Glass uses `P.GLASS`. Fixed greys are for roof, bogies and underframe.
- Build models from `puenktlich.voxel.parts` (Shell, bogie, buffers, pantograph…). If a shape recurs, add a part rather than copying code between recipes.
- Hand-edited models: set `model.kind: vox` and put `model.vox` in the model dir. It can be opened in MagicaVoxel.
- Hand touch-ups of rendered sprites go in `overrides/<id>/<scale>x/<id>_<kind>.png` and replace the whole sheet. Re-check them after model changes.

## Rendering model (curves, hills, lights)
- Vehicles of length 3–8 are 3 articulated parts of the same item (`render.PARTS`). Only the middle part draws. It picks ±15° curve views and ±10° hill views from its neighbours. **Articulated engines can't be flipped in the depot.**
- Recipes can take `build(lights: Lights)` and set `model.lights: true` in YAML. That gets them 4 variants (solo/head/tail/none) chosen in-game by position in the train. **Paint lamps only via `voxel.parts.lights` (`lamps()`, or `lamp_cluster()` with `lights.state(...)`)**, so the dark body (`Lights.dark`) stays lamp-free.
- Sheet names: `<id>_body<k>` = bodies (lamps dark), `<id>_<variant>` = lit render (build intermediate), `<id>_<variant>_ovl` = lamp overlay (in the GRF). `models.variant_plan()` shows the mapping.
- Coaches and control cars: build them with `voxel.parts.coach.build_coach(CoachSpec(...), lights)`. Give a `CabSpec` for a control car; push-pull orientation is automatic. Wagons have `power_kw: 0`, a `capacity` (split evenly over the 3 parts) and `railtype: standard`. Control cars get a nominal `power_kw` (1–10), so they can lead a train.
- Multiple units: `cars:` instead of `model:` in the vehicle YAML. One recipe can build all cars via `model.params`. Car recipes paint lamps by role (`CoachSpec(mu_role="front"|"middle"|"rear")`). Sheet names are prefixed `<id>_c<k>_`.
- Freight wagons: paint the load space with `voxel.cargo.CARGO_MASK` (255) and define `CARGO = CargoSpec(...)` in the recipe (see `models/sbb/eanos`). Model recolourable cargo in CC1 and keep the wagon body out of company colours. Set `refit_classes` and the default cargo in `capacity`.
- Metre gauge: `railtype: metre_ac`/`metre_diesel` and `bogie(..., gauge="metre")`. The vehicles need `build/puenktlich_tracks.grf` (built by `pk build`, loaded first by `pk ingame`).
- Keep models at z ≤ 68 so the 10° hill tilt has headroom (a test checks this).
- A full render of a light-variant vehicle is ~1 min (4 variants × 3 renders). Unchanged vox files are skipped.

## Adding a vehicle
Use the `new-vehicle` skill (`.claude/skills/new-vehicle/SKILL.md`). In short: add a reference entry → write the YAML → write the recipe → `pk preview` loop → `pk build` → tests.

## Gotchas
- Don't name scratch scripts after stdlib modules (`re.py`, `types.py`…).
- GoRender skips outputs newer than the input. Use `pk render --force` after changing the manifest or palette.
- GoRender fills unused sheet area with opaque white / index 255. Only the manifest rectangles matter.
- In-game checks: use `pk ingame` (automated) or `pk install`, then enable "Pünktlich" in your own game. OpenTTD's null video driver can't take screenshots; `pk ingame` uses SDL's offscreen backend instead.
