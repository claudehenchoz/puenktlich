# SBB RABe 511 Regio-Dosto (Stadler KISS, first generation): reference

SBB calls it the "Regio double-decker" / "Regio-Dosto". Stadler called it DOSTO during
development. It is the third generation of double-deck trains on the S-Bahn Zürich. All units were
built by Stadler Rail Altenrhein, 93 in total:
- **69 six-car units** (511 001–069): 50 ordered in June 2008, 19 more in 2015 (first delivered
  January 2016). Mainly S-Bahn Zürich and RE Wettingen–Olten–Luzern.
- **24 four-car units** (511 101–124): ordered in April 2010 for RegioExpress lines.

From 2020 to 2024, 511 015–030, 036–038 and all of 101–124 were refitted as InterRegio-Dosto
(IRD), which removed some seats. A mid-life refit started in 2026 (511 013 first, back in service
September 2026). It brings new GFK cab fronts and white frames round the red doors; it is not
modelled.

Modelled in **true proportions** (see "Scale" below), like the FV-Dosto, the RABe 503 and the
RABe 512.

## Sources (docs/research/rabe511)
- **Stadler datasheets:**
  - `RABe511-Stadler-Datasheet-KISS-SBB-6car-EN.pdf`, reference sheet KISS DOSBBZ0908e, covering
    all 69 six-car units. Vector type sketch of the full train.
  - `RABe511-Stadler-Datenblatt-KISS-SBB-6tlg-DE.pdf`, the original 2008 sheet KISS DOSBBZ0708d
    (50 units).
- **Modelling references:** `SBB RABe 511 - 3D Models and Modelling References.pdf`. It contains:
  - Both type sketches, rendered at high resolution:
    - the full 6-car train (5822 px, 2015 sheet);
    - the cab car and two intermediate cars at about 1.5 times the scale (4382 px, 2008 sheet).

    Each shows upper-deck plans, side elevation and lower-deck plan.
  - The data table.
  - 16 Wikimedia Commons photos (1920 px).
  - The finding that no free general-purpose 3D model exists (searched 2026-11-23).
- **3D props:** REV0's Cities: Skylines props in `docs/train-3d-models/SBB RABe 511 (KISS)/`:
  `Prop SBB RABe 511Bt` (cab car), `Bt2` (cab car with pantograph), `AB`, `B`. They're 2016-era
  models of the original KISS in the grey RE livery.
  - Their absolute size is off: about 0.95 scale (cab car 23.88 m, intermediate cars 23.42 m,
    2.756 m wide, 4.365 m high).
  - So they were used only for the cross-section and the livery heights, scaled to the 4.595 m
    roof (× 1.053) and the 2.80 m width (× 1.016). Lengths and positions come from the sketches.
- **Photos used** (in the references PDF; Commons):
  - cab car side and intermediate cars at Chur (Bahnfrend, CC BY-SA 4.0);
  - whole train side-on at Lyssach (Nelso Silva, CC BY-SA 2.0): the class layout;
  - head-on 511 120 at Ziegelbrücke (NAC, CC BY-SA 3.0);
  - 3/4 front of 511 001 with the blue S-Bahn band (Alainkaa, public domain).

## Data (Stadler datasheets, de.wikipedia for the 4-car unit)
| | 6-car | 4-car |
|---|---|---|
| Units | 511 001–069 | 511 101–124 |
| Length over couplers | 150,000 mm | 100,360 mm |
| Axle layout | Bo'Bo' + 2'2' + 2'2' + 2'2' + 2'2' + Bo'Bo' | Bo'Bo' + 2'2' + 2'2' + Bo'Bo' |
| Seats (1st + 2nd) | 120 + 415, 838 standing | 60 + 277 (52 + 265 after the IR refit), 548 standing |
| Mass empty | 297 t | 211.9 t |

Both versions share the rest:
- **Body:** width 2,800 mm, height 4,595 mm.
- **Floor heights:** 555 mm at the entrance (low floor), 440 mm on the lower deck, 2,515 mm on the
  upper deck.
- **Doors:** entrance width 1,400 mm, 12 doors per side on the 6-car.
- **Running gear:** bogie wheelbase 2,500 mm (motor and trailer), wheels Ø 920 mm.
- **Performance:**
  - 4,000 kW continuous, 6,000 kW peak (the model uses 6,000 kW for both versions);
  - 400 kN starting tractive effort, 1.1 m/s², 160 km/h;
  - 15 kV 16.7 Hz.

Only the two cab cars are motored, so power and tractive effort are the same for both versions.

