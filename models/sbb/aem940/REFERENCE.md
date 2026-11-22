# SBB Aem 940 (Alstom Prima H4): reference

Bi-mode (15 kV 16.7 Hz / 25 kV 50 Hz electric, diesel) Bo'Bo' hood unit for SBB Infrastruktur
works trains and heavy shunting. First units 2018 (tests); the 5 pre-series went to Sersa in 2022;
deliveries to SBB until May 2024 (de: last 940 052; fr: 47 units, 940 001–047; conflicting).

## Data (de.wikipedia "Alstom Prima H4", fr.wikipedia "CFF Aem 940", retrieved 2026-11-22)
| | Value |
|---|---|
| Length over buffers / width / height | 18,750 / 2,955 / 4,478 mm |
| Axle layout | Bo'Bo' |
| Power | 2,000 kW electric; 900 kW diesel (2 × CAT C18) |
| Max speed | 120 km/h |
| Tractive effort | 300 kN (hourly; starting value not found) |
| Mass | 90 t, 22.5 t axle load |
| Wheel Ø | 920 mm (de) / 960 mm (fr) |

## Photos used (Wikimedia Commons, Category:SBB Aem 940)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [4 FFS Aem 940 018-5 Giubiasco 160622.jpg](https://commons.wikimedia.org/wiki/File:4_FFS_Aem_940_018-5_Giubiasco_160622.jpg) | NAC | CC BY-SA 4.0 |

## Measurements (ref01, near side-on; m from the front buffer beam, z ≈ 12.2 per m)
| Part | m | top z |
|---|---|---|
| Frame (dark) | full length | 12–25 |
| Taller hood with grilles (front) | 0.3–7.8 | 45 |
| Cab (off-centre, pantograph on its roof) | 7.8–11.8 | 54 |
| Lower hood with railings (rear) | 11.8–17.3 | 40 |
| Bogie centres | ≈4.3 / 13.3 (**approximate**) | |

## Livery
Red body (CC1), dark frame, white SBB crosses on the cab sides; yellow handrails not modelled.

Builder: `parts/hood.py` (`HoodSpec`, `livery="sbb"`).
