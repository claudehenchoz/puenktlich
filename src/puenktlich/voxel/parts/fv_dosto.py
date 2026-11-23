"""SBB FV-Dosto (RABe 502 / RABDe 502, Bombardier TWINDEXX Swiss Express) in true proportions.

`build_fv_car(spec, lights)` builds one car on the train canvas from an `FvSpec`. All sizes are
measured from the 3D model and the Bombardier factsheets (models/sbb/fv_dosto/REFERENCE.md):
x 10 voxels per metre along the car (positions are metres from the car's front end, cab cars
from the nose tip), y and z both 12.2 voxels per metre (roof 4.59 m = z 56), so the 2.80 m body
is 34 voxels wide. The recipe sets RENDER_WIDEN = False: the render step keeps this width
instead of the 1.5x aBase widening (docs/SCALE.md).

Structure: lower deck between the doors (body down to 0.25 m), intermediate levels over the
bogies (0.75 m), upper deck along the whole car; end cars have a single-level cab section with
a lower roof (4.15 m) up to 7.6 m and a long, raked nose that is also strongly tapered in plan.
Livery: white body CC2, red (CC1) nose mask and door leaves, black lower band and nose wedge,
dark upper band and roof, blue door bands, yellow headers on 1st class.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    side_skin,
)
from puenktlich.voxel.parts.dosto import deck_floor
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

ZM = 56 / 4.59  # voxels per metre across and up (true proportions)

# heights (z), REFERENCE.md "Measurements"
LOW_FLOOR = 3  # lower deck body bottom, 0.25 m
HIGH_FLOOR = 9  # intermediate levels over the bogies, 0.75 m
BLACK_TOP = 17  # black lower band up to 1.42 m
LOWER_WIN = (15, 24)  # 1.25–1.95 m
MEZZ_WIN = (22, 27)
GUTTER = (39, 40)  # thin black line at 3.25 m
UPPER_WIN = (40, 48)  # 3.30–3.92 m
DARK_FROM = 48  # dark upper band and roof from 3.95 m
ROOF = 56  # 4.59 m
CAB_ROOF = 51  # cab section 4.15 m
DOOR_Z = (6, 32)  # red leaves 0.45–2.65 m
DOOR_BAND = (32, 34)  # blue band
DOOR_YELLOW = (35, 37)  # 1st-class header
LOGO_Z = (33, 36)
HALF_WIDTH = 17  # 1.40 m

# measured cross-section: vertical sides 0.5–3.25 m, rounded in below 0.5 m and over the roof
SECTION = CrossSection(
    floor=LOW_FLOOR,
    roof=ROOF,
    half_width=HALF_WIDTH,
    roof_radius=13,
    tumblehome=2,
    tumble_from=7,
    chamfer_from=40,
    chamfer_inset=1.5,
)
# nose: tip at 0.75–1.05 m (z 9–13); windscreen rake 1.4 power curve, 3.2 m long at the roof line;
# plan taper from 1.38 m half-width 2.5 m back to 0.74 m at 0.1 m; undercut to 0.25 m at 1.5 m
NOSE = EndShape(
    rake=32, rake_from=13, rake_curve=1.35, corner_radius=2, undercut=15, undercut_height=6, plan_depth=26, plan_power=5
)
END = EndShape(rake=0, corner_radius=2)

# nose livery boundaries (metres from the tip -> height in metres), REFERENCE.md "Nose"
RED_LOW = (
    (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 5.9, 5.95, 6.5, 7.0, 7.4),
    (0.95, 1.0, 1.15, 1.35, 2.0, 2.55, 2.95, 3.25, 3.45, 3.65, 3.75, 3.85, 3.95, 3.95, 3.65, 3.75, 4.15, 4.6),
)
WEDGE_LOW = (
    (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 5.9),
    (1.45, 1.75, 2.1, 2.15, 2.45, 2.75, 3.05, 3.25, 3.45, 3.6),
)

WHITE = P.BODY_CC2
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
BLACK = P.BLACK
DARK = P.DARK
ROOF_GREY = P.ROOF_DARK
DOOR_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
OUTLINE = P.ramp(P.BLUE_GREY, 0.6)  # grey-blue outline round the black face panel
FIRST_YELLOW = P.YELLOW
DISPLAY = P.YELLOW
HATCH = P.ramp(P.GREY, 0.72)

Span = tuple[float, float]


@dataclass
class FvSpec:
    """Positions in metres from the car's front end (cab cars: from the nose tip)."""

    cab: bool = False
    length_m: float = 24.28
    doors: tuple[Span, ...] = ((5.55, 7.2), (17.1, 18.75))
    luggage_door: bool = False  # IC200 1st-class end car: white loading door instead of door 1
    bogies: tuple[float, float] = (3.1, 21.0)
    lower_windows: tuple[Span, ...] = ((8.55, 9.95), (10.55, 11.95), (12.55, 13.95), (14.9, 15.7))
    upper_windows: tuple[Span, ...] = tuple(
        (a, a + (1.0 if abs(a - 17.48) < 0.1 else 1.4))
        for a in (1.38, 3.4, 5.4, 7.42, 9.43, 11.43, 13.43, 15.43, 17.48, 19.48, 21.5)
    )
    mezz_windows: tuple[Span, ...] = ((1.75, 2.4), (20.3, 20.95))
    end_panels: tuple[Span, ...] = ((0.3, 1.45), (22.85, 24.0))  # louvred equipment panels
    logo: float = 16.45  # rear edge of the red SBB box (lettering behind it)
    first_class: bool = False
    dining: bool = False
    pantograph: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"
    gangway_to_slot: bool = True  # bellows out to the 8/8 slot ends (cars shorter than 25.6 m)
    extras: list = field(default_factory=list)


