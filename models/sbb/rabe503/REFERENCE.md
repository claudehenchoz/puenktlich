# SBB RABe 503 "Astoro" (Alstom ETR 610, New Pendolino): reference

Seven-car tilting multi-system EuroCity units. Cisalpino ordered 14 ETR 610 in 2004; 7 went to
SBB (later renumbered 503 001–007), and SBB added 503 011–018 (ordered 2012, in service 2015) and
503 019–022 (2017). SBB calls them "Astoro" since 2018. Routes: Simplon (Genève/Basel–Milano),
Gotthard since December 2015, Zürich–München since December 2020. Modelled in **true
proportions** (see "Scale" below), like the FV-Dosto.

## Sources (docs/research/rabe503-etr610, docs/train-3d-models)
- **GDL brochure:** "Technische Kurzbeschreibung des ETR 610" (Gewerkschaft Deutscher
  Lokomotivführer, 2011, technical state October 2010):
  `docs/research/rabe503-etr610/RABe503-GDL-Technische-Kurzbeschreibung-ETR610.pdf`. Key data,
  car configuration, pantograph layout, brakes, cab.
- **3D models:** `docs/train-3d-models/SBB ETR 610 (RABe 503)/`: four converted Cities: Skylines
  props (workshop 1043207438, third party), used for measurements only, nothing copied. Cars:
  end car `ETR610Eng_Prop`, 1st `ETR6101st_Prop`, 2nd with pantographs `ETR6102nd_Prop`,
  restaurant `ETR610resto_Prop`. glTF units are metres (y up, z along the car, nose at −z).
  **Not to scale between cars:** the end car is 27.16 m, but the intermediates are 22.35 m with
  only 8 windows (the real ones have 10). All cars are 2.555 m wide and 3.98 m high (real 2.83 ×
  4.10 m). Used for the cross-section, the nose (profile, plan, sections), the end-car layout and
  the livery, normalised to the real height (× 1.03) and width (× 1.097).
- **Lima H0 photos:** `RABe503-lima-h0-01…16.jpg` (Lima HL 1680/1–4, 503 018; photos Markus
  Inderst / modellbahninfo.org). Near-orthographic side views of the end, 1st and 2nd
  (pantograph) cars, used for the intermediate-car layout (scaled by the 2.7 m bogie
  wheelbase) and the pantograph positions.
- **Real photos:** `RABe503-photo-01…15.jpg`. 01 is the end car side-on (red cant line, door,
  skirt); 03 is the restaurant car side-on; 05 and 14 show doors and end panels; 07–12 the nose
  and front. City advertising wraps (Zürich, München) are not modelled.

## Data
| | Value | Source |
|---|---|---|
| Length over couplers | 187.4 m (GDL: 188 m) | de/fr/it.wikipedia, GDL |
| Cars | 7: A (cab) · A · WR + A · B · B · B · B (cab) | GDL, de.wikipedia car table |
| Width / height | 2.83 m / 4.10 m | wikipedia (it for the height), trainspo |
| Seats | 104 1st + 304 2nd (restaurant 8 + 18 not counted) | GDL |
| Max speed / power / starting tractive effort | 250 km/h / 5,500 kW / 226 kN | GDL |
| Mass / axle load | 442 t / 17.3 t | GDL |
| Pantographs | cars 4 and 5: SBB/IT AC 1,450 mm + DC 1,950 mm each; cars 3 and 6: DB AC 1,950 mm; one roof line per traction unit (cars 1–4, 5–7) | GDL p. 5, 7 |
| Traction | motors under cars 1, 2, 6, 7; transformers in cars 4 and 5 | GDL p. 6 |
| Tilt | up to 8°, hydraulic | GDL |
| Wheel Ø / bogie wheelbase | 890 mm / 2.7 m | it, fr.wikipedia |

**Car lengths:** no per-car figures were found. The real end car is ≈27.7 m (3D model end car
27.2 m), and the intermediates are 26.2 m (trainspo "car length 26.2 m"; the Lima
intermediate measures 26.5 m against its bogie wheelbase). 2 × 27.7 + 5 × 26.2 = 186.4 m, plus
the couplers ≈ 187.4 m. Every car is compressed to its 8/8 slot (25.6 m), and positions scale
with it.

## Measurements (z and y: 12.2 voxels per metre, roof 4.10 m = z 50; x: 10 per modelled metre)
Cross-section (3D model, intermediate car, half-width by height, normalised to the 2.83 m
width): 1.415 m from 0.9 to 2.9 m (vertical sides), 1.37 at 3.06, 1.33 at 3.29, 1.29 at 3.45,
1.17 at 3.68, 0.97 at 3.83, 0.80 at 3.91 m; skirt 0.93 of the width below 0.85 m. Modelled:
half-width 17, chamfer from z 33 inwards by 3 to the roof, roof radius 13, tumblehome 1 below
z 11.

| Feature | m | z |
|---|---|---|
| Body underside between the bogies / over the bogies / under the nose | 0.46 / 1.0 / 0.30 | 6 / 12 / 4 |
| Dark skirt (louvred between the bogies) | below 1.05 | below 13 |
| Dark window band (3D model; photo 01 reads 2.07–2.90 with an uncertain rail line) | 1.80–2.75 | 22–34 |
| Thin red cant line (3D model and photo 01 agree) | 3.70–3.85 | 45–46 |
| Anthracite roof | from 3.85 | from 47 |
| Plug doors (white, grey seams, oval window in the band) | 1.0–3.1 | 12–38 |
| SBB logo and lettering | 1.45–1.70 | 18–21 |
| "Restaurant" lettering | 3.0–3.2 | 37–39 |