## Type sketches (measurement source)
**Scales:**
- **Large sketch (2008):** 55.06 px/m from rail to roof (253 px for 4.595 m). Lengthways it is
  55.27 px/m, which makes 2 cab cars and 4 intermediate cars come to 150.0 m; the two scales agree
  within 0.4 %.
- **Full-train sketch:** 36.34 px/m up and 36.54 px/m along (5481 px over couplers for 150 m).

Both sketches give the same positions within ±0.05 m. Car lengths come from the gangway bellows
centres (the coupling planes).

**Car order and classes** (front to rear). The whole-train photo shows the yellow first-class
lines on car 2, wheelchair pictograms on car 3, and the WC on car 4 in the full-train plan.
1. Bt, cab car, 2nd class, motor bogie; pantograph in a roof well over the inner end.
2. AB: 1st class upstairs and in the rear half of the lower deck.
3. B: multi-purpose area and wheelchair toilet on the lower deck.
4. B.
5. AB: car 2's counterpart.
6. Bt, the cab car turned round, pantograph raised.

The 4-car unit is modelled as cars 1, 2, 3 and 6. No sketch of it exists; 100.36 m is 2 cab cars
plus 2 intermediate cars.

**Car lengths** (coupling plane to coupling plane):
- **Cab cars:** 24.92 m from the nose tip. The coupler face is 0.63 m ahead, so 25.55 m including
  it; the car's lettering says 25.36 m over couplers. Modelled at 24.9 m.
- **Intermediate cars:** 24.72 m, modelled at 24.7 m.
- The cab car's bogie centres are 17.74 m apart (lettering: 17.84 m).

## Measurements (z and y: 12.2 voxels per metre, roof 4.595 m = z 56; x: 10 per metre)
Window and door positions are from the sketches; the livery heights are from the 3D props, scaled.

| Feature | m | z |
|---|---|---|
| Lower-deck body bottom / over the bogies | 0.25 / 1.0 | 3 / 12 |
| CC2 skirt / white above | – 1.44 | – 18 |
| Lower-deck windows | 1.24–1.93 | 15–24 |
| Passenger displays over the middle lower windows | 2.05–2.22 | 25–27 |
| Windows of the intermediate levels | 2.16–2.83 | 26–35 |
| CC2 line at the upper-deck floor | 2.56–2.72 | 31–33 |
| Door leaves | 0.55–2.47 | 7–30 |
| Blue band with pictograms / blue band with the class number | 2.50–2.71 / 2.97–3.18 | 30–33 / 36–39 |
| SBB logo | 3.0–3.35 | 37–41 |
| Upper-deck windows (the upper half in the roof-side band) | 3.31–3.94 | 40–48 |
| Anthracite roof sides | 3.55– | 43– |
| First-class yellow lines: lower deck / upper deck | 1.48–1.56 / 3.40–3.48 | 18–19 / 41–42 |
| Louvred air-conditioning covers at the roof edge | 4.10–4.57 | 50–55 |
| Pantograph well / roof | 4.10 / 4.595 | 50 / 56 |

**Cross-section** (3D props): the sides are vertical up to 3.4 m, then rounded right across. The
half-width is 1.31 m at 3.6 m, 1.16 m at 4.0 m, 0.79 m at 4.3 m and 0.51 m at 4.53 m. A roof radius
of the full half-width (17 voxels) matches it within half a voxel.

Positions along each car (metres from its front coupling plane; cab car from the nose tip):

**Cab car (cars 1, 6):**
- motor bogie 3.98, trailer bogie 21.72;
- cab side window 1.19–1.81 (2.14–2.94 m) in a black surround;
- louvred hatch 2.6–3.5 (1.56–2.85 m), service flap 3.9–4.45, window 4.98–5.48 (the hatch and
  flap are from photo 01, which is near side-on there);
- doors 7.05–8.69 and 16.96–18.54;
- upper deck 9.17–10.35, 10.87–12.05, 12.50–13.08, 13.55–14.73, 15.25–16.43, plus a window over
  each door;
- lower deck 9.17–10.0, 10.51–11.69, 12.21–13.39, 13.90–15.07, 15.60–16.43;
- displays 12.3–13.28 and 14.0–14.98;
- window 20.12–20.94;
- roof well from 20.1 (0.3 m slope), pantograph at 22.9;
- louvred roof cover 3.95–5.79;
- SBB logo behind the cab from 2.55.

**Intermediate cars (all):**
- bogies 3.2 and 21.52;
- doors 5.87–7.46 and 17.28–18.87;
- windows of the intermediate levels 0.96–2.13, 2.65–3.83, 20.91–22.09, 22.61–23.78;
- louvred roof covers 0.4–2.7 and 22.03–24.33 (car 5 also 2.74–4.57);
- SBB logo at the rear end from 20.9.

