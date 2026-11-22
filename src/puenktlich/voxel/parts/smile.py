"""Articulated single-deck high-speed cars (Stadler SMILE / SBB RABe 501 "Giruno").

`build_smile_car(spec, lights)` builds one car on the train canvas from a `SmileSpec`.
Measurements come from photos: models/sbb/giruno/REFERENCE.md. Positions along the car are
given in *real* metres from the car's front end (cab cars: from the nose tip) and scaled to the
modelled length (intermediate cars 17.5 m -> 16.0 m = 5/8, end cars 22.25 m -> 22.4 m = 7/8).

Jakobs bogies: neighbouring cars share a bogie centred on the joint. OpenTTD draws every car
separately, so each car draws the half of the bogie under its own body (one wheelset and half
the frame); the two halves meet at the joint. Cab ends run on an ordinary bogie.

Livery (fixed colours except CC1/CC2): white body CC2; black window band, black skirt, dark
roof; red (CC1) doors, cant-rail stripe, nose mask and swoosh; dining car with a red band.
Multiple-unit lamp roles work like `DostoSpec.mu_role`.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    side_band,
    side_skin,
    windows_in_gaps,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import pantograph, roof_box
from puenktlich.voxel.parts.running_gear import bogie, half_jakobs_bogies
from puenktlich.voxel.variants import Lights

# heights (z, ≈12.1 voxels per metre), REFERENCE.md "Measurements"
SKIRT_FLOOR = 4  # body bottom between the bogies (low-floor car)
BOGIE_FLOOR = 11  # body bottom over the bogies
SKIRT_TOP = 10  # black skirt below, white band above
BAND = (17, 32)  # black window band
WIN = (18, 31)
DOOR_Z = (5, 38)
STRIPE = (44, 46)  # red cant-rail stripe
ROOF = 51

SECTION = CrossSection(floor=BOGIE_FLOOR, roof=ROOF, half_width=19.5, roof_radius=8, tumblehome=1.0, tumble_from=17)
# REFERENCE.md "Nose": bumper tip at ~1.25 m (z 15), quarter ellipse to the roof ~6 m back,
# pointed in plan, the chin tucked under
NOSE = EndShape(rake=60, rake_from=15, corner_radius=13, undercut=6, undercut_height=11, profile="ellipse")
JOINT = EndShape(rake=0, corner_radius=4)

WHITE = P.BODY_CC2
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
BLACK = P.BLACK
DARK = P.DARK
ROOF_DARK = P.ROOF_DARK
CLASS_BLUE = P.ramp(P.BRIGHT_BLUE, 0.4)
FIRST_YELLOW = P.YELLOW
CROSS = P.OFF_WHITE

JAKOBS_WHEELBASE = 2.75  # m
END_WHEELBASE = 2.7
WHEEL = 9  # 920 mm


@dataclass
class SmileSpec:
    cab: bool = False  # cab at the front (high x)
    real_m: float = 17.5
    length_m: float = 16.0  # modelled length (OpenTTD length x 3.2 m)
    doors: tuple[float, ...] = (8.0,)  # door centres, real metres from the front end
    door_width: float = 1.2
    first_class: bool = False
    dining: bool = False
    pantograph: bool = False
    pantograph_raised: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"
    window_pitch: float = 1.75
    window_width: float = 1.1


def end_car(**kw) -> SmileSpec:
    """Cab end car (REFERENCE.md "End car"): nose 0–6.5 m, window band from 8.85 m, one door."""
    return SmileSpec(cab=True, real_m=22.25, length_m=22.4, doors=(16.7,), **kw)


def build_smile_car(spec: SmileSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.cab
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    scale = spec.length_m / spec.real_m

    def at(u: float) -> float:
        """Real metres from the front end -> x."""
        return x_front - u * 10 * scale

    end_bogie = 4.5  # cab bogie centre behind the nose tip

    def floor_at(X: np.ndarray) -> np.ndarray:
        u = (x_front - X) / (10 * scale)
        d_rear = spec.real_m - u
        # how far inside a bogie zone (voxels, < 0 outside): body raised over the bogies,
        # low skirt between them, 3-voxel ramps
        d = (2.3 - d_rear) * 10
        if spec.cab:
            d = np.maximum(d, (2.2 - np.abs(u - end_bogie)) * 10)
            d = np.where(u < 2.3, -3, d)  # aerodynamic skirt under the nose
        else:
            d = np.maximum(d, (2.3 - u) * 10)
        return np.clip(SKIRT_FLOOR + (BOGIE_FLOOR - SKIRT_FLOOR) * (d + 3) / 3, SKIRT_FLOOR, BOGIE_FLOOR)

    shell = Shell(x_rear, x_front, SECTION, front=NOSE if spec.cab else JOINT, rear=JOINT, floor_at=floor_at)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (x_front - X) / (10 * scale)

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), WHITE)
    band_from = 8.85 if spec.cab else 0.0
    band = RED if spec.dining else BLACK
    mdl.paint((Z < SKIRT_TOP) & (u >= (2.3 if spec.cab else 0)), BLACK)
    mdl.paint((BAND[0] <= Z) & (BAND[1] > Z) & (u >= band_from), band)
    mdl.paint((STRIPE[0] <= Z) & (STRIPE[1] > Z), RED)
    mdl.paint(STRIPE[1] <= Z, DARK)
    mdl.paint((Z >= ROOF - 4) & (dy <= SECTION.half_width - 5), ROOF_DARK)

    # --- nose (cab cars) --------------------------------------------------------
    if spec.cab:
        nose = u < 6.6
        low = 14 + 30 * np.clip(u / 6.5, 0, 1)  # red swoosh: from the bumper up to the stripe
        swoosh = nose & (low <= Z) & (np.minimum(low + 7, STRIPE[1]) > Z)
        screen = nose & (np.minimum(low + 7, STRIPE[1]) <= Z)
        mdl.paint(nose & (low <= Z), BLACK)  # windscreen over the raked top; swoosh on the sides only
        # front face (seen head-on): white chin, red mask, black windscreen
        face = face_mask(mdl, True, depth=3) & (u < 5.0)
        mdl.paint(face & (Z < 12), WHITE)
        mdl.paint(face & (Z >= 12) & (Z < 25), RED)
        mdl.paint(face & (Z >= 25), BLACK)
        mdl.inset(face & (Z >= 27) & (Z < 45) & (dy <= 15), P.GLASS)
        mdl.paint(face & (Z >= 6) & (Z < 8) & (dy <= 1), BLACK)  # coupler cover
        mdl.paint(face & (Z >= 21) & (Z < 24) & (dy <= 3) & (Z % 2 == 0), BLACK)  # grille
        mdl.paint(face & (Z >= 17) & (Z < 19) & (dy <= 1), CROSS)  # SBB logo
        # the rounded nose corners belong to the side livery again
        side = side_skin(mdl) & (u >= 1.0) & nose
        mdl.paint(side & (Z >= SKIRT_TOP) & (low > Z), WHITE)
        mdl.paint(side & swoosh, RED)
        mdl.paint(side & screen, BLACK)
        # cab side window under the end of the swoosh, cab door behind it
        mdl.inset(side_band(mdl, at(6.7), at(6.0), 31, 38), P.GLASS)
        door = side_band(mdl, at(8.3), at(7.3), 9, 39)
        mdl.inset(door & ~side_band(mdl, at(8.2), at(7.4), 10, 39), P.LIGHT_GREY)

    # --- doors (both sides): red leaf, window, class panel ------------------------------
    door_x = []
    for c in spec.doors:
        x0, x1 = at(c + spec.door_width / 2), at(c - spec.door_width / 2)
        door_x.append((x0, x1))
        z0, z1 = DOOR_Z
        leaf = side_band(mdl, x0, x1, z0, z1)
        mdl.paint(leaf, RED)
        door_outline(mdl, x0, x1, z0, z1, RED_DARK, sill=0)
        mid = (x0 + x1) / 2
        mdl.inset(side_band(mdl, mid - 2, mid + 2, WIN[0], WIN[1] - 1), P.GLASS)
        mdl.paint(side_band(mdl, x1, x1 + 2, BAND[0], BAND[1]), CLASS_BLUE)  # "1"/"2" panel
        if spec.first_class:
            mdl.paint(side_band(mdl, x0 - 1, x1 + 1, z1, z1 + 1), FIRST_YELLOW)

    # --- windows: evenly in every free stretch of the band ------------------------------
    keep = [(at(spec.real_m - 0.9), at(spec.real_m))]  # rear joint
    keep.append((at(band_from + 0.9), x_front + 1) if spec.cab else (at(0.9), x_front + 1))
    keep += [(x0 - 4, x1 + 4) for x0, x1 in door_x]
    ww, pitch = spec.window_width * 10 * scale, spec.window_pitch * 10 * scale
    windows_in_gaps(mdl, keep, ww, pitch, *WIN, frame=DARK)

    # SBB logo near the rear end of every car: red box with the white cross, then the lettering
    lx = at(spec.real_m - 1.2)
    mdl.paint(side_band(mdl, lx, lx + 10, 11, 16), RED)
    mdl.paint(side_band(mdl, lx + 4, lx + 6, 13, 14), CROSS)
    mdl.paint(side_band(mdl, lx + 12, lx + 32, 13, 14), DARK)
    if spec.dining:  # "Restaurant" lettering above the band
        mdl.paint(side_band(mdl, at(9.0), at(4.0), 34, 36) & (X.astype(int) % 3 != 0), RED)

    # --- joints: black end caps (bellows covers) ---------------------------------------
    for front in (False, True) if not spec.cab else (False,):
        mdl.paint(face_mask(mdl, front, depth=3), BLACK)

    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(19, 22),
            top_z=(43, 45),
            spacing=12,
            lamp_half_width=2,
            face=True,
        )

    # --- roof ----------------------------------------------------------------------
    roof_box(mdl, at(spec.real_m / 2 + 2.0), at(spec.real_m / 2 - 2.0), 8, ROOF - 1, 2, ROOF_DARK)  # air-con
    if spec.pantograph:
        px = at(spec.real_m - 3.5)
        roof_box(mdl, px - 12, px + 12, 7, ROOF - 1, 1, ROOF_DARK)  # pantograph well
        pantograph(mdl, px, ROOF + 1, raised=spec.pantograph_raised, facing_front=False)

    # --- running gear --------------------------------------------------------------
    jb = JAKOBS_WHEELBASE * 10 * scale
    half_jakobs_bogies(mdl, x_rear, x_front, (True, not spec.cab), jb, WHEEL, BOGIE_FLOOR)
    if spec.cab:
        bogie(mdl, at(end_bogie), wheelbase=END_WHEELBASE * 10, wheel_diameter=WHEEL, top=BOGIE_FLOOR)

    if turn_round:
        mdl.rotate_180()
    return mdl
