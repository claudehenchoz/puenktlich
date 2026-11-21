# Pünktlich — agent guide

Swiss trains & buses for OpenTTD. Vision: `docs/IDEA.md`. Architecture: `docs/ARCHITECTURE.md`.

## Pipeline (one line)
`data/vehicles/*.yaml` + `models/<op>/<id>/recipe.py` → `build/vox/<id>.vox` → GoRender (1×/2×/4×, 8bpp + 32bpp + mask) → `overrides/` → generated NML → `nmlc` → `build/puenktlich.grf`

## Commands
- `uv run pk list`: list vehicles
- `uv run pk preview <id>`: build the model, render it, and write the contact sheet `build/previews/<id>.png`. **Look at it** (Read the PNG) after every model change.
- `uv run pk build`: full build to `build/puenktlich.grf`
- `uv run pk ingame <id> [--zoom 4x] [--scene loop|infra|cargo|road]`: headless OpenTTD 15+ run (isolated profile in `build/ingame/`). It builds a test loop, runs the vehicle, and screenshots `build/ingame/<zoom>/…/screenshot/*.png`. `--scene cargo` puts a fitting loco in front of two wagons and full-loads them at a station next to a raw industry (empty → loading → full); buses always use the road loop. Takes ~1 min per shot, so run it in the background. Read the screenshots.
- `uv run pk lint`, `make lint`, `make test` (~8 s; `make test-fast` ~1 s skips GRF compiles): always green before committing
- `uv run pk coverage`: completeness vs `data/reference/*.yaml`, writes `docs/COMPLETENESS.md`
- First-time setup: `make setup` (needs Go; builds gorender + cargopositor into `.tools/bin`)

## Rules that protect saved games (never break these)
- `grf_id` in vehicle YAML is permanent. Never change or reuse one. Pick the next free id (`pk list`).
- `liveries:` lists are **append-only**. Item id = `grf_id * 8 + livery index`.
- The GRFID (`PKCH`, in `src/puenktlich/nml/generate.py`) never changes.

## Modelling conventions (details: docs/SCALE.md, docs/STYLE.md)
- Canvas 256 × 42 × 72 voxels = one 8/8 vehicle. **x is length, and high x is the FRONT/cab 1.** y is width, z is height, and z=0 is the rail head.
- 10 voxels/m along x. Width and height are exaggerated: a body is 40 wide (y 1..40), the floor is at z≈15, and a roof is at z≈50.
- Trains are **rendered at half length and 1.5× wider body** (`voxel/squash.py`, calibrated to aBase; wheels keep their gauge): OpenTTD draws 1/8 unit as 16 rendered voxels. Recipes are authored unchanged on the 256 × 42 × 72 canvas; GoRender gets derived manifests from `build/manifests/`. A model must not be longer than `ottd_length × 3.2 m`, or it overlaps its neighbours in trains and in the depot window (a test checks this). Compress longer prototypes to their OpenTTD length. Check against base-set wagons with `pk ingame <id> --with "Passenger Carriage" --baseset abase`.
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
- Metre gauge: `railtype: metre_ac`/`metre_diesel` (rack: `metre_rack_ac`/`metre_rack_diesel`) and `bogie(..., gauge="metre")`. Coaches/wagons use `metre_diesel` (wagons' railtypes don't limit where a train goes). **Rack rule:** a train may only enter track on which one of its engines has power, so `data/tracks.yaml` gives adhesion railtypes no power on rack track: only trains with a rack engine (`metre_rack_*`, e.g. HGe 4/4 II) can climb rack sections. Coaches: `CoachSpec(length_m=…, gauge="metre", body_colour=…)` (see `models/rhb/ew4`). Track GRF art: `pk tracks-preview`; in-game check of crossings/bridges/tunnels/depots/rack: `pk ingame <id> --scene infra`. The vehicles need `build/puenktlich_tracks.grf` (built by `pk build`, loaded first by `pk ingame`).
- Keep models at z ≤ 68 so the 10° hill tilt has headroom (a test checks this).
- Road vehicles (`kind: bus`, no `railtype`): canvas **126 × 40 × 48** (`Model.new(ROAD_CANVAS)`, `render/manifests/road.json`, 8 views, offsets ported from Timberwolf's Road Vehicles), 10 vox/m, not squashed. 1/8 = 1.4 m, so 8/8 = 11.2 m; fit models to it (12 m Citaro → 11.2 m). Parts in `voxel.parts.road`; doors on the right-hand side (`DOOR_SIDE`, high y). No articulation split, curve or hill sprites; an articulated bus is `cars:` with one OpenTTD part per car (Citaro G = 6 + 4). Lamps are painted statically (no light variants yet). Use `model.cy` (not `CENTRE_Y`) in parts that serve both canvases.
- A full render of a light-variant vehicle is ~1 min (4 variants × 3 renders). Unchanged vox files are skipped.

## Adding a vehicle
Use the `new-vehicle` skill (`.claude/skills/new-vehicle/SKILL.md`). In short: add a reference entry → write the YAML → write the recipe → `pk preview` loop → `pk build` → tests.

## Gotchas
- `pk ingame` defaults to 4x and 3 shots (straight, ramp, corner) ≈ 3.5 min; `--shots 6 --zoom all` for the full set. Each shot costs one game month ≈ 67 s, and OpenTTD can't run faster headless (no fast-forward without the GUI; the calendar can only be slowed). Zoom levels run one after another (`--parallel` opts in); renderers run under `nice`.
- Caches: `build/.cache/vox/` (recipe grids, keyed by recipe + voxel library source), `build/.cache/cargopositor/` (keyed by batch + inputs; Cargopositor's `scale` is non-deterministic, the cache pins the first result), track GRF skipped by a source digest. A no-op `pk build` takes ~3 s and renders nothing; `pk render` reports how many sheets it rewrote. `pk clean` wipes all caches.
- Don't name scratch scripts after stdlib modules (`re.py`, `types.py`…).
- GoRender skips outputs newer than the input. Use `pk render --force` after changing the manifest or palette.
- GoRender fills unused sheet area with opaque white / index 255. Only the manifest rectangles matter.
- In-game checks: use `pk ingame` (automated) or `pk install`, then enable "Pünktlich" in your own game. OpenTTD's null video driver can't take screenshots; `pk ingame` uses SDL's offscreen backend instead.
