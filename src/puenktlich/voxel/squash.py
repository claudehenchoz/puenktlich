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


# --- true width (docs/SCALE.md) --------------------------------------------------------------
# Train bodies are authored 40 voxels wide (36 on metre gauge), wider than their real width at
# the height scale (~12.2 voxels per metre). The render step rescales each body to its real
# width (the recipe's BODY_WIDTH_M) on a 64-voxel-wide render canvas, while the running gear
# below the body (wheels, bogie frames, buffers) keeps its gauge so trains sit on the rails.
AUTHOR_WIDTH = 42
RENDER_WIDTH = 64
BODY_ROW_MIN = 30  # a row (x, z) at least this many voxels across belongs to the body
Z_PER_M = 12.2  # height scale of the train models (most REFERENCE.md files); recipes can override


def body_split(grid: VoxelGrid) -> np.ndarray:
    """Per x: the lowest z whose row is body-wide. Rows from there up are rescaled; the
    running gear below keeps its width. No body in a column -> nothing rescaled there."""
    occ = grid.data != 0
    sy = occ.shape[1]
    has = occ.any(axis=1)
    first = np.argmax(occ, axis=1)
    last = sy - 1 - np.argmax(occ[:, ::-1, :], axis=1)
    wide = has & (last - first + 1 >= BODY_ROW_MIN)  # (x, z)
    return np.where(wide.any(axis=1), np.argmax(wide, axis=1), occ.shape[2])


def authored_body_width(grid: VoxelGrid) -> int:
    """The body width a model is authored at: the widest row width among body-wide rows that
    occurs at least a fifth as often as the most common one. Rounded roofs and tumblehome make
    many rows narrower; mirrors or steps that stick out over a few rows don't count."""
    occ = grid.data != 0
    sy = occ.shape[1]
    has = occ.any(axis=1)
    first = np.argmax(occ, axis=1)
    last = sy - 1 - np.argmax(occ[:, ::-1, :], axis=1)
    width = np.where(has, last - first + 1, 0)
    width = width[width >= BODY_ROW_MIN]
    if not width.size:
        return 0
    counts = np.bincount(width)
    return int(np.flatnonzero(counts >= counts.max() / 5).max())


def true_width_factor(authored: int, width_m: float | None, z_per_m: float = Z_PER_M) -> float:
    """Factor that renders a body authored `authored` voxels wide at its real width `width_m`,
    on the same scale as the height (`z_per_m`), rounded to an even voxel count so the body
    stays symmetric about the centre line. No real width given: authored width kept."""
    if not width_m or not authored:
        return 1.0
    return 2 * round(width_m * z_per_m / 2) / authored


def _narrow_y(d: np.ndarray, factor: float, counts: np.ndarray, width: int) -> np.ndarray:
    """Narrow every row onto `width` (factor <= 1), centred. Each source row lands on exactly
    one output row, symmetrically about the centre line; where two land on the same one, the
    colour that is rarer in `counts` wins, so one-voxel details (pillars, lamps) survive."""
    sx, sy, sz = d.shape
    c, nc = (sy - 1) / 2, (width - 1) / 2
    out = np.zeros((sx, width, sz), dtype=np.uint8)
    rank = np.full((sx, width, sz), np.inf)
    for k in range(sy):
        off = (k - c) * factor
        j = int(round(nc + np.sign(off) * (np.floor(abs(off)) + 0.5))) if off else int(round(nc))
        if not 0 <= j < width:
            continue
        r = counts[d[:, k, :]]
        better = r < rank[:, j, :]
        out[:, j, :] = np.where(better, d[:, k, :], out[:, j, :])
        rank[:, j, :] = np.where(better, r, rank[:, j, :])
    return out


def widen_y(
    grid: VoxelGrid,
    split: np.ndarray | None = None,
    full: bool = False,
    render_width: int = RENDER_WIDTH,
    factor: float = 1.0,
    counts: np.ndarray | None = None,
) -> VoxelGrid:
    """Rescale `grid` across (y) for rendering. Vehicles: onto `render_width`, centred, rows
    from `split` (default: body_split of this grid) up scaled by `factor`, the rest (running
    gear) only re-centred. factor < 1 narrows with rarer-colour merging (`counts`, default
    this grid's). full=True (cargo shapes): scale everything to round(width * factor)."""
    d = grid.data
    sx, sy, sz = d.shape
    if full:
        ny = int(round(sy * factor))
        src = np.floor((sy - 1) / 2 + (np.arange(ny) - (ny - 1) / 2) / factor + 0.5).astype(int)
        ok = (src >= 0) & (src < sy)
        out = d[:, np.clip(src, 0, sy - 1), :] * ok[None, :, None]
        return VoxelGrid(np.ascontiguousarray(out.astype(np.uint8)))
    if split is None:
        split = body_split(grid)
    c, nc = (sy - 1) / 2, (render_width - 1) / 2
    ny = np.arange(render_width)
    if factor < 1:
        scaled = _narrow_y(d, factor, colour_counts(grid) if counts is None else counts, render_width)
    else:
        s_src = np.floor(c + (ny - nc) / factor + 0.5).astype(int)
        s_ok = (s_src >= 0) & (s_src < sy)
        scaled = d[:, np.clip(s_src, 0, sy - 1), :] * s_ok[None, :, None]
    k_src = (ny - int(round(nc - c))).astype(int)
    k_ok = (k_src >= 0) & (k_src < sy)
    kept = d[:, np.clip(k_src, 0, sy - 1), :] * k_ok[None, :, None]
    rows = np.arange(sz)[None, :] >= split[:, None]  # (x, z)
    out = np.where(rows[:, None, :], scaled, kept)
    return VoxelGrid(np.ascontiguousarray(out.astype(np.uint8)))


# --- road vehicles ---------------------------------------------------------------------------
# Road models are rescaled across as a whole (no rails to keep a gauge for) to their real width,
# like train bodies, and keep their height. The render canvas stays 126 x 60 x 64 (it once held
# buses widened 1.5x and raised 1.15x), so the sprite offsets don't change.
ROAD_RENDER = (126, 60, 64)


def for_road_render(grid: VoxelGrid, factor: float = 1.0, counts: np.ndarray | None = None) -> VoxelGrid:
    """Road authoring grid (126x40x48) -> render grid (126x60x64): every row scaled across by
    `factor` and centred, then padded upwards to the render height (z = 0 stays the road)."""
    split = np.zeros(grid.data.shape[0], dtype=int)  # every row
    d = widen_y(grid, split, render_width=ROAD_RENDER[1], factor=factor, counts=counts).data
    out = np.zeros((*d.shape[:2], ROAD_RENDER[2]), dtype=np.uint8)
    out[:, :, : d.shape[2]] = d[:, :, : ROAD_RENDER[2]]
    return VoxelGrid(out)
