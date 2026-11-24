"""SBB RABe 511 "Regio-Dosto" (Stadler KISS, first generation) in true proportions.

`build_regio_car(spec, lights)` builds one car on the train canvas from a `RegioSpec`. Every
position is measured from Stadler's type sketches in the datasheets (the 2008 half-train sketch
and the 2015 full-train sketch, scaled to 150,000 mm over couplers and 4.595 m rail to roof), the
cross-section and livery heights from REV0's 3D props and Wikimedia photos
(models/sbb/rabe511/REFERENCE.md). Positions are *real* metres from the car's front coupling plane
(cab cars: from the nose tip), scaled to the modelled length; heights and widths are 12.2 voxels
per metre (roof 4.595 m = z 56, the 2.80 m body 34 voxels wide), so the recipe's BODY_WIDTH_M
keeps the authored width when rendered (docs/SCALE.md).

Structure: lower deck between the doors (body down to 0.25 m), intermediate levels over the
bogies (body bottom 1.0 m), upper deck along the double-deck section, a roof rounded right across
from 3.2 m. Cab cars: full-height cab with a blunt nose (measured side and plan tables) over the
motor bogie, a louvred equipment hatch behind the cab, and the pantograph in a lowered roof well
(4.1 m) over the inner intermediate level.
Livery: white body (fixed), skirt and the thin line at the upper-deck floor CC2 dark shade (S-Bahn
Zürich: dark blue; RegioExpress / InterRegio: anthracite), anthracite roof sides from 3.55 m with
the upper-deck windows reaching into them, red (CC1) door panels with two blue bands (pictograms,
class number), first class: yellow lines. Nose: red U round a black windscreen, anthracite roof cap
with the destination display and top lamp, black "eyes" with the lamps, white wings and lower
band, CC2 skirt with the coupler recess and grilles; on the side a red stripe along the nose edge
up to the roof and a black cab window.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import (
    CrossSection,
    EndShape,
    Shell,
    door_outline,
    face_mask,
    louvres,
    rounded_window,
    side_band,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

ZM = 12.2  # voxels per metre across and up (true proportions)

# heights (z), REFERENCE.md "Measurements" (type sketch and 3D props, rail to roof 4.595 m)
LOW_FLOOR = 3  # lower-deck body bottom, 0.25 m
HIGH_FLOOR = 12  # over the bogies, 1.0 m
SKIRT_TOP = 18  # CC2 below 1.44 m
LOWER_WIN = (15, 24)  # 1.24–1.93 m
DISPLAY_Z = (25, 27)  # passenger displays over the lower windows, 2.05–2.22 m
MEZZ_WIN = (26, 35)  # 2.16–2.83 m
WAIST = (31, 33)  # CC2 line at the upper-deck floor, 2.56–2.72 m
UPPER_WIN = (40, 48)  # 3.31–3.94 m
BAND_FROM = 43  # anthracite roof sides from 3.55 m
DOOR_Z = (7, 30)  # leaves 0.55–2.47 m
DOOR_BAND = (30, 33)  # blue band with the pictograms over the leaves, 2.50–2.71 m
CLASS_BAND = (36, 39)  # blue band with the class number, 2.97–3.18 m
FIRST_UPPER = (41, 42)  # yellow first-class lines: under the upper windows, 3.40–3.48 m
FIRST_LOWER = (18, 19)  # and at the foot of the lower windows, 1.48–1.56 m
LOGO_Z = (37, 41)  # SBB logo, 3.0–3.35 m
ROOF = 56  # 4.595 m
WELL_ROOF = 50  # pantograph well, 4.1 m
ROOF_LOUVRE_Z = (50, 55)  # louvred air-conditioning covers at the roof edge, 4.10–4.57 m
HALF_WIDTH = 17  # 1.40 m

# the 3D props' section: vertical sides to 3.4 m, then rounded right across (0.51 m half-width
# at 4.53 m); a roof radius of the full half-width matches it within half a voxel
SECTION = CrossSection(floor=HIGH_FLOOR, roof=ROOF, half_width=HALF_WIDTH, roof_radius=17, tumblehome=0)
FLAT = EndShape(rake=0, corner_radius=2)

# nose (REFERENCE.md "Nose"), metres from the tip: side setback by height, plan setback by
# half-width; the nose recedes by the larger of the two
NOSE_SIDE = (
    (0.0, 0.6), (0.25, 0.42), (0.4, 0.22), (0.6, 0.15), (0.75, 0.05), (1.4, 0.05), (1.8, 0.0), (2.0, 0.0),
    (2.1, 0.07), (2.2, 0.09), (2.4, 0.16), (2.6, 0.22), (2.8, 0.31), (3.0, 0.40), (3.2, 0.51), (3.4, 0.63),
    (3.6, 0.80), (3.8, 0.94), (4.0, 1.10), (4.1, 1.21), (4.2, 1.32), (4.3, 1.47), (4.4, 1.63), (4.5, 1.94),
    (4.6, 2.8),
)  # fmt: skip
NOSE_PLAN = ((0.0, 0.0), (1.02, 0.02), (1.09, 0.2), (1.16, 0.25), (1.23, 0.33), (1.30, 0.40), (1.38, 0.52), (1.42, 0.9))
STRIPE_W = 0.45  # red stripe on the side, behind the nose edge (m)

WHITE = P.OFF_WHITE
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
ACCENT = P.DARK_CC2
BLACK = P.BLACK
DARK = P.DARK
ROOF_GREY = P.ROOF_DARK
DOOR_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = P.YELLOW
HATCH = P.ramp(P.GREY, 0.72)

Span = tuple[float, float]


@dataclass
class RegioSpec:
    cab: bool = False  # cab at the front (high x)
    real_m: float = 24.72  # coupling plane to coupling plane (cab cars: nose tip to coupling plane)
    length_m: float = 24.7  # modelled
    doors: tuple[Span, ...] = ((5.87, 7.46), (17.28, 18.87))
    bogies: tuple[float, float] = (3.2, 21.52)
    upper: tuple[Span, ...] = ()
    lower: tuple[Span, ...] = ()
    mezz: tuple[Span, ...] = ((0.96, 2.13), (2.65, 3.83), (20.91, 22.09), (22.61, 23.78))
    displays: tuple[Span, ...] = ((12.31, 13.29), (13.99, 14.97))
    roof_louvres: tuple[Span, ...] = ((0.4, 2.7), (22.03, 24.33))
    logo: float = 20.9  # start of the SBB logo (red box), the lettering follows towards the rear
    first_class: bool = False  # yellow lines, class number "1" on the door bands
    first_lower: Span | None = None  # stretch of the lower deck with first-class seats
    pantograph: float | None = None  # position (m) in the roof well of a cab car's inner end
    pantograph_raised: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"


def cab_car(**kw) -> RegioSpec:
    """Cab end car (cars 1 and 6, Bt with the motor bogie): cab, equipment hatch, double-deck
    section between the doors, pantograph in the roof well over the inner intermediate level."""
    base = RegioSpec(
        cab=True,
        real_m=24.92,
        length_m=24.9,
        doors=((7.05, 8.69), (16.96, 18.54)),
        bogies=(3.98, 21.72),
        upper=((9.17, 10.35), (10.87, 12.05), (12.5, 13.08), (13.55, 14.73), (15.25, 16.43)),
        lower=((9.17, 10.0), (10.51, 11.69), (12.21, 13.39), (13.9, 15.07), (15.6, 16.43)),
        mezz=((4.98, 5.48), (20.12, 20.94)),
        displays=((12.3, 13.28), (14.0, 14.98)),
        roof_louvres=((3.95, 5.79),),
        logo=2.55,
        pantograph=22.9,
    )
    return replace(base, **kw)


def first_car(**kw) -> RegioSpec:
    """Car 2 (AB): first class upstairs and in the rear half of the lower deck, larger windows."""
    base = RegioSpec(
        upper=((7.97, 9.43), (9.96, 11.45), (11.95, 12.79), (13.3, 14.76), (15.3, 16.77)),
        lower=((8.12, 9.3), (9.82, 11.0), (11.5, 12.68), (13.3, 14.76), (15.3, 16.77)),
        displays=((11.61, 12.58), (13.54, 14.52)),
        first_class=True,
        first_lower=(12.2, 17.28),
    )
    return replace(base, **kw)


def multi_car(**kw) -> RegioSpec:
    """Car 3 (B): multi-purpose area and wheelchair toilet in the front half of the lower deck."""
    base = RegioSpec(
        upper=((7.98, 9.18), (9.67, 10.82), (11.23, 11.81), (12.19, 13.37), (13.89, 15.07), (15.59, 16.76)),
        lower=((7.98, 8.8), (12.19, 13.37), (13.89, 15.07), (15.59, 16.76)),
    )
    return replace(base, **kw)


def second_car(**kw) -> RegioSpec:
    """Car 4 (B): six windows on each deck."""
    w = ((7.98, 9.15), (9.67, 10.85), (11.23, 11.81), (12.22, 13.4), (13.92, 15.09), (15.59, 16.76))
    return replace(RegioSpec(upper=w, lower=w), **kw)


def first_car_b(**kw) -> RegioSpec:
    """Car 5 (AB): car 2's counterpart, its first-class lower deck at the front."""
    base = RegioSpec(
        upper=((7.96, 9.44), (9.96, 11.44), (11.96, 12.78), (13.3, 14.78), (15.3, 16.78)),
        lower=((7.96, 9.44), (9.96, 11.44), (12.07, 13.22), (13.74, 14.92), (15.44, 16.61)),
        roof_louvres=((0.38, 2.68), (2.74, 4.57), (22.06, 24.36)),
        first_class=True,
        first_lower=(7.46, 12.5),
    )
    return replace(base, **kw)


