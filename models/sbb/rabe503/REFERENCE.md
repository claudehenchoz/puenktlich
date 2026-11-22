# SBB RABe 503 "Astoro" (Alstom ETR 610, New Pendolino): reference

Seven-car tilting multi-system EuroCity units. Cisalpino ordered 14 ETR 610 in 2004; 7 went to
SBB (later renumbered 503 001–007), and SBB added 503 011–018 (ordered 2012, in service 2015) and
503 019–022 (2017). SBB calls them "Astoro" since 2018. Routes: Simplon (Genève/Basel–Milano),
Gotthard since December 2015, Zürich–München since December 2020.

## Data (de.wikipedia "Alstom ETR 610", fr/it.wikipedia, retrieved 2026-11-22)
| | Value | Note |
|---|---|---|
| Length over couplers | 187.4 m | de, fr, it |
| Width / height | 2.83 m / 4.10 m | height from it only |
| Axle layout | (1A)(A1)+(1A)(A1)+2'2'+2'2'+2'2'+(1A)(A1)+(1A)(A1) | de; cars 1, 2, 6, 7 powered |
| Seats | 431: 109 1st, 304 2nd, 18 restaurant | fr; de text gives 422 for the second series |
| Continuous power | 5,500 kW | de, fr, it |
| Max speed | 250 km/h | |
| Starting tractive effort | 225 kN | de |
| Mass | 450 t (de, it); fr: 387/406 t | conflicting |
| Pantographs | 6: car 3 (DE/AT), car 4 (IT, CH), car 5 (CH, IT), car 6 (DE/AT) | de car table |
| Wheel Ø / bogie wheelbase | 890 mm / 2.7 m | it, fr |

Car lengths are not given: 187.4 m / 7 suggests end cars ≈27.6 m and intermediates ≈26.4 m
(**unverified**); every car is modelled at 25.6 m (8/8). Car order from the de car table:
1 A (cab, 44), 2 A (54), 3 WR + A (18 + 8), 4–6 B (80 each), 7 B (cab, 64). The model shows the
Swiss pantographs only (cars 4 and 5, car 4 raised).

## Photos used (Wikimedia Commons, Category:ETR 610 of SBB-CFF-FFS)
| Ref | File | Author | Licence |
|---|---|---|---|
| ref01 | [33 FFS RABe 503 013 Zuerich Brunau 120415 EC30012.jpg](https://commons.wikimedia.org/wiki/File:33_FFS_RABe_503_013_Zuerich_Brunau_120415_EC30012.jpg) | NAC | CC BY-SA 4.0 |
| ref02 | [Allgäubahn Astoro.jpg](https://commons.wikimedia.org/wiki/File:Allg%C3%A4ubahn_Astoro.jpg) | Bergerbse | CC BY-SA 4.0 |
| ref03 | [7 FFS RABe 503 022 Bern 120818 EC59.jpg](https://commons.wikimedia.org/wiki/File:7_FFS_RABe_503_022_Bern_120818_EC59.jpg) (advertising wrap, nose shape only) | NAC | CC BY-SA 4.0 |

## Measurements (z ≈ 12.2 per m, roof z 50; ref01/ref02, approximate)
| Feature | z |
|---|---|
| Continuous dark window band | 20–31 |
| Thin red cant line | 37–39 |
| Dark roof (tapered tilting profile above the band) | from 40 |
| Plug doors (white, seams only) | 10–35, one behind the cab, one at each car end |

Nose: ≈5.6 m long, pointed; red mask from the white bumper tip back to the cant line; black
visor over the windscreen; round lamps low on the white tip; black cab side window behind the
visor.

## Livery
White body (CC2), dark window band, red (CC1) nose mask and cant line, dark roof. 1st-class cars
get a yellow line over the band; the restaurant car a red edge round its band (approximation).
Advertising wraps (e.g. 503 022 "Goethe") are not modelled.

Builder: `parts/tilting.py`, `style="etr610"`.
