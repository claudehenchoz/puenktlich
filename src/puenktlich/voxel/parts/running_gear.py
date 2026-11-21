"""Bogies, wheelsets, buffers and couplers."""

from __future__ import annotations

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model

# Track geometry on the canvas (see docs/SCALE.md): OpenTTD rails are drawn
# broader than real standard gauge, so wheels sit at y≈7..9 / 32..34. Metre gauge is
# 1000/1435 of that, matching the rails drawn by the companion track GRF (tracks/raster.py).
WHEEL_Y_OUTER = 7
WHEEL_THICKNESS = 3
GAUGES = {"standard": 7, "metre": 11}  # y of the outer face of the left wheel


def wheelset(model: Model, x: float, diameter: float = 11, colour: int = P.DARK_GREY, gauge: str = "standard") -> None:
    r = diameter / 2
    zc = r - 0.5
    wy = GAUGES[gauge]
    for y0 in (wy, model.d.shape[1] - wy - WHEEL_THICKNESS):
        model.solid(model.cylinder_y(x, zc, r, y0, y0 + WHEEL_THICKNESS), colour)
        # rim highlight
        ring = model.cylinder_y(x, zc, r, y0, y0 + WHEEL_THICKNESS) & ~model.cylinder_y(
            x, zc, r - 1, y0, y0 + WHEEL_THICKNESS
        )
        model.paint(ring, P.MID_GREY)
    # axle
    model.solid(model.cylinder_y(x, zc, 1.2, wy, model.d.shape[1] - wy), P.BLACK)


def bogie(
    model: Model,
    centre: float,
    wheelbase: float = 28,
    wheel_diameter: float = 11,
    frame_colour: int = P.DARK_GREY,
    top: float = 14,
    gauge: str = "standard",
) -> None:
    """Two-axle bogie: wheelsets, outer side frames with axle boxes, springs."""
    half = wheelbase / 2
    for ax in (centre - half, centre + half):
        wheelset(model, ax, wheel_diameter, gauge=gauge)
    r = wheel_diameter / 2
    # side frames outside the wheels
    y_out1 = GAUGES[gauge]
    y_out0 = y_out1 - 4
    frame = model.box(centre - half - r - 2, centre + half + r + 2, y_out0, y_out1, r - 1, top - 1)
    # lighten the frame: cut the window between the axles below the top member
    cut = model.box(centre - half + r + 1, centre + half - r - 1, y_out0, y_out1, r - 1, top - 5)
    model.solid(model.mirror_y(frame & ~cut), frame_colour)
    # axle boxes
    for ax in (centre - half, centre + half):
        boxm = model.box(ax - 2, ax + 3, y_out0 - 1, y_out1, r - 2, r + 2)
        model.solid(model.mirror_y(boxm), P.BLACK)
    # bolster / transom across the bogie
    model.solid(model.centred_box(centre - 3, centre + 3, CENTRE_Y - 3, r, top - 1), frame_colour)


def buffers(
    model: Model,
    x_end: float,
    front: bool,
    z: float = 14,
    length: float = 6,
    spacing: float = 13,
    colour: int = P.DARK_GREY,
) -> None:
    """Side buffers + buffer beam detail at one end. `x_end` = face of the body."""
    x0, x1 = (x_end, x_end + length) if front else (x_end - length, x_end)
    for yc in (CENTRE_Y - spacing, CENTRE_Y + spacing):
        stem = model.box(x0, x1, yc - 1.5, yc + 2.5, z - 1, z + 3)
        model.solid(stem, colour)
        plate_x = (x1 - 1, x1) if front else (x0, x0 + 1)
        plate = model.box(plate_x[0], plate_x[1], yc - 2.5, yc + 3.5, z - 2, z + 4)
        model.solid(plate, P.MID_GREY)
    # screw coupling hook
    hook = model.box(*(sorted((x_end, x_end + (3 if front else -3)))), CENTRE_Y - 1, CENTRE_Y + 2, z, z + 2)
    model.solid(hook, P.BLACK)


def skirt(
    model: Model, x0: float, x1: float, z0: float, z1: float, half_width: float, colour: int = P.DARK_GREY
) -> None:
    """Equipment skirt / underframe box between the bogies."""
    model.solid(model.centred_box(x0, x1, half_width, z0, z1), colour)


def rack_drive(model: Model, centre: float, wheelbase: float = 25, colour: int = P.BLACK) -> None:
    """Rack (cog) drive between the axles of a bogie: gear housing hanging low on the centre
    line, with the cog wheels just above rail level. Mostly visible in the diagonal views."""
    half = wheelbase / 2
    model.solid(model.centred_box(centre - half + 5, centre + half - 5, 6, 1, 7), colour)
    for c in (centre - half / 2, centre + half / 2):
        model.solid(model.cylinder_y(c, 4, 3.5, CENTRE_Y - 3, CENTRE_Y + 3), P.DARK_GREY)
