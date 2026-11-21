"""Metre-gauge infrastructure sprites: level crossings, bridges, tunnels, depots, GUI icons.

How OpenTTD draws each group was read from its source (master, 2026-11):

level_crossings (road_cmd.cpp DrawTile_Road, Crossing)
    0/1  rail over the road for rail axis X/Y: DrawGroundSprite on top of the base road
    2..9 corner posts via DrawRailTileSeq(_crossing_layout, base = crossing + axis):
         sprite 2/4/6/8 (+ axis) at tile offsets (0,0) (0,13) (13,0) (13,13), box 3x3x20.
         So each pair is the same post for rail axis X and Y. The base set blinks its lamps
         with animated palette colours; ours are drawn as plain dark-red lamps.
bridge_surfaces (tunnelbridge_cmd.cpp)
    0/1  deck track X/Y (middle tiles at bridge height, flat ramp heads on foundations)
    2..5 sloped ramp heads, by bridge direction NE, SE, SW, NW (= the track slope order)
tunnels / tunnel_overlay (tunnelbridge_cmd.cpp DrawTile_TunnelBridge)
    tunnels: ground sprite per tunnel direction NE, SE, SW, NW. A tunnel_overlay group
    switches the base to SPR_RAILTYPE_TUNNEL_BASE (portal without standard rails); ours is
    4 transparent sprites, so only the narrow track shows.
depots (rail_cmd.cpp, table/track_land.h _depot_gfx_*; relocation from SPR_RAIL_DEPOT_SE_1)
    0 SE-exit back walls (2,2) 1x13   1 SE-exit front: SW wall + roof (13,2) 1x13
    2 SW-exit back walls (2,2) 13x1   3 SW-exit front: SE wall + roof (2,13) 13x1
    4 NE-exit whole shed (2,13)       5 NW-exit whole shed (13,2)
    Each sprite is placed at its own tile offset, so it is drawn relative to that origin.
    SE/SW depots show our underlay track in front; NE/NW depots stand on grass.
gui (rail_gui.cpp ResolveRailTypeGUISprites)
    toolbar: NS, X, EW, Y, autorail, depot, tunnel, convert; then the 8 cursors, same order.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from puenktlich.tracks.raster import (
    SLOPES,
    TILE,
    Poly3D,
    Sprite,
    TrackStyle,
    flat,
    overlay_layers,
    rasterise,
    rasterise3d,
    underlay_layers,
)

WALL_HEIGHT = 9.0
RIDGE_HEIGHT = 14.5
PLASTER_SW = (222, 204, 168)  # wall faces towards the SW (lit)
PLASTER_SE = (186, 168, 136)  # wall faces towards the SE (shade)
PLASTER_TOP = (204, 188, 154)
PLINTH_SW = (150, 146, 140)
PLINTH_SE = (118, 114, 110)
ROOF_LIT = (156, 76, 56)
ROOF_SHADE = (116, 54, 42)
INSIDE = (40, 36, 34)
WINDOW = (52, 58, 70)
POST = (120, 120, 124)
SIGN_WHITE = (236, 236, 236)
SIGN_RED = (176, 32, 32)
LAMP = (150, 20, 20)


# --- level crossings --------------------------------------------------------------------


def crossing_sprites(style: TrackStyle, zoom: int) -> list[Sprite]:
    out = [rasterise(overlay_layers([axis], style), flat, zoom) for axis in ("X", "Y")]
    for _corner in range(4):
        for axis in ("X", "Y"):
            out.append(rasterise3d(_crossing_post(axis), zoom))
    return out


def _box(x0, x1, y0, y1, z0, z1, top, sw, se) -> Poly3D:
    """Visible faces of an axis-aligned box: SE face (+y), SW face (+x), top."""
    return [
        ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], se),
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], sw),
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top),
    ]


def _crossing_post(rail_axis: str) -> Poly3D:
    """Post with a white/red sign plate and two lamps, in its own 3x3 box (origin 0,0)."""
    c = 1.5
    polys = _box(c - 0.25, c + 0.25, c - 0.25, c + 0.25, 0, 9, POST, POST, POST)
    # the plate faces along the road, i.e. across the rail axis
    if rail_axis == "X":  # road along Y: plate in the x/z plane
        plate = _box(c - 1.2, c + 1.2, c - 0.1, c + 0.1, 7.5, 10.5, SIGN_WHITE, SIGN_WHITE, SIGN_WHITE)
        lamps = _box(c - 1.0, c - 0.4, c + 0.1, c + 0.35, 6, 7.2, LAMP, LAMP, LAMP)
        lamps += _box(c + 0.4, c + 1.0, c + 0.1, c + 0.35, 6, 7.2, LAMP, LAMP, LAMP)
    else:  # road along X: plate in the y/z plane
        plate = _box(c - 0.1, c + 0.1, c - 1.2, c + 1.2, 7.5, 10.5, SIGN_WHITE, SIGN_WHITE, SIGN_WHITE)
        lamps = _box(c + 0.1, c + 0.35, c - 1.0, c - 0.4, 6, 7.2, LAMP, LAMP, LAMP)
        lamps += _box(c + 0.1, c + 0.35, c + 0.4, c + 1.0, 6, 7.2, LAMP, LAMP, LAMP)
    border = [(pts, SIGN_RED) for pts, _ in plate]
    inner = []
    for pts, _ in plate:  # slightly smaller white panel on top of the red border
        cx = sum(p[0] for p in pts) / 4
        cy = sum(p[1] for p in pts) / 4
        cz = sum(p[2] for p in pts) / 4
        inner.append(([(cx + (x - cx) * 0.7, cy + (y - cy) * 0.7, cz + (z - cz) * 0.7) for x, y, z in pts], SIGN_WHITE))
    return polys + border + inner + lamps


# --- bridges and tunnels ----------------------------------------------------------------


def bridge_sprites(style: TrackStyle, zoom: int) -> list[Sprite]:
    """Sleepers and rails only: the bridge deck itself comes from the bridge graphics."""

    def deck(pieces, zf):
        layers = [ly for ly in underlay_layers(pieces, style) if ly[1] == style.sleeper]
        return rasterise(layers + overlay_layers(pieces, style), zf, zoom)

    out = [deck(["X"], flat), deck(["Y"], flat)]
    for name in ("SLOPE_NE", "SLOPE_SE", "SLOPE_SW", "SLOPE_NW"):
        piece, zf = SLOPES[name]
        out.append(deck([piece], zf))
    return out


def tunnel_sprites(style: TrackStyle, zoom: int) -> list[Sprite]:
    """Ballast + rails into the portal, per tunnel direction NE, SE, SW, NW."""
    out = []
    for axis in ("X", "Y", "X", "Y"):
        out.append(rasterise(underlay_layers([axis], style) + overlay_layers([axis], style), flat, zoom))
    return out


STONE = (138, 132, 122)
STONE_TOP = (160, 154, 144)
PORTAL_DARK = (16, 14, 14)


def tunnel_portal_sprites(zoom: int) -> list[Sprite]:
    """Portal arches, per tunnel direction NE, SE, SW, NW. Providing this group makes OpenTTD
    draw a blank (rail-less) tunnel base. The game anchors these sprites at the tile's
    south corner (roof_bounds origin + offset = 15, 15), so geometry is shifted by -15.
    Portals of NE/NW tunnels face the viewer; SE/SW portals face away and stay hidden by
    the hillside, so those sprites are empty."""

    def portal(axis: str) -> Sprite:
        at = 3.0
        if axis == "x":  # NE tunnel: face at x = at, normal +x (towards the viewer)
            polys = _box(at - 0.8, at, 2.5, 13.5, 0, 10.5, STONE_TOP, STONE, STONE)
            hole = [([(at + 0.01, y, z) for y, z in pts], PORTAL_DARK) for pts in [_arch_pts(5.2, 10.8, 0, 5.2)]]
        else:  # NW tunnel: face at y = at, normal +y
            polys = _box(2.5, 13.5, at - 0.8, at, 0, 10.5, STONE_TOP, STONE, STONE)
            hole = [([(x, at + 0.01, z) for x, z in pts], PORTAL_DARK) for pts in [_arch_pts(5.2, 10.8, 0, 5.2)]]
        return rasterise3d(_shift(polys + hole, 15, 15), zoom)

    empty = Sprite(Image.new("RGBA", (1, 1)), 0, 0)
    return [portal("x"), empty, empty, portal("y")]


def _arch_pts(lo: float, hi: float, base: float, spring: float, steps: int = 12) -> list[tuple[float, float]]:
    import math

    mid, r = (lo + hi) / 2, (hi - lo) / 2
    pts = [(lo, base), (lo, spring)]
    pts += [
        (mid - r * math.cos(math.pi * i / steps), spring + r * math.sin(math.pi * i / steps)) for i in range(1, steps)
    ]
    pts += [(hi, spring), (hi, base)]
    return pts


# --- depots -----------------------------------------------------------------------------


def _walls_box(x0, x1, y0, y1) -> Poly3D:
    """Wall segment with a stone plinth."""
    return _box(x0, x1, y0, y1, 0, 2, PLINTH_SW, PLINTH_SW, PLINTH_SE) + _box(
        x0, x1, y0, y1, 2, WALL_HEIGHT, PLASTER_TOP, PLASTER_SW, PLASTER_SE
    )


def _roof(axis: str) -> Poly3D:
    """Pitched roof over x,y in [1.5, 14.5], ridge along the track axis, plus gables."""
    lo, hi, mid = 1.5, 14.5, 8.0
    w, r = WALL_HEIGHT, RIDGE_HEIGHT
    if axis == "Y":  # ridge along y at x = mid; planes fall towards NE (x=lo) and SW (x=hi)
        return [
            ([(lo, lo, w), (mid, lo, r), (mid, hi, r), (lo, hi, w)], ROOF_SHADE),
            ([(hi, lo, w), (mid, lo, r), (mid, hi, r), (hi, hi, w)], ROOF_LIT),
            ([(2.0, 14.0, w), (14.0, 14.0, w), (mid, 14.0, r - 0.5)], PLASTER_SE),  # SE gable
        ]
    return [  # ridge along x at y = mid
        ([(lo, lo, w), (lo, mid, r), (hi, mid, r), (hi, lo, w)], ROOF_SHADE),
        ([(lo, hi, w), (lo, mid, r), (hi, mid, r), (hi, hi, w)], ROOF_LIT),
        ([(14.0, 2.0, w), (14.0, 14.0, w), (14.0, mid, r - 0.5)], PLASTER_SW),  # SW gable
    ]


def _windows(axis: str) -> Poly3D:
    """Two small windows on the long outer wall facing the viewer."""
    out = []
    for a in (4.5, 9.5):
        if axis == "Y":  # long walls along y; SW wall outer face at x = 14
            out.append(([(14.01, a, 4.5), (14.01, a + 2, 4.5), (14.01, a + 2, 7.5), (14.01, a, 7.5)], WINDOW))
        else:  # long walls along x; SE wall outer face at y = 14
            out.append(([(a, 14.01, 4.5), (a + 2, 14.01, 4.5), (a + 2, 14.01, 7.5), (a, 14.01, 7.5)], WINDOW))
    return out


def _shift(polys: Poly3D, dx: float, dy: float) -> Poly3D:
    return [([(x - dx, y - dy, z) for x, y, z in pts], c) for pts, c in polys]


def depot_sprites(zoom: int) -> list[Sprite]:
    # SE exit: track along Y, door at y = 14 (towards the viewer, right)
    se_back = (
        _walls_box(2, 14, 2, 3)
        + _walls_box(2, 3, 2, 14)
        + [
            ([(3, 3, 0), (13, 3, 0), (13, 3, WALL_HEIGHT), (3, 3, WALL_HEIGHT)], INSIDE),  # dark interior
        ]
    )
    se_front = (
        _walls_box(13, 14, 2, 14)
        + _windows("Y")
        + _roof("Y")
        + [
            ([(2, 14, 6.5), (13, 14, 6.5), (13, 14, WALL_HEIGHT), (2, 14, WALL_HEIGHT)], PLASTER_SE),  # lintel
        ]
    )
    # SW exit: track along X, door at x = 14 (towards the viewer, left)
    sw_back = (
        _walls_box(2, 3, 2, 14)
        + _walls_box(2, 14, 2, 3)
        + [
            ([(3, 3, 0), (3, 13, 0), (3, 13, WALL_HEIGHT), (3, 3, WALL_HEIGHT)], INSIDE),
        ]
    )
    sw_front = (
        _walls_box(2, 14, 13, 14)
        + _windows("X")
        + _roof("X")
        + [
            ([(14, 2, 6.5), (14, 13, 6.5), (14, 13, WALL_HEIGHT), (14, 2, WALL_HEIGHT)], PLASTER_SW),
        ]
    )
    # NE / NW exit: door faces away from the viewer; the whole closed shed is one sprite
    ne_whole = _walls_box(2, 14, 13, 14) + _walls_box(13, 14, 2, 14) + _windows("X") + _roof("X")
    nw_whole = _walls_box(13, 14, 2, 14) + _walls_box(2, 14, 13, 14) + _windows("Y") + _roof("Y")
    parts = [
        (se_back, 2, 2),
        (se_front, 13, 2),
        (sw_back, 2, 2),
        (sw_front, 2, 13),
        (ne_whole, 2, 13),
        (nw_whole, 13, 2),
    ]
    return [rasterise3d(_shift(polys, dx, dy), zoom) for polys, dx, dy in parts]


# --- GUI ----------------------------------------------------------------------------------


def _fit(sprite: Sprite, size: int) -> Image.Image:
    img = sprite.image
    k = min(size / img.width, size / img.height)
    small = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size))
    canvas.alpha_composite(small, ((size - small.width) // 2, (size - small.height) // 2))
    return canvas


def gui_sprites(style: TrackStyle, zoom: int) -> list[Sprite]:
    """8 toolbar icons + the same 8 as cursors, `20 * zoom` px square."""
    size = 20 * zoom

    def piece(name: str) -> Image.Image:
        return _fit(rasterise(underlay_layers([name], style) + overlay_layers([name], style), flat, 4), size)

    def badge(img: Image.Image, kind: str) -> Image.Image:
        img = img.copy()
        d = ImageDraw.Draw(img)
        s = size / 20
        if kind == "auto":
            d.polygon([(13 * s, 2 * s), (19 * s, 2 * s), (19 * s, 8 * s)], fill=(250, 230, 60, 255))
        elif kind == "tunnel":
            d.pieslice([4 * s, 2 * s, 16 * s, 16 * s], 180, 360, fill=(70, 60, 50, 255))
            d.rectangle([4 * s, 9 * s, 16 * s, 16 * s], fill=(70, 60, 50, 255))
            d.pieslice([6.5 * s, 5 * s, 13.5 * s, 14 * s], 180, 360, fill=(10, 10, 10, 255))
            d.rectangle([6.5 * s, 9.5 * s, 13.5 * s, 16 * s], fill=(10, 10, 10, 255))
        elif kind == "convert":
            d.arc([3 * s, 3 * s, 17 * s, 17 * s], 200, 340, fill=(250, 230, 60, 255), width=max(1, round(2 * s)))
            d.polygon([(15 * s, 4 * s), (19 * s, 7 * s), (14 * s, 8 * s)], fill=(250, 230, 60, 255))
        return img

    depot = _fit(depot_sprites(4)[1], size)  # SE-exit front part as the depot icon
    icons = [
        piece("N"),
        piece("X"),
        piece("E"),
        piece("Y"),
        badge(piece("X"), "auto"),
        depot,
        badge(piece("Y"), "tunnel"),
        badge(piece("X"), "convert"),
    ]
    return [Sprite(img, 0, 0) for img in icons] * 2  # toolbar, then cursors


def infra_sprites(style: TrackStyle, zoom: int) -> dict[str, list[Sprite]]:
    return {
        "level_crossings": crossing_sprites(style, zoom),
        "bridge_surfaces": bridge_sprites(style, zoom),
        "tunnels": tunnel_sprites(style, zoom),
        "tunnel_overlay": tunnel_portal_sprites(zoom),  # portal arches (NE, NW visible)
        "depots": depot_sprites(zoom),
        "gui": gui_sprites(style, zoom),
    }


__all__ = ["infra_sprites", "TILE"]
