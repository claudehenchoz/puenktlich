# SBB RABe 512 IR-Dosto (Stadler KISS, second generation): reference

SBB calls it the "new IR double-decker" / "IR-Dosto". 60 six-car units RABe 512 001–060, built
2022–2026 by Stadler; first in passenger service 17 July 2023 (RE48 Zürich HB – Schaffhausen),
last unit handed over 2 October 2026. Modelled in **true proportions** (see "Scale" below), like
the FV-Dosto and the RABe 503.

## Sources (docs/research/rabe512)
- **Stadler datasheet:** `RABe512-Stadler-Datasheet-KISS-SBB-IR-EN.pdf`, reference sheet
  KSBBDOSIR0222 (2022). Vehicle data table and feature list.
- **Modelling references:** `SBB RABe 512 - 3D Models and Modelling References.pdf`. It contains:
  - **Stadler's type sketch** of the full train, cropped from the datasheet's vector drawing.
    Each half-train has upper-deck plan, side elevation and lower-deck plan.
  - The data table.
  - 17 Wikimedia Commons photos (1920 px): side, head-on, 3/4 views, roof, coupler, the
    RABe 511 / 512 comparison.
  - The finding that no free 3D model of the RABe 512 exists (searched 2026-11-23).

  So the type sketch is the measurement source, playing the role the 3D model played for the
  RABe 502 and 503.
- **Photos used** (in the references PDF; Commons):
  - side profile of the cab car (Chme82, CC BY 4.0);
  - head-on at the Stadler yard (Kecko, CC BY 2.0);
  - 3/4 front views (Kecko, CC BY 2.0);
  - roof equipment behind the cab (Kecko, CC BY 2.0);
  - RABe 511 / 512 side by side (ProloSozz, CC BY 4.0).