**Car 2:**
- upper deck 7.97–9.43, 9.96–11.45, 11.95–12.79, 13.30–14.76, 15.30–16.77;
- lower deck 8.12–9.30, 9.82–11.0, 11.5–12.68, 13.30–14.76, 15.30–16.77;
- displays 11.61–12.58 and 13.54–14.52.

**Car 3:**
- upper deck 7.98–9.18, 9.67–10.82, 11.23–11.81, 12.19–13.37, 13.89–15.07, 15.59–16.76;
- lower deck 7.98–8.80, then the multi-purpose area, then 12.19–13.37, 13.89–15.07, 15.59–16.76.

**Car 4:** both decks 7.98–9.15, 9.67–10.85, 11.23–11.81, 12.22–13.40, 13.92–15.09, 15.59–16.76.

**Car 5:**
- upper deck 7.96–9.44, 9.96–11.44, 11.96–12.78, 13.30–14.78, 15.30–16.78;
- lower deck 7.96–9.44, 9.96–11.44, 12.07–13.22, 13.74–14.92, 15.44–16.61.

## Nose (type sketch side elevation and plan, 3D prop, head-on photos)
Side setback from the nose tip by height:

| Height (m) | 0.25 | 0.4 | 0.75–1.8 | 2.0 | 2.4 | 2.8 | 3.2 | 3.6 | 4.0 | 4.2 | 4.4 | 4.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Setback (m) | 0.42 | 0.22 | 0.05–0 | 0 | 0.16 | 0.31 | 0.51 | 0.80 | 1.10 | 1.32 | 1.63 | 1.94 |

- **Roof:** reaches its full height 2.8 m behind the tip.
- **Coupler and energy absorbers:** stand 0.63 m proud of the tip, at 0.7–1.3 m.
- **Plan:** blunt; flat over ±1.02 m, then 0.2 m back at 1.09 m, 0.4 m at 1.30 m and 0.52 m at
  1.38 m.

The side and plan setbacks are combined by max() (`parts/regio_dosto.py` `NOSE_SIDE`,
`NOSE_PLAN`).

Front livery (3D prop front view and photos, half-widths from the centre):
- **Windscreen:** black, 2.16–3.45 m, ±0.85 m at the bottom and ±0.975 m at the top.
- **Roof cap:** anthracite above it, with the destination display (3.47–3.79 m, ±0.7 m) and the
  top lamp (3.82–4.03 m).
- **Red U:** round the windscreen, up the sides of the cap to 4.2 m. Its outer edge narrows from
  ±1.28 m at 3.6 m to ±0.76 m at 1.55 m.
- **White:** the wings outside the red, and a band under the eyes (1.44–1.55 m).
- **Eyes:** black lens-shaped housings at 1.55–1.87 m, ±0.52–1.2 m, with the lamps at ±0.6–0.95 m.
- **Skirt (CC2):** the coupler recess (±0.6 m, 0.5–1.29 m) and the grilles of the energy absorbers
  (±0.69–1.07 m, 0.84–1.29 m).

Side of the nose: a red stripe 0.45 m wide runs behind the nose edge from the eyes (1.5 m) up to
the roof cap (4.2 m). A black cab-window surround follows behind it up to 2.0 m (2.1–3.25 m).

## Livery
- Body white (fixed); roof sides anthracite from 3.55 m.
- Door panels red (CC1) from the sill to the roof-side band, with two blue bands and a window on
  top.
- **Regional schemes** (the only difference is the skirt and the line at the upper-deck floor, =
  CC2 dark shade):
  - **S-Bahn Zürich (ZVV):** dark blue (photos 09, 10, 12). en.wikipedia calls it "red-white-blue".
  - **RegioExpress / InterRegio:** anthracite grey (photos 01, 03, the 3D props). en.wikipedia
    calls it "red-white-grey".
- ZVV logo on the door panels of Zürich units: omitted (too small at 1×).

## Scale (true proportions)
The body is authored 34 voxels wide (2.80 m at the same 12.2 voxels per metre as the height),
and the recipe's `BODY_WIDTH_M = 2.8` matches it, so the render step keeps that width.

## Approximations
- **Car 5:** modelled like car 2 with its own window positions; its first-class part of the lower
  deck is assumed to be at the front (car 2's counterpart).
- **Pantographs:** which cab car runs with it raised is a choice (car 6, the rear one).
- **Lettering:** suggested by light patches and a dotted dark line; pictograms and class numerals
  are single light voxels.
- **Roof equipment:** air-conditioning covers are louvred panels at the sketch positions.
- **Hatch and flap:** the cab car's hatch and flap are taken from a photo, so ±0.2 m.
