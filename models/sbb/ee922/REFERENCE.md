# SBB Ee 922 (Stadler): reference

Two-axle electric shunting locomotive (15 kV 16.7 Hz / 25 kV 50 Hz) for shunting passenger
trains in the large stations. 25 units Ee 922 001–025: 21 built 2009–2010 (first in service at
Zürich Herdern in July 2009), 4 more in 2015.

## Data (de/en/fr.wikipedia "SBB Ee 922", retrieved 2026-11-22)
| | Value |
|---|---|
| Length over buffers / width / height | 8,800 / 3,100 / 4,306 mm |
| Axle layout / wheelbase / wheel Ø | Bo / 4,000 mm / 1,100 mm |
| Power | 600 kW continuous, 750 kW short-term (en/fr: 612 kW) |
| Tractive effort | 120 kN |
| Max speed | 100 km/h (de infobox: 40 km/h under own power, 100 km/h hauled) |
| Mass | 44 t (ballast removable to 40 t) |

The model uses 100 km/h so it can run in a game; the 40 km/h shunting limit is noted here.

## Photos used (Wikimedia Commons, Category:SBB Ee 922)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [SBB Ee 922 010 Bern.JPG](https://commons.wikimedia.org/wiki/File:SBB_Ee_922_010_Bern.JPG) (near side-on) | Hoff1980 | CC BY-SA 3.0 |
| ref02 | [FFS Ee 922 012-0 Brig 040217.jpg](https://commons.wikimedia.org/wiki/File:FFS_Ee_922_012-0_Brig_040217.jpg) | NAC | CC BY-SA 4.0 |

## Measurements (ref01; m from the front buffer beam, z ≈ 12.2 per m)
| Part | m | top z |
|---|---|---|
| Frame (dark grey) | full length | 5–16 |
| Low front hood with railings | 0.2–2.3 | 33 |
| Cab (black window frames, roof canopy with pantograph) | 2.3–6.0 | 50 |
| Short rear section | 6.0–7.4 | 32 |
| Axles | 1.8 / 5.8 (4.0 m wheelbase) | |

## Livery
SBB red (CC1), dark grey frame, white SBB symbol on the cab sides (modelled as a plain white
cross), yellow handrails not modelled.

Builder: `parts/hood.py` (`HoodSpec`, `livery="sbb"`).