**Intermediate car** (26.2 m, Lima, metres from one end, symmetric):
- door 0.35–1.35;
- red end panel to 2.6, with the door in it and a yellow top third on 1st-class cars (z 31–34);
- blue class marker with the class numeral 2.6–2.85;
- dark window band 2.85–23.35 with 10 framed windows 1.4 m wide at a 1.95 m pitch, centred on the car;
- bogies 3.7 m from each end;
- anthracite roof hump over the middle 8.6 m;
- pantographs (cars 4, 5) 5.8 m from each end over the inner side of the bogies, knees towards the car centre.

**End car** (27.7 m, 3D model × 1.018, metres from the nose tip):
- bogies 5.6 and 23.65 (wheel contacts at 4.1/6.9 and 21.9/24.6 in the model);
- door 7.55–8.55 behind the cab;
- window band 8.75–23.6 with 8 windows 1.4 m wide every 1.88 m from 8.85;
- in the model the nose is stretched (see "Approximations"), so the door is at 11.0–12.0 and
  the band runs 12.2–23.6 with 6 windows from 12.3;
- blue marker 24.7–24.95;
- red end panel from 24.95 to the end, with the door 25.55–26.75;
- roof equipment 12.0–19.5 (model: 15.45–22.95).

**Restaurant car** (photo 03; 1st-class end towards car 2):
- door 0.35–1.35, red/yellow end panel and blue "1" marker;
- red window band 2.85–14.1 with 5 windows 1.45 m wide every 2.03 m from 4.55, "Restaurant" over it;
- plain white kitchen half with a service door 16.6–17.7 (small high window);
- no door at the far end;
- DB pantograph 5.5 m from the rear end (towards car 4).

## Nose (3D model end car, real metres from the tip)
Side silhouette top: 0 → 1.18, 0.25 → 1.33, 0.5 → 1.46, 0.75 → 1.59, 1.0 → 1.69, 1.5 → 1.87,
2.0 → 2.03, 2.5 → 2.18, 3.0 → 2.34, 3.5 → 2.52, 3.75 → 2.72, 4.0 → 2.98, 4.25 → 3.24, 4.5 → 3.39,
5.0 → 3.65, 5.5 → 3.83, 6.0 → 3.96, 6.5 → 4.05, 6.9 → 4.10 (roof). Bottom: 0.95 at the tip, 0.66
at 0.25, 0.55 at 0.5, 0.30 from 0.75. Plan half-width: 0.15 at the tip, 0.50 at 0.25, 0.76 at
0.5, 0.89 at 0.75, 1.03 at 1.0, 1.14 at 1.5, 1.22 at 2.0, 1.27 at 2.5, 1.33 at 3.0, 1.38 at 3.5,
1.415 from 4.0. Sections through the nose have near-vertical sides and a rounded top edge
(≈0.35 m). Modelled as interpolation tables (`parts/etr610.py` `nose_mask`) with a 4-voxel top
rounding, not as an `EndShape`.

Livery:
- **Top of the nose:** red from the bumper tip (above 1.5 m) back to the windscreen at 2.9 m.
- **Windscreen and roof cap:** black from 2.9 m, with red edges. Glass from 3.0 to 4.7 m.
- **Side view:** the black reaches down the flank as a wedge (0 at 2.9 m, 0.15 m at 4.0,
  0.33 m at 5.5) over a thin red line that runs on into the cant line.
- **Bumper tip:** white (0.55–1.5 m, ±0.77 m), with a dark lower lip under the nose below 0.55 m.
- **Lamps:** round, at 1.65 m height, ±0.9 m.
- **Cab side window:** a slanted black parallelogram 3.6–5.75 m (lower edge 2.05 → 2.75 m, upper
  2.2 → 3.3 m) with two panes.
- **Cab module seam:** a thin grey diagonal from (4.3 m, 0.95 m) to (7.0 m, 3.85 m).

## Scale (true proportions)
The body is authored 34 voxels wide (2.83 m at the same 12.2 voxels per metre as the height),
and the recipe's `BODY_WIDTH_M = 2.83` matches it, so the render step keeps that width.

## Approximations
- **Car lengths:** see "Data" above; all cars are compressed to 25.6 m.
- **Nose stretched 1.5×:** trains render at half length but full height (docs/SCALE.md), so the
  measured nose (roof reached 6.9 m behind the tip) looked about 2.7× too steep in game. Every
  nose feature is stretched 1.5× along the car (roof reached at 10.35 m; `parts/etr610.py`
  `NOSE_STRETCH`, the measured tables are kept as `MEASURED_*`). The door and windows behind it
  move back 3.45 m, so the end car shows 6 of its 8 windows. Bogies keep their real positions.
- **Window band height:** the 3D model and photo 01 disagree by ~0.2 m; the 3D model is used.
- **Pantographs:** which of the two on cars 4 and 5 is the SBB one, and that car 4's is the
  raised one, are assumptions (one SBB pantograph raised in Switzerland).
- **Lettering:** the "Restaurant" lettering and "SBB CFF FFS" are suggested by strokes. The
  class numerals are a light patch on the blue marker.
- **Wraps:** the city advertising wraps (Zürich, München, Goethe) are not modelled.
