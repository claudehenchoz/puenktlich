# Pünktlich — agent guide

Swiss trains & buses for OpenTTD. Vision: `docs/IDEA.md`. Architecture: `docs/ARCHITECTURE.md`.

## Pipeline (one line)
`data/vehicles/*.yaml` + `models/<op>/<id>/recipe.py` → `build/vox/<id>.vox` → GoRender (1×/2×/4×, 8bpp + 32bpp + mask) → `overrides/` → generated NML → `nmlc` → `build/puenktlich.grf`

## Commands
- `uv run pk list`: list vehicles
- `uv run pk new <operator> <id> --kind locomotive|coach|control_car|emu|wagon|bus`: start a vehicle from a stub that already builds (YAML with the next free `grf_id`, recipe, `REFERENCE.md`).
- `uv run pk elevation <id>`: orthographic side/front/rear views of every car in livery colours (`build/previews/<id>_elevation.png`, seconds, no GoRender). Use it to compare proportions with reference photos at the same scale.
- `uv run pk preview <id>`: build the model, render it, and write the contact sheet `build/previews/<id>.png` (in the first livery's colours). **Look at it** (Read the PNG) after every model change. `--draft` is the quick look while modelling: 4× only with GoRender's fast sampler, into `build/previews/<id>_draft.png`.
- `uv run pk build`: full build to `build/puenktlich.grf`. `pk build <ids>` builds only those vehicles into `build/puenktlich_partial.grf`, which `pk ingame <ids>` picks up when it is newer.
- `uv run pk lock`: record new vehicles and liveries in `data/ids.lock`.
- `uv run pk ingame <id> [--zoom 4x] [--scene loop|infra|cargo|road]`: headless OpenTTD 15+ run (isolated profile in `build/ingame/`). It builds a test loop, runs the vehicle, and screenshots `build/ingame/<zoom>/…/screenshot/*.png`. `--scene cargo` puts a fitting loco in front of two wagons and full-loads them at a station next to a raw industry (empty → loading → full); buses always use the road loop. Takes ~1 min per shot, so run it in the background. Read the screenshots.
- `uv run pk lint`: data, `data/ids.lock`, the modelling conventions (`src/puenktlich/checks.py`) and the rendered sheets. `make lint` adds ruff and skips the sheets.
- `make test` (renders anything that changed, then compiles), `make test-fast` (seconds, no renders or GRF compiles): always green before committing
- `uv run pk coverage`: completeness vs `data/reference/*.yaml`, writes `docs/COMPLETENESS.md`
- First-time setup: `make setup` (needs Go; builds gorender + cargopositor into `.tools/bin`)

## Rules that protect saved games (never break these)
- `grf_id` in vehicle YAML is permanent. Never change or reuse one. Each operator owns a block of 100 (`grf_id_block` in `data/operators.yaml`); `pk new` picks the next free id.
- `liveries:` lists are **append-only**. Item id = `grf_id * 8 + livery index`.
- The GRFID (`PKCH`, in `src/puenktlich/nml/generate.py`) never changes.
- `data/ids.lock` records both rules; `pk lint` and the tests fail when the data disagrees with it. Run `pk lock` after adding a vehicle or livery, and never edit or remove its entries.

## Modelling conventions (details: docs/SCALE.md, docs/STYLE.md)
- Canvas 256 × 42 × 72 voxels = one 8/8 vehicle. **x is length, and high x is the FRONT/cab 1.** y is width, z is height, and z=0 is the rail head.
- 10 voxels/m along x. Width and height are exaggerated: a body is 40 wide (y 1..40), the floor is at z≈15, and a roof is at z≈50.
- Trains are **rendered at half length and at their real body width** (`voxel/squash.py`; wheels keep their gauge): OpenTTD draws 1/8 unit as 16 rendered voxels. Recipes are authored unchanged on the 256 × 42 × 72 canvas; GoRender gets derived manifests from `build/manifests/`. A model must not be longer than `ottd_length × 3.2 m`, or it overlaps its neighbours in trains and in the depot window (a test checks this). Compress longer prototypes to their OpenTTD length. Check against base-set wagons with `pk ingame <id> --with "Passenger Carriage" --baseset abase`. **Every train recipe sets `BODY_WIDTH_M`** (real body width in metres; `Z_PER_M` if its height scale isn't 12.2 vox/m): the render step rescales the body across to that width at the height scale (2.80 m → 34 voxels). Author bodies as usual (40 wide); a model authored at its real width (`models/sbb/fv_dosto`) renders unchanged.
- Centre the vehicle in x. OpenTTD length (1/8 units) = round(length_m / 3.2).
- Voxel values are **TTD palette indices**. Use `puenktlich.voxel.palette` names and ramps, never magic numbers.
  - The body colour that should follow the livery is **CC1 (198–205)**. Secondary/stripe colour is **CC2 (80–87)**.
  - Glass uses `P.GLASS`. Fixed greys are for roof, bogies and underframe.
  - Flat surfaces take their shade from the **shade table** in `palette.py` (`P.BODY_CC1`, `P.SEAM_CC1`, `P.BODY_CC2`, `P.STRIPE_CC2`, `P.ROOF`, `P.ROOF_DARK`, `P.DARK`, `P.UNDERFRAME`; docs/STYLE.md), not from a recipe's own `P.ramp(...)`. Painted white is `P.OFF_WHITE`; `P.WHITE` is only for lit headlamps.
- Build models from `puenktlich.voxel.parts` (Shell, bogie, buffers, pantograph…). If a shape recurs, add a part rather than copying code between recipes. Shared details: `body.door_outline`, `body.louvres`, `body.rounded_window`, `body.gangway`, `roof.roof_ribs`, `roof.roof_vents`, `running_gear.underframe`.
- `running_gear.buffers(..., gauge=...)` puts buffers and couplers at the gauge's coupling height (`COUPLING_Z`: standard gauge side buffers, metre gauge a central buffer), so coupled vehicles line up. Bogies: `bogie(style="loco"|"coach"|"freight")`.
- `pk lint` checks the conventions on every model (`checks.py`): canvas, z ≤ 68, centred in x, left/right symmetric below z 44 (buses exempt), length between 85 % and 100 % of the OpenTTD length, buffer plates at the coupling height, no lit lamps in dark bodies, no white lamps on coaches and wagons, no special palette indices, no company colours on wagons with recolourable cargo, a `BODY_WIDTH_M` on every recipe.
- Hand-edited models: set `model.kind: vox` and put `model.vox` in the model dir. It can be opened in MagicaVoxel.
- Hand touch-ups of rendered sprites go in `overrides/<id>/<scale>x/<id>_<kind>.png` and replace the whole sheet. Re-check them after model changes.

## Rendering model (curves, hills, lights)
- Vehicles of length 3–8 are 3 articulated parts of the same item (`render.PARTS`). Only the middle part draws. It picks ±15° curve views and ±10° hill views from its neighbours. **Articulated engines can't be flipped in the depot.**
- Recipes can take `build(lights: Lights)` and set `model.lights: true` in YAML. That gets them 4 variants (solo/head/tail/none) chosen in-game by position in the train. **Paint lamps only via `voxel.parts.lights` (`lamps()`, or `lamp_cluster()` with `lights.state(...)`)**, so the dark body (`Lights.dark`) stays lamp-free.
- Sheet names: `<id>_body<k>` = bodies (lamps dark), `<id>_<variant>` = lit render (build intermediate), `<id>_<variant>_ovl` = lamp overlay (in the GRF). `models.variant_plan()` shows the mapping.
- Locomotives with a cab at each end: `voxel.parts.loco.build_loco(LocoSpec(...), lights)` (see `models/sbb/re460`).
- Coaches and control cars: build them with `voxel.parts.coach.build_coach(CoachSpec(...), lights)`. Give a `CabSpec` for a control car; push-pull orientation is automatic. Wagons have `power_kw: 0`, a `capacity` (split evenly over the 3 parts) and `railtype: standard`. Control cars get a nominal `power_kw` (1–10), so they can lead a train.
- Double-deck cars: the Stadler KISS units and the FV-Dosto have builders in true proportions, measured from type sketches, 3D models and photos: `voxel.parts.regio_dosto.build_regio_car(RegioSpec(...))` (RABe 511, `models/sbb/rabe511/REFERENCE.md`), `voxel.parts.ir_dosto.build_ir_car(IrSpec(...))` (RABe 512). The RABe 514 and IC2000 use `voxel.parts.kiss.build_kiss_car(KissSpec(...))` on the shared layout in `voxel/parts/dosto.py`. The FV-Dosto is `voxel.parts.fv_dosto.build_fv_car(FvSpec(...))` in true proportions, measured from a 3D model and the factsheets (`models/sbb/fv_dosto/REFERENCE.md`). Shells can vary their floor and roof along x (`Shell(floor_at=..., roof_at=...)`). `EndShape(profile="ellipse")` gives rounded modern noses. `body.face_mask()` paints the front skin of raked noses, and `lamp_cluster(face=True)` puts lamps on it.
- Panorama coaches (Glacier Express): `voxel.parts.panorama.build_panorama_car(PanoramaSpec(kind=...))`, on a `CrossSection(chamfer_from=…, chamfer_inset=…)` bevelled roof that carries the roof glazing (see `models/mgb/glacier`).
- Articulated units on Jakobs bogies: `voxel.parts.smile.build_smile_car(SmileSpec(...))` (see `models/sbb/giruno`). Each car draws its own half of every shared bogie (one wheelset, frame clipped at the car end); positions are real metres scaled to the fitted length (`real_m` → `length_m`).
- Multiple units: `cars:` instead of `model:` in the vehicle YAML. One recipe can build all cars via `model.params`. Car recipes paint lamps by role (`CoachSpec(mu_role="front"|"middle"|"rear")`, `lights.mu_lights`). Sheet names are prefixed `<id>_c<k>_`. The buy menu shows `<id>_purchase`: front, second and rear car side by side (`sprites.make_purchase_sheet`).
- Capacity is shared out exactly over the articulated parts (`nml.generate.split_capacity`, a `cargo_capacity` callback when it doesn't divide evenly). The buy menu can only show the per-part property times the part count, so it may be a few seats off for such vehicles.
- Freight wagons: paint the load space with `voxel.cargo.CARGO_MASK` (255) and define `CARGO = CargoSpec(...)` in the recipe (see `models/sbb/eanos`). Model recolourable cargo in CC1 and keep the wagon body out of company colours. Set `refit_classes` and the default cargo in `capacity`.
- Metre gauge: `railtype: metre_ac`/`metre_diesel` (rack: `metre_rack_ac`/`metre_rack_diesel`) and `bogie(..., gauge="metre")`. Coaches/wagons use `metre_diesel` (wagons' railtypes don't limit where a train goes). **Rack rule:** a train may only enter track on which one of its engines has power, so `data/tracks.yaml` gives adhesion railtypes no power on rack track: only trains with a rack engine (`metre_rack_*`, e.g. HGe 4/4 II) can climb rack sections. Coaches: `CoachSpec(length_m=…, gauge="metre", body_colour=…)` (see `models/rhb/ew4`). Track GRF art: `pk tracks-preview`; in-game check of crossings/bridges/tunnels/depots/rack: `pk ingame <id> --scene infra`. The vehicles need `build/puenktlich_tracks.grf` (built by `pk build`, loaded first by `pk ingame`).
- Keep models at z ≤ 68 so the 10° hill tilt has headroom (a test checks this).
- Road vehicles (`kind: bus`, no `railtype`): canvas **126 × 40 × 48** (`Model.new(ROAD_CANVAS)`, `render/manifests/road.json`, 8 views, offsets ported from Timberwolf's Road Vehicles), 10 vox/m, not squashed; rendered at the real width like trains (`BODY_WIDTH_M`, `Z_PER_M = 13.9`), height unchanged. 1/8 = 1.4 m, so 8/8 = 11.2 m; fit models to it (12 m Citaro → 11.2 m). Parts in `voxel.parts.road`; doors on the right-hand side (`DOOR_SIDE`, high y). No articulation split, curve or hill sprites; an articulated bus is `cars:` with one OpenTTD part per car (Citaro G = 6 + 4). Lamps are painted statically (no light variants yet). Use `model.cy` (not `CENTRE_Y`) in parts that serve both canvases.
- A full render of a light-variant vehicle is ~1 min (4 variants × 3 renders). Unchanged vox files are skipped.

## Adding a vehicle
Use the `new-vehicle` skill (`.claude/skills/new-vehicle/SKILL.md`). In short: add a reference entry → write the YAML → write the recipe → `pk preview` loop → `pk build` → tests.

## Gotchas
- `pk ingame` defaults to 4x and 3 shots (straight, ramp, corner) ≈ 3.5 min; `--shots 6 --zoom all` for the full set. Each screenshot costs one game month ≈ 67 s, and OpenTTD can't run faster headless (no fast-forward without the GUI; the calendar can only be slowed). Several zoom levels share one OpenTTD run in `build/ingame/all/` (the train waits one month per zoom at each stop); `--parallel` starts one OpenTTD per zoom instead. A run that times out or misses a screenshot is reported as an error. Renderers run under `nice`.
- Rendering runs several vehicles at once: `--jobs N` or `PK_JOBS` (default: half the cores, and no more than fit into free memory at about 3.5 GB per GoRender process; `render.gorender` caps each process with `GOMEMLIMIT`). `PK_TIMING=1 pk render` prints time per stage.
- Caches: `build/.cache/vox/` (recipe grids, keyed by the recipe and the `puenktlich` modules it imports, so editing one part only rebuilds the models that use it), `build/.cache/cargopositor/` (keyed by batch + inputs; Cargopositor's `scale` is non-deterministic, the cache pins the first result), track GRF and `nmlc` skipped by stamps. A no-op `pk build` renders nothing and doesn't run `nmlc`; `pk render` reports how many sheets it rewrote. A full `pk build` prunes cache entries unused for 14 days. `pk clean` wipes all caches.
- Don't name scratch scripts after stdlib modules (`re.py`, `types.py`…).
- GoRender skips outputs newer than the input. A changed GoRender binary, palette or manifest re-renders by itself (`.render_<manifest>.stamp` in each sprite directory); `pk render --force` is only needed after changing the render code in `src/`.
- Never use palette index 1 (GoRender renders it transparent: holes in black bands and frames). `P.BLACK` is index 2 and `P.ramp(P.GREY, …)` skips 1; the build maps stray 1s to 2.
- GoRender fills unused sheet area with opaque white / index 255. Only the manifest rectangles matter.
- In-game checks: use `pk ingame` (automated) or `pk install`, then enable "Pünktlich" in your own game. OpenTTD's null video driver can't take screenshots; `pk ingame` uses SDL's offscreen backend instead.
