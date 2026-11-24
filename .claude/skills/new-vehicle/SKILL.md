---
name: new-vehicle
description: Add a new Swiss train/bus to Pünktlich end-to-end — reference entry, vehicle YAML, voxel recipe, render/preview loop, GRF build. Use when asked to add, model or create a vehicle (e.g. "add the Re 420", "model the RhB Ge 4/4 III").
---

# Add a vehicle

Work through these steps in order. Don't skip the preview loop.

## 1. Scaffold
```sh
uv run pk new <operator> <id> --kind locomotive|coach|control_car|emu|wagon|bus --name "SBB Re 420"
```
This writes three files. The stub already builds, so you can look at it straight away.
- `data/vehicles/<operator>/<id>.yaml` with the next free `grf_id` in the operator's block.
- `models/<operator>/<id>/recipe.py` using the builder for that kind.
- `models/<operator>/<id>/REFERENCE.md` for facts and sources.

A new operator needs an entry in `data/operators.yaml` first (with its own `grf_id_block`).

## 2. Research → REFERENCE.md
- Prototype facts: length over buffers, width, height, wheel arrangement and Ø, bogie centres, power (kW), max speed, weight, tractive effort, intro year, number built.
- Visual facts: nose shape, window layout per side, door positions, roof equipment, pantograph positions, livery (which parts follow the main colour, which stay fixed).
- Write every fact with its source into `REFERENCE.md`. Mark anything from memory as unverified. Photos go in the table with author and licence; keep local copies in `refs/` only if the licence allows.
- `models/sbb/fv_dosto/REFERENCE.md` is a good example, with measurements taken from photos.

## 3. Data
- Make sure the class exists in `data/reference/<operator>.yaml` (add it, keeping the file's ordering) and list its id under `reference:`.
- Replace every `TODO` in the vehicle YAML.
  - `length_m` is the prototype length. OpenTTD length = round(length / 3.2), at most 8 (25.6 m). The model must not be longer than `ottd_length × 3.2 m`: compress longer prototypes.
  - `railtype`: id from `data/railtypes.yaml`. Metre-gauge coaches and wagons use `metre_diesel`; rack engines use `metre_rack_*`.
  - `liveries`: the historically correct fixed livery first, then `company`. The list is append-only.
  - Names in en/de/fr/it. Operator prefixes are SBB / CFF / FFS.
  - `retire_year` only if the class has left service; otherwise `model_life_years` applies.
  - Multiple units use `cars:` (front to rear) with one recipe building every car through `model.params`. Articulated buses too (one part per car).
  - Wagons and coaches have `power_kw: 0` and a `capacity`. Control cars get a nominal `power_kw` of 1–10.

## 4. Recipe
Pick the builder and describe the vehicle as a spec. Don't copy geometry between recipes: if a shape recurs, add it to `puenktlich.voxel.parts` with a test.

| Vehicle | Builder | Example |
|---|---|---|
| Locomotive with two cabs | `parts.loco.build_loco(LocoSpec(...))` | `models/sbb/re460` |
| Coach, control car, single-deck multiple unit | `parts.coach.build_coach(CoachSpec(...))`, `CabSpec` for a cab, `mu_role` for unit cars | `models/sbb/ew4_bt`, `models/sbb/npz` |
| Double-deck multiple unit | in true proportions: `parts.regio_dosto.build_regio_car(RegioSpec(...))` (RABe 511), `parts.ir_dosto.build_ir_car(IrSpec(...))` (RABe 512), `parts.fv_dosto.build_fv_car(FvSpec(...))` (FV-Dosto); older shared layout: `parts.kiss.build_kiss_car(KissSpec(...))` (styles dtz, ic2000 on `parts/dosto.py`) | `models/sbb/rabe511`, `models/sbb/fv_dosto` |
| Articulated unit on Jakobs bogies | `parts.smile.build_smile_car(SmileSpec(...))` | `models/sbb/giruno` |
| Panorama coach | `parts.panorama.build_panorama_car(PanoramaSpec(...))` | `models/mgb/glacier` |
| Freight wagon | parts + `CARGO = CargoSpec(...)` | `models/sbb/eanos`, `models/sbb/sgns` |
| Bus | `parts.road` on `ROAD_CANVAS` | `models/postauto/citaro` |

Rules that `pk lint` checks (`src/puenktlich/checks.py`):
- High x is the front. The model is centred in x and left/right symmetric below the roof gear.
- Height: z ≤ 68, so the hill tilt has headroom.
- Buffers and couplers come from `running_gear.buffers(..., gauge=...)`, which puts them at the gauge's coupling height.
- Lamps are painted only through `parts.lights`. A recipe that takes `build(lights: Lights)` needs `model.lights: true` in the YAML. Coaches and wagons never show white lamps.
- Colours come from the shade table in `palette.py` (`P.BODY_CC1`, `P.ROOF`, `P.DARK`, … see docs/STYLE.md). Painted white is `P.OFF_WHITE`; `P.WHITE` is for lit headlamps. Never palette index 1.
- Wagons with recolourable cargo keep company colours off the body.

## 5. Look at it (repeat until it passes the checklist)
```sh
uv run pk elevation <id>          # seconds: side/front/rear at scale, in livery colours
uv run pk preview <id> --draft    # quick render: 4x only, fast sampler -> build/previews/<id>_draft.png
uv run pk preview <id>            # full contact sheet -> build/previews/<id>.png
```
- Compare `build/previews/<id>_elevation.png` with the reference photos at the same scale first; fix proportions there.
- Then read the contact sheet and go through the docs/STYLE.md review checklist. The 1× row decides whether the class is recognisable.
- Usually 3–6 iterations are needed. A full render of a light-variant vehicle takes a minute or more.

## 6. Build + verify
```sh
uv run pk lock                    # record the new grf_id and liveries in data/ids.lock
uv run pk build && make lint test && uv run pk coverage
```
- In-game: `uv run pk ingame <id>` in the background (default: 3 shots at 4x, about 4 min). Read the screenshots.
  - `--with "Passenger Carriage" --baseset abase` compares the size with base-set vehicles.
  - `--scene cargo` loads wagons at a station; buses use the road loop; `--scene infra` shows metre-gauge track pieces.
- Check: sits on the rails in every direction, livery colours are right, no offset jumps on curves and hills, couplings have no gaps, lamps are white in front and red at the rear.

## 7. Report
Tell the user what you modelled, which facts are unverified, what is approximate, and which visual details still need work. Include the preview paths.
