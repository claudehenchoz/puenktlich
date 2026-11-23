"""SBB Cargo Re 484 (Bombardier TRAXX F140 MS): multi-system Bo'Bo' freight locomotive for the
Gotthard/Simplon routes into Italy. Measurements, photos and livery: REFERENCE.md.

Colour plan: body CC1 (SBB Cargo blue), cab ends CC2 (red) to just behind the cab doors, white
"cargo" lettering, grey roof and a grey stripe along the bottom of the side, black windscreen.
"""

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, side_band
from puenktlich.voxel.parts.loco import LocoSpec, Louvres, Panel, Windscreen, build_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

# TRAXX: near-vertical front with a slightly raked windscreen, flat sides
BODY_WIDTH_M = 2.977  # 2,977 mm (docs/SCALE.md)

TRAXX_NOSE = EndShape(rake=10, rake_from=31, rake_curve=1.2, corner_radius=6, undercut=2, undercut_height=5)

SPEC = LocoSpec(
    length_m=18.9,
    section=CrossSection(floor=15, roof=51, half_width=19.5, roof_radius=6, tumblehome=1.0, tumble_from=26),
    nose=TRAXX_NOSE,
    windscreen=Windscreen(
        frame_z=(31, 49), frame_half_width=18, glass_z=(33, 47), glass_half_width=16, depth=14, centre_pillar=1
    ),
    cab_window=(12, 20),
    cab_window_z=(35, 45),
    door=(22, 29),
    door_z=(17, 47),
    door_glass_z=(38, 44),
    louvres=Louvres(offsets=(-36, 36), half_length=10, z=(41, 48)),
    panels=(Panel(z=(15, 19), colour=P.ROOF),),
    bogie_centres_m=5.2,
    wheelbase_m=2.6,
    pantograph_offset=36,
    roof_boxes=((-18, -8, 8), (8, 18, 8)),
    wheel_diameter=12,
)

END_RED = 32  # red cab ends, voxels from each body end


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    mdl = build_loco(SPEC, lights)
    X, _, Z = mdl.coords()
    body = np.flatnonzero((mdl.d == P.BODY_CC1).any(axis=(1, 2)))
    x0, x1 = body[0], body[-1]
    ends = (x0 + END_RED > X) | (x1 - END_RED < X)
    mdl.paint((mdl.d == P.BODY_CC1) & ends, P.BODY_CC2)
    # white "cargo" lettering across the middle of each side
    mid = (x0 + x1) / 2
    letters = side_band(mdl, mid - 46, mid + 46, 23, 41) & (Z >= 23)
    strokes = ((X.astype(int) % 12) < 8) & ~(
        ((X.astype(int) % 12) >= 2) & ((X.astype(int) % 12) < 6) & (Z >= 27) & (Z < 37)
    )
    mdl.paint(letters & strokes & (mdl.d == P.BODY_CC1), P.OFF_WHITE)
    return mdl
