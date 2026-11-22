"""Metre-gauge panorama coaches (Stadler Glacier Express cars of RhB / MGB, 2006–2009).

`build_panorama_car(spec, lights)` builds one 18.5 m coach on the train canvas. Measurements
come from photos: models/mgb/glacier/REFERENCE.md. Positions along the car are metres from
the door end (high x, the front of the model); the other end has no door.

Shape: vertical sides up to the window line, then a steep bevel (`CrossSection.chamfer_*`) that
carries the roof glazing, and a narrow flat roof. Livery: pale blue body, red (CC1) car ends
with a slanted boundary and white slanted stripes, red skirt band along the bottom, black
window frames. The bar car (WRp) is red all over; the Excellence Class car adds gold stripes.
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
    gangway,
    side_band,
    side_skin,
)
from puenktlich.voxel.parts.lights import lamp_cluster
from puenktlich.voxel.parts.roof import roof_ribs
from puenktlich.voxel.parts.running_gear import COACH_UNDERFRAME, bogie, buffers, underframe
from puenktlich.voxel.variants import Lights

# heights (z, ≈12.5 voxels per metre on metre gauge), REFERENCE.md "Measurements"
FLOOR = 9  # body bottom (top of the red skirt band at 0.71 m)
RED_BAND = (9, 12)  # red skirt band 0.71–1.0 m
FRAME = (20, 44)  # black frame around the lower windows and the roof glazing
LOWER_WIN = (21, 34)
UPPER_WIN = (36, 43)  # roof glazing in the bevel
CHAMFER_FROM = 35  # 2.8 m
ROOF = 46  # 3.695 m

SECTION = CrossSection(
    floor=FLOOR,
    roof=ROOF,
    half_width=17.5,
    roof_radius=2,
    tumblehome=0.5,
    tumble_from=14,
    chamfer_from=CHAMFER_FROM,
    chamfer_inset=8,
)
END = EndShape(rake=0, corner_radius=2)

RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
PALE = P.ramp(P.ICY_BLUE, 1.0)  # 214: GoRender lighting brightens it to the real pale blue
STRIPE_WHITE = P.OFF_WHITE
GOLD = P.ramp(P.GOLDEN_BROWN, 0.5)
FRAME_BLACK = P.BLACK
GANGWAY = P.DARK
UNDER = P.DARK

SLANT = 0.043  # m of end-boundary shift per voxel of height (red ends lean towards the end)


@dataclass
class PanoramaSpec:
    kind: Literal["first", "second", "bar", "excellence"] = "second"
    length_m: float = 18.5  # over buffers
    windows: int = 6  # window bays (seat pitch 2050 mm)


def build_panorama_car(spec: PanoramaSpec, lights: Lights) -> Model:
    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2 + 4, sx / 2 + lob / 2 - 5  # 0.4 m for buffers/gangways
    body_m = (x_front - x_rear) / 10

    def at(u: float) -> float:
        """Metres from the door end -> x."""
        return x_front - u * 10

    shell = Shell(x_rear, x_front, SECTION, front=END, rear=END)
    X, Y, Z = mdl.coords()
    u = (x_front - X) / 10  # from the door end
    v = body_m - u  # from the plain end
    bar = spec.kind == "bar"

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), RED if bar else PALE)
    h = Z - 10  # slant reference height
    door_end = u < 3.0 - SLANT * h
    plain_end = v < 2.6 - SLANT * h
    mdl.paint(door_end | plain_end, RED)
    mdl.paint(RED_BAND[1] > Z, RED)
    if spec.kind == "excellence":  # gold stripes next to the red ends
        mdl.paint(
            ((u >= 3.0 - SLANT * h) & (u < 3.45 - SLANT * h)) | ((v >= 2.6 - SLANT * h) & (v < 3.05 - SLANT * h)), GOLD
        )
    # white slanted stripes on the red ends (upper part of the side)
    upper = side_skin(mdl) & (Z >= 18) & (Z < 42)
    mdl.paint(upper & (u >= 1.4 - SLANT * h) & (u < 2.1 - SLANT * h), STRIPE_WHITE)
    mdl.paint(upper & (v >= 0.9 - SLANT * h) & (v < 1.5 - SLANT * h), STRIPE_WHITE)

    # --- narrow flat roof between the glazed bevels: grey, with panel seams ------------
    mdl.paint((ROOF - 1 <= Z) & (x_rear + 2 < X) & (x_front - 2 > X), P.ROOF)
    roof_ribs(mdl, x_rear + 4, x_front - 4, ROOF - 1, half_width=9)

    # --- windows: one black-framed block, panes in the side and in the bevel ----------
    if bar:  # panorama bar (REFERENCE.md, g02): two bays, then service door and kitchen
        block, bays = (5.5, 10.6), 2
    else:
        block, bays = (3.2, body_m - 2.9), spec.windows
    x0, x1 = at(block[1]), at(block[0])
    mdl.paint(side_band(mdl, x0, x1, *FRAME), FRAME_BLACK)
    pitch = (x1 - x0) / bays
    for i in range(bays):
        a = x0 + i * pitch
        mdl.inset(side_band(mdl, a + 1, a + pitch - 1, *LOWER_WIN), P.GLASS)
        mdl.inset(side_band(mdl, a + 1, a + pitch - 1, *UPPER_WIN), P.GLASS)
    if bar:
        for a, b in ((13.1, 14.3), (14.9, 15.9)):  # kitchen windows
            mdl.paint(side_band(mdl, at(b) - 1, at(a) + 1, 26, 35), FRAME_BLACK)
            mdl.inset(side_band(mdl, at(b), at(a), 27, 34), P.GLASS)
        door_outline(mdl, at(12.0), at(11.3), FLOOR + 2, 36, RED_DARK)  # service door
        letters = side_skin(mdl) & (X.astype(int) % 3 != 0)  # "GLACIER" over "EXPRESS"
        mdl.paint(letters & side_band(mdl, at(15.0), at(12.2), 20, 25), STRIPE_WHITE)
        mdl.paint(letters & side_band(mdl, at(15.0), at(12.9), 15, 19), STRIPE_WHITE)
    else:  # class number on the pale side next to the window block, at the door end
        n = {"first": 1, "excellence": 1, "second": 2}[spec.kind]
        xc = at(2.85)
        mdl.paint(side_band(mdl, xc - n, xc, 30, 34), RED)
    if spec.kind == "excellence":  # "Excellence Class" lettering above the windows
        mdl.paint(side_band(mdl, at(6.0), at(3.6), 16, 19) & (X.astype(int) % 2 == 0), GOLD)

    # --- entrance door at the door end (both sides; the bar car has none) ----------------
    if not bar:
        door_outline(mdl, at(1.25), at(0.35), FLOOR + 1, 37, RED_DARK)
        mdl.inset(side_band(mdl, at(1.1), at(0.5), 24, 33), P.GLASS)

    # --- ends: dark gangways, central buffer, tail lamps -------------------------------
    for front in (True, False):
        xe = x_front if front else x_rear
        if not (spec.kind == "excellence" and not front):  # the bar end has no gangway
            gangway(mdl, xe, front, 8, FLOOR + 1, ROOF - 8, GANGWAY)
        end = face_mask(mdl, front, depth=1) & (Z >= FLOOR + 1) & (Z < ROOF - 8) & (abs(Y - mdl.cy) <= 9)
        mdl.paint(end & ~np.broadcast_to((x_front < X) | (x_rear > X), mdl.d.shape), GANGWAY)
        buffers(mdl, xe, front=front, length=4, gauge="metre", beam=False)
    # tail lamps: a coach never leads, so its front lamps stay off and only the rear ones turn red
    for front, state in ((True, "off"), (False, lights.state("rear"))):
        lamp_cluster(mdl, shell, front, state, low_z=(12, 15), top_z=None, spacing=13, lamp_half_width=1.5)

    # --- running gear (pivots 12.83 m apart, air-sprung bogies) -------------------------
    mid = shell.mid
    for c in (mid - 64, mid + 64):
        bogie(mdl, c, wheelbase=18, wheel_diameter=7, top=FLOOR, gauge="metre", style="coach")
    # low-slung body: only shallow equipment cases fit under the floor
    layout = tuple((a, b, kind, 4 if kind == "box" else 5) for a, b, kind, _ in COACH_UNDERFRAME)
    underframe(mdl, mid - 46, mid + 46, FLOOR, 14, layout, colour=UNDER)
    return mdl
