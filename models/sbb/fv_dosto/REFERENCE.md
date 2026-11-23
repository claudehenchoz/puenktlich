# SBB FV-Dosto (RABe 502 / RABDe 502, Bombardier TWINDEXX Swiss Express): reference

SBB calls it the "LD double-decker". Built by Bombardier/Alstom, 62 units 2018–2022:
IC 200 RABDe 502 001–023 (8 cars, restaurant), IR 200 RABe 502 201–230 (8 cars),
IR 100 RABe 502 401–409 (4 cars). Modelled in **true proportions** (see "Scale" below).

## Data (Bombardier factsheets in docs/train-3d-models: RABe502-Factsheet-IR100.pdf, RABDe502-Factsheet-IC200.pdf)
| | IR100 | IC200 |
|---|---|---|
| Train length | 101,000 mm | 200,600 mm |
| Cars | 4 | 8 |
| Car width / height | 2,800 / 4,590 mm | same |
| Entrance height above rail / passenger-room height | 600 / 2,000 mm | same |
| Doors per side / clear width | 8 / 1,300 mm | 16 / 1,300 mm |
| Seats (1st / 2nd / restaurant) | 330 (47 / 283) | 606 (176 / 401 / 29) |
| Power / starting tractive effort | 3.75 MW / 241 kN | 7.5 MW / 482 kN |
| Driven axles | 37.5 % | 37.5 % |
| Max speed | 200 km/h | 200 km/h |
| Wheel Ø new / worn | 920 / 840 mm | same |
| Bogie | FLEXX Tronic WAKO (roll compensation) | same |

Car order from the factsheet diagrams. IR100: Endwagen 2. Klasse · Mittelwagen 2. Klasse mit
Behindertenbereich · Mittelwagen 2. Klasse · Endwagen 1. Klasse. IC200: Endwagen 1. Klasse (with
the luggage room and its separate loading door) · Mittelwagen 1. Klasse · Mittelwagen 1. Klasse ·
Mittelwagen 2. Klasse mit Behindertenbereich (restaurant upstairs) · Mittelwagen 2. Klasse ×3 ·
Endwagen 2. Klasse. de.wikipedia "SBB RABe 502" (bogie wheelbase 2,500 mm) agrees.

## 3D model (measurement source)
`docs/train-3d-models/SBB RABDe 502 (TWINDEXX)/SBB TWINDEXX-IC Zurich (8)/*.glb`, a converted
Cities: Skylines workshop asset (third party): used for measurements only, nothing copied.
glTF units are metres (y up, z along the car). Measured by rasterizing the meshes orthographically
with their textures (side, top, front, rear) at 40 px/m:
- end car (mesh 0 "Cube.060", the other end car mesh 8 with the pantograph): 25.32 m long,
  2.93 m over the mirrors, 4.60 m high; intermediate cars (meshes 4–7): 24.28 m.
- The model's intermediate cars share one texture, so the class of each intermediate car comes
  from the factsheet, not from the model.

## Measurements (z and y: 12.2 voxels per metre, roof 4.59 m = z 56; x: 10 voxels per metre)
Cross-section (intermediate car, half-width by height): 1.19 m at 0.25 m, 1.40 m from 0.5 to
3.25 m (vertical sides), 1.35 at 3.5, 1.30 at 3.75, 1.18 at 4.0, 0.93 at 4.25, 0.60 at 4.5, roof
4.59 m. Modelled: half-width 17 (1.40 m), tumblehome 2 below z 7, roof radius 13 with a 1.5 voxel
chamfer from z 40.

| Feature | m | z |
|---|---|---|
| Lower-deck body bottom / intermediate levels over the bogies | 0.25 / 0.75 | 3 / 9 |
| Black lower band (all cars) | 0.25–1.42 | 3–17 |
| Lower-deck windows | 1.25–1.95 | 15–24 |
| Thin black line | 3.25 | 39–40 |
| Upper-deck windows | 3.30–3.92 | 40–48 |
| Dark upper band and roof | from 3.95 | from 48 |
| Door: red leaves / blue band / yellow header (1st class) | 0.45–2.65 / 2.65–2.80 / 2.90–3.00 | 6–32 / 32–34 / 35–37 |
| SBB logo and lettering | 2.75–2.95 | 33–36 |
| Cab section roof (end car, up to 7.6 m, double-deck roof from 8.0 m) | 4.15 | 51 |

