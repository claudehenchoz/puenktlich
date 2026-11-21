"""Bogies, wheelsets, buffers and couplers."""

from __future__ import annotations

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model

# Track geometry on the canvas (see docs/SCALE.md): OpenTTD rails are drawn
# broader than real standard gauge, so wheels sit at y≈7..10 / 31..34.
WHEEL_Y_OUTER = 7
WHEEL_THICKNESS = 3


def wheelset(model: Model, x: float, diameter: float = 11, colour: int = P.DARK_GREY) -> None:
    r = diameter / 2
    zc = r - 0.5
    for y0 in (WHEEL_Y_OUTER, model.d.shape[1] - WHEEL_Y_OUTER - WHEEL_THICKNESS):
        model.solid(model.cylinder_y(x, zc, r, y0, y0 + WHEEL_THICKNESS), colour)
        # rim highlight
        ring = model.cylinder_y(x, zc, r, y0, y0 + WHEEL_THICKNESS) & ~model.cylinder_y(
            x, zc, r - 1, y0, y0 + WHEEL_THICKNESS
        )
        model.paint(ring, P.MID_GREY)
    # axle
    model.solid(model.cylinder_y(x, zc, 1.2, WHEEL_Y_OUTER, model.d.shape[1] - WHEEL_Y_OUTER), P.BLACK)


def bogie(
    model: Model,
    centre: float,
    wheelbase: float = 28,
    wheel_diameter: float = 11,
    frame_colour: int = P.DARK_GREY,
    top: float = 14,
) -> None:
    """Two-axle bogie: wheelsets, outer side frames with axle boxes, springs."""
    half = wheelbase / 2
    for ax in (centre - half, centre + half):
        wheelset(model, ax, wheel_diameter)
    r = wheel_diameter / 2
    # side frames outside the wheels
    y_out0, y_out1 = 3, WHEEL_Y_OUTER
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
