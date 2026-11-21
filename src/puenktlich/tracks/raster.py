"""Procedural track sprites for the companion track GRF (metre gauge).

Everything is drawn in OpenTTD world coordinates and projected exactly like the game:

    tile = 16 x 16 units, one height level = 8 units
    screen (normal zoom):  sx = (y - x) * 2,   sy = (x + y) - z
    north corner of the tile = (0, 0); x grows to the SW, y to the SE

so a sprite's offset is simply the minimum of its projected bounding box (the game draws
ground sprites at the tile's north corner). Polygons are clipped to the tile square, so
neighbouring tiles join seamlessly; they are rendered supersampled and box-filtered.

Railtype sprite order (OpenTTD RailTrackOffset): X, Y, N, S, E, W, slope NE/SE/SW/NW,
then (underlay only) crossing X+Y and the 3-way junctions SW, NE, SE, NW and all six.

OpenTTD draws single pieces, slopes and the X/Y crossing from the *underlay alone* ("no
track overlay is necessary"), so those underlay sprites include the rails; only junction
tiles draw ballast-only underlays plus one `track_overlay` rail sprite per track bit.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

TILE = 16.0
LEVEL = 8.0
SUPERSAMPLE = 4

Vec = tuple[float, float]

# centre lines of the six track pieces, (start, end) in tile coordinates
PIECES: dict[str, tuple[Vec, Vec]] = {
    "X": ((0, 8), (16, 8)),
    "Y": ((8, 0), (8, 16)),
    "N": ((0, 8), (8, 0)),
    "S": ((16, 8), (8, 16)),
    "E": ((0, 8), (8, 16)),
    "W": ((8, 0), (16, 8)),
}
# slope pieces: (piece, height function z(x, y)) — "NE" = north-east side raised, etc.
SLOPES: dict[str, tuple[str, Callable[[float, float], float]]] = {
    "SLOPE_NE": ("X", lambda x, y: LEVEL * (1 - x / TILE)),
    "SLOPE_SE": ("Y", lambda x, y: LEVEL * (y / TILE)),
    "SLOPE_SW": ("X", lambda x, y: LEVEL * (x / TILE)),
    "SLOPE_NW": ("Y", lambda x, y: LEVEL * (1 - y / TILE)),
}
OVERLAY_ORDER = ["X", "Y", "N", "S", "E", "W", "SLOPE_NE", "SLOPE_SE", "SLOPE_SW", "SLOPE_NW"]
UNDERLAY_ORDER = OVERLAY_ORDER + ["CROSS", "JUNCTION_SW", "JUNCTION_NE", "JUNCTION_SE", "JUNCTION_NW", "JUNCTION_ALL"]
COMBOS = {
    "CROSS": ["X", "Y"],
    "JUNCTION_SW": ["X", "S", "W"],  # every piece touching the SW edge
    "JUNCTION_NE": ["X", "N", "E"],
    "JUNCTION_SE": ["Y", "S", "E"],
    "JUNCTION_NW": ["Y", "N", "W"],
    "JUNCTION_ALL": ["X", "Y", "N", "S", "E", "W"],
}


@dataclass(frozen=True)
class TrackStyle:
    half_gauge: float  # world units from centre line to each rail
    ballast_half_width: float
    sleeper_half_length: float
    sleeper_width: float = 0.4
    sleeper_pitch: float = 1.1
    rail_width: float = 0.4  # thin rails vanish at 1x: keep >= ~0.35 units
    ballast: tuple[int, int, int] = (98, 90, 80)
    ballast_edge: tuple[int, int, int] = (74, 68, 60)
    sleeper: tuple[int, int, int] = (64, 50, 38)
    rail_top: tuple[int, int, int] = (200, 200, 206)
    rail_side: tuple[int, int, int] = (44, 40, 40)


# Standard OpenTTD rails sit ~1.53 units apart (≈ 26 voxels at our vehicle scale);
# metre gauge is 1000/1435 of that.
STANDARD_HALF_GAUGE = 0.765
METRE_GAUGE = TrackStyle(
    half_gauge=STANDARD_HALF_GAUGE * 1000 / 1435,
    ballast_half_width=1.45,
    sleeper_half_length=0.95,
)


@dataclass
class Sprite:
    image: Image.Image  # RGBA
    xofs: int
    yofs: int


def _project(x: float, y: float, z: float) -> Vec:
    return (y - x) * 2.0, (x + y) - z


def _clip(poly: list[Vec], lo: float = 0.0, hi: float = TILE) -> list[Vec]:
    """Sutherland–Hodgman clip of a polygon (tile coordinates) to the tile square."""

    def clip_edge(pts, inside, intersect):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(intersect(prev, cur))
        return out

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    for axis in (0, 1):
        for bound, keep in ((lo, lambda v, b: v >= b), (hi, lambda v, b: v <= b)):
            if not poly:
                return poly
            poly = clip_edge(
                poly,
                lambda p, a=axis, b=bound, k=keep: k(p[a], b),
                lambda p, q, a=axis, b=bound: lerp(p, q, (b - p[a]) / (q[a] - p[a])),
            )
    return poly


def _strip(a: Vec, b: Vec, offset: float, half_width: float, extend: float = 2.0) -> list[Vec]:
    """Rectangle along a->b, shifted sideways by `offset`, extended past both ends."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    a2 = (a[0] - ux * extend + nx * offset, a[1] - uy * extend + ny * offset)
    b2 = (b[0] + ux * extend + nx * offset, b[1] + uy * extend + ny * offset)
    return [
        (a2[0] + nx * half_width, a2[1] + ny * half_width),
        (b2[0] + nx * half_width, b2[1] + ny * half_width),
        (b2[0] - nx * half_width, b2[1] - ny * half_width),
        (a2[0] - nx * half_width, a2[1] - ny * half_width),
    ]


