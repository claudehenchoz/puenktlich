"""Double-deck multiple-unit cars (SBB FV-Dosto / Twindexx Swiss Express family).

`build_dosto_car(spec, lights)` builds one 8/8 car on the train canvas from a `DostoSpec`.
Measurements come from photos: models/sbb/fv_dosto/REFERENCE.md. Positions along the car are
given in metres from the car's front end (`u`); the builder converts them to voxels.

Structure of every car:
    intermediate level over each bogie: body bottom high (HIGH_FLOOR), small window
    lower deck between the bogies: body down to LOW_FLOOR, one door at each end
    upper deck along the whole car, roof at ROOF (cab section lower: CAB_ROOF)
Livery: white body CC2, red doors and nose CC1, black lower band, dark grey upper band
and roof (fixed colours).

Multiple-unit lamp roles (`mu_role`) work like `CoachSpec.mu_role`: the first car shows the
unit's head lamps at its cab, the last car is built cab-first and turned round, so its cab
shows the unit's rear lamps.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, face_mask, side_band
from puenktlich.voxel.parts.lights import lamp_cluster
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

# heights (z), REFERENCE.md "Measurements"
LOW_FLOOR = 3
HIGH_FLOOR = 12
BLACK_TOP = 17
LOWER_WIN = (14, 26)
DOOR_Z = (6, 38)
DOOR_BAND = 34  # blue band from here to the door top
GUTTER = 38
UPPER_WIN = (42, 51)
DARK_FROM = 48
ROOF = 56
CAB_ROOF = 53
MEZZ_WIN = (27, 35)

SECTION = CrossSection(floor=HIGH_FLOOR, roof=ROOF, half_width=19.5, roof_radius=9, tumblehome=0.5, tumble_from=20)
# REFERENCE.md: tip at ~1.3 m (z 15), quarter-ellipse up to the roof 3.7 m back, skirt tucked under
NOSE = EndShape(rake=37, rake_from=15, corner_radius=9, undercut=5, undercut_height=10, profile="ellipse")
FLAT_END = EndShape(rake=0, corner_radius=2)

WHITE = P.ramp(P.CC2, 0.75)
RED = P.ramp(P.CC1, 0.6)
RED_DARK = P.ramp(P.CC1, 0.3)
BLACK = P.BLACK
DARK = P.ramp(P.GREY, 0.18)
ROOF_GREY = P.ramp(P.GREY, 0.3)
DOOR_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = 66
DISPLAY = 66
HATCH = P.ramp(P.GREY, 0.72)


@dataclass
class DostoSpec:
    cab: bool = False  # cab at the front (high x)
    first_class: bool = False
    dining: bool = False
    pantograph: bool = False  # on the cab roof
    mu_role: Literal["front", "middle", "rear"] = "middle"
    length_m: float = 25.6
    # metres from the front end (cab cars: from the nose tip)
    doors: tuple[tuple[float, float], ...] = ((3.6, 5.4), (20.2, 22.0))
    bogies: tuple[float, float] = (2.1, 23.5)
    lower_windows: int = 6
    upper_from: float = 0.8  # first upper-deck window
    upper_pitch: float = 2.0
    upper_width: float = 1.38
    lower_width: float = 1.47
    mezz_windows: tuple[tuple[float, float], ...] = ((1.0, 2.2), (23.4, 24.6))
    extras: list = field(default_factory=list)


def end_car(**kw) -> DostoSpec:
    """Cab end car (REFERENCE.md "End car"): nose 0–3.8 m, door 1 at 9.0 m."""
    base = DostoSpec(
        cab=True,
        doors=((8.8, 10.5), (20.2, 22.0)),
        bogies=(4.6, 23.5),
        lower_windows=4,
        upper_from=9.2,
        mezz_windows=((23.4, 24.6),),
    )
    return replace(base, **kw)


def side_skin(mdl: Model) -> np.ndarray:
    """Filled voxels with an empty neighbour outwards in y (the visible body sides)."""
    occ = mdl.d != 0
    out = np.zeros_like(occ)
    cy = int(mdl.cy)
    out[:, : cy + 1] = occ[:, : cy + 1] & ~np.pad(occ, ((0, 0), (1, 0), (0, 0)))[:, : cy + 1]
    out[:, cy + 1 :] = occ[:, cy + 1 :] & ~np.pad(occ, ((0, 0), (0, 1), (0, 0)))[:, cy + 2 :]
    return out


def _window(mdl: Model, x0: float, x1: float, z0: float, z1: float, frame: int = BLACK) -> None:
    """Rounded-rectangle window on both sides: black frame, glass inset, corners clipped."""
    X, _, Z = mdl.coords()
    outer = side_band(mdl, x0, x1, z0, z1)
    corner = ((x0 + 1 > X) | (x1 - 1 <= X)) & ((z0 + 1 > Z) | (z1 - 1 <= Z))
    mdl.paint(outer & ~corner, frame)
    mdl.inset(side_band(mdl, x0 + 1, x1 - 1, z0 + 1, z1 - 1), P.GLASS)


def build_dosto_car(spec: DostoSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.cab
    if spec.mu_role == "rear":  # cab built at the front, carrying the unit's rear lamps
        lights = Lights(front=lights.rear, rear="off", dark=lights.dark)  # type: ignore[arg-type]
    elif spec.mu_role == "front":
        lights = Lights(front=lights.front, rear="off", dark=lights.dark)
    else:
        lights = Lights(front="off", rear="off", dark=lights.dark)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2 + 1, sx / 2 + lob / 2 - 2

    def at(u: float) -> float:
        """Metres from the front end -> x."""
        return x_front - u * 10

    door_x = [(at(b), at(a)) for a, b in spec.doors]
    low0, low1 = min(x for x, _ in door_x), max(x for _, x in door_x)

    def floor_at(X: np.ndarray) -> np.ndarray:
        # lower deck between the doors (inclusive), 3-voxel ramp up to the intermediate level
        d = np.maximum(low0 - X, X - low1)
        floor = np.clip(LOW_FLOOR + (HIGH_FLOOR - LOW_FLOOR) * d / 3, LOW_FLOOR, HIGH_FLOOR)
        if spec.cab:  # aerodynamic skirt under the nose, down to ~0.5 m, ending before the bogie
            uu = (x_front - X) / 10
            floor = np.where(uu < 2.6, np.clip(6 + (uu - 1.8) * 8, 6, HIGH_FLOOR), floor)
        return floor

    def roof_at(X: np.ndarray) -> np.ndarray:
        if not spec.cab:
            return np.full_like(X, ROOF)
        u = (x_front - X) / 10  # cab section lower, rising to the double-deck roof at 8.1–8.5 m
        return np.clip(CAB_ROOF + (ROOF - CAB_ROOF) * (u - 8.1) / 0.4, CAB_ROOF, ROOF)

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
    mdl.paint(Z < BLACK_TOP, BLACK)
    mdl.paint(Z >= DARK_FROM, DARK)
    mdl.paint((Z >= ROOF - 3) & (dy <= SECTION.half_width - 5), ROOF_GREY)
    mdl.paint(side_band(mdl, x_rear + 4, x_front - 4, GUTTER, GUTTER + 1) & (Z >= GUTTER), P.LIGHT_GREY)

    if spec.dining:  # red band around the upper-deck windows (REFERENCE.md, ref15)
        mdl.paint(side_band(mdl, x_rear + 12, x_front - 12, UPPER_WIN[0] - 1, UPPER_WIN[1] + 1), RED)

    # --- nose (cab cars) ------------------------------------------------------
    if spec.cab:
        nose = u < 8.1
        red_b = 24 + 25 * np.clip(u / 4.0, 0, 1)  # red above: rises from the tip to the roof edge
        white_b = 17.7 + 31.3 * np.clip((u - 0.95) / 5.45, 0, 1)  # black wedge above this line
        wedge = nose & (Z >= BLACK_TOP) & (red_b > Z) & (white_b <= Z)
        reds = nose & (red_b <= Z) & (Z >= BLACK_TOP)
        mdl.paint(wedge, BLACK)
        mdl.paint(reds, RED)
        mdl.paint((u < 5.0) & (Z >= CAB_ROOF - 1) & (dy <= 7), BLACK)  # roof cap
        # front face (seen head-on): skirt, apron, white U-band, black panel, windscreen
        face = face_mask(mdl, True, depth=3) & (u < 4.5)
        mdl.paint(face & (Z < 7), BLACK)
        mdl.paint(face & (Z >= 7) & (Z < 47), RED)
        mdl.paint(face & (Z >= 16) & (Z < 31) & (dy <= 15), WHITE)
        mdl.paint(face & (Z >= 19) & (Z < 31) & (dy <= 12), BLACK)
        mdl.paint(face & (Z >= 31) & (Z < 47) & (dy <= 16), BLACK)
        mdl.inset(face & (Z >= 33) & (Z < 44) & (dy <= 14), P.GLASS)
        mdl.paint(face & (Z >= 44) & (Z < 46) & (dy <= 9), DISPLAY)  # destination display
        mdl.paint(face & (Z >= 47) & (dy <= 9), BLACK)
        # the rounded nose corners belong to the side livery again (black wedge, red, white)
        side = side_skin(mdl) & (u >= 0.9)
        mdl.paint(side & nose & (Z >= BLACK_TOP), WHITE)
        mdl.paint(side & wedge, BLACK)
        mdl.paint(side & reds, RED)
        # cab side window inside the black wedge (trapezoid: front edge raked)
        cab_win = side_band(mdl, at(3.4), at(2.0), 31, 42) & (X - at(2.0) < -(Z - 31) * 0.6)
        mdl.inset(cab_win, P.GLASS)
        # display window and equipment hatch behind the cab
        mdl.paint(side_band(mdl, at(5.7), at(4.8), 23, 31), HATCH)
        mdl.inset(side_band(mdl, at(5.6), at(4.9), 24, 30), BLACK)
        mdl.paint(side_band(mdl, at(6.9), at(5.9), 18, 38), HATCH)
        grille = side_band(mdl, at(6.8), at(6.0), 20, 36) & (Z.astype(int) % 2 == 0)
        mdl.inset(grille, P.MID_GREY)

    # --- doors (both sides), REFERENCE.md: red, blue top band, narrow window ------------
    for x0, x1 in door_x:
        z0, z1 = DOOR_Z
        leaf = side_band(mdl, x0, x1, z0, z1)
        mdl.paint(leaf, RED)
        mdl.paint(side_band(mdl, x0, x1, DOOR_BAND, z1), DOOR_BLUE)
        seam = leaf & ~side_band(mdl, x0 + 1, x1 - 1, z0 + 1, z1)
        mdl.inset(seam, RED_DARK)
        c = (x0 + x1) / 2
        mdl.inset(side_band(mdl, c - 1.5, c + 1.5, 17, 31), P.GLASS)
        if spec.first_class:
            mdl.paint(side_band(mdl, x0, x1, z1, z1 + 2), FIRST_YELLOW)

    # --- windows ---------------------------------------------------------------
    # lower deck: evenly between the doors
    gap0, gap1 = door_x[-1][1] + 5, door_x[0][0] - 5
    lw = spec.lower_width * 10
    n = spec.lower_windows
    pitch = (gap1 - gap0) / n
    for i in range(n):
        a = gap0 + i * pitch + (pitch - lw) / 2
        _window(mdl, a, a + lw, *LOWER_WIN)
    # upper deck: from upper_from to the rear end
    uw = spec.upper_width * 10
    k = 0
    while True:
        a_u = spec.upper_from + k * spec.upper_pitch
        if a_u + spec.upper_width > spec.length_m - 0.7:
            break
        _window(mdl, at(a_u + spec.upper_width), at(a_u + spec.upper_width) + uw, *UPPER_WIN)
        k += 1
    for a, b in spec.mezz_windows:
        _window(mdl, at(b), at(a), *MEZZ_WIN)

    # SBB logo: red box with the white cross, upper side next to the first door
    lx = door_x[0][0] - 16
    mdl.paint(side_band(mdl, lx, lx + 11, 33, 37), RED)
    mdl.paint(side_band(mdl, lx + 4, lx + 7, 34, 36), P.ramp(P.GREY, 0.93))  # not P.WHITE: lamp colour
    mdl.paint(side_band(mdl, lx - 28, lx - 2, 34, 36), DARK)  # "SBB CFF FFS"

    # --- ends --------------------------------------------------------------------
    # gangway end(s): dark end face with the bellows frame
    for front in (False, True) if not spec.cab else (False,):
        skin = face_mask(mdl, front, depth=2) & (Z >= HIGH_FLOOR)
        mdl.paint(skin & (dy <= 8) & (Z < ROOF - 4), BLACK)  # bellows
        mdl.paint(skin & (dy <= 6) & (Z >= HIGH_FLOOR + 2) & (Z < ROOF - 6), DARK)
    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(26, 29),
            top_z=(48, 50),
            spacing=11,
            lamp_half_width=1.5,
            face=True,
        )

    # --- roof ----------------------------------------------------------------------
    if spec.cab and spec.pantograph:
        pantograph(mdl, at(5.0), CAB_ROOF + 1, raised=spec.mu_role == "rear", facing_front=False, raise_height=12)
        main_switch(mdl, at(6.8), CAB_ROOF + 1)
        roof_cable(mdl, at(7.6), at(4.0), CAB_ROOF + 1)
    else:
        for a in (3.0, 22.6):  # air-conditioning units over the intermediate levels
            roof_box(mdl, at(a + 1.2), at(a), 9, ROOF - 1, 2, ROOF_GREY)

    # --- running gear ----------------------------------------------------------------
    for b in spec.bogies:
        bogie(mdl, at(b), wheelbase=25, wheel_diameter=9, top=HIGH_FLOOR)

    for extra in spec.extras:
        extra(mdl, shell)
    if turn_round:
        mdl.rotate_180()
    return mdl
