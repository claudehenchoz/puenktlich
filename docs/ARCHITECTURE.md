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
| model | recipe.py / model.vox | `build/vox/<id>/base/<id>_body<k>.vox` (lamps dark) + `<id>_<variant>.vox` (lit, only where different) | numpy |
| cargo | wagon vox with mask colour 255 + cargo shapes | empty body + one model per load stage | Cargopositor `produce_empty` / `scale` / `repeat` |
| hills | base vox | `build/vox/<id>/hill/<id>_<variant>_{up,down}.vox` (tilted ±10°) | Cargopositor `rotate_y` |
| render | vox | `build/sprites/<id>/{1,2,4}x/<name>_{8bpp,32bpp,mask}.png`: base = 24 views (8 directions + ±15° curve views), hill = 4 diagonal views | GoRender |
| overlays | lit + body sheets | `<id>_<variant>_ovl_*.png`: only the pixels that differ (lamps) | numpy |
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
- **Lamps are a sprite layer** (OpenTTD sprite stacking, `TRAIN_FLAG_SPRITE_STACK`). Each distinct body is rendered and stored once with dark lamps. Each lit variant is stored as an overlay of just the pixels that differ from its body (GoRender is deterministic, so the difference is exactly the lamps). This cut the GRF from 7.4 MB to 2.4 MB; a test guards the size.
- **Multiple units** (`cars:` in the vehicle YAML) are one articulated vehicle of several cars. Each car is 3 parts (front/middle/rear) with its own model, bodies and lamp overlays. Only the end cars carry lamps; the rear cab car is always built turned round. One recipe can build all cars through `model.params` (e.g. `{car: motor}`).
- **Freight cargo** (`voxel/cargo.py`): the wagon recipe masks its load space with palette index 255 and declares `CARGO = CargoSpec(...)`. Cargopositor builds the empty body and one model per load stage (half, full). Those become sprite overlays chosen by load. The cargo *look* per cargo label is free: the heap is modelled in CC1, and the cargo layer is drawn with `palette_1cc(COLOUR_…)`. Such wagons keep their body out of the company colours, so the recolour can't bleed into it.
- **Metre gauge** ships as a companion GRF, `puenktlich_tracks.grf` (`data/tracks.yaml`, `src/puenktlich/tracks/`).
  - Railtypes: `NAAN`/`NAAE` (plain, electrified) and the rack types `NRAN`/`NRAE` (central rack bar, 40 km/h). Plain and rack metre gauge share track.
  - All sprites are drawn procedurally in world coordinates and projected exactly like OpenTTD: track (underlay, track_overlay), level crossings (rails + corner posts), bridge decks, tunnel track (with an empty portal overlay, so the base set's standard rails disappear), depots (shaded boxes with a pitched roof, one sprite per OpenTTD depot part) and GUI icons. How OpenTTD draws each group is documented in `tracks/infra.py`.
  - Still base set: catenary wires/pylons, signals, fences, the bridge structure itself.
  - Metre-gauge vehicles use `gauge="metre"` running gear, whose wheels match the narrower rails.
- **Push-pull** reuses the light variants: the control car recipe turns the model round for the `tail` variant (last in the train), so no extra NML logic is needed. OpenTTD keeps the locomotive leading when a train reverses, so this is the look players see in both directions.
- **Direction-aware lights.** OpenTTD always draws a vehicle front-first, so the model's front end faces the direction of travel. The middle part picks a light variant from its position in the train: white lamps when the unit leads, red when it is last, dark in between. Pantographs need no switching for symmetric locos: the rear (trailing) one is modelled raised.

## Roadmap after milestone 1
1. ~~Verify in-game~~: done with `pk ingame`. Lighting could still be tuned in `render/manifests/train.json`.
2. ~~EW IV coaches + push-pull~~: done (A, B, Bt IC). `voxel/parts/coach.py` builds coaches and control cars from a spec. A control car that is last in the train (`tail` light variant) is built turned round, so its cab faces outward with red lamps. Verified in OpenTTD 15.3: a reversing train swaps its vehicles end to end and the locomotive stays in front, and wagons can't lead. So a wagon control car would always ride last. The Bt is therefore a nominal 1 kW engine: players can put it at the front (cab leading, white lamps, the Re 460 pushing at the rear with red tail lamps) or at the back (cab outward, red lamps). Open: IC2000 double-deckers, older EW I/II, EW IV liveries before 2000.
3. ~~Curve sprites~~ and ~~hill sprites~~ for vehicles ≤ 8/8: done. ~~Multiple units~~: done (NPZ/Domino, 3 cars). Deferred: single bodies longer than 8/8 (Timberwolf's section sheets); Swiss stock fits by mild compression or as MU cars.
4. ~~Pantograph switching~~: not needed for symmetric electrics. Done instead: direction-aware head/tail lights. Open: dual-mode locos lowering pantographs off the wire (`tile_powers_railtype`).
5. ~~Cargopositor freight wagons~~: done (Eanos bulk with 5 recoloured cargo looks, Sgns containers). Open: car carriers, covered wagons, more cargo labels.
6. ~~Metre gauge~~: done (companion track GRF with crossings, bridges, tunnels, depots, GUI icons and rack railtypes; RhB Ge 4/4 III). Open: rack vehicles (HGe 4/4 II), metre-gauge catenary masts, PostAuto buses (road vehicle manifest).
8. GRF size: about 0.4–0.5 MB per car body (all zooms). With hundreds of vehicles, consider a split "HD" GRF for the 4× sprites.
7. Blender → voxeliser path for complex noses (Giruno, FLIRT).