def _sleepers(a: Vec, b: Vec, style: TrackStyle) -> list[list[Vec]]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    n = int(L / style.sleeper_pitch)
    rects = []
    for i in range(n + 1):
        t = (i + 0.5) * L / (n + 1)
        c = (a[0] + ux * t, a[1] + uy * t)
        nx, ny = -uy, ux
        hw, hl = style.sleeper_width / 2, style.sleeper_half_length
        rects.append(
            [
                (c[0] - ux * hw + nx * hl, c[1] - uy * hw + ny * hl),
                (c[0] + ux * hw + nx * hl, c[1] + uy * hw + ny * hl),
                (c[0] + ux * hw - nx * hl, c[1] + uy * hw - ny * hl),
                (c[0] - ux * hw - nx * hl, c[1] - uy * hw - ny * hl),
            ]
        )
    return rects


Layer = list[tuple[list[Vec], tuple[int, int, int]]]  # (tile-coordinate polygon, colour)


def underlay_layers(pieces: list[str], style: TrackStyle) -> Layer:
    layers: Layer = []
    for p in pieces:  # ballast first, then all sleepers on top
        a, b = PIECES[p]
        layers.append((_strip(a, b, 0, style.ballast_half_width + 0.25), style.ballast_edge))
        layers.append((_strip(a, b, 0, style.ballast_half_width), style.ballast))
    for p in pieces:
        a, b = PIECES[p]
        layers += [(r, style.sleeper) for r in _sleepers(a, b, style)]
    return layers


def overlay_layers(pieces: list[str], style: TrackStyle) -> Layer:
    layers: Layer = []
    for p in pieces:
        a, b = PIECES[p]
        for side in (-1, 1):
            off = side * style.half_gauge
            # dark rail body, light running surface on top (slightly towards the viewer)
            layers.append((_strip(a, b, off, style.rail_width / 2), style.rail_side))
            layers.append((_strip(a, b, off - style.rail_width * 0.15, style.rail_width * 0.28), style.rail_top))
    return layers


def rasterise(layers: Layer, z: Callable[[float, float], float], zoom: int) -> Sprite:
    """Clip, project and draw polygons; returns an RGBA sprite with game offsets."""
    polys = []
    for poly, colour in layers:
        clipped = _clip(poly)
        if len(clipped) >= 3:
            polys.append(([_project(x, y, z(x, y)) for x, y in clipped], colour))
    if not polys:
        return Sprite(Image.new("RGBA", (1, 1)), 0, 0)
    xs = [p[0] for pts, _ in polys for p in pts]
    ys = [p[1] for pts, _ in polys for p in pts]
    x0, y0 = math.floor(min(xs) * zoom), math.floor(min(ys) * zoom)
    x1, y1 = math.ceil(max(xs) * zoom), math.ceil(max(ys) * zoom)
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    s = SUPERSAMPLE
    big = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    for pts, colour in polys:
        draw.polygon([((px * zoom - x0) * s, (py * zoom - y0) * s) for px, py in pts], fill=(*colour, 255))
    img = big.resize((w, h), Image.Resampling.BOX)
    return Sprite(img, x0, y0)


def flat(x: float, y: float) -> float:
    return 0.0


def track_sprites(style: TrackStyle, zoom: int) -> dict[str, list[Sprite]]:
    """{"underlay": 16 sprites, "track_overlay": 10 sprites} in OpenTTD order."""

    def pieces_and_z(name: str):
        if name in SLOPES:
            piece, zf = SLOPES[name]
            return [piece], zf
        return COMBOS.get(name, [name]), flat

    out: dict[str, list[Sprite]] = {"underlay": [], "track_overlay": []}
    for name in UNDERLAY_ORDER:
        pieces, zf = pieces_and_z(name)
        layers = underlay_layers(pieces, style)
        if not name.startswith("JUNCTION"):  # drawn without overlay: include the rails
            layers += overlay_layers(pieces, style)
        out["underlay"].append(rasterise(layers, zf, zoom))
    for name in OVERLAY_ORDER:
        pieces, zf = pieces_and_z(name)
        out["track_overlay"].append(rasterise(overlay_layers(pieces, style), zf, zoom))
    return out


def quantise(img: Image.Image, palette: list[tuple[int, int, int]], allowed: np.ndarray) -> Image.Image:
    """8bpp version: nearest allowed TTD palette index, alpha < 128 -> index 0 (transparent)."""
    a = np.array(img.convert("RGBA")).astype(np.int32)
    pal = np.array(palette, dtype=np.int32)[allowed]
    rgb = a[..., :3].reshape(-1, 1, 3)
    idx = allowed[np.argmin(((rgb - pal[None]) ** 2).sum(axis=2), axis=1)].reshape(a.shape[:2])
    idx[a[..., 3] < 128] = 0
    out = Image.fromarray(idx.astype(np.uint8), "P")
    out.putpalette([c for rgb_ in palette for c in rgb_])
    return out
