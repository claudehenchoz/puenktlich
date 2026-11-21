"""SBB Cargo Sgns — four-axle 60 ft container flat, with Cargopositor container loads.

Approximate (the cited sources have no Sgns data sheet): ~19.7 m over buffers, load
length 18.4 m for 60 ft (three 20 ft containers), Y25 bogies, 120 km/h. Containers:
20 ft ISO, 6.06 × 2.44 × 2.59 m, in fixed colours (not company colours).
"""

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.cargo import CARGO_MASK, CargoSpec, CargoState
from puenktlich.voxel.model import Model, m
from puenktlich.voxel.parts.running_gear import bogie, buffers
from puenktlich.voxel.vox import VoxelGrid

LENGTH_M = 19.7
BUFFER_DEPTH = 6
DECK = 15
FRAME = P.ramp(P.CC1, 0.5)
FRAME_DARK = P.ramp(P.CC1, 0.2)
LOAD = (184, 36, 31)  # load space: 18.4 m long, container width/height in canvas voxels
CONTAINER_LEN = 60
CONTAINER_COLOURS = [P.ramp(P.PALE_RED, 0.3), P.ramp(P.BRIGHT_BLUE, 0.4), P.ramp(P.GREY, 0.75)]


def build() -> Model:
    mdl = Model.new()
    mid = mdl.d.shape[0] / 2
    half = m(LENGTH_M) / 2
    x0, x1 = mid - half + BUFFER_DEPTH, mid + half - BUFFER_DEPTH
    X, _, _ = mdl.coords()
    # deck frame: two deep side sills + cross members, open in between
    for side in (-1, 1):
        y0 = 21 + side * 16 - (2 if side > 0 else 0)
        mdl.solid(mdl.box(x0, x1, y0, y0 + 3, DECK - 6, DECK), FRAME)
    mdl.solid(mdl.centred_box(x0, x1, 17, DECK - 2, DECK) & ((X.astype(int) % 16) < 3), FRAME_DARK)
    mdl.solid(mdl.centred_box(x0, x0 + 4, 18, DECK - 6, DECK), FRAME)
    mdl.solid(mdl.centred_box(x1 - 4, x1, 18, DECK - 6, DECK), FRAME)
    # container load space for Cargopositor
    lx, ly, lz = LOAD
    mdl.solid(mdl.centred_box(mid - lx / 2, mid + lx / 2, ly / 2, DECK, DECK + lz), CARGO_MASK)
    for c in (mid - m(7.1), mid + m(7.1)):
        bogie(mdl, c, wheelbase=m(1.8), wheel_diameter=9, top=DECK - 5)
    buffers(mdl, x1, front=True, z=DECK - 3, length=BUFFER_DEPTH)
    buffers(mdl, x0, front=False, z=DECK - 3, length=BUFFER_DEPTH)
    return mdl


def _containers(count: int) -> VoxelGrid:
    """`count` 20 ft containers in a load-space-sized block (empty slots stay empty)."""
    lx, ly, lz = LOAD
    d = np.zeros((lx, ly, lz), dtype=np.uint8)
    gap = (lx - 3 * CONTAINER_LEN) // 2
    for i in range(count):
        a = i * (CONTAINER_LEN + gap)
        col = CONTAINER_COLOURS[i % len(CONTAINER_COLOURS)]
        d[a : a + CONTAINER_LEN, :, :] = col
        d[a : a + CONTAINER_LEN : 3, :, 2 : lz - 2] = col - 1  # corrugation
        d[a : a + 2, :, :] = col - 2  # door / end frames
        d[a + CONTAINER_LEN - 2 : a + CONTAINER_LEN, :, :] = col - 2
    return VoxelGrid(d)


CARGO = CargoSpec(
    shapes={"containers_2": lambda: _containers(2), "containers_3": lambda: _containers(3)},
    stages={1: CargoState("containers_2", "repeat", n=1), 2: CargoState("containers_3", "repeat", n=1)},
    looks={"containers": None},  # containers keep their own colours
    default_look="containers",
)
