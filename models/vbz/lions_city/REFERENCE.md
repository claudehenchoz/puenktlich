# VBZ MAN Lion's City: reference

| Vehicle | Type | VBZ nos. | Built | Length | OpenTTD |
|---|---|---|---|---|---|
| `vbz_lions_city_12e` | Lion's City 12 E (NL 367, "12CE"), battery | 636–657 | 2022/23 | 12.2 m | 8 |
| `vbz_lions_city_18e` | Lion's City 18 E (NG 734, "18CE"), battery | 474–503 | 2022–2024 | 18.06 m | 6 + 5 |
| `vbz_lions_city_gl` | Lion's City GL (A40, NG 363), diesel | 510–515 | 2015 | 18.75 m | 6 + 5 |

Builder: `puenktlich.voxel.parts.citybus`, front style `man` (raked front, long roof slope,
white "V" over the glazing behind the front door).

## Sources
Research notes "VBZ MAN Lion's City 12 E / 18 E / G – 3D Models and Modelling References"
(docs/research/vbz):
- MAN "Einfach einsteigen" eMobility brochure (2020, drawings p. 16): 12 E and 18 E side views,
  including the **3-door right sides** VBZ uses; MAN datasheet "Lion's City 18 E".
- MAN Lion's City GL flyer and type sketch (3 doors).
- VBZ vehicle pages (Batteriebusse, Autobusse) and the VBZ 12CE livery rendering (2021).

## Layout (metres behind the front tip)
- **12 E** (drawing, 104.9 px/m): axles 2.75, 8.82; doors 0.45–1.83, 5.73–7.1, 9.7–11.1;
  battery packs, heat-pump A/C and further packs on the roof.
- **18 E** (datasheet overhangs 2,775 / 3,405 mm, wheelbases 5,200 / 6,680 mm; drawing row 3,
  89.4 px/m): axles 2.74, 8.0, 14.7; joint 9.79; doors 0.45–1.81, 4.9–6.3, 11.6–13.0.
- **GL** (wheelbases 5,875 / 6,770 mm): axles 2.75, 8.63, 15.4; joint about 10.2; doors
  0.45–1.8, 5.0–6.3, 12.2–13.5 (estimated from the type sketch); engine at the rear, no rear
  window; 2.50 m wide, 2.98 m high.

## Data
| | 12 E | 18 E | GL |
|---|---|---|---|
| Height | 3.32 m | 3.32 m | 2.98 m (with A/C) |
| Drive | 160 kW cont. / 240–270 kW peak | 2 motors, 320 kW cont. / 400–540 kW peak | D2066 LUH52, 265 kW |
| Top speed | 85 km/h | 85 km/h | – (80 assumed) |
| Places | 67 | 103 | 97 |
| Gross weight | 19.5 t | 29.9 t | 28 t |

## Livery
VBZ white and blue (see `models/vbz/hess_trolley/REFERENCE.md`).

## Approximations
- The GL is drawn 2.55 m wide like the others (the canvas section is shared); `BODY_WIDTH_M`
  is 2.55 for the recipe.
- Articulated buses fitted to 6 + 5 OpenTTD units (15.4 m).
