# VBZ Volvo 7900 hybrids: reference

| Vehicle | Type | VBZ nos. | Built | Length | OpenTTD |
|---|---|---|---|---|---|
| `vbz_volvo7900_eh` | 7900 Electric Hybrid (plug-in, OppCharge) | 620–635 | 2019/20 | 12.13 m | 8 |
| `vbz_volvo7900_lah` | 7900 Hybrid articulated "LAH" | 190, 440–457 | 2015, 2017/18 | 18.13 m | 6 + 5 |
| `vbz_volvo7900_ha` | 7900 Hybrid articulated "HA", 18.7 m option | 458–472 | 2020 | 18.74 m | 6 + 5 |

Builder: `puenktlich.voxel.parts.citybus`, front style `volvo` (domed roof cap over the
windscreen, black grille band between the lamps).

## Sources
Research notes "VBZ Volvo 7900 Electric Hybrid / HA / LAH – 3D Models and Modelling References"
(docs/research/vbz): Volvo brochures (12,134 mm and 18,044 mm drawings), Swiss Volvo rescue sheets
(Rettungsdatenblätter 7900H 12 m 3 doors, 7900HA 18 m and 18.7 m), the Volvo OppCharge fact
sheet, VBZ [Hybridbusse](https://www.stadt-zuerich.ch/vbz/de/die-vbz/fahrzeuge/busse/hybridbusse.html)
page and bus-bild.de photos of VBZ 455, 462, 621 and others.

## Layout (metres behind the front tip)
- **Electric Hybrid**: front overhang 2,664, wheelbase 5,945, rear overhang 3,435 mm (Volvo
  drawing layer); axles 2.66, 8.61; doors 0.4–1.6, 4.6–5.9, 9.8–11.0 (2+2+2); OppCharge
  contact rails on the roof at 4.4–6.0, battery and cooling behind them; glazed rear.
- **LAH**: axles 2.66, 8.4, 15.0 (estimated from the rescue-sheet drawing); joint about 9.9;
  doors 0.4–1.6, 4.6–5.9, 11.0–12.3, 16.3–17.5 (2+2+2+2, the fourth door behind the driven axle,
  photo busbild-455).
- **HA**: front section identical; the rear section is 0.6 m longer (axle 3 at 15.6, door 4
  at 17.0–18.2).

## Data
| | Electric Hybrid | LAH | HA |
|---|---|---|---|
| Height | 3.52 m (VBZ, with rails) / 3.28 m | 3.28 m | 3.30 m |
| Drive | D5K 240 177 kW + I-SAM 150 kW | same | D5K 240 + I-SAM 180 kW |
| Max. weight | 19 t | 28 t | 29 t |
| Places | 69 | 107 (43 seats) | "61" on the VBZ page (implausible); 110 assumed |

## Livery
VBZ white and blue (see `models/vbz/hess_trolley/REFERENCE.md`).

## Approximations
- Hybrid power given as one figure (diesel plus part of the electric motor).
- Both articulated versions are fitted to 6 + 5 OpenTTD units; the HA's extra 0.6 m shows only
  in the rear door and axle positions.