Intermediate car (24.28 m, metres from one end): doors 5.55–7.20 and 17.10–18.75; bogies 3.1 and
21.0; upper windows 1.4 m wide every 2.0 m from 1.38 to 22.9 (1.0 m over a door); lower windows
8.55–9.95, 10.55–11.95, 12.55–13.95, 14.9–15.7; small windows over the intermediate levels
1.75–2.40 and 20.30–20.95; louvred equipment panels at both ends.

End car (25.32 m, metres from the nose tip): door 1 7.2–8.8 (IC200 1st class: white loading door
with a narrow window), door 2 18.1–19.8; bogies 5.2 and 22.5; upper windows 10.50–11.93,
12.5–13.9, 14.5–15.9, 16.5–17.9, 18.55–19.55, 20.52–21.95, 22.52–23.93; lower windows 12.6–14.0,
14.55–15.35, 15.95–16.75; pantograph on the cab section roof at ≈5 m.

## Nose
Side profile (top of the silhouette, metres from the tip → height): 0.1 → 1.23, 0.25 → 1.58,
0.5 → 2.01, 0.75 → 2.33, 1.0 → 2.63, 1.5 → 3.13, 2.0 → 3.66, 2.5 → 4.06, 3.0 → 4.13 (cab roof).
Bottom: 0.73 at the tip, 0.5 at 0.5–1.0, 0.23 from 1.5. Plan half-width: 0.74 at 0.1, 0.85 at
0.25, 0.98 at 0.5, 1.14 at 1.0, 1.26 at 1.5, 1.34 at 2.0, 1.38 from 2.5.
Modelled: `EndShape(rake=32, rake_from=13, rake_curve=1.35, undercut=15, undercut_height=6,
plan_depth=26, plan_power=5)` (rake and plan taper combined by max()).

Livery boundaries on the side (metres from the tip → height), used as interpolation tables in
`parts/fv_dosto.py`: lower edge of the red mask 0.95 (tip), 1.35 (1.0), 2.0 (1.5), 2.55 (2.0),
2.95 (2.5), 3.25 (3.0), 3.65 (4.0), 3.85 (5.0), 3.95 (5.5–5.9), then as the red roof-edge band
3.65 (6.0) rising to the roof at 7.0–7.4; lower edge of the black wedge 1.45 (1.5), 1.75 (2.0),
2.1 (2.5), 2.15 (3.0), 2.45 (3.5), 2.75 (4.0), 3.05 (4.5), 3.25 (5.0), 3.45 (5.5), 3.6 (5.9),
white below it; below 1.5 m from the tip the nose is black up to the red mask. The red mask
covers the nose top to ≈3.8 m, then runs on along both roof edges.

Front face (half-width by height): dark roof cap above 4.25 m; black windscreen panel ±1.0 m
from 2.3 to 4.15 m, glass ±0.85 m 2.35–3.65 m; grey-blue U outline at ±0.95–1.05 m from 1.15 m
up to ≈2.95 m, round a black lower panel 1.2–2.25 m; red outside the outline and as a chin
0.85–1.05 m; black bumper below 0.85 m.

## Scale (true proportions)
The body is authored 34 voxels wide (2.80 m at the same 12.2 voxels per metre as the height)
and the recipe's `BODY_WIDTH_M = 2.8` matches it, so the render step keeps that width (the other
trains are authored wider and scaled to their real width, docs/SCALE.md). Width:height = 0.61, as on the
real train. Cars keep their real lengths in their 8/8 slots; the intermediates' gangway bellows
reach out to the slot ends so coupled cars meet.

## Approximations
- Pantograph positions (one on each end car's cab section, the rear one raised) and the restaurant
  car's red window band are from photos, not the 3D model.
- Lamps, the SBB logo on the front and the door window are simplified.
