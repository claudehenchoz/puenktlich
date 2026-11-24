"""Shared layout of double-deck cars (used by parts/kiss.py: SBB RABe 514 and the IC2000
coaches). The SBB FV-Dosto itself is built by parts/fv_dosto.py.

Structure of every car:
    intermediate level over each bogie: body bottom high (HIGH_FLOOR), small window
    lower deck between the bogies: body down to LOW_FLOOR, one door at each end
    upper deck along the whole car, roof at ROOF
`deck_floor`, `deck_windows` and `gangway_ends` lay this out from a `DostoSpec`; positions are
metres from the car's front end. The heights below are the KISS family's (roof 4.59 m = z 56).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import (
    CrossSection,
    EndShape,
    face_mask,
    rounded_window,
)

# heights (z) of the KISS-proportioned layout (roof 4.595 m = z 56)
LOW_FLOOR = 3
HIGH_FLOOR = 12
ROOF = 56

SECTION = CrossSection(floor=HIGH_FLOOR, roof=ROOF, half_width=19.5, roof_radius=9, tumblehome=0.5, tumble_from=20)
FLAT_END = EndShape(rake=0, corner_radius=2)

BLACK = P.BLACK
DARK = P.DARK
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
    upper_to: float | None = None  # last upper-deck window ends here (None: 0.7 m before the rear end)
    extras: list = field(default_factory=list)


def deck_floor(door_x: list[tuple[float, float]]):
    """floor_at for a double-deck car: lower deck (LOW_FLOOR) between the outermost doors
    (inclusive), a 3-voxel ramp up to the intermediate level (HIGH_FLOOR) over the bogies."""
    low0, low1 = min(x for x, _ in door_x), max(x for _, x in door_x)

    def floor_at(X: np.ndarray) -> np.ndarray:
        d = np.maximum(low0 - X, X - low1)
        return np.clip(LOW_FLOOR + (HIGH_FLOOR - LOW_FLOOR) * d / 3, LOW_FLOOR, HIGH_FLOOR)

    return floor_at


def deck_windows(
    mdl: Model,
    spec: DostoSpec,
    at,
    door_x: list[tuple[float, float]],
    lower_z: tuple[float, float],
    upper_z: tuple[float, float],
    mezz_z: tuple[float, float],
) -> None:
    """Window rows of a double-deck car: `spec.lower_windows` spread evenly between the doors,
    upper-deck windows every `upper_pitch` m from `upper_from` to `upper_to` (default: the rear
    end), and the
    `mezz_windows` of the intermediate levels. `at` maps metres from the front end to x."""
    gap0, gap1 = door_x[-1][1] + 5, door_x[0][0] - 5
    lw = spec.lower_width * 10
    n = spec.lower_windows
    pitch = (gap1 - gap0) / n
    for i in range(n):
        a = gap0 + i * pitch + (pitch - lw) / 2
        rounded_window(mdl, a, a + lw, *lower_z)
    uw = spec.upper_width * 10
    k = 0
    while True:
        a_u = spec.upper_from + k * spec.upper_pitch
        if a_u + spec.upper_width > (spec.length_m - 0.7 if spec.upper_to is None else spec.upper_to):
            break
        rounded_window(mdl, at(a_u + spec.upper_width), at(a_u + spec.upper_width) + uw, *upper_z)
        k += 1
    for a, b in spec.mezz_windows:
        rounded_window(mdl, at(b), at(a), *mezz_z)


def gangway_ends(mdl: Model, cab: bool) -> None:
    """Dark end face with the bellows frame at each gangway end (the rear only on cab cars)."""
    _, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    for front in (False, True) if not cab else (False,):
        skin = face_mask(mdl, front, depth=2) & (Z >= HIGH_FLOOR)
        mdl.paint(skin & (dy <= 8) & (Z < ROOF - 4), BLACK)  # bellows
        mdl.paint(skin & (dy <= 6) & (Z >= HIGH_FLOOR + 2) & (Z < ROOF - 6), DARK)
