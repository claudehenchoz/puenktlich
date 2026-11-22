# SBB RABe 512 IR-Dosto (Stadler KISS, second generation): reference

SBB calls it the "new IR double-decker" / "IR-Dosto". 60 six-car units RABe 512 001–060, built
2022–2026 by Stadler; first in passenger service 17 July 2023 (RE48 Zürich HB – Schaffhausen).
It can run in multiple with the RABe 511 converted to IR-Dosto.

## Data (de.wikipedia "SBB RABe 512", retrieved 2026-11-22; sbb.ch "new IR double decker" via search snippet)
| | Value |
|---|---|
| Length over couplers | 151,880 mm |
| Width / height | 2,800 / 4,595 mm |
| Axle layout | Bo'Bo'+2'2'+2'2'+2'2'+2'2'+Bo'Bo' |
| Seats | 466 (94 1st, 372 2nd) |
| Power | 6,000 kW short-term, 4,000 kW continuous |
| Starting tractive effort | 400 kN (up to 54 km/h) |
| Max speed | 160 km/h |
| Mass | 299 t empty, 382 t in service |
| Coupler | Schwab automatic |

Car lengths are not published in these sources: 151.88 m / 6 ≈ 25.3 m, every car modelled at
25.3 m (8/8). The position of the 1st class (car 3) and of the pantographs (cars 2 and 5, as on
the RABe 511) is **unverified**.

## Photos used (Wikimedia Commons)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [SBB IR-Dosto - RABe 512 (52240972658).jpg](https://commons.wikimedia.org/wiki/File:SBB_IR-Dosto_-_RABe_512_(52240972658).jpg) | Kecko | CC BY 2.0 |
| ref02 | [SBB RABe 512 032 Sargans 20250813.jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_512_032_Sargans_20250813.jpg) | Moliva | CC BY-SA 4.0 |
| ref03 | [SBB RABe 512 als R1 nach Bex (Yverdon-les-Bains, 2026).jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_512_als_R1_nach_Bex_(Yverdon-les-Bains,_2026).jpg) | JoachimKohler-HB | CC BY-SA 4.0 |
| ref04 | [RABe 512 in Rheinfelden.jpg](https://commons.wikimedia.org/wiki/File:RABe_512_in_Rheinfelden.jpg) | Chloe0331 | CC0 |

## Measurements (cab car 512 001, ref01, near side-on)
Heights scaled by the roof height 4.595 m (z ≈ 12.2 per m, roof z 56 as the RABe 511). Lengths
as fractions of the car between nose tip and gangway, scaled to 25.3 m (±0.4 m, oblique photo).

| Feature | m | z |
|---|---|---|
| Lower-deck windows (in a continuous dark band) | 1.23–1.98 | 15–25 |
| Door leaves / blue band above | 0.5–2.45 / 2.45–2.65 | 6–30 / 30–33 |
| SBB logo and lettering | 2.53–2.85 | 31–35 |
| Upper-deck windows (dark band) | 3.05–3.9 | 37–48 |
| Thin red line under the roof edge | 4.25–4.37 | 52–54 |
| Cab side window | 2.26–3.25 | 28–40 |

| Cab car (from nose tip) | m |
|---|---|
| Nose, windscreen meets the roof line | 0–4.6 |
| Cab side window | 2.6–5.4 |
| Louvred equipment hatch | 6.0–7.2 |
| Motor bogie centre | ≈7.4 |
| Small window | 9.1–9.8 |
| Door 1 / door 2 | 11.5–13.0 / 20.1–21.6 |
| Upper deck (6 windows) | 11.9–21.4, only between the doors |
| Rear bogie centre | ≈22.8 (photo suggests up to 23.8; moved in so the wheels stay under the body) |

Intermediate cars (ref02, unverified): doors near both ends, 6 lower-deck windows between them,
upper deck between the doors, small windows over the intermediate levels.

## Livery (colour map)
- Body white (CC2) down to the sill; dark grey roof; thin red (CC1) line under the roof edge.
- Windows in continuous dark bands on both decks.
- Doors: red leaves (CC1) with a dark blue band above them carrying the class number; 1st class
  with a yellow line above it (unverified detail, as on the RABe 511).
- Nose: black windscreen shield with a V-shaped lower edge in a red frame; red lower nose, white
  lower corners, lamps at the outer corners; on the sides a red line rises from the lower nose
  along the windscreen edge into the roof-edge line, the windscreen wraps round above it.
- One scheme only: no regional variants are known.

Builder: `parts/kiss.py` with `style="kiss2"` (`kiss2_car`, `kiss2_cab_car`); the nose is the
shared `parts/stadler.py` shield nose.