def end_car(**kw) -> FvSpec:
    """Cab end car, 25.32 m (REFERENCE.md "End car"): nose and cab section 0–7.6 m, door 1 at
    7.2 m (IC200 1st class: luggage loading door), lower deck, door 2 at 18.1 m."""
    base = FvSpec(
        cab=True,
        length_m=25.32,
        doors=((7.2, 8.8), (18.1, 19.8)),
        bogies=(5.2, 22.5),
        lower_windows=((12.6, 14.0), (14.55, 15.35), (15.95, 16.75)),
        upper_windows=(
            (10.5, 11.93),
            (12.5, 13.9),
            (14.5, 15.9),
            (16.5, 17.9),
            (18.55, 19.55),
            (20.52, 21.95),
            (22.52, 23.93),
        ),
        mezz_windows=((21.3, 22.0),),
        end_panels=((23.9, 25.0),),
        logo=17.5,
        gangway_to_slot=False,
    )
    return replace(base, **kw)


def build_fv_car(spec: FvSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.cab
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1

    def at(u: float) -> float:
        """Metres from the front end -> x."""
        return x_front - u * 10

    door_x = [(at(b), at(a)) for a, b in spec.doors]
    deck = deck_floor(door_x)

    def floor_at(X: np.ndarray) -> np.ndarray:
        floor = np.clip(deck(X), LOW_FLOOR, HIGH_FLOOR)
        if spec.cab:  # nose skirt at 0.5 m, cab section down to 0.25 m in front of the bogie
            u = (x_front - X) / 10
            floor = np.where(u < 1.5, 6, np.where(u < 3.9, LOW_FLOOR, floor))
        return floor

    def roof_at(X: np.ndarray) -> np.ndarray:
        if not spec.cab:
            return np.full_like(X, ROOF)
        u = (x_front - X) / 10  # cab section 4.15 m, rising to the double-deck roof at 7.6–8.0 m
        return np.clip(CAB_ROOF + (ROOF - CAB_ROOF) * (u - 7.6) / 0.4, CAB_ROOF, ROOF)

    shell = Shell(
        x_rear,
        x_front,
        SECTION,
        front=NOSE if spec.cab else END,
        rear=END,
        floor_at=floor_at,
        roof_at=roof_at,
    )
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (x_front - X) / 10

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), WHITE)
    mdl.paint(Z < BLACK_TOP, DARK)
    mdl.paint(Z >= DARK_FROM, ROOF_GREY)
    mdl.paint(side_band(mdl, x_rear + 3, at(7.6) if spec.cab else x_front - 3, *GUTTER), BLACK)
    if spec.dining:  # red band round the upper-deck windows (REFERENCE.md, IC200 restaurant car)
        mdl.paint(side_band(mdl, x_rear + 12, x_front - 12, UPPER_WIN[0] - 1, UPPER_WIN[1] + 1), RED)

    if spec.cab:
        _nose(mdl, at, u, dy, Z)

    # --- doors (both sides) -----------------------------------------------------------
    for i, (x0, x1) in enumerate(door_x):
        z0, z1 = DOOR_Z
        c = (x0 + x1) / 2
        if spec.cab and spec.luggage_door and i == 0:  # white loading door, narrow window
            door_outline(mdl, x0, x1, BLACK_TOP + 1, 45, P.MID_GREY)  # 1.47–3.73 m, band runs on below
            mdl.inset(side_band(mdl, c - 2, c + 2, 24, 37), P.GLASS)
            continue
        mdl.paint(side_band(mdl, x0, x1, z0, z1), RED)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_BAND), DOOR_BLUE)
        if spec.first_class:
            mdl.paint(side_band(mdl, x0, x1, *DOOR_YELLOW), FIRST_YELLOW)
        door_outline(mdl, x0, x1, z0, z1, RED_DARK, lintel=0)
        mdl.inset(side_band(mdl, c - 1.5, c + 1.5, 15, 27), P.GLASS)

    # --- windows ---------------------------------------------------------------------
    for a, b in spec.lower_windows:
        rounded_window(mdl, at(b), at(a), *LOWER_WIN)
    for a, b in spec.upper_windows:
        rounded_window(mdl, at(b), at(a), *UPPER_WIN)
    for a, b in spec.mezz_windows:
        rounded_window(mdl, at(b), at(a), *MEZZ_WIN)
    for a, b in spec.end_panels:  # louvred equipment panels over the bogies
        mdl.paint(side_band(mdl, at(b), at(a), BLACK_TOP + 1, 29), HATCH)
        louvres(mdl, at(b) + 1, at(a) - 1, BLACK_TOP + 2, 28, pitch=2, back=P.MID_GREY, slat=P.LIGHT_GREY)

    # SBB logo: red box with the white cross, "SBB CFF FFS" lettering behind it
    lx = at(spec.logo)
    mdl.paint(side_band(mdl, lx, lx + 10, *LOGO_Z), RED)
    mdl.paint(side_band(mdl, lx + 4, lx + 6, LOGO_Z[0] + 1, LOGO_Z[1] - 1), P.OFF_WHITE)
    mdl.paint(side_band(mdl, lx - 24, lx - 1, LOGO_Z[0] + 1, LOGO_Z[1] - 1), DARK)

    # --- ends ------------------------------------------------------------------------------
    for front in (False, True) if not spec.cab else (False,):
        skin = face_mask(mdl, front, depth=2) & (Z >= HIGH_FLOOR)
        mdl.paint(skin & (dy <= 8) & (Z < ROOF - 5), BLACK)  # bellows
        mdl.paint(skin & (dy <= 6) & (Z >= HIGH_FLOOR + 2) & (Z < ROOF - 7), DARK)
        if spec.gangway_to_slot:  # bellows out to the slot end so coupled cars meet
            xe, xs = (x_front, sx - 1) if front else (x_rear, 0)
            lo, hi = sorted((xe, xs))
            mdl.solid(mdl.centred_box(lo, hi + 1, 9, HIGH_FLOOR + 2, ROOF - 6), BLACK)
    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(17, 19),
            top_z=(52, 54),
            spacing=8,
            lamp_half_width=1.5,
            face=True,
        )

    # --- roof -----------------------------------------------------------------------------
    if spec.cab and spec.pantograph:
        pantograph(mdl, at(5.0), CAB_ROOF + 1, raised=spec.mu_role == "rear", facing_front=False, raise_height=12)
        main_switch(mdl, at(6.6), CAB_ROOF + 1)
        roof_cable(mdl, at(7.4), at(4.2), CAB_ROOF + 1)
    elif not spec.cab:
        for a in (3.0, spec.length_m - 4.2):  # air-conditioning units over the intermediate levels
            roof_box(mdl, at(a + 1.2), at(a), 8, ROOF - 1, 2, ROOF_GREY)

    # --- running gear ----------------------------------------------------------------------
    for b in spec.bogies:
        bogie(mdl, at(b), wheelbase=25, wheel_diameter=9, top=HIGH_FLOOR)

    for extra in spec.extras:
        extra(mdl, shell)
    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose(mdl: Model, at, u: np.ndarray, dy: np.ndarray, Z: np.ndarray) -> None:
    """Nose livery from the measured boundaries (REFERENCE.md "Nose"): black wedge between the
    white side and the red mask, red mask over the nose top and along the roof edge to 7 m,
    black lower nose; front face with the grey-blue U outline round the black lower panel,
    the black windscreen panel, red frame and chin, black bumper, dark roof cap."""
    red_low = np.interp(u, *RED_LOW) * ZM
    wedge_low = np.interp(u, *WEDGE_LOW) * ZM
    nose = u < 7.6
    # sides (all of the nose section): black below the red mask in front of 1.5 m, the wedge
    # between the white side and the mask behind it, red above
    mdl.paint(nose & (u < 1.5) & (Z >= 5) & (red_low > Z), BLACK)
    mdl.paint(nose & (u >= 1.5) & (u < 5.9) & (wedge_low <= Z) & (red_low > Z), BLACK)
    mdl.paint(nose & (red_low <= Z) & ((u < 3.8) | (dy >= 12) | (Z < 50)), RED)
    # cab side window: a slightly lighter tinted pane inside the black wedge (no bright glass:
    # on the real train it reads as part of the wedge)
    side = side_skin(mdl)
    cab_win = side & (u > 2.6) & (u < 4.2) & (Z >= 30) & (wedge_low + 3 <= Z) & (red_low - 3 > Z)
    mdl.inset(cab_win, P.GLASS_DARK)
    # front face (central panel only: the tapered flanks keep the side livery)
    face = face_mask(mdl, True, depth=3) & (u < 3.4) & (dy <= 13)
    mdl.paint(face & (Z >= 10), RED)
    mdl.paint(face & (Z < 10), BLACK)  # bumper
    mdl.paint(face & (Z >= 13) & (Z < 36) & (dy >= 11) & (dy < 13), OUTLINE)  # U sides
    mdl.paint(face & (Z >= 13) & (Z < 15) & (dy < 13), OUTLINE)  # U bottom
    mdl.paint(face & (Z >= 15) & (Z < 28) & (dy < 11), BLACK)  # lower panel
    mdl.paint(face & (Z >= 28) & (Z < 51) & (dy < 12.5), BLACK)  # windscreen panel
    mdl.inset(face & (Z >= 29) & (Z < 44) & (dy < 10.5), P.GLASS)
    mdl.paint(face & (Z >= 46) & (Z < 48) & (dy < 7), DISPLAY)  # destination display
    mdl.paint(face & (Z >= 51) & (dy < 12), ROOF_GREY)  # roof cap
    mdl.paint(face & (Z >= 19) & (Z < 21) & (dy < 1.5), P.OFF_WHITE)  # SBB logo
