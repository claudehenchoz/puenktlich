# VBZ Hess lighTram 10 Plug: reference

Battery midibus ("Batterie-Quartierbus"), VBZ 340–354: 340–347 in 2022, 348–354 in 2023.
Two axles, two doors (single front door, double middle door), aluminium CO-BOLT body, all
batteries (333 kWh) on the roof, depot charging through CCS2 at 100 kW.

Vehicle `vbz_lightram10`, 8/8 at its true length (10.8 m of the 11.2 m road length).
Builder: `puenktlich.voxel.parts.citybus`, front style `lightram`.

## Sources
Research note "VBZ Hess lighTram 10 Plug – 3D Models and Modelling References" (docs/research/vbz):
VBZ vehicle page ([Batteriebusse](https://www.stadt-zuerich.ch/vbz/de/die-vbz/fahrzeuge/busse/batteriebusse.html)),
Hess VBZ flyer and lighTram Plug brochure, the Hess vector side sketch, and the near-orthographic
VBZ press photo of 340 (side, door side).

## Dimensions
| Item | Value | Source |
|---|---|---|
| Length / width / height | 10.80 / 2.55 / 3.30 m | VBZ |
| Front overhang / wheelbase / rear overhang | about 2.5 / 4.8 / 3.5 m (±0.15 m) | measured on the press photo, 73.6 px/m |
| Doors | 0.67–1.59 m (single), 4.85–6.25 m (double), behind the front tip | press photo |
| Top speed | 80 km/h | VBZ |
| Places | 60 (26 seats + 34 standing) | VBZ |

## Livery
VBZ white and blue (see `models/vbz/hess_trolley/REFERENCE.md`).

## Approximations
- Motor power is not published (Siemens motor on axle 2); 160 kW is an estimate.
- Roof batteries as one long, low fairing.
