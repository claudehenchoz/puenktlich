---
name: new-vehicle
description: Add a new Swiss train/bus to Pünktlich end-to-end — reference entry, vehicle YAML, voxel recipe, render/preview loop, GRF build. Use when asked to add, model or create a vehicle (e.g. "add the Re 420", "model the RhB Ge 4/4 III").
---

# Add a vehicle

Work through these steps in order. Don't skip the preview loop.

## 1. Research
- Collect the prototype facts: length over buffers, height, wheel arrangement and Ø, bogie centres, power (kW), max speed, weight, tractive effort, intro year and number built.
- Collect the visual facts: nose shape, window layout per side, door positions, roof equipment, pantograph positions, and the livery (which parts follow the main colour, which stay fixed).
- Write each fact with its source into the docstring at the top of the recipe.

## 2. Reference + data
- Make sure the class exists in `data/reference/<operator>.yaml`. Add it if it's missing, keeping the file's ordering.
- Create `data/vehicles/<operator>/<id>.yaml`. Copy `data/vehicles/sbb/re460.yaml` as the template.
  - `grf_id`: next free id (`uv run pk list`), permanent.
  - `railtype`: id from `data/railtypes.yaml`.
  - `liveries`: put the historically correct fixed livery first, then `company` (company_colours: true). The list is append-only.
  - Names in en/de/fr/it. Operator prefixes are SBB / CFF / FFS.

## 3. Recipe
- Create `models/<operator>/<id>/recipe.py` exposing `build() -> Model`. Use `models/sbb/re460/recipe.py` as the pattern.
- Compute length from `m(length_m)` and centre on the canvas. Remember that high x is the front.
- Use parts from `puenktlich.voxel.parts`. If you need a new generic shape (e.g. a coach door or a different bogie), add it to the parts library with a test in `tests/test_voxel.py`.
- Colours: body in `P.ramp(P.CC1, …)`, secondary in CC2, glass inset. See docs/STYLE.md.

## 4. Preview loop (repeat until it passes the checklist)
```sh
uv run pk preview <id>
```
- Read `build/previews/<id>.png`. Check each item in the docs/STYLE.md review checklist.
- Compare against reference photos in `models/<op>/<id>/refs/` if present.
- Adjust the recipe and preview again. Usually 3–6 iterations are needed.

## 5. Build + verify
```sh
uv run pk build && make lint test && uv run pk coverage
```
- In-game: `uv run pk ingame <id>` (in the background, ~4 min). Read the screenshots for each zoom. Check that the vehicle sits on the rails in every direction, the livery colours are right, there are no offset jumps, and couplings have no gaps.

## 6. Report
Tell the user what you modelled, what is approximate, and which visual details still need work. Include the preview path.
