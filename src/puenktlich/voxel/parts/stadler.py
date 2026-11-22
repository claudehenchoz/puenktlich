"""Stadler's current family face (KISS 2 / SBB RABe 512, FLIRT 3 / SBB RABe 523 1xx and 5xx).

`shield_nose(...)` paints a raked cab end: a black windscreen shield with a V-shaped lower edge
in a red (CC1) frame, white lower corners, the dark roof cap, and on the sides a red line that
rises from the red lower nose along the windscreen edge into the red roof-edge line, with the
black windscreen wrap above it. Photos: models/sbb/rabe512/REFERENCE.md,
models/sbb/rabe523/REFERENCE.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import Shell, face_mask, side_band

RED = P.BODY_CC1
WHITE = P.BODY_CC2
BLACK = P.BLACK
DARK = P.DARK
DISPLAY = P.YELLOW


@dataclass(frozen=True)
class ShieldNose:
    """Heights (z) and lengths (m from the nose tip) of one vehicle's shield nose."""

    red_line_z: float  # lower edge of the red roof-edge line (3 voxels high)
    roof_from: float  # dark roof above this
    shield_top: float  # top of the windscreen glass; display just below, roof cap above
    rise: float = 3.6  # the red line rises from 1.0 m behind the tip over this length (m)
    length: float = 5.0  # nose section painted from the tip
    line_from_z: float = 28  # lower edge of the red line at the nose tip
    cab_window: tuple[float, float, float, float] = (2.6, 5.4, 28, 40)  # u0, u1, z0, z1


def shield_nose(mdl: Model, shell: Shell, at: Callable[[float], float], n: ShieldNose) -> None:
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (shell.x_front - X) / 10
    nose = u < n.length
    # sides: black wrap above the rising red line, red lower nose below it
    edge = n.line_from_z + (n.red_line_z - n.line_from_z) * np.clip((u - 1.0) / n.rise, 0, 1)
    mdl.paint(nose & (edge + 3 <= Z) & (n.roof_from > Z), BLACK)
    mdl.paint(nose & (edge <= Z) & (edge + 3 > Z) & (n.roof_from > Z), RED)
    mdl.paint(nose & (u < 1.6) & (Z >= 14) & (edge > Z), RED)
    mdl.paint((u < 3.0) & (n.roof_from - 2 <= Z) & (dy <= 14), DARK)  # roof cap
    # cab side window, front edge raked
    u0, u1, z0, z1 = n.cab_window
    cab_win = side_band(mdl, at(u1), at(u0), z0, z1) & (X - at(u0) < -(Z - z0) * 0.8)
    mdl.paint(cab_win, BLACK)
    mdl.inset(cab_win & side_band(mdl, at(u1 - 0.2), at(u0 + 0.3), z0 + 1, z1 - 1), P.GLASS)
    # front face: black shield with a V-shaped lower edge in a red frame
    face = face_mask(mdl, True, depth=3) & (u < 4.0) & (dy <= 17)  # corners keep the side livery
    mdl.paint(face & (Z >= 14), RED)
    v_bottom = 33 - 6 * np.clip(1 - dy / 16, 0, 1)
    mdl.paint(face & (v_bottom <= Z) & (dy <= 16), BLACK)
    mdl.inset(face & (v_bottom + 2 <= Z) & (n.shield_top > Z) & (dy <= 14), P.GLASS)
    mdl.paint(face & (n.shield_top - 3 <= Z) & (n.shield_top > Z) & (dy <= 8), DISPLAY)
    mdl.paint(face & (n.shield_top + 1 <= Z) & (dy <= 14), DARK)
    mdl.paint(face & (Z < 20) & (dy > 9), WHITE)  # white lower corners
    mdl.paint(face & (Z < 14), WHITE)
    mdl.paint(face & (Z < 12) & (dy <= 6), BLACK)  # coupler recess
