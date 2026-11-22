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
    frame_colour: int = P.UNDERFRAME,
    top: float = 14,
    gauge: str = "standard",
    style: str = "loco",
) -> None:
    """Two-axle bogie: wheelsets, outer side frames with axle boxes, bolster.

    style  "loco"     deep plate frame with a window between the axles
           "coach"    the same frame with a light secondary (air) spring on top of the centre
           "freight"  Y25-type: a low bar frame and a coil-spring pack above each axle box
    """
    half = wheelbase / 2
    for ax in (centre - half, centre + half):
        wheelset(model, ax, wheel_diameter, gauge=gauge)
    r = wheel_diameter / 2
    # side frames outside the wheels
    y_out1 = GAUGES[gauge]
    y_out0 = y_out1 - 4
    if style == "freight":
        # low bar from axle box to axle box; the wagon rests on the spring packs
        bar = model.box(centre - half - 2, centre + half + 3, y_out0, y_out1, r - 1, r + 2)
        model.solid(model.mirror_y(bar), frame_colour)
        for ax in (centre - half, centre + half):
            springs = model.box(ax - 3, ax + 4, y_out0, y_out1, r + 2, top - 1)
            model.solid(model.mirror_y(springs), P.shade(frame_colour, 2))
    else:
        frame = model.box(centre - half - r - 2, centre + half + r + 2, y_out0, y_out1, r - 1, top - 1)
        # lighten the frame: cut the window between the axles below the top member
        cut = model.box(centre - half + r + 1, centre + half - r - 1, y_out0, y_out1, r - 1, top - 5)
        model.solid(model.mirror_y(frame & ~cut), frame_colour)
        if style == "coach":
            spring = model.box(centre - 3, centre + 3, y_out0, y_out1, top - 5, top - 1)
            model.solid(model.mirror_y(spring), P.MID_GREY)
    # axle boxes
    for ax in (centre - half, centre + half):
        boxm = model.box(ax - 2, ax + 3, y_out0 - 1, y_out1, r - 2, r + 2)
        model.solid(model.mirror_y(boxm), P.BLACK)
    # bolster / transom across the bogie, from side frame to side frame
    model.solid(model.centred_box(centre - 3, centre + 3, model.cy - y_out0, r, top - 1), frame_colour)


# Coupling height per gauge, the same on every vehicle so that coupled vehicles line up:
# the buffer centre line is at COUPLING_Z + 1. Standard gauge: side buffers 1.06 m above the
# rail, just below the floor (z 15). Metre gauge (RhB, MGB): one central buffer, lower down.
COUPLING_Z = {"standard": 12, "metre": 9}


def buffers(
    model: Model,
    x_end: float,
    front: bool,
    length: float = 6,
    spacing: float = 13,
    colour: int = P.UNDERFRAME,
    gauge: str = "standard",
    beam: bool = True,
) -> None:
    """Buffers and coupling at one end, at the gauge's coupling height. `x_end` = face of the
    body. Standard gauge: two side buffers `spacing` from the centre line and a screw-coupling
    hook. Metre gauge: a central buffer with the coupling hook below it.
    beam: buffer beam (headstock) under the body end for the buffers to sit on."""
    z = COUPLING_Z[gauge]
    x0, x1 = (x_end, x_end + length) if front else (x_end - length, x_end)
    plate_x = (x1 - 1, x1) if front else (x0, x0 + 1)
    hook_x = sorted((x_end, x_end + (3 if front else -3)))
    if gauge == "metre":
        if beam:
            model.solid(model.centred_box(*sorted((x_end, x_end + (-2 if front else 2))), 6, z - 1, z + 4), colour)
        model.solid(model.centred_box(x0, x1, 2, z - 1, z + 3), colour)
        model.solid(model.centred_box(*plate_x, 3, z - 2, z + 4), P.MID_GREY)
        model.solid(model.centred_box(*hook_x, 1, z - 3, z - 1), P.BLACK)
        return
    if beam:
        model.solid(
            model.centred_box(*sorted((x_end, x_end + (-2 if front else 2))), spacing + 4, z - 1, z + 4), colour
        )
    for side in (-1, 1):
        yc = model.cy + side * spacing
        model.solid(model.box(x0, x1, yc - 2, yc + 2, z - 1, z + 3), colour)
        model.solid(model.box(*plate_x, yc - 3, yc + 3, z - 2, z + 4), P.MID_GREY)
    # screw coupling hook
    model.solid(model.centred_box(*hook_x, 1, z, z + 2), P.BLACK)


def skirt(
    model: Model, x0: float, x1: float, z0: float, z1: float, half_width: float, colour: int = P.UNDERFRAME
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


# Underfloor equipment between the bogies, as (from, to, kind, drop): positions are fractions
# of the space, `drop` is how far the item hangs below the floor.
#   box   equipment case as wide as the underframe (battery, converter, air conditioning)
#   tank  a pair of cylinders along the sides (air reservoirs)
COACH_UNDERFRAME = ((0.03, 0.27, "box", 8), (0.33, 0.53, "tank", 6), (0.59, 0.83, "box", 6), (0.88, 0.97, "box", 8))
LOCO_UNDERFRAME = ((0.0, 0.2, "box", 6), (0.2, 0.8, "box", 9), (0.8, 1.0, "box", 6))  # transformer in the middle


def underframe(
    model: Model,
    x0: float,
    x1: float,
    top: float,
    half_width: float,
    layout: tuple[tuple[float, float, str, float], ...] = COACH_UNDERFRAME,
    colour: int = P.UNDERFRAME,
) -> None:
    """Underfloor equipment between the bogies (x0..x1, hanging from `top`): a centre sill
    with separate cases and air tanks, instead of one solid skirt box."""
    X, Y, Z = model.coords()
    model.solid(model.centred_box(x0, x1, half_width - 5, top - 3, top), colour)  # centre sill
    span = x1 - x0
    for a, b, kind, drop in layout:
        xa, xb = round(x0 + a * span), round(x0 + b * span)
        if kind == "box":
            model.solid(model.centred_box(xa, xb, half_width, top - drop, top), colour)
        else:
            r = 2.5
            for side in (-1, 1):
                yc = model.cy + side * (half_width - r)
                tank = (xa <= X) & (xb > X) & ((Y - yc) ** 2 + (Z - (top - drop + r)) ** 2 <= r * r)
                model.solid(tank, P.shade(colour, 2))
