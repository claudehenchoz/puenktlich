# SBB RABe 511 Regio-Dosto (Stadler KISS): reference

SBB calls it the "Regio double-decker" / "Regio-Dosto" (sbb.ch "Regio double decker" page; the page
refuses automated fetches, so its text was not read). Built by Stadler Rail Altenrhein, 93 units:
69 six-car (511 001–069, mainly S-Bahn Zürich and RE Wettingen–Olten–Luzern) and 24 four-car
(511 101–124, ordered 2010 for RegioExpress lines). From 2020 to 2024, 511 015–030, 036–038 and all
of 101–124 were converted from Regio-Dosto (RVD) to InterRegio-Dosto (IRD), which removed some seats.

## Data (de.wikipedia "SBB RABe 511", en.wikipedia "Stadler KISS", retrieved 2026-11-22)
| | 6-car | 4-car |
|---|---|---|
| Units | 511 001–069 (69) | 511 101–124 (24) |
| Length over couplers | 150,000 mm | 100,360 mm |
| Axle layout | Bo'Bo'+2'2'+2'2'+2'2'+2'2'+Bo'Bo' | Bo'Bo'+2'2'+2'2'+Bo'Bo' |
| Seats (1st + 2nd) | 120 + 415 | 60 + 277 (52 + 265 after IR conversion) |
| Standing | 838 | 548 |
| Mass empty | 297 t | 211.9 t |

Both: width 2,800 mm, height 4,595 mm, 160 km/h, 6,000 kW short-term / 4,000 kW continuous,
400 kN starting tractive effort, wheel Ø 920 mm, bogie wheelbase 2,500 mm, 15 kV 16.7 Hz.
Floor heights 550 mm (entrance), 440 mm (lower deck), 2,515 mm (upper deck).
Built 2010–2012 and 2015–2016 (orders: 50 six-car 2008, 24 four-car 2010, 19 six-car 2015).

Both variants have only the two end cars motored, so power and tractive effort are the same.
The model uses the short-term rating (6,000 kW) for both.

Cab car Bt 511 022 lettering (ref06): **25.36 m** over couplers, **17.84 m** bogie centres, 62 t empty.

## Photos used (Wikimedia Commons)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [SBB RABe 511 als S12 in Effretikon.jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_511_als_S12_in_Effretikon.jpg) | Kabelleger / David Gubler | CC BY-SA 4.0 |
| ref02 | [SBB RABe 511 (511 028 A W).jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_511_(511_028_A_W).jpg) | Joachim Lutz | CC BY-SA 4.0 |
| ref03 | [SBB RABe 511 (511 103 A W).jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_511_(511_103_A_W).jpg) | Joachim Lutz | CC BY-SA 4.0 |
| ref04 | [RABe 511 044 als S 30 nach Winterthur in Weinfelden.jpg](https://commons.wikimedia.org/wiki/File:RABe_511_044_als_S_30_nach_Winterthur_in_Weinfelden.jpg) | JoachimKohler-HB | CC BY-SA 4.0 |
| ref05 | [RABe 511 End-Coach.jpg](https://commons.wikimedia.org/wiki/File:RABe_511_End-Coach.jpg) | TnTch | CC BY-SA 3.0 |
| ref06 | [SBB RABe 511 Wagen 6 2015-09-15.jpg](https://commons.wikimedia.org/wiki/File:SBB_RABe_511_Wagen_6_2015-09-15.jpg) | Tinu G | CC BY-SA 4.0 |
| ref07 | [SBB CFF FFS RABe 511 120 RE Genève-Romont Denges-Echandens](https://commons.wikimedia.org/wiki/File:SBB_CFF_FFS_RABe_511_120_RE_Gen%C3%A8ve-Romont_Denges-Echandens_(16635208307).jpg) | Markus Eigenheer | CC BY-SA 2.0 |

## Measurements
Heights from ref05 (cab car 511 001, near side-on), scaled by the roof height 4.595 m. The photo
is slightly oblique, so lengths along the car are approximate (±0.3 m). Voxels: z ≈ 12.2 per m
(roof z 56, as the FV-Dosto in `parts/dosto.py`), x 10 per m.

| Feature | Height (m) | z |
|---|---|---|
| Skirt band top (CC2 below) | 1.37 | 17 |
| Lower-deck windows | 1.4–2.4 | 17–30 |
| Thin waist line (CC2) | 2.65–2.8 | 32–34 |
| Door leaves / blue band above them | 0.5–2.7 / 2.7–2.95 | 6–33 / 33–36 |
| Upper-deck windows (also in the red door panel) | 3.0–4.1 | 37–50 |
| SBB logo (cab car, over the equipment bay) | 3.2–3.5 | 40–44 |
| Cab side window | 2.15–3.3 | 27–40 |
| Grey roof sides from | 4.1 | 50 |

| Cab car (from nose tip) | m | Notes |
|---|---|---|
| Nose | 0–2.2 | windscreen raked ≈1.8 m; red stripe sweeps from the nose corner to the roof at ≈3.4 m |
| Motor bogie centre | 4.4 | Bo'Bo' |
| Equipment hatch (louvred) | 4.2–5.4 | full height to 3.3 m |
| Small window | 6.5–7.3 | |
| Door 1 / door 2 | 8.4–9.8 / 19.6–21.0 | lower deck between them, 5 windows |
| Rear bogie | 22.2 | 17.8 m bogie centres (ref06) |
| Intermediate-level window | 22.4–23.6 | |

Intermediate cars (unverified, from ref01/ref04, scaled to 25.0 m): bogies 3.6 / 21.4 m, doors
5.0–6.4 and 18.6–20.0 m, 6 lower-deck windows, upper-deck windows at ≈1.4 m pitch. The pantographs
stand in a roof well over the intermediate level at the cab-car end of the second car (ref04);
the position of the second pantograph in 6-car units (car 5) is assumed.

## Livery (colour map)
- Body: white. Roof and roof sides above 4.1 m: grey.
- Door panels: red (CC1) from the sill up to the top of the upper-deck window in the panel, a
  dark blue band with the class number above the door leaves (both schemes, ref03, ref04).
  1st class: yellow line above the blue band (unverified detail, drawn as on the FV-Dosto).
- Nose: red U around a black windscreen, dark grey roof cap with the top lamp; black "eyes" with
  the headlamps at the lower corners, white below them; red stripe from the nose corner up to
  the roof line on each side.
- **Regional schemes** (the only difference is the skirt band and the waist line, = CC2 dark shade):
  - S-Bahn Zürich (ZVV) units: **dark blue** (ref01, ref04, ref05, ref06). en.wikipedia: "red-white-blue".
  - RegioExpress / InterRegio units (Romandie RE Genève–Vevey/Romont, St. Gallen–Chur, IR-Dosto):
    **anthracite grey** (ref02, ref03, ref07). en.wikipedia: "red-white-grey".
- ZVV logo on the door panels of Zürich units: omitted (too small at 1×).

## Simplifications
- Car lengths: every car 25.0 m (8/8); Bt is 25.36 m.
- Cab-car roof equipment cover and the air-conditioning boxes are plain boxes.
