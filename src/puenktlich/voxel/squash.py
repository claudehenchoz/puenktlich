"""Halve a model along x for rendering (docs/SCALE.md).

Recipes are authored at 10 voxels per metre on the 256-voxel canvas (8/8 = 25.6 m), but
OpenTTD draws one 1/8 unit as 4 px at 1x in the 90° view, which on the GoRender train
manifest is 16 voxels: an 8/8 vehicle must render 128 voxels long. Width and height stay.

Each output voxel takes one of an input pair (2k, 2k+1). If both are filled with different
colours, the colour that is rarer in a reference model wins, so one-voxel details (door seams,
window pillars, lamps, stripes) survive. Lit and dark variants of one model must be squashed
with the same reference (their dark body) so the lamp overlay stays a pure lamp diff.
"""

from __future__ import annotations

import numpy as np

from puenktlich.voxel.vox import VoxelGrid

FACTOR = 2


def colour_counts(ref: VoxelGrid) -> np.ndarray:
    """Per palette index: how often it occurs in `ref` (empty = never preferred)."""
    counts = np.bincount(ref.data.ravel(), minlength=256).astype(float)
    counts[0] = np.inf
    return counts


def squash_x(grid: VoxelGrid, counts: np.ndarray | None = None, centre: bool = True) -> VoxelGrid:
    """Halve `grid` along x. centre=True keeps the canvas size and the model centred on it
    (vehicles); centre=False returns a grid half as long from the same origin (cargo shapes)."""
    d = grid.data
    if counts is None:
        counts = colour_counts(grid)
    if d.shape[0] % FACTOR:
        d = np.concatenate([d, np.zeros((1, *d.shape[1:]), dtype=d.dtype)])
    a, b = d[0::FACTOR], d[1::FACTOR]
    out = np.where(counts[b] < counts[a], b, a).astype(np.uint8)
    if not centre:
        return VoxelGrid(np.ascontiguousarray(out))
    full = np.zeros_like(grid.data)
    off = grid.data.shape[0] // (2 * FACTOR)
    full[off : off + out.shape[0]] = out[: full.shape[0] - off]
    return VoxelGrid(full)


# --- widening (calibrated to aBase / original-TTD proportions) ------------------------------
# Timberwolf's proportions render a 40-voxel body 7 px wide at 1x (end-on view); aBase draws
# its wagons about 11.5 px wide at the same length and height. Bodies are therefore widened
# 1.5x onto a 64-voxel-wide render canvas, while the running gear below the body (wheels,
# bogie frames, buffers) keeps its gauge so trains still sit on the rails.
AUTHOR_WIDTH = 42
RENDER_WIDTH = 64
WIDEN = 1.5
BODY_ROW_MIN = 30  # a row (x, z) at least this many voxels across belongs to the body


def body_split(grid: VoxelGrid) -> np.ndarray:
    """Per x: the lowest z whose row is body-wide. Rows from there up are widened; the
    running gear below keeps its width. No body in a column -> nothing widened there."""
    occ = grid.data != 0
    sy = occ.shape[1]
    has = occ.any(axis=1)
    first = np.argmax(occ, axis=1)
    last = sy - 1 - np.argmax(occ[:, ::-1, :], axis=1)
    wide = has & (last - first + 1 >= BODY_ROW_MIN)  # (x, z)
    return np.where(wide.any(axis=1), np.argmax(wide, axis=1), occ.shape[2])


def widen_y(
    grid: VoxelGrid, split: np.ndarray | None = None, full: bool = False, render_width: int = RENDER_WIDTH
) -> VoxelGrid:
    """Widen `grid` (authoring width) for rendering. Vehicles: onto RENDER_WIDTH, centred,
    rows from `split` (default: body_split of this grid) up stretched by WIDEN, the rest
    only re-centred. full=True (cargo shapes): stretch everything to round(width * WIDEN)."""
    d = grid.data
    sx, sy, sz = d.shape
    if full:
        ny = int(round(sy * WIDEN))
        src = np.floor((sy - 1) / 2 + (np.arange(ny) - (ny - 1) / 2) / WIDEN + 0.5).astype(int)
        ok = (src >= 0) & (src < sy)
        out = d[:, np.clip(src, 0, sy - 1), :] * ok[None, :, None]
        return VoxelGrid(np.ascontiguousarray(out.astype(np.uint8)))
    if split is None:
        split = body_split(grid)
    c, nc = (sy - 1) / 2, (render_width - 1) / 2
    ny = np.arange(render_width)
    s_src = np.floor(c + (ny - nc) / WIDEN + 0.5).astype(int)
    s_ok = (s_src >= 0) & (s_src < sy)
    k_src = (ny - int(round(nc - c))).astype(int)
    k_ok = (k_src >= 0) & (k_src < sy)
    stretched = d[:, np.clip(s_src, 0, sy - 1), :] * s_ok[None, :, None]
    kept = d[:, np.clip(k_src, 0, sy - 1), :] * k_ok[None, :, None]
    rows = np.arange(sz)[None, :] >= split[:, None]  # (x, z)
    out = np.where(rows[:, None, :], stretched, kept)
    return VoxelGrid(np.ascontiguousarray(out.astype(np.uint8)))


def for_render(grid: VoxelGrid, counts: np.ndarray, split: np.ndarray | None = None) -> VoxelGrid:
    """Authoring grid -> render grid: half length (squash_x), widened body (widen_y)."""
    return widen_y(squash_x(grid, counts), split)


# --- road vehicles ---------------------------------------------------------------------------
# aBase's buses are ~1.6x wider (end-on) and ~1.3x taller than a bus on Timberwolf's road
# canvas (widening alone adds some height in the 30° view); road models are widened and
# raised as a whole (no rails to keep a gauge for).
ROAD_RENDER = (126, 60, 64)
ROAD_WIDEN, ROAD_RAISE = 1.5, 1.15


def stretch_z(grid: VoxelGrid, factor: float, new_z: int) -> VoxelGrid:
    """Stretch upwards from z = 0 (the ground) by `factor` onto `new_z` levels (nearest)."""
    d = grid.data
    src = np.floor(np.arange(new_z) / factor).astype(int)
    ok = src < d.shape[2]
    out = d[:, :, np.clip(src, 0, d.shape[2] - 1)] * ok[None, None, :]
    return VoxelGrid(np.ascontiguousarray(out.astype(np.uint8)))


def for_road_render(grid: VoxelGrid) -> VoxelGrid:
    """Road authoring grid (126x40x48) -> render grid (126x60x64)."""
    split = np.zeros(grid.data.shape[0], dtype=int)  # widen every row
    wide = widen_y(grid, split, render_width=ROAD_RENDER[1])
    return stretch_z(wide, ROAD_RAISE, ROAD_RENDER[2])
