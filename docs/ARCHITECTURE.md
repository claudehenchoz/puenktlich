# Architecture

```
data/                       ← source of truth (YAML, validated by pydantic)
  vehicles/<op>/<id>.yaml     stats, liveries, model ref, reference ids
  operators.yaml              → badges  "operator/<id>"
  railtypes.yaml              → railtypetable (Standardised Railtype Scheme labels)
  reference/<op>.yaml         official fleet lists → completeness
models/<op>/<id>/
  recipe.py                   parametric voxel model (build() -> Model)   ┐ one of
  model.vox                   hand-made MagicaVoxel model                 ┘
  refs/                       reference images (local only unless licensed)
render/
  manifests/train.json        GoRender manifest: canvas size, lighting, 8 views
  palettes/ttd_palette.json   TTD palette + ramps (company colour, glass, …)
overrides/<id>/<scale>x/      hand-touched sprite sheets (replace rendered ones)
lang/strings.yaml             static strings (en/de/fr/it)
src/puenktlich/
  schema.py                   pydantic models + loaders + cross-file validation
  voxel/                      vox IO, palette names, Model canvas, parts library
  models.py                   recipe/vox loading → build/vox/<id>.vox
  render.py                   GoRender/Cargopositor wrappers, sprite layout + offsets
  sprites.py                  lint + preview contact sheets
  nml/generate.py + templates NML + .lng generation, nmlc compile
  completeness.py             reference lists vs implemented vehicles
  cli.py                      `pk` command
```

## Build stages

| Stage | Input | Output | Tool |
|---|---|---|---|
| model | recipe.py / model.vox | `build/vox/<id>/base/<id>_<variant>.vox` (light variants solo/head/tail/none) | numpy |
| hills | base vox | `build/vox/<id>/hill/<id>_<variant>_{up,down}.vox` (tilted ±10°) | Cargopositor `rotate_y` |
| render | vox | `build/sprites/<id>/{1,2,4}x/<name>_{8bpp,32bpp,mask}.png`: base = 24 views (8 directions + ±15° curve views), hill = 4 diagonal views | GoRender |
| touch-up | `overrides/` | replaces sheets | (GIMP/Aseprite by hand) |
| code | data + sheets | `build/nml/puenktlich.nml`, `lang/*.lng` | Jinja2 |
| compile | nml | `build/puenktlich.grf` | nmlc ≥ 0.9 |

## Key decisions

- **NML, not grf-py.** grf-py has no badge support, and its released versions hard-pin old numpy/Pillow/nml. NML 0.9 supports badges, `variant_group`, 32bpp + mask alternative sprites at all zoom levels, and is maintained by OpenTTD. Large sets (FIRS, Iron Horse, Timberwolf's) also generate NML from Python.
- **Voxels from code.** MagicaVoxel is a GUI, so AI agents can't operate it. Every model is therefore a Python recipe over a parts library, which keeps models diffable, reviewable and parametric. Hand-made `.vox` stays a first-class option.
- **Scale and offsets come from Timberwolf's Trains**, a proven GoRender set: the 256×42×72 canvas and the `temporarily_late` offset formula. A unit test pins our offsets to his generated templates.
- **Liveries are vehicle variants** (`variant_group`). Each fixed livery recolours the same company-colour sprites through `colour_mapping` → `palette_2cc(...)`, so one render serves every livery that only differs in colour.
- **Badges** tag operators (`operator/sbb`). Planned: `gauge/*`, `traction/*`, `era/*`.
- **Railtypes** use standard labels (`SAAA`→`SAAE`→`ELRL`). We never ship tracks.
- **3-part articulation** (from Timberwolf's Trains). Every vehicle of length 3–8 is an invisible front part, a sprite-carrying middle part and an invisible rear part, all the same item (`render.PARTS`). The middle part reads `curv_info` and the height of its neighbours to pick the ±15° curve views or the tilted hill views. Articulated parts add no weight or power in OpenTTD, so stats are unaffected.
  - Consequence: **articulated engines can't be flipped** in the depot (OpenTTD rejects it for any engine with the articulation callback).
- **Direction-aware lights.** OpenTTD always draws a vehicle front-first, so the model's front end faces the direction of travel. The middle part picks a light variant from its position in the train: white lamps when the unit leads, red when it is last, dark in between. Pantographs need no switching for symmetric locos: the rear (trailing) one is modelled raised.

## Roadmap after milestone 1
1. ~~Verify in-game~~: done with `pk ingame`. Lighting could still be tuned in `render/manifests/train.json`.
2. Coaches (EW IV, IC2000) with the same parts library. Push-pull control cars choose their cab-end view from their position in the train (same mechanism as the lights). Flipping isn't available for articulated vehicles.
3. ~~Curve sprites~~ and ~~hill sprites~~ for vehicles ≤ 8/8: done. Still open: vehicles longer than 8/8 and multiple units (Timberwolf's front/mid/rear section sheets).
4. ~~Pantograph switching~~: not needed for symmetric electrics. Done instead: direction-aware head/tail lights. Open: dual-mode locos lowering pantographs off the wire (`tile_powers_railtype`).
5. Cargopositor for SBB Cargo wagons (containers, car carriers). Cargopositor is already used for hill tilting.
6. Metre gauge (RhB, MGB) and rack railtypes. PostAuto buses (road vehicle manifest).
7. Blender → voxeliser path for complex noses (Giruno, FLIRT).
