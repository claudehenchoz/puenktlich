"""Double-deck cars on the shared KISS-proportioned layout: the Siemens Desiro Double Deck
(SBB RABe 514, `style="dtz"`) and the SBB IC2000 coaches (`style="ic2000"`, `coach=True`).

`build_kiss_car(spec, lights)` builds one 8/8 car on the train canvas from a `KissSpec`.
Positions along the car are metres from the car's front end (`u`), as in `parts/dosto.py`, whose
deck layout (`deck_floor`, `deck_windows`, `gangway_ends`) and heights this builder shares.

The Stadler KISS units themselves have their own builders in true proportions: the RABe 511
Regio-Dosto in parts/regio_dosto.py, the RABe 512 IR-Dosto in parts/ir_dosto.py.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import (
    EndShape,
    Shell,
    door_outline,
    face_mask,
    side_band,
)
from puenktlich.voxel.parts.dosto import (
    FLAT_END,
    HIGH_FLOOR,
    ROOF,
    SECTION,
    DostoSpec,
    deck_floor,
    deck_windows,
    gangway_ends,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box
from puenktlich.voxel.parts.running_gear import bogie, buffers
from puenktlich.voxel.variants import Lights

# heights (z, 12.2 per m, roof 4.595 m = z 56) shared by both styles
SKIRT_TOP = 17  # dark CC2 band below 1.37 m (RABe 514)
WAIST = (32, 34)  # thin CC2 line between the decks, 2.65–2.8 m (RABe 514)
MEZZ_WIN = (25, 36)
GREY_FROM = 50  # grey roof sides above 4.1 m

# Siemens Desiro Double Deck (style="dtz"), REFERENCE.md of the RABe 514
DTZ_NOSE = EndShape(rake=10, rake_from=30, corner_radius=10, undercut=2, undercut_height=6, profile="ellipse")
DTZ_LOWER_WIN = (18, 28)
DTZ_UPPER_WIN = (37, 48)
DTZ_DOOR_Z = (6, 31)
# SBB IC2000 coaches (style="ic2000", coach=True), REFERENCE.md of the IC2000
IC_NOSE = EndShape(rake=12, rake_from=28, rake_curve=1.4, corner_radius=8, undercut=2, undercut_height=6)
IC_LOWER_BAND = 21  # anthracite below
IC_WAIST = (31, 35)  # anthracite mid band
IC_LOWER_WIN = (15, 27)
IC_UPPER_WIN = (38, 49)

WHITE = P.OFF_WHITE
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
ACCENT = P.DARK_CC2
BLACK = P.BLACK
DARK = P.DARK
ROOF_GREY = P.ROOF
DOOR_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = P.YELLOW
DISPLAY = P.YELLOW


@dataclass
class KissSpec(DostoSpec):
    """`DostoSpec` layout fields (doors, bogies, windows, mezz_windows) in KISS proportions."""

    length_m: float = 25.0
    doors: tuple[tuple[float, float], ...] = ((5.0, 6.4), (18.6, 20.0))
    bogies: tuple[float, float] = (3.6, 21.4)
    lower_windows: int = 6
    lower_width: float = 1.4
    upper_from: float = 0.6
    upper_pitch: float = 1.4
    upper_width: float = 1.0
    mezz_windows: tuple[tuple[float, float], ...] = ((1.4, 2.6), (22.4, 23.6))
    pantograph_raised: bool = True
    style: Literal["dtz", "ic2000"] = "dtz"
    coach: bool = False  # loco-hauled coach: buffers at both ends, stand-alone tail/cab lamps


def dtz_car(**kw) -> KissSpec:
    """Siemens Desiro Double Deck intermediate car (RABe 514): doors at the lower-deck ends."""
    return replace(KissSpec(style="dtz", lower_windows=6, upper_pitch=1.55, upper_width=1.15), **kw)


def dtz_cab_car(**kw) -> KissSpec:
    """Desiro Double Deck end car (RABe 514, REFERENCE.md "End car"): near-vertical red front,
    motor bogie and pantograph over the cab section, upper deck from 7.6 m."""
    base = dtz_car(
        cab=True,
        doors=((8.6, 10.1), (20.6, 22.1)),
        bogies=(4.4, 22.4),
        lower_windows=5,
        upper_from=7.6,
        mezz_windows=((22.8, 23.8),),
        pantograph_raised=False,
    )
    return replace(base, **kw)


def ic2000_coach(**kw) -> KissSpec:
    """IC2000 double-deck coach (26.8 m, compressed to 25.6 m over buffers, body 24.4 m): doors at
    both lower-deck ends; positions in metres along the modelled body."""
    return replace(
        KissSpec(
            style="ic2000",
            coach=True,
            length_m=25.6,
            doors=((3.4, 5.0), (19.4, 21.0)),
            bogies=(2.1, 22.3),
            lower_windows=6,
            upper_from=0.8,
            upper_pitch=2.0,
            upper_width=1.4,
            mezz_windows=((1.0, 2.2), (22.2, 23.4)),
        ),
        **kw,
    )


def ic2000_bt(**kw) -> KissSpec:
    """IC2000 Bt control car: single-level cab section 0–5.6 m (Re 460-style front), then the
    double-deck body."""
    return ic2000_coach(
        cab=True,
        doors=((5.8, 7.4), (19.4, 21.0)),
        bogies=(3.2, 22.3),
        lower_windows=5,
        upper_from=8.0,
        mezz_windows=((22.2, 23.4),),
        **kw,
    )


def build_kiss_car(spec: KissSpec, lights: Lights) -> Model:
    if spec.coach:  # stand-alone coach / control car (as parts/coach.py)
        turn_round = spec.cab and lights.front == "off" and lights.rear == "red"
        if turn_round:  # control car last in the train: cab outward with red lamps
            lights = Lights(front="red", rear="off", dark=lights.dark)  # type: ignore[arg-type]
    else:
        turn_round = spec.mu_role == "rear" and spec.cab
        lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10 - (12 if spec.coach else 0)  # coaches: length over buffers (0.6 m each)
    x_rear, x_front = sx / 2 - lob / 2 + 1, sx / 2 + lob / 2 - 2

    def at(u: float) -> float:
        """Metres from the front end -> x."""
        return x_front - u * 10

    door_x = [(at(b), at(a)) for a, b in spec.doors]
    deck = deck_floor(door_x)

    def floor_at(X: np.ndarray) -> np.ndarray:
        floor = deck(X)
        if spec.cab:  # skirt under the nose down to ~0.5 m, ending before the motor bogie
            uu = (x_front - X) / 10
            floor = np.where(uu < 2.6, np.clip(6 + (uu - 2.0) * 10, 6, HIGH_FLOOR), floor)
        return floor

    shell = Shell(
        x_rear,
        x_front,
        SECTION,
        front={"dtz": DTZ_NOSE, "ic2000": IC_NOSE}[spec.style] if spec.cab else FLAT_END,
        rear=FLAT_END,
        floor_at=floor_at,
    )
    mdl.solid(shell.mask(mdl), WHITE)
    if spec.style == "dtz":
        _paint_dtz(mdl, spec, shell, at, door_x)
    else:
        _paint_ic2000(mdl, spec, shell, at, door_x)

    # --- ends --------------------------------------------------------------------
    gangway_ends(mdl, spec.cab)
    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z={"dtz": (16, 19), "ic2000": (21, 24)}[spec.style],
            top_z={"dtz": (50, 52), "ic2000": (48, 50)}[spec.style],
            spacing=13,
            lamp_half_width=2,
            face=True,
        )

    if spec.coach:  # tail lamps on the gangway end, buffers and couplers at both ends
        lamp_cluster(
            mdl,
            shell,
            False,
            lights.state("rear"),
            low_z=(18, 21),
            top_z=None,
            spacing=13,
            lamp_half_width=1.5,
            face=True,
        )
        buffers(mdl, x_front, front=True)
        buffers(mdl, x_rear, front=False)

    # --- roof ----------------------------------------------------------------------
    if spec.style == "dtz" and spec.cab:  # one pantograph on each end car, over the cab section
        pantograph(mdl, at(5.2), ROOF, raised=spec.pantograph_raised, facing_front=False, raise_height=10)
        main_switch(mdl, at(6.6), ROOF)
    for a in (8.0, 15.5) if not spec.cab else (14.0,):  # air-conditioning units
        roof_box(mdl, at(a + 1.4), at(a), 9, ROOF - 1, 2, P.MID_GREY)

    # --- running gear ----------------------------------------------------------------
    for i, b in enumerate(spec.bogies):
        motor = spec.cab and i == 0
        bogie(mdl, at(b), wheelbase=25, wheel_diameter=9, top=HIGH_FLOOR, style="loco" if motor else "coach")

    if turn_round:
        mdl.rotate_180()
    return mdl


def _paint_dtz(mdl: Model, spec: KissSpec, shell: Shell, at, door_x) -> None:
    """Desiro Double Deck in the S-Bahn Zürich scheme (RABe 514): white body, dark CC2 skirt and
    waist line as the RABe 511, red (CC1) front with a red arc sweeping onto the sides, red door
    leaves, yellow panels over the 1st-class doors, grey roof."""
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (shell.x_front - X) / 10

    mdl.paint(Z < SKIRT_TOP, ACCENT)
    mdl.paint(Z >= GREY_FROM, ROOF_GREY)
    mdl.paint(side_band(mdl, shell.x_rear + 3, shell.x_front - (60 if spec.cab else 3), *WAIST), ACCENT)

    if spec.cab:
        # red front and side arc: red in front of a curve from 1.7 m at the sill to 3.3 m at the roof
        arc = 1.7 + 1.6 * np.clip((Z - 8) / (ROOF - 8), 0, 1) ** 0.6
        mdl.paint((arc > u) & (Z >= 8) & (Z < GREY_FROM), RED)
        mdl.paint((arc > u) & (arc - 0.5 <= u) & (Z >= GREY_FROM), RED)  # arc over the roof edge
        face = face_mask(mdl, True, depth=3) & (u < 2.0)
        mdl.paint(face & (Z >= 30) & (Z < 48) & (dy <= 16), BLACK)  # windscreen
        mdl.inset(face & (Z >= 32) & (Z < 46) & (dy <= 15), P.GLASS)
        mdl.paint(face & (Z >= 44) & (Z < 46) & (dy <= 8), DISPLAY)
        mdl.paint(face & (Z < 8), BLACK)  # coupler area
        mdl.paint(face & (Z >= GREY_FROM) & (dy <= 12), DARK)  # roof grille
        # cab side window behind the arc
        cab_win = side_band(mdl, at(4.6), at(3.4), 31, 43)
        mdl.paint(cab_win, BLACK)
        mdl.inset(side_band(mdl, at(4.5), at(3.5), 32, 42), P.GLASS)
        door_outline(mdl, at(6.4), at(5.2), 12, 38, P.MID_GREY)  # equipment door

    for x0, x1 in door_x:
        if spec.first_class:  # yellow panel round the upper-deck window over the door
            mdl.paint(side_band(mdl, x0, x1, DTZ_DOOR_Z[1] + 4, GREY_FROM - 1), FIRST_YELLOW)
        mdl.paint(side_band(mdl, x0, x1, *DTZ_DOOR_Z), RED)
        door_outline(mdl, x0, x1, *DTZ_DOOR_Z, RED_DARK, lintel=0)
        c = (x0 + x1) / 2
        for a, b in ((x0 + 2, c - 1), (c + 1, x1 - 2)):
            mdl.inset(side_band(mdl, a, b, 15, 28), P.GLASS)

    deck_windows(mdl, spec, at, door_x, DTZ_LOWER_WIN, DTZ_UPPER_WIN, MEZZ_WIN)

    if spec.cab:  # SBB logo and lettering just above the waist line, behind the first door
        lx = door_x[0][0] - 2
        mdl.paint(side_band(mdl, lx - 9, lx, WAIST[1], WAIST[1] + 3), RED)
        mdl.paint(side_band(mdl, lx - 6, lx - 3, WAIST[1] + 1, WAIST[1] + 2), P.OFF_WHITE)
        mdl.paint(side_band(mdl, lx - 30, lx - 11, WAIST[1] + 1, WAIST[1] + 2), DARK)


def _paint_ic2000(mdl: Model, spec: KissSpec, shell: Shell, at, door_x) -> None:
    """IC2000 (de.wikipedia "Design"): white body (CC2), anthracite lower band and mid band, red
    (CC1) door panels up to the roof with a blue class strip, red marks on the roof edge over the
    doors, grey roof; 1st class with a yellow line over the mid band. Bt: Re 460-style front, red
    lower front, anthracite windscreen band and red band above it running back along the cab."""
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (shell.x_front - X) / 10
    mdl.paint(mdl.d != 0, P.BODY_CC2)
    mdl.paint(Z < IC_LOWER_BAND, DARK)
    mdl.paint(Z >= GREY_FROM, ROOF_GREY)
    band_from = 5.6 if spec.cab else 0.0
    mdl.paint(side_band(mdl, shell.x_rear + 2, at(band_from), *IC_WAIST), DARK)
    if spec.first_class:
        mdl.paint(side_band(mdl, shell.x_rear + 2, at(band_from), IC_WAIST[1], IC_WAIST[1] + 1), FIRST_YELLOW)

    if spec.cab:
        cab = u < 5.6
        mdl.paint(cab & (Z >= 30) & (Z < 42), DARK)  # windscreen band, round the cab section
        mdl.paint(cab & (Z >= 42) & (Z < 47), RED)  # red band above it
        face = face_mask(mdl, True, depth=3) & (u < 3.0) & (dy <= 18)
        mdl.paint(face & (Z >= 6) & (Z < 30), RED)
        mdl.paint(face & (Z < 6), DARK)
        mdl.inset(face & (Z >= 32) & (Z < 41) & (dy <= 14), P.GLASS)
        mdl.paint(face & (Z >= 47), ROOF_GREY)
        mdl.paint(face & (Z >= 49) & (Z < 52) & (dy <= 4) & (X.astype(int) % 2 == 0), DARK)  # grille
        cab_win = side_band(mdl, at(3.6), at(2.4), 31, 41)
        mdl.inset(cab_win, P.GLASS)
        door_outline(mdl, at(5.2), at(4.3), 8, 40, P.MID_GREY)  # cab door

    for x0, x1 in door_x:
        mdl.paint(side_band(mdl, x0, x1, 6, GREY_FROM), RED)
        mdl.paint(side_band(mdl, x1, x1 + 1, 18, 47), DOOR_BLUE)  # class number strip
        mdl.paint(side_band(mdl, x0 + 2, x1 - 2, GREY_FROM, GREY_FROM + 2) & (dy >= 15), RED)  # roof mark
        door_outline(mdl, x0 + 1, x1 - 1, 6, 33, RED_DARK, lintel=0)
        mdl.inset(side_band(mdl, (x0 + x1) / 2 - 1.5, (x0 + x1) / 2 + 1.5, 15, 30), P.GLASS)

    deck_windows(mdl, spec, at, door_x, IC_LOWER_WIN, IC_UPPER_WIN, MEZZ_WIN)

    lx = door_x[0][0] - 4  # SBB logo and lettering between the upper windows and the mid band
    mdl.paint(side_band(mdl, lx - 9, lx, IC_WAIST[1] + 1, IC_WAIST[1] + 4), RED)
    mdl.paint(side_band(mdl, lx - 6, lx - 3, IC_WAIST[1] + 2, IC_WAIST[1] + 3), P.OFF_WHITE)
