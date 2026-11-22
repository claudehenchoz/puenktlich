"""Double-deck multiple-unit cars of the Stadler KISS family (SBB RABe 511 Regio-Dosto).

`build_kiss_car(spec, lights)` builds one 8/8 car on the train canvas from a `KissSpec`.
Measurements and photos: models/sbb/rabe511/REFERENCE.md. Positions along the car are metres
from the car's front end (`u`), as in `parts/dosto.py`, whose deck layout (`deck_floor`,
`deck_windows`, `gangway_ends`) and heights this builder shares.

Differences from the FV-Dosto (parts/dosto.py):
    blunt KISS nose: red U around the windscreen, dark roof cap, black "eyes" with the lamps,
    red stripe sweeping from the nose corner up to the roof line
    full-height cab car (no lowered cab roof); the pantographs stand in a roof well over the
    intermediate level of an intermediate car (`pantograph=True`)
    tall upper-deck windows at a short pitch; doors in a red panel that reaches up to the roof,
    with the upper-deck window in it and a blue band above the door leaves
Livery: white body (fixed), red nose and door panels CC1, skirt band and thin waist line
CC2 dark shade (S-Bahn Zürich: dark blue; RegioExpress / InterRegio: anthracite grey).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import (
    EndShape,
    Shell,
    door_outline,
    face_mask,
    louvres,
    rounded_window,
    side_band,
    side_skin,
)
from puenktlich.voxel.parts.dosto import (
    FLAT_END,
    HATCH,
    HIGH_FLOOR,
    ROOF,
    SECTION,
    DostoSpec,
    deck_floor,
    deck_windows,
    gangway_ends,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

# heights (z), REFERENCE.md "Measurements" (12.2 z per m, roof 4.595 m = z 56)
SKIRT_TOP = 17  # dark CC2 band below 1.37 m
LOWER_WIN = (17, 30)
WAIST = (32, 34)  # thin CC2 line between the decks, 2.65–2.8 m
UPPER_WIN = (37, 50)
MEZZ_WIN = (25, 36)
GREY_FROM = 50  # grey roof sides above 4.1 m
DOOR_Z = (6, 33)  # door leaves
DOOR_BAND = (33, 36)  # blue band above the leaves ("2" / "1" class numbers)
PANEL_TOP = 51  # red door panel up to the upper-deck window top
WELL_ROOF = 50  # roof well under the pantograph

# REFERENCE.md: windscreen rake ~1.8 m, near-vertical lower front, rounded corners
NOSE = EndShape(rake=18, rake_from=28, corner_radius=10, undercut=3, undercut_height=8, profile="ellipse")

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
    turned: bool = False  # built front-first, then turned round (pantograph well at the rear)


def cab_car(**kw) -> KissSpec:
    """Cab end car (REFERENCE.md "Cab car"): nose 0–2.2 m, equipment bay 3.5–8.2 m over the
    motor bogie, double-deck section between the doors, intermediate level at the rear."""
    base = KissSpec(
        cab=True,
        doors=((8.4, 9.8), (19.6, 21.0)),
        bogies=(4.4, 22.2),
        lower_windows=5,
        upper_from=8.6,
        mezz_windows=((22.4, 23.6),),
    )
    return replace(base, **kw)


def build_kiss_car(spec: KissSpec, lights: Lights) -> Model:
    turn_round = (spec.mu_role == "rear" and spec.cab) or spec.turned
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
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

    def roof_at(X: np.ndarray) -> np.ndarray:
        if not spec.pantograph:
            return np.full_like(X, ROOF)
        u = (x_front - X) / 10  # roof well over the front intermediate level, 0.4–4.2 m
        well = (u > 0.4) & (u < 4.2)
        return np.where(well, WELL_ROOF, ROOF)

    shell = Shell(
        x_rear,
        x_front,
        SECTION,
        front=NOSE if spec.cab else FLAT_END,
        rear=FLAT_END,
        floor_at=floor_at,
        roof_at=roof_at,
    )
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (x_front - X) / 10

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), WHITE)
    mdl.paint(Z < SKIRT_TOP, ACCENT)
    mdl.paint(Z >= GREY_FROM, ROOF_GREY)
    side = side_skin(mdl)
    mdl.paint(side_band(mdl, x_rear + 3, x_front - (40 if spec.cab else 3), *WAIST), ACCENT)

    # --- nose (cab cars) ------------------------------------------------------
    if spec.cab:
        nose = u < 4.0
        # red stripe on the side: from the nose corner up and back to the roof line
        lo = 22 + 30 * np.clip(u / 3.4, 0, 1)  # lower edge reaches the roof at 3.4 m
        hi = 40 + 16 * np.clip((u - 0.2) / 1.8, 0, 1)  # upper edge reaches it at 2.0 m
        stripe = nose & (lo <= Z) & (hi > Z)
        mdl.paint(stripe, RED)
        mdl.paint(nose & (hi <= Z) & (Z >= SKIRT_TOP), BLACK)  # windscreen wrap / roof cap
        mdl.paint((u < 2.6) & (Z >= ROOF - 6) & (dy <= 14), DARK)  # roof cap
        # cab side window: black swoosh under the red stripe
        cab_win = side & (u > 0.6) & (u < 3.3) & (Z >= 27) & (Z < 41) & (lo - 1 > Z)
        mdl.paint(cab_win, BLACK)
        mdl.inset(side_band(mdl, at(3.1), at(1.6), 29, 39) & (lo - 2 > Z), P.GLASS)
        # front face (seen head-on)
        face = face_mask(mdl, True, depth=3) & (u < 3.0)
        mdl.paint(face & (Z >= SKIRT_TOP), RED)
        mdl.paint(face & (Z >= SKIRT_TOP) & (Z < 23) & (dy > 9), WHITE)  # white lower corners
        mdl.paint(face & (Z >= 29) & (Z < 49) & (dy <= 15), BLACK)  # windscreen frame
        mdl.inset(face & (Z >= 31) & (Z < 45) & (dy <= 13), P.GLASS)
        mdl.paint(face & (Z >= 45) & (Z < 48) & (dy <= 8), DISPLAY)  # destination display
        mdl.paint(face & (Z >= 49) & (dy <= 13), DARK)  # roof cap
        mdl.paint(face & (Z < 8), BLACK)  # coupler recess / skirt
        # equipment bay behind the cab: louvred hatch, small windows, roof cover
        mdl.paint(side_band(mdl, at(5.4), at(4.2), 12, 40), HATCH)
        louvres(mdl, at(5.3), at(4.3), 14, 38, pitch=2, back=P.MID_GREY, slat=P.LIGHT_GREY)
        rounded_window(mdl, at(7.3), at(6.5), 27, 37)
        roof_box(mdl, at(8.0), at(3.2), 14, ROOF - 1, 2, P.MID_GREY)

    # --- door panels (both sides): red from the sill to the upper-deck window top ---------
    for x0, x1 in door_x:
        mdl.paint(side_band(mdl, x0, x1, DOOR_Z[0], PANEL_TOP), RED)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_BAND), DOOR_BLUE)
        if spec.first_class:
            mdl.paint(side_band(mdl, x0, x1, DOOR_BAND[1], DOOR_BAND[1] + 1), FIRST_YELLOW)
        door_outline(mdl, x0 + 1, x1 - 1, *DOOR_Z, RED_DARK, lintel=0)
        c = (x0 + x1) / 2
        for a, b in ((x0 + 2, c - 1), (c + 1, x1 - 2)):  # two leaves, a window in each
            mdl.inset(side_band(mdl, a, b, 15, 30), P.GLASS)

    # --- windows ---------------------------------------------------------------
    deck_windows(mdl, spec, at, door_x, LOWER_WIN, UPPER_WIN, MEZZ_WIN)

    if spec.cab:  # SBB logo (red box, white cross) and "SBB CFF FFS" over the equipment bay
        lx = at(6.2)
        mdl.paint(side_band(mdl, lx, lx + 9, 40, 44), RED)
        mdl.paint(side_band(mdl, lx + 3, lx + 6, 41, 43), P.OFF_WHITE)
        mdl.paint(side_band(mdl, lx - 20, lx - 2, 41, 43), DARK)

    # --- ends --------------------------------------------------------------------
    gangway_ends(mdl, spec.cab)
    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(20, 24),
            top_z=(50, 52),
            spacing=13,
            lamp_half_width=2,
            face=True,
        )

    # --- roof ----------------------------------------------------------------------
    if spec.pantograph:
        pantograph(mdl, at(2.4), WELL_ROOF + 1, raised=spec.pantograph_raised, facing_front=False, raise_height=14)
        main_switch(mdl, at(3.6), WELL_ROOF + 1)
        roof_cable(mdl, at(4.0), at(1.0), WELL_ROOF + 1)
    for a in (8.0, 15.5) if not spec.cab else (14.0,):  # air-conditioning units
        roof_box(mdl, at(a + 1.4), at(a), 9, ROOF - 1, 2, P.MID_GREY)

    # --- running gear ----------------------------------------------------------------
    for i, b in enumerate(spec.bogies):
        motor = spec.cab and i == 0
        bogie(mdl, at(b), wheelbase=25, wheel_diameter=9, top=HIGH_FLOOR, style="loco" if motor else "coach")

    if turn_round:
        mdl.rotate_180()
    return mdl
