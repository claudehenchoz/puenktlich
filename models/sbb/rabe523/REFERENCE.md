# SBB RABe 523 (Stadler FLIRT) and the FLIRT 3 "Mouette": reference

Two vehicles share this recipe:
- `rabe523`: FLIRT 1, 4-car regional units RABe 523 001–073 (Stadtbahn Zug 001–012, RER Vaud
  013–031, S-Bahn Luzern 032–043, RegiOlten 044–073), built 2004–2017.
- `rabe523_mouette`: FLIRT 3 with long-distance interior, RABe 523 501–511 ("Mouette"), in
  service since December 2022 on IR 36 Basel – Zürich Flughafen (IR 56 Basel – Biel planned).

## Data
| | FLIRT 1 (523 0xx) | Mouette (523 5xx) | Source |
|---|---|---|---|
| Cars, axle layout | 4, Bo'2'2'2'Bo' | 4, Bo'2'2'2'Bo' | de.wikipedia "Stadler Flirt" (SBB table) |
| Total length | 74.078 m | not found (assumed the same) | fr.wikipedia "RABe 523" |
| Seats | 20 1st + 161 2nd | 27 1st + 154 2nd | fr.wikipedia "RABe 523"; sbb.ch: 181 |
| Power | 2,000 kW continuous | not found (assumed the same) | fr.wikipedia "RABe 523" |
| Max speed | 160 km/h | not found (assumed 160) | fr.wikipedia, it.wikipedia |
| Starting tractive effort | 200 kN (FLIRT family) | 175 kN (FLIRT 3 family) | de.wikipedia "Stadler Flirt" infobox |
| Mass | 127 t | not found (130 t assumed) | fr.wikipedia "RABe 523" |
| Height | 4.185 m (FLIRT 1/2) | 4.120 m (FLIRT 3) | fr/de.wikipedia, family values |
| Number | 73 | 11 (text also says 7, then an option) | de/fr.wikipedia (conflicting) |

Retrieved 2026-11-22. Car lengths, doors per car and wheelbase are not in these sources.
**Unverified (from photos):** end cars ≈19.4 m, intermediate cars ≈17.6 m (sum ≈74 m); two
doors per car side; 1st class behind the cab of one end car; a pantograph on the rear roof of each
end car. Wikimedia Commons has no photo of a Mouette: its exterior follows the FLIRT 3 RABe 523
1xx (RER Vaud / TILO) photos, and its door and window layout is assumed to equal the FLIRT 1's.

Modelled: end cars 19.2 m (6/8), intermediate cars compressed to 16.0 m (5/8), as the Giruno's.

## Photos used (Wikimedia Commons)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [RABe 523 066.jpg](https://commons.wikimedia.org/wiki/File:RABe_523_066.jpg) | Heitersberg | CC BY-SA 4.0 |
| ref02 | [20230605 SBB 523038.jpg](https://commons.wikimedia.org/wiki/File:20230605_SBB_523038.jpg) | Alex Noble | CC0 |
| ref03 | [FFS RABe 523111 Minusio 020521 S20 25666.jpg](https://commons.wikimedia.org/wiki/File:FFS_RABe_523111_Minusio_020521_S20_25666.jpg) | NAC | CC BY-SA 4.0 |
| ref04 | [Bahnhof Yverdon-les-Bains mit SBB RABe 523 109 (2026).jpg](https://commons.wikimedia.org/wiki/File:Bahnhof_Yverdon-les-Bains_mit_SBB_RABe_523_109_(2026).jpg) | JoachimKohler-HB | CC BY-SA 4.0 |

## Measurements (z ≈ 12.1 per m, roof z 51 as the Giruno; ref01/ref02, approximate)
| Feature | m | z |
|---|---|---|
| FLIRT 1 black skirt | below 0.9 | below 11 |
| Windows (large, dark frames) | 1.3–2.55 | 16–31 |
| Door leaves / blue class band | 0.4–2.7 / 2.7–2.9 | 5–33 / 33–35 |
| FLIRT 1 red roof-edge band | 3.55–3.95 | 43–48 |
| FLIRT 3 thin red line | 3.7–3.9 | 45–47 |
| Dark roof from | 3.95 | 48 |

| End car (from nose tip, real m) | m |
|---|---|
| Nose / cab side window | 0–3 / 1.4–3.6 |
| Motor bogie centre | ≈3.6 |
| Door centres | ≈8.9, ≈14.0 |
| Pantograph | ≈16.2 |
| Jakobs bogie | rear joint |

Intermediate car door centres ≈4.8 and ≈12.8 m.

## Livery (colour map)
- FLIRT 1: white body (CC2); black skirt; broad red (CC1) band along the roof edge that the nose's
  red U frame runs into; dark roof. Nose: black windscreen in a red U, white lower front with the
  lamps, small white SBB logo, black skirt.
- FLIRT 3 / Mouette: white body (CC2) down to the sill; thin red line under the dark roof; the
  Stadler shield nose shared with the RABe 512 (`parts/stadler.py`).
- Both: red sliding doors (CC1) with a blue class band; large windows in dark frames; yellow line
  above the 1st-class windows; SBB logo and lettering under the windows near each car's rear.
- Regional schemes: the RABe 523 0xx run in the standard SBB livery. Not modelled: the four
  transN units 523 074–077 (de.wikipedia) and advertising wraps; no photos were checked.

Builder: `parts/flirt.py` (`FlirtSpec`, `end_car`, `generation=1|3`).
