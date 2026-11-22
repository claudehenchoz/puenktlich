# SBB Cargo Eem 923 (Stadler): reference

Two-axle electro-diesel shunting locomotive for SBB Cargo's local freight: electric 15/25 kV
plus a diesel engine for sidings without catenary. 30 units 923 001–030 (2011–2013), named after
Swiss hills and mountains (e.g. 923 020 "Stockhorn").

## Data (de/en/fr.wikipedia "SBB Eem 923", retrieved 2026-11-22)
| | Value |
|---|---|
| Length over buffers / width / height | 9,132 / 3,100 / 4,306 mm |
| Axle layout / wheelbase | Bo / 4.3 m (lettering on ref01) |
| Power at the wheel | 1,500 kW electric, 290 kW diesel (engine 336 kW) |
| Max speed | 120 km/h as built; 100 km/h since December 2025 (fr) |
| Starting tractive effort | 150 kN |
| Mass | 47 t (de) / 46 t (fr) / 45 t (en) |
| Wheel Ø | 1,100 mm |

## Photos used (Wikimedia Commons, Category:SBB Eem 923)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [FFS Eem 923 020 Thun 310813.jpg](https://commons.wikimedia.org/wiki/File:FFS_Eem_923_020_Thun_310813.jpg) (side-on) | NAC | CC BY-SA 4.0 |

## Measurements (ref01; m from the front buffer beam, z ≈ 12.2 per m)
| Part | m | top z |
|---|---|---|
| Frame (dark grey) | full length | 5–16 |
| Red short hood (front) | 0.3–2.75 | 36 |
| Cab (wider roof canopy, pantograph on top) | 2.75–5.2 | 50 |
| Blue long hood with "cargo" lettering (rear) | 5.2–7.6 | 36 |
| Axles | 1.8 / 6.1 | |

## Livery
SBB Cargo: blue (CC1) long hood and cab, red (CC2) short hood running diagonally into the cab,
white "cargo" lettering with three red dashes, dark grey frame. Names not modelled.

Builder: `parts/hood.py` (`HoodSpec`, `livery="cargo"`).