## Data (Stadler datasheet)
| | Value |
|---|---|
| Length over couplers | 151,880 mm (SBB: 150 m; builder's plate: 152 m) |
| Width / height | 2,800 / 4,595 mm |
| Axle layout | Bo'Bo' + 2'2' + 2'2' + 2'2' + 2'2' + Bo'Bo' (motor bogies under the two cab cars) |
| Seats | 466: 94 1st, 372 2nd, 15 tip-up seats, 838 standing |
| Floor heights | entrance (low floor) 495 mm, lower deck 443 mm, upper deck 2,527 mm |
| Entrance width | 1,400 mm |
| Bogie wheelbase | motor 2,700 mm, trailer 2,500 mm; wheel Ø 920 mm new |
| Power / starting tractive effort / max speed | 4,000 kW continuous, 6,000 kW peak / 400 kN / 160 km/h |
| Mass | 299 t empty (de.wikipedia); builder's plate 303 t |

## Type sketch (measurement source)
The sketch shows both half-trains. Rail to roof is 234 px for 4.595 m, and 7,748 px between the
coupler faces and the middle coupling plane (bellows centre) for 151.88 m, so 51.0 px/m. Both
scales agree within 1 %. Measured on the 4341 × 1474 px crop with metre rulers; positions are
±0.05 m.

**Car order and classes** (front to rear; the plans show 2+1 seats upstairs in cars 3 and 4):
1. Bt, cab car, 2nd class, motor bogie, pantograph over the inner end.
2. B, multi-purpose area and wheelchair toilet on the lower deck.
3. AB, 1st class upstairs.
4. AB, 1st class upstairs; car 3's counterpart, turned.
5. B.
6. Bt, the cab car turned round, pantograph raised.

**Car lengths** (coupling plane to coupling plane):
- **Cab cars:** 26.07 m including the coupler (nose tip 0.33 m behind the coupler face), so
  25.74 m tip to coupling plane, compressed to 25.6 m (8/8).
- **Intermediates:** 24.88 (car 2), 24.86 (car 3), 24.80 (cars 4 and 5); modelled at their real
  length.

## Measurements (z and y: 12.2 voxels per metre, roof 4.595 m = z 56; x: 10 per metre)
| Feature | m | z |
|---|---|---|
| Lower-deck body bottom / over the bogies | 0.49 / 1.33 | 6 / 16 |
| Lower-deck windows (framed, white between them) | 1.20–1.90 | 15–23 |
| Small displays over the lower windows next to the doors | 2.04–2.24 | 25–27 |
| Windows over the intermediate levels | 2.12–2.86 | 26–35 |
| Door leaves (red) / blue band with the class numbers | 0.45–2.45 / 2.45–2.71 | 6–30 / 30–33 |
| SBB panel behind the first door | 2.6–2.95 | 32–36 |
| Upper-deck windows (in a continuous dark band) | 3.27–3.98 | 40–49 |
| Louvred grilles at the roof edge over the intermediate levels | 3.6–4.1 | 44–50 |
| Thin red line under the roof edge | 4.25–4.40 | 52–54 |
| Cab section roof / full roof | 4.41 / 4.595 | 54 / 56 |

Positions along each car (metres from its front coupling plane; cab car from the nose tip):

**Cab car (cars 1, 6):**
- motor bogie 4.76, trailer bogie 22.61;
- cab side window band 0.6–2.7;
- louvred hatch 3.30–4.20, service flap 4.61–5.21, window 5.72–6.32;
- doors 7.87–9.53 and 17.78–19.43;
- upper deck 8.39–18.93: small, 4 large, small;
- lower deck 4 windows 10.15–17.11;
- window 20.94–21.85, equipment door 23.97–24.98;
- pantograph 23.87, with a louvred roof box 23.97–25.38;
- cab roof up to 4.66.

**Car 2:**
- bogies 3.06 and 21.92;
- doors 5.94–7.60 and 17.38–19.05;
- upper deck: small, 5 large (1.26 m), small;
- lower deck 3 windows (8.0–8.96, 12.34–13.85, 14.96–16.53);
- end windows 1.05–2.31, 2.76–3.37, 21.62–22.22, 22.62–23.88;
- roof box 22.14–23.9.

**Car 3:**
- bogies 2.90 and 21.82;
- doors 5.86–7.52 and 17.30–18.99;
- upper deck: small, 2 wide (1.55 m), small, 2 wide, small;
- lower deck 5 windows 8.16–16.70;
- end windows 3.23–3.89, 21.30–21.95, 22.35–23.88.

**Car 4:**
- bogies 2.97 and 21.80;
- doors 5.89–7.51 and 17.31–18.96;
- upper deck as car 3;
- lower deck 4 + 1 small (8.08–16.79);
- end windows 0.95–2.47, 2.90–3.53, 20.96–21.59;
- roof box 1.0–2.3.

**Car 5:**
- bogies 3.13 and 22.04;
- doors 5.88–7.54 and 17.30–18.95;
- 5 windows of 1.23 m on each deck at a 1.84 m pitch, centred, plus small windows by the doors upstairs;
- end windows 0.99–2.23, 2.68–3.25, 21.58–22.13, 22.58–23.82;
- roof boxes 2.7–4.0 and 20.85–22.1.

## Nose (type sketch side elevation and plan, head-on photo)
Side setback from the nose tip by height:

| Height (m) | ≤ 1.95 | 2.25 | 2.55 | 3.0 | 3.45 | 3.9 | 4.2 | 4.35 | 4.41 (cab roof) |
|---|---|---|---|---|---|---|---|---|---|
| Setback (m) | 0 | 0.14 | 0.40 | 0.67 | 0.98 | 1.38 | 1.75 | 2.08 | ≈2.6 |

Below 1.95 m the front is vertical down to 0.9 m, then undercut to 0.12 m back at 0.75 m, 0.4 m
at 0.6 m and 1.3 m at 0.45 m (the skirt). The plan is blunt: 2.16 m wide at the tip, 2.55 m at
0.3 m and the full width from 1.1 m. Combined by max() (`parts/ir_dosto.py` `NOSE_SIDE`,
`NOSE_PLAN`).

Front livery (head-on photo, half-widths from the centre):
- **Windscreen:** black frame with a V-shaped lower edge (2.54 m in the middle, 2.75 m at
  ±1.15 m); glass up to 3.95 m; destination display behind the glass at 3.98–4.31 m (±0.7 m);
  dark roof cap.
- **Red mask:** round the frame, down to 1.61 m in the middle (±0.61 m) and to 2.12 m at the sides.
- **Lamps:** dark recess 1.61–2.12 m at ±0.61–1.07 m with the LED lamps (1.73–2.07 m).
- **Lower front:** dark coupler recess below 1.61 m (±0.7 m); white lower corners 0.51–1.59 m
  with dark grilles at 0.74–1.36 m, ±0.9–1.3 m.

Side view (photo 01): a red line rises along the windscreen edge from 1.9 m at the front (2.83 m
at 0.47, 3.54 at 1.1, 3.94 at 1.77) into the roof-edge line at 2.4 m, with the black windscreen
wrap above it. Behind the windscreen edge a black band carries the cab side window (2.2–3.1 m).

## Scale (true proportions)
The body is authored 34 voxels wide (2.80 m at the same 12.2 voxels per metre as the height),
and the recipe's `BODY_WIDTH_M = 2.8` matches it, so the render step keeps that width.

## Approximations
- **Cab cars:** compressed from 25.74 m to 25.6 m; the intermediate cars keep their real lengths.
- **Car 4:** its upper deck is modelled like car 3's; its small fifth lower window is from the sketch.
- **Pantograph:** which cab car runs with it raised is a choice (car 6, the rear one).
- **Class numerals and lettering:** suggested by light patches; the SBB panel has no lettering.
- **Roof:** air-conditioning and equipment boxes are simple boxes at the sketch positions.
