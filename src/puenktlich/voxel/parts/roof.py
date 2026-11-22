"""Roof equipment: single-arm pantographs, insulators, main switch, cable runs, vents, ribs."""

from __future__ import annotations

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model


def _line(
    model: Model, a: tuple[float, float], b: tuple[float, float], half_width: float, thickness: float, colour: int
) -> None:
    """Thin bar in the x/z plane from a=(x,z) to b=(x,z), spanning ±half_width in y."""
    X, Y, Z = model.coords()
    (ax, az), (bx, bz) = a, b
    vx, vz = bx - ax, bz - az
    L2 = vx * vx + vz * vz
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / L2, 0, 1)
    dist2 = (X - (ax + t * vx)) ** 2 + (Z - (az + t * vz)) ** 2
    m = (dist2 <= thickness * thickness) & (np.abs(Y - CENTRE_Y) <= half_width)
    model.solid(m, colour)


def pantograph(
    model: Model,
    x_base: float,
    roof_z: float,
    raised: bool = False,
    facing_front: bool = True,
    colour: int = P.LIGHT_GREY,
    raise_height: float = 15,
) -> None:
    """Single-arm (Schunk WBL-style) pantograph. The knee points towards `facing_front`.
    raise_height: head above the roof when raised (lower on tall double-deck roofs, so the
    model stays within the hill-tilt headroom)."""
    s = 1 if facing_front else -1
    base = model.centred_box(x_base - 6, x_base + 7, 6, roof_z + 1, roof_z + 3)
    model.solid(base, P.DARK_GREY)
    # insulators
    for dx in (-5, 5):
        for dy in (-5, 5):
            model.solid(
                model.box(x_base + dx, x_base + dx + 2, CENTRE_Y + dy, CENTRE_Y + dy + 2, roof_z, roof_z + 3),
                P.LIGHT_GREY,
            )
    hinge = (x_base - 4 * s, roof_z + 3)
    if raised:
        # head stays <= z 67 so a model tilted 10° for hill sprites is not clipped at z 72
        knee = (x_base + 12 * s, roof_z + 10 * raise_height / 15)
        head = (x_base - 1 * s, roof_z + raise_height)
    else:
        knee = (x_base + 14 * s, roof_z + 4.5)
        head = (x_base - 2 * s, roof_z + 5.5)
    _line(model, hinge, knee, 2, 0.8, colour)  # lower arm (narrow frame)
    _line(model, knee, head, 0.5, 0.7, colour)  # upper arm
    # collector head across the vehicle
    hx, hz = head
    model.solid(model.centred_box(hx - 1, hx + 2, 11, hz, hz + 1.5), P.BLACK)
    model.solid(model.centred_box(hx - 0.5, hx + 1, 12, hz + 1, hz + 2), P.MID_GREY)


def roof_box(
    model: Model, x0: float, x1: float, half_width: float, z0: float, height: float, colour: int = P.MID_GREY
) -> None:
    model.solid(model.centred_box(x0, x1, half_width, z0, z0 + height), colour)


def main_switch(model: Model, x: float, roof_z: float) -> None:
    model.solid(model.centred_box(x - 4, x + 4, 2, roof_z, roof_z + 4), P.LIGHT_GREY)
    model.solid(model.centred_box(x - 2, x + 2, 3, roof_z + 4, roof_z + 6), P.MID_GREY)


def roof_cable(model: Model, x0: float, x1: float, roof_z: float, y_offset: float = 4) -> None:
    model.solid(model.box(x0, x1, CENTRE_Y + y_offset, CENTRE_Y + y_offset + 1, roof_z, roof_z + 1.5), P.BLACK)


def roof_ribs(model: Model, x0: float, x1: float, z_from: float, pitch: float = 20, half_width: float = 15) -> None:
    """Transverse panel seams on a plain coach roof: every `pitch` voxels one row of the roof
    skin a shade darker, so a long bare roof gets some texture at 2x/4x without adding height."""
    X, Y, Z = model.coords()
    seam = (((X - x0) % pitch) < 1) & (x0 <= X) & (x1 > X) & (z_from <= Z) & (abs(Y - model.cy) <= half_width)
    model.paint(seam & model.surface(), P.shade(P.ROOF, -2), only=(P.ROOF, P.ROOF))


def roof_vents(model: Model, centres: list[float], roof_z: float, half_width: float = 2, length: float = 4) -> None:
    """Low ventilator hoods on the roof centre line."""
    for c in centres:
        model.solid(model.centred_box(c - length / 2, c + length / 2, half_width, roof_z, roof_z + 1), P.MID_GREY)