def build_regio_car(spec: RegioSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.cab
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    scale = spec.length_m / spec.real_m

    def at(u: float) -> float:
        """Real metres from the front -> x."""
        return x_front - u * 10 * scale

    def span(s: Span) -> tuple[float, float]:
        return at(s[1]), at(s[0])

    d0, d1 = spec.doors[0][0], spec.doors[-1][1]

    def floor_at(X: np.ndarray) -> np.ndarray:
        ur = (x_front - X) / 10 / scale
        # lower deck from 0.75 m before the first door to 1.35 m behind the last, 0.5 m ramps
        d = np.maximum((d0 - 0.75) - ur, ur - (d1 + 1.35))
        floor = np.clip(LOW_FLOOR + (HIGH_FLOOR - LOW_FLOOR) * d / 0.5, LOW_FLOOR, HIGH_FLOOR)
        if spec.cab:  # nose block down to the skirt, rising to the motor bogie
            floor = np.where(ur < 2.4, np.clip(LOW_FLOOR + (ur - 1.5) * 12, LOW_FLOOR, HIGH_FLOOR), floor)
        return floor

    def roof_at(X: np.ndarray) -> np.ndarray:
        if spec.pantograph is None:
            return np.full_like(X, ROOF, dtype=float)
        ur = (x_front - X) / 10 / scale
        # roof well from 20.1 m, a 0.3 m slope down from the full roof
        return np.clip(ROOF - (ur - 19.8) / 0.3 * (ROOF - WELL_ROOF), WELL_ROOF, ROOF)

    shell = Shell(x_rear, x_front, SECTION, front=FLAT, rear=FLAT, floor_at=floor_at, roof_at=roof_at)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    ur = (x_front - X) / 10 / scale
    body = shell.mask(mdl)
    if spec.cab:
        side_sb = np.interp(Z / ZM, *zip(*NOSE_SIDE, strict=True))
        plan_sb = np.interp(dy / ZM, *zip(*NOSE_PLAN, strict=True))
        body &= ur >= np.maximum(side_sb, plan_sb)

    # --- body colours -------------------------------------------------------------
    mdl.solid(body, WHITE)
    mdl.paint(Z < SKIRT_TOP, ACCENT)
    mdl.paint(Z >= BAND_FROM, ROOF_GREY)
    mdl.paint(side_band(mdl, x_rear, x_front, *WAIST), ACCENT)

    # --- windows ------------------------------------------------------------------
    for s in spec.upper:
        rounded_window(mdl, *span(s), *UPPER_WIN)
    for s in spec.lower:
        rounded_window(mdl, *span(s), *LOWER_WIN)
    for s in spec.mezz:
        rounded_window(mdl, *span(s), *MEZZ_WIN)
    for s in spec.displays:
        mdl.paint(side_band(mdl, *span(s), *DISPLAY_Z), BLACK)

    # --- first class: yellow lines along the upper windows and part of the lower deck ----------
    if spec.first_class:
        upper = side_band(mdl, at(spec.doors[-1][0]), at(spec.doors[0][1]), *FIRST_UPPER)
        mdl.paint(upper & (mdl.d != P.GLASS) & (mdl.d != BLACK), FIRST_YELLOW)
        if spec.first_lower is not None:
            lower = side_band(mdl, *span(spec.first_lower), *FIRST_LOWER)
            mdl.paint(lower & (mdl.d != P.GLASS) & (mdl.d != BLACK), FIRST_YELLOW)

    # --- door panels: red up to the roof sides, the leaves, two blue bands, a window on top -----
    for a, b in spec.doors:
        x0, x1 = span((a, b))
        mdl.paint(side_band(mdl, x0, x1, DOOR_Z[0], BAND_FROM), RED)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_BAND), DOOR_BLUE)
        mdl.paint(side_band(mdl, x0, x1, *CLASS_BAND), DOOR_BLUE)
        c = (x0 + x1) / 2
        for p in (x0 + 0.25 * (x1 - x0), x1 - 0.25 * (x1 - x0)):  # pictograms
            mdl.paint(side_band(mdl, p - 0.5, p + 0.5, DOOR_BAND[0] + 1, DOOR_BAND[1]), P.OFF_WHITE)
        num = side_band(mdl, x0 + 0.15 * (x1 - x0), x0 + 0.15 * (x1 - x0) + 1, CLASS_BAND[0] + 1, CLASS_BAND[1])
        mdl.paint(num, FIRST_YELLOW if spec.first_class else P.OFF_WHITE)  # class number
        door_outline(mdl, x0 + 1, x1 - 1, *DOOR_Z, RED_DARK, lintel=0)
        for g0, g1 in ((x0 + 2, c - 1), (c + 1, x1 - 2)):
            mdl.inset(side_band(mdl, g0, g1, 12, 27), P.GLASS)
        w = (b - a) * 0.36 / 2  # upper-deck window over the door, into the roof-side band
        rounded_window(mdl, *span(((a + b) / 2 - w, (a + b) / 2 + w)), *UPPER_WIN)

    # SBB logo (red box, white cross) and the "SBB CFF FFS" lettering behind it
    lg = span((spec.logo, spec.logo + 0.7))
    mdl.paint(side_band(mdl, *lg, *LOGO_Z), RED)
    lc = (lg[0] + lg[1]) / 2
    mdl.paint(side_band(mdl, lc - 1.5, lc + 1.5, LOGO_Z[0] + 1, LOGO_Z[1] - 1), P.OFF_WHITE)
    text = side_band(mdl, *span((spec.logo + 0.9, spec.logo + 3.0)), LOGO_Z[0] + 1, LOGO_Z[1] - 1)
    mdl.paint(text & (np.floor(X) % 3 != 0), DARK)

    # louvred air-conditioning covers at the roof edge
    for s in spec.roof_louvres:
        louvres(mdl, *span(s), *ROOF_LOUVRE_Z, pitch=2, back=P.DARK_GREY, slat=P.MID_GREY)

    # --- cab car: equipment hatch, nose ----------------------------------------------------
    if spec.cab:
        hatch = span((2.6, 3.5))
        mdl.paint(side_band(mdl, *hatch, 19, 35), HATCH)
        louvres(mdl, hatch[0] + 1, hatch[1] - 1, 20, 34, pitch=2, back=P.MID_GREY, slat=P.LIGHT_GREY)
        door_outline(mdl, *span((3.9, 4.45)), 31, 35, P.MID_GREY)  # service flap
        _nose(mdl, ur, dy, Z)
        lamp_cluster(
            mdl, shell, True, lights.state("front"), low_z=(19, 23), top_z=(47, 49), spacing=9, lamp_half_width=2,
            face=True,
        )  # fmt: skip

    # --- ends: gangway bellows ------------------------------------------------------------
    for front in (False,) if spec.cab else (False, True):
        skin = face_mask(mdl, front, depth=2) & (Z >= HIGH_FLOOR)
        mdl.paint(skin & (dy <= 8) & (ROOF - 4 > Z), BLACK)
        mdl.paint(skin & (dy <= 6) & (Z >= HIGH_FLOOR + 2) & (ROOF - 6 > Z), DARK)

    # --- roof: pantograph in the well of a cab car ----------------------------------------
    if spec.pantograph is not None:
        px = at(spec.pantograph)
        pantograph(mdl, px, WELL_ROOF - 1, raised=spec.pantograph_raised, facing_front=False, raise_height=14)
        main_switch(mdl, px + 14, WELL_ROOF)
        roof_cable(mdl, px + 4, at(20.3), WELL_ROOF)

    # --- running gear: four bogies of 2.5 m wheelbase, 920 mm wheels ------------------------------
    for i, b in enumerate(spec.bogies):
        motor = spec.cab and i == 0
        style = "loco" if motor else "coach"
        bogie(mdl, at(b), wheelbase=25 * scale, wheel_diameter=9, top=HIGH_FLOOR - 3, style=style)

    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose(mdl: Model, ur: np.ndarray, dy: np.ndarray, Z: np.ndarray) -> None:
    """Front (head-on photos and the 3D prop, REFERENCE.md "Nose"): red U round the black
    windscreen, anthracite roof cap with the display and top lamp, black eyes with the lamps,
    white wings and lower band, CC2 skirt with the coupler recess and grilles. Side: red stripe
    along the nose edge up to the roof, black cab window behind it."""
    h = Z / ZM  # height (m)
    w = dy / ZM  # half-width (m)
    # the nose edge seen from the side: the body's front-most voxel in each (y, z) column
    occ = mdl.d != 0
    tip = (mdl.d.shape[0] - 1 - np.argmax(occ[::-1], axis=0))[None, :, :]
    X, _, _ = mdl.coords()
    per_voxel = float(np.ravel(ur)[0] - np.ravel(ur)[1])  # metres per voxel along x
    edge = ur - (tip - X) * per_voxel
    nose = ur < 3.2
    # the outermost columns are the sides wrapping round and keep the side livery
    face = face_mask(mdl, True, depth=3) & (ur < 3.0) & (w <= 1.3)

    # side: red stripe behind the nose edge, from the eyes up to the roof cap
    side = nose & ~face
    mdl.paint(side & (ur < edge + STRIPE_W) & (h >= 1.5) & (h < 4.2), RED)
    # black cab window behind the stripe, glass in it
    cab_win = side & (ur >= edge + STRIPE_W + 0.08) & (ur < 2.0) & (h >= 2.1) & (h < 3.25)
    mdl.paint(cab_win, BLACK)
    mdl.inset(cab_win & (ur >= 1.19) & (ur < 1.81) & (h >= 2.18) & (h < 2.94), P.GLASS)

    # front face
    red_outer = 0.76 + (1.28 - 0.76) * np.clip((h - 1.55) / (3.6 - 1.55), 0, 1)  # the U widens upwards
    mdl.paint(face & (h >= 1.44), WHITE)  # wings and the band under the eyes
    mdl.paint(face & (h >= 1.55) & (w <= red_outer), RED)
    mdl.paint(face & (h >= 3.6) & (h < 4.2), RED)  # the U reaches up round the roof cap
    ws_hw = 0.85 + 0.125 * np.clip((h - 2.16) / 1.29, 0, 1)  # windscreen, wider at the top
    mdl.paint(face & (h >= 2.16) & (h < 3.45) & (w <= ws_hw), BLACK)
    mdl.inset(face & (h >= 2.28) & (h < 3.37) & (w <= ws_hw - 0.1), P.GLASS)
    mdl.paint(face & (h >= 3.45) & (w <= 1.0), ROOF_GREY)  # roof cap
    mdl.paint(face & (h >= 3.47) & (h < 3.79) & (w <= 0.7), BLACK)  # destination display
    # eyes: black lens-shaped housings round the lamps
    eye_mid = 1.71
    eye_h = 0.16 * np.sqrt(np.clip(1 - ((w - 0.86) / 0.34) ** 2, 0, 1))
    mdl.paint(face & (abs(h - eye_mid) <= eye_h + 0.02) & (w >= 0.52) & (w <= 1.2), BLACK)
    mdl.paint(face & (h >= 1.62) & (h < 1.75) & (w <= 0.12), P.OFF_WHITE)  # SBB logo
    # skirt: coupler recess and the grilles of the energy absorbers
    mdl.paint(face & (h < 1.29) & (h >= 0.5) & (w <= 0.6), BLACK)
    mdl.paint(face & (h < 1.29) & (h >= 0.84) & (w >= 0.69) & (w < 1.07), DARK)
