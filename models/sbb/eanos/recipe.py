"""SBB Cargo Eanos — four-axle open bulk wagon, with Cargopositor loads.

Prototype (de.wikipedia "Eaos", dimensions from an SBB Cargo data sheet): 14.04 m over
buffers, 3.04 m wide, 3.255 m high, pivots 9.0 m, Y25 bogies (1.8 m wheelbase, wheels
920 mm), floor 1.235 m, load space 12.79 × 2.76 × 2.02 m, 58 t payload, 120 km/h empty /
100 km/h loaded. Typical loads: coal, ores, stone, scrap, timber.

The load space is painted with CARGO_MASK; Cargopositor fills it with a heap stretched to
the box, at half and full height. The heap is modelled in the CC1 ramp, so the game can
recolour it per cargo (looks below) without extra sprites.
"""

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.cargo import CARGO_MASK, CargoSpec, CargoState
from puenktlich.voxel.model import Model, m
from puenktlich.voxel.parts.running_gear import bogie, buffers

LENGTH_M = 12.8  # real 14.04 m, fitted to its OpenTTD length 4/8 (12.8 m) so it does not overlap neighbours
BUFFER_DEPTH = 6
FLOOR = 15
BOX_TOP = 39
HALF_WIDTH = 19.5
# Fixed colours, not company colours: the heap is the only CC1 in this model, so the game
# can recolour the cargo layer per cargo without touching the wagon (see voxel/cargo.py).
WALL = P.ramp(P.REDDISH_BROWN, 0.45)
RIB = P.ramp(P.REDDISH_BROWN, 0.2)
FRAME = P.ramp(P.GREY, 0.15)


def build() -> Model:
    mdl = Model.new()
    mid = mdl.d.shape[0] / 2
    half = m(LENGTH_M) / 2
    x0, x1 = mid - half + BUFFER_DEPTH, mid + half - BUFFER_DEPTH
    X, Y, Z = mdl.coords()
    # underframe and floor
    mdl.solid(mdl.centred_box(x0, x1, HALF_WIDTH - 1, FLOOR - 3, FLOOR), FRAME)
    # box: outer walls with vertical ribs, empty inside
    box = mdl.centred_box(x0, x1, HALF_WIDTH, FLOOR, BOX_TOP)
    inner = mdl.centred_box(x0 + 2, x1 - 2, HALF_WIDTH - 2, FLOOR + 1, BOX_TOP + 1)
    mdl.solid(box & ~inner, WALL)
    ribs = (box & ~inner) & ((X.astype(int) - int(x0)) % 11 < 2)
    mdl.paint(ribs, RIB)
    mdl.paint(mdl.centred_box(x0, x1, HALF_WIDTH, BOX_TOP - 1, BOX_TOP), RIB)  # top rail
    # load space for Cargopositor
    mdl.solid(mdl.centred_box(x0 + 2, x1 - 2, HALF_WIDTH - 2, FLOOR, BOX_TOP - 1), CARGO_MASK)
    # running gear
    for c in (mid - m(4.5), mid + m(4.5)):
        bogie(mdl, c, wheelbase=m(1.8), wheel_diameter=9, top=FLOOR - 2)
    buffers(mdl, x1, front=True, z=FLOOR - 2, length=BUFFER_DEPTH)
    buffers(mdl, x0, front=False, z=FLOOR - 2, length=BUFFER_DEPTH)
    return mdl


def _heap(fill: float) -> Model:
    """Bulk heap in the dark half of the CC1 ramp (recoloured per cargo in-game). The canvas
    is the full box height; the heap rises to `fill` of it with a rounded crest."""
    sx, sy, sz = 120, 32, 24
    grid = Model(Model.new().grid.__class__(np.zeros((sx, sy, sz), dtype=np.uint8)))
    X, Y, Z = grid.coords()
    dy = np.abs(Y - (sy - 1) / 2) / (sy / 2)
    dx = np.abs(X - (sx - 1) / 2) / (sx / 2)
    height = sz * fill * (1 - 0.35 * dy**2) * (1 - 0.25 * dx**4)
    inside = height > Z
    shade = np.clip(P.CC1[0] + 1 + (Z / max(1.0, sz * fill)) * 2, P.CC1[0], P.CC1[0] + 3).astype(np.uint8)
    grid.d[np.broadcast_to(inside, grid.d.shape)] = np.broadcast_to(shade, grid.d.shape)[
        np.broadcast_to(inside, grid.d.shape)
    ]
    return grid


CARGO = CargoSpec(
    shapes={"heap_half": lambda: _heap(0.5), "heap_full": lambda: _heap(1.0)},
    stages={1: CargoState("heap_half", "scale"), 2: CargoState("heap_full", "scale")},
    looks={
        "coal": "GREY",
        "ore": "BROWN",
        "stone": "WHITE",
        "scrap": "ORANGE",
        "generic": "CREAM",  # sand, earth, anything else
    },
    labels={
        "COAL": "coal",
        "IORE": "ore",
        "CORE": "ore",  # copper ore (sub-arctic / tropic)
        "AORE": "ore",
        "STON": "stone",  # FIRS & friends
        "GRVL": "stone",
        "SCMT": "scrap",
        "SAND": "generic",
        "CLAY": "generic",
    },
    default_look="generic",
)
