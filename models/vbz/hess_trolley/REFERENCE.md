# VBZ Hess trolleybuses: reference

One recipe for all five Hess trolleybus types in the VBZ fleet (November 2026):

| Vehicle | Type | VBZ nos. | Built | Length | Sections (OpenTTD) |
|---|---|---|---|---|---|
| `vbz_swisstrolley3` | Swisstrolley 3, BGT-N2C | 144–161 (8 left) | 2006/07 | 18.7 m | 6 + 5 |
| `vbz_swisstrolley4` | Swisstrolley 4, BGT-N2D | 162–182 | 2013 | 18.7 m | 6 + 5 |
| `vbz_lightram19` | lighTram 19 DC (battery trolleybus) | 183, 200–229 | 2016, 2020–2026 | 18.74 m | 6 + 5 |
| `vbz_lightram3` | lighTram 3, BGGT-N2C/N2D (double-articulated) | 61–91 | 2007/08, 2012/14 | 24.66 m | 6 + 5 + 4 |
| `vbz_lightram25` | lighTram 25 DC (double-articulated battery trolleybus) | 1–13 | 2025/26 | 24.7 m | 6 + 5 + 4 |

Builder: `puenktlich.voxel.parts.citybus` (front style `hess` for the Swisstrolleys and the
lighTram 3, `lightram` for the DC buses).

## Sources
The research notes in docs/research/vbz, "VBZ Bus Fleet 2026 – Overview" and one note per type
("VBZ Hess Swisstrolley 3/4", "VBZ Hess lighTram 19 DC", "VBZ Hess lighTram 3 Double-Articulated
Trolleybus", "VBZ Hess lighTram 25 DC – 3D Models and Modelling References"). The key ones:
- **VBZ type drawing 1-2441** (lighTram 3, 61–77, vector, 1:50): 24,660 × 2,550 × 3,440 mm,
  wheelbases 5,845 / 6,698 / 6,710 mm, roof housings 370 mm high, 1 single + 4 double doors.
- **Hess/Designwerk side view of the lighTram 19 DC** (transN design book, 2386 px,
  orthographic): the layout of the 18.7 m buses.
- VBZ vehicle pages ([Trolleybusse](https://www.stadt-zuerich.ch/vbz/de/die-vbz/fahrzeuge/busse/trolleybusse.html)):
  dimensions, motors, speeds and capacities; [Wikipedia DE – Trolleybus Zürich](https://de.wikipedia.org/wiki/Trolleybus_Z%C3%BCrich).

## Layout (metres behind the front tip)
**18.7 m buses**, measured on the lighTram 19 DC side view (112 px/m):
- axles 2.72, 8.6, 15.35 (axles 2 and 3 driven, twin tyres); joint 10.47;
- doors: 0.9–1.7 (single, inward gliding), 5.0–6.4, 12.6–14.0, 16.4–17.8 (double);
- trolley pole base 14.6 on the rear section, poles lowered onto the hooks at the rear.

The Swisstrolley 3 and 4 share the body and layout; they differ in the front and the roof
equipment, which at OpenTTD's zoom shows as different roof housings only.

**24.7 m buses**, measured on drawing 1-2441 (96.6 px/m):
- axles 2.8, 8.65, 15.3, 22.0; joints 10.4 and 17.84;
- doors 0.5–1.3 (single), 4.9–6.2, 11.5–12.8, 19.8–21.1, 23.0–24.3;
- roof housings 5.3–8.3 (370 mm) and smaller boxes; trolley pole base at 19.6.

The lighTram 25 DC layout is not published; it takes the lighTram 3 layout with the lighTram front.

## Dimensions and data
| | ST3 | ST4 | lighTram 19 DC | lighTram 3 | lighTram 25 DC |
|---|---|---|---|---|---|
| Height | 3.45 m | 3.45 m | 3.50 m | 3.44 m | 3.5 m |
| Motors | 2 × 160 kW | 2 × 120 kW | 2 × 160 kW (210–: 2 × 230 kW) | 2 × 160 kW | 2 × 160 kW (DGT plus) |
| Top speed | 60 km/h | 60 km/h | 60 (210–: 70) km/h | 60/65 km/h | – |
| Places | – | 115 | 117 | 155 (60 + 95) | 156 (52 + 104, DGT plus) |

## Livery
VBZ "Züri-Linie": white body, blue skirt up to the wheel hubs, black glazing in one band, a thin
blue line along the cantrail, white roof. CC2 = white (body), CC1 = blue (`BLUE` is the closest
TTD company colour to the VBZ blue; `LIGHT_BLUE` renders teal).

## Approximations
- Bodies fitted to OpenTTD lengths: 18.7 m to 6 + 5 (15.4 m), 24.7 m to 6 + 5 + 4 (21 m); each
  section is scaled on its own, so doors and axles stay in place within it.
- Height compressed: the road canvas is 48 voxels high, so the roof housings top out at z 46
  (3.3 m) and the lowered poles at z 46 instead of 3.45–3.5 m.
- Window pillars at a regular pitch, not at the real pillar positions.
