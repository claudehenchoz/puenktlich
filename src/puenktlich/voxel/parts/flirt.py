"""Articulated single-deck regional cars (Stadler FLIRT, SBB RABe 523).

`build_flirt_car(spec, lights)` builds one car on the train canvas from a `FlirtSpec`.
Measurements and photos: models/sbb/rabe523/REFERENCE.md. Positions along the car are *real*
metres from the car's front end (cab cars: from the nose tip), scaled to the modelled length
like `parts/smile.py` (Giruno), whose cross-section and low-floor heights this builder shares.
Cars run on Jakobs bogies (`running_gear.half_jakobs_bogies`); the cab ends on a motor bogie.

generation 1 (RABe 523 0xx): rounded nose, black windscreen in a red U; white body CC2,
    black skirt, broad red band along the roof edge, dark roof.
generation 3 (RABe 523 1xx, "Mouette" 5xx): raked nose with Stadler's black shield in a red
    V frame (`parts/stadler.py`, shared with the KISS 2), white body CC2 down to the sill,
    thin red line under the dark roof.
Both: red sliding doors (CC1) with a blue class band, large windows in dark frames, the 1st-class
section with a yellow line above the windows.
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
    side_skin,
    windows_in_gaps,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import pantograph, roof_box
from puenktlich.voxel.parts.running_gear import bogie, half_jakobs_bogies
from puenktlich.voxel.parts.smile import BOGIE_FLOOR, JOINT, ROOF, SECTION, SKIRT_FLOOR
from puenktlich.voxel.parts.stadler import ShieldNose, shield_nose
from puenktlich.voxel.variants import Lights

# heights (z, ≈12.1 voxels per metre), REFERENCE.md "Measurements"
SKIRT_TOP = 11  # generation 1: black skirt below 0.9 m
WIN = (16, 31)
DOOR_Z = (5, 33)
DOOR_BAND = (33, 35)  # blue class band above the leaves
ROOF_BAND = (43, 48)  # generation 1: broad red band along the roof edge
RED_LINE = (45, 47)  # generation 3: thin red line under the roof edge
ROOF_FROM = 48  # dark roof above
LOGO_Z = (12, 15)

NOSE_1 = EndShape(rake=24, rake_from=22, corner_radius=12, undercut=4, undercut_height=10, profile="ellipse")
NOSE_3 = EndShape(rake=32, rake_from=24, corner_radius=12, undercut=3, undercut_height=8, profile="ellipse")
SHIELD_3 = ShieldNose(
    red_line_z=RED_LINE[0],
    roof_from=ROOF_FROM,
    shield_top=45,
    rise=2.6,
    length=4.0,
    line_from_z=27,
    cab_window=(2.2, 3.8, 25, 37),
)

WHITE = P.BODY_CC2
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
BLACK = P.BLACK
DARK = P.DARK
ROOF_DARK = P.ROOF_DARK
CLASS_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = P.YELLOW
DISPLAY = P.YELLOW

JAKOBS_WHEELBASE = 2.7  # m
END_WHEELBASE = 2.7
WHEEL = 9  # 860–920 mm
CAB_BOGIE = 3.6  # motor bogie centre behind the nose tip (m)
CAB_END = 4.2  # windows start behind the cab


@dataclass
class FlirtSpec:
    cab: bool = False  # cab at the front (high x)
    generation: Literal[1, 3] = 1
    real_m: float = 17.6
    length_m: float = 16.0  # modelled length (OpenTTD length x 3.2 m)
    doors: tuple[float, ...] = (4.8, 12.8)  # door centres, real metres from the front end
    door_width: float = 1.3
    first_class: tuple[float, float] | None = None  # 1st-class section (real m), yellow line
    pantograph: bool = False  # on the rear roof (end cars)
    pantograph_raised: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"
    window_pitch: float = 2.0
    window_width: float = 1.7


def end_car(**kw) -> FlirtSpec:
    """Cab end car (REFERENCE.md "End car"): motor bogie under the cab, two doors in the rear
    half, pantograph on the rear roof."""
    return replace(FlirtSpec(cab=True, real_m=19.4, length_m=19.2, doors=(8.9, 14.0), pantograph=True), **kw)


def build_flirt_car(spec: FlirtSpec, lights: Lights) -> Model:
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

    def floor_at(X: np.ndarray) -> np.ndarray:
        # body raised over the bogies (Jakobs at the joints, motor bogie under the cab), low
        # floor between them, 3-voxel ramps
        u = (x_front - X) / (10 * scale)
        d = (1.8 - (spec.real_m - u)) * 10
        if spec.cab:
            d = np.maximum(d, (2.0 - np.abs(u - CAB_BOGIE)) * 10)
            d = np.where(u < 1.6, -3, d)  # skirt under the nose
        else:
            d = np.maximum(d, (1.8 - u) * 10)
        return np.clip(SKIRT_FLOOR + (BOGIE_FLOOR - SKIRT_FLOOR) * (d + 3) / 3, SKIRT_FLOOR, BOGIE_FLOOR)

    nose = NOSE_1 if spec.generation == 1 else NOSE_3
    shell = Shell(x_rear, x_front, SECTION, front=nose if spec.cab else JOINT, rear=JOINT, floor_at=floor_at)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (x_front - X) / (10 * scale)
    side = None

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), WHITE)
    mdl.paint(Z >= ROOF_FROM, ROOF_DARK)
    if spec.generation == 1:
        mdl.paint((Z < SKIRT_TOP) & (u >= (1.6 if spec.cab else 0)), BLACK)
        mdl.paint((ROOF_BAND[0] <= Z) & (ROOF_BAND[1] > Z), RED)
    else:
        side = side_skin(mdl)
        mdl.paint(side & (u >= (SHIELD_3.length if spec.cab else 0)) & (RED_LINE[0] <= Z) & (RED_LINE[1] > Z), RED)

    # --- nose (cab cars) --------------------------------------------------------
    if spec.cab:
        if spec.generation == 1:
            _nose_gen1(mdl, at, u, dy)
        else:
            shield_nose(mdl, shell, lambda m: at(m / scale), SHIELD_3)

    # --- doors (both sides): red leaves, blue class band, windows ------------------------
    door_x = []
    for c in spec.doors:
        x0, x1 = at(c + spec.door_width / 2), at(c - spec.door_width / 2)
        door_x.append((x0, x1))
        mdl.paint(side_band(mdl, x0, x1, *DOOR_Z), RED)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_BAND), CLASS_BLUE)
        door_outline(mdl, x0, x1, *DOOR_Z, RED_DARK, sill=0)
        mid = (x0 + x1) / 2
        for a, b in ((x0 + 1.5, mid - 0.5), (mid + 0.5, x1 - 1.5)):
            mdl.inset(side_band(mdl, a, b, WIN[0], WIN[1] - 2), P.GLASS)

    # --- windows: evenly in every free stretch --------------------------------------------
    keep = [(at(spec.real_m - 0.6), at(spec.real_m))]  # rear joint
    keep.append((at(CAB_END), x_front + 1) if spec.cab else (at(0.6), x_front + 1))
    keep += [(x0 - 3, x1 + 3) for x0, x1 in door_x]
    ww, pitch = spec.window_width * 10 * scale, spec.window_pitch * 10 * scale
    windows_in_gaps(mdl, keep, ww, pitch, *WIN, frame=DARK)
    if spec.first_class is not None:
        a, b = spec.first_class
        mdl.paint(side_band(mdl, at(b), at(a), WIN[1], WIN[1] + 1), FIRST_YELLOW)

    # SBB logo and lettering under the windows near the rear end of every car
    lx = at(spec.real_m - 1.0)
    mdl.paint(side_band(mdl, lx, lx + 8, *LOGO_Z), RED)
    mdl.paint(side_band(mdl, lx + 3, lx + 5, LOGO_Z[0] + 1, LOGO_Z[1] - 1), P.OFF_WHITE)
    mdl.paint(side_band(mdl, lx + 10, lx + 26, LOGO_Z[0] + 1, LOGO_Z[1] - 1), DARK)

    # --- joints: dark bellows covers ---------------------------------------------------------
    for front in (False, True) if not spec.cab else (False,):
        mdl.paint(face_mask(mdl, front, depth=3) & (Z < ROOF_FROM), BLACK)

    if spec.cab:
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(19, 22),
            top_z=(46, 48) if spec.generation == 1 else (47, 49),
            spacing=12,
            lamp_half_width=2,
            face=True,
        )

    # --- roof ----------------------------------------------------------------------------
    if spec.cab:  # traction equipment over the cab half, behind the cab
        roof_box(mdl, at(11.0), at(4.5), 12, ROOF - 1, 2, P.MID_GREY)
    else:  # air conditioning
        roof_box(mdl, at(spec.real_m / 2 + 1.8), at(spec.real_m / 2 - 1.8), 9, ROOF - 1, 2, P.MID_GREY)
    if spec.pantograph:
        px = at(spec.real_m - 3.2)
        pantograph(mdl, px, ROOF, raised=spec.pantograph_raised, facing_front=False)

    # --- running gear ----------------------------------------------------------------------
    jb = JAKOBS_WHEELBASE * 10 * scale
    half_jakobs_bogies(mdl, x_rear, x_front, (True, not spec.cab), jb, WHEEL, BOGIE_FLOOR)
    if spec.cab:  # motor bogie under the cab
        bogie(mdl, at(CAB_BOGIE), wheelbase=END_WHEELBASE * 10, wheel_diameter=WHEEL, top=BOGIE_FLOOR)

    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose_gen1(mdl: Model, at, u: np.ndarray, dy: np.ndarray) -> None:
    """FLIRT 1 nose: black windscreen in a red U that runs on into the roof-edge band, white
    lower front with the lamps, black skirt; black cab side window behind the windscreen."""
    X, _, Z = mdl.coords()
    nose = u < 4.0
    # sides: red frame line rising from the nose corner into the roof band, windscreen above
    edge = 24 + (ROOF_BAND[0] - 24) * np.clip((u - 0.6) / 2.8, 0, 1)
    mdl.paint(nose & (edge <= Z) & (edge + 4 > Z) & (ROOF_FROM > Z), RED)
    mdl.paint(nose & (edge + 4 <= Z) & (ROOF_FROM > Z), BLACK)
    mdl.paint((u < 2.4) & (Z >= ROOF_FROM - 1) & (dy <= 12), DARK)  # roof cap
    cab_win = side_band(mdl, at(3.6), at(1.4), 25, 37) & (X - at(1.4) < -(Z - 25) * 0.8) & (edge > Z)
    mdl.paint(cab_win, BLACK)
    mdl.inset(cab_win & side_band(mdl, at(3.4), at(1.7), 26, 36), P.GLASS)
    # front face: red U around the black windscreen, white lower front, black skirt
    face = face_mask(mdl, True, depth=3) & (u < 3.0) & (dy <= 17)
    mdl.paint(face & (Z >= SKIRT_TOP), WHITE)
    mdl.paint(face & (Z >= 22), RED)
    mdl.paint(face & (Z >= 27) & (dy <= 14), BLACK)
    mdl.inset(face & (Z >= 29) & (Z < 44) & (dy <= 12), P.GLASS)
    mdl.paint(face & (Z >= 41) & (Z < 44) & (dy <= 7), DISPLAY)
    mdl.paint(face & (Z >= 45) & (dy <= 12), DARK)
    mdl.paint(face & (Z < SKIRT_TOP), BLACK)
    mdl.paint(face & (Z >= 17) & (Z < 19) & (dy <= 1), P.OFF_WHITE)  # SBB logo
