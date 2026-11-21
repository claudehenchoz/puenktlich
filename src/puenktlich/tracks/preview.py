"""Contact sheet of the companion track GRF: track pieces, rack, crossing, bridge, tunnel,
depots (in their real tile positions) and GUI icons, as the game would compose them."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from puenktlich.tracks.infra import infra_sprites
from puenktlich.tracks.raster import METRE_GAUGE, METRE_GAUGE_RACK, Sprite, track_sprites

BG = (88, 112, 72, 255)


def tracks_preview(out: Path, zoom: int = 4) -> Path:
    z = zoom
    tile_w, tile_h = 32 * z, 16 * z  # half sizes of the tile diamond
    infra, plain, rack = (
        infra_sprites(METRE_GAUGE, z),
        track_sprites(METRE_GAUGE, z),
        track_sprites(METRE_GAUGE_RACK, z),
    )
    cols, rows = 6, 3
    sheet = Image.new("RGBA", (cols * 2 * tile_w + 40, rows * (3 * tile_h) + 40), BG)
    draw = ImageDraw.Draw(sheet)

    def cell(i: int) -> tuple[int, int]:
        return 20 + tile_w + (i % cols) * 2 * tile_w, 20 + tile_h + (i // cols) * 3 * tile_h

    def tile(ox: int, oy: int, label: str) -> None:
        draw.polygon(
            [(ox, oy), (ox + tile_w, oy + tile_h), (ox, oy + 2 * tile_h), (ox - tile_w, oy + tile_h)],
            outline=(70, 92, 60, 255),
        )
        draw.text((ox - tile_w + 4, oy + 2 * tile_h + 2), label, fill=(255, 255, 255, 255))

    def put(s: Sprite, ox: int, oy: int, dx: float = 0, dy: float = 0) -> None:
        px, py = ox + (dy - dx) * 2 * z, oy + (dx + dy) * z  # part origin -> screen
        sheet.alpha_composite(s.image, (int(px + s.xofs), int(py + s.yofs)))

    scenes = [
        ("track X", lambda o: put(plain["underlay"][0], *o)),
        ("track N", lambda o: put(plain["underlay"][2], *o)),
        ("slope NE", lambda o: put(plain["underlay"][6], *o)),
        (
            "junction NE",
            lambda o: [put(plain["underlay"][12], *o)] + [put(plain["track_overlay"][i], *o) for i in (0, 2)],
        ),
        ("rack X", lambda o: put(rack["underlay"][0], *o)),
        ("rack slope SW", lambda o: put(rack["underlay"][8], *o)),
        (
            "crossing",
            lambda o: (
                [put(infra["level_crossings"][0], *o)]
                + [
                    put(infra["level_crossings"][2 + 2 * k], *o, dx, dy)
                    for k, (dx, dy) in enumerate([(0, 0), (0, 13), (13, 0), (13, 13)])
                ]
            ),
        ),
        ("bridge deck X", lambda o: put(infra["bridge_surfaces"][0], *o)),
        ("bridge ramp NE", lambda o: put(infra["bridge_surfaces"][2], *o)),
        ("tunnel track SW", lambda o: put(infra["tunnels"][2], *o)),
        (
            "depot SE exit",
            lambda o: [
                put(plain["underlay"][1], *o),
                put(infra["depots"][0], *o, 2, 2),
                put(infra["depots"][1], *o, 13, 2),
            ],
        ),
        (
            "depot SW exit",
            lambda o: [
                put(plain["underlay"][0], *o),
                put(infra["depots"][2], *o, 2, 2),
                put(infra["depots"][3], *o, 2, 13),
            ],
        ),
        ("depot NE exit", lambda o: put(infra["depots"][4], *o, 2, 13)),
        ("depot NW exit", lambda o: put(infra["depots"][5], *o, 13, 2)),
    ]
    for i, (label, fn) in enumerate(scenes):
        ox, oy = cell(i)
        tile(ox, oy, label)
        fn((ox, oy))
    gx, gy = cell(len(scenes))
    for i, s in enumerate(infra["gui"][:8]):
        sheet.alpha_composite(s.image, (gx - tile_w + i * (s.image.width + 6), gy))
    draw.text((gx - tile_w, gy + infra["gui"][0].image.height + 4), "GUI icons", fill=(255, 255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
