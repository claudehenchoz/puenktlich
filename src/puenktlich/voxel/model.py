"""`Model`: a voxel canvas with modelling helpers that recipes use.

All coordinates are voxels on the GoRender train canvas (see docs/SCALE.md):
    x: 0..255 along the vehicle, high x = FRONT (cab 1)
    y: 0..41 across, centre line between y=20 and y=21
    z: 0..71 up, z=0 = rail head

Shapes are added with `solid()` (a boolean mask over the canvas) and coloured with
`paint()`. Masks are numpy boolean arrays, so parts compose with &, |, ~.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from puenktlich.voxel.vox import VoxelGrid

VOX_PER_M = 10  # along x — see docs/SCALE.md
CANVAS = (256, 42, 72)
CENTRE_Y = 20.5  # train canvas; use Model.cy for code that also serves road vehicles
ROAD_CANVAS = (126, 40, 48)  # road vehicles (render/manifests/road.json): 8/8 = 12.6 m


def m(metres: float) -> int:
    """Metres (along the vehicle) -> voxels."""
    return int(round(metres * VOX_PER_M))


@dataclass
class Model:
    grid: VoxelGrid

    @classmethod
    def new(cls, canvas: tuple[int, int, int] = CANVAS) -> Model:
        return cls(VoxelGrid.empty(*canvas))

    @property
    def cy(self) -> float:
        """Centre line across the canvas (20.5 on the train canvas)."""
        return (self.d.shape[1] - 1) / 2

    # --- coordinate helpers -------------------------------------------------
    @property
    def d(self) -> np.ndarray:
        return self.grid.data

    def coords(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Broadcastable X, Y, Z index arrays (float) for building masks."""
        sx, sy, sz = self.d.shape
        return (
            np.arange(sx, dtype=float)[:, None, None],
            np.arange(sy, dtype=float)[None, :, None],
            np.arange(sz, dtype=float)[None, None, :],
        )

    def box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> np.ndarray:
        """Inclusive-exclusive box mask [x0,x1) x [y0,y1) x [z0,z1)."""
        X, Y, Z = self.coords()
        return (x0 <= X) & (x1 > X) & (y0 <= Y) & (y1 > Y) & (z0 <= Z) & (z1 > Z)

    def centred_box(self, x0: float, x1: float, half_width: float, z0: float, z1: float) -> np.ndarray:
        """Box [x0,x1) x [z0,z1) reaching `half_width` to each side of the centre line: always
        symmetric (half_width 13 -> 26 voxels, 19.5 -> the full 40-voxel body width)."""
        X, Y, Z = self.coords()
        return (x0 <= X) & (x1 > X) & (abs(Y - self.cy) <= half_width) & (z0 <= Z) & (z1 > Z)

    def cylinder_y(self, xc: float, zc: float, r: float, y0: float, y1: float) -> np.ndarray:
        """Cylinder with its axis along y (wheels, axles)."""
        X, Y, Z = self.coords()
        return ((X - xc) ** 2 + (Z - zc) ** 2 <= r * r) & (y0 <= Y) & (y1 > Y)

    def mirror_y(self, mask: np.ndarray) -> np.ndarray:
        """Mask OR its left/right mirror (canvas is symmetric about CENTRE_Y)."""
        return mask | mask[:, ::-1, :]

    def mirror_x(self, mask: np.ndarray, centre: float) -> np.ndarray:
        """Mask OR its mirror about the x-plane `centre` (e.g. the vehicle midpoint)."""
        sx = self.d.shape[0]
        src = np.arange(sx)
        dst = np.round(2 * centre - src).astype(int)
        ok = (dst >= 0) & (dst < sx)
        out = mask.copy()
        out[dst[ok]] |= mask[src[ok]]
        return out

    # --- mutation -------------------------------------------------------------
    def solid(self, mask: np.ndarray, colour: int) -> None:
        """Fill voxels in `mask` with `colour` (overwrites)."""
        self.d[np.broadcast_to(mask, self.d.shape)] = colour

    def carve(self, mask: np.ndarray) -> None:
        self.d[np.broadcast_to(mask, self.d.shape)] = 0

    def paint(self, mask: np.ndarray, colour: int, only: tuple[int, int] | None = None) -> None:
        """Recolour *existing* voxels in `mask` (optionally only those in colour range `only`)."""
        sel = np.broadcast_to(mask, self.d.shape) & (self.d != 0)
        if only is not None:
            sel &= (self.d >= only[0]) & (self.d <= only[1])
        self.d[sel] = colour

    def surface(self) -> np.ndarray:
        """Occupied voxels with at least one empty 6-neighbour (the visible skin)."""
        occ = self.d != 0
        pad = np.pad(occ, 1, constant_values=False)
        inner = (
            pad[2:, 1:-1, 1:-1]
            & pad[:-2, 1:-1, 1:-1]
            & pad[1:-1, 2:, 1:-1]
            & pad[1:-1, :-2, 1:-1]
            & pad[1:-1, 1:-1, 2:]
            & pad[1:-1, 1:-1, :-2]
        )
        return occ & ~inner

    def inset(self, mask: np.ndarray, colour: int, depth: int = 1) -> None:
        """Push the skin inside `mask` inwards by `depth` and colour the new face —
        used for windows, grilles and door seams so they catch shading."""
        for _ in range(depth):
            skin = self.surface() & np.broadcast_to(mask, self.d.shape)
            self.d[skin] = 0
        skin = self.surface() & np.broadcast_to(mask, self.d.shape)
        self.d[skin] = colour

    def rotate_180(self) -> None:
        """Turn the model around (swap front and rear ends, and left/right sides).
        The canvas is symmetric, so the vehicle stays centred."""
        self.grid.data = np.ascontiguousarray(self.d[::-1, ::-1, :])
