"""Sprite post-processing: lint checks and human/AI review previews."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from puenktlich.render import SCALES, SpriteRect, sheet_path, sprite_layout
from puenktlich.voxel.palette import CC1, CC2, rgb_palette

# Preview company colours when a livery uses the player's colours: red and white.
_DEFAULT_CC1, _DEFAULT_CC2 = "RED", "WHITE"
_BACKGROUND = (88, 112, 72, 255)  # roughly OpenTTD grass


# Approximate start of each TTD company colour's 8-step ramp (preview only; the game uses
# its own recolour tables).
COLOUR_RAMPS = {
    "DARK_BLUE": 198,
    "PALE_GREEN": 96,
    "PINK": 42,
    "YELLOW": 62,
    "RED": 179,
    "LIGHT_BLUE": 154,
    "GREEN": 80,
    "DARK_GREEN": 88,
    "BLUE": 146,
    "CREAM": 112,
    "MAUVE": 128,
    "PURPLE": 136,
    "ORANGE": 185,
    "BROWN": 104,
    "GREY": 4,
    "WHITE": 8,
}


# Colours whose TTD recolour table is not 8 consecutive palette entries. Red runs through the
# dark reds and then into the pale reds (consecutive entries would turn its highlights orange).
# Written from memory of TTD's company-colour table; the game uses its own recolour sprites.
COLOUR_TABLES = {"RED": [179, 180, 181, 182, 183, 164, 165, 166]}


def colour_indices(colour: str) -> list[int]:
    """The 8 palette indices a TTD company colour maps the CC ramp to (preview only)."""
    return COLOUR_TABLES.get(colour) or list(range(COLOUR_RAMPS[colour], COLOUR_RAMPS[colour] + 8))


def _remap_table(cc1: str | None = None, cc2: str | None = None) -> np.ndarray:
    t = np.arange(256, dtype=np.uint8)
    for (lo, hi), colour in ((CC1, cc1 or _DEFAULT_CC1), (CC2, cc2 or _DEFAULT_CC2)):
        t[lo : hi + 1] = colour_indices(colour)
    return t


def composite_cc(
    rgba: Image.Image, mask: Image.Image | None, cc1: str | None = None, cc2: str | None = None
) -> Image.Image:
    """OpenTTD's 32bpp+mask blitter: a masked pixel takes the remapped palette colour, scaled by
    the 32bpp pixel's brightness (its largest channel; 128 = unchanged). Overbright channels
    spill into the others, so highlights turn towards white instead of shifting hue (port of
    ReallyAdjustBrightness in OpenTTD's blitter/32bpp_base.hpp).
    cc1/cc2: TTD colour names (default red/white)."""
    out = np.array(rgba.convert("RGBA")).astype(np.int32)
    if mask is None:
        return rgba
    m = np.array(mask)
    pal = np.array(rgb_palette(), dtype=np.int32)
    remap = _remap_table(cc1, cc2)
    sel = m != 0
    if sel.any():
        bright = out[..., :3].max(axis=2)[sel]
        col = pal[remap[m[sel]]] * bright[:, None] // 128
        over = np.clip(col - 255, 0, None).sum(axis=1, keepdims=True) // 2
        spilled = np.minimum(col + over * (255 - col) // 256, 255)
        out[..., :3][sel] = np.where(col >= 255, 255, spilled)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


TRAIN_KINDS = ("normal", "turn_1", "turn_2", "up", "down")


def layout_kinds(road: bool) -> tuple[str, ...]:
    """Sprite kinds a car's sheets must provide."""
    return ("road",) if road else TRAIN_KINDS


def sheet_kinds(road: bool) -> tuple[str, ...]:
    """Distinct sheet files per model: base (+ hill sheets for trains)."""
    return ("road",) if road else ("normal", "up", "down")


def sheet_for(sprite_dir: Path, name: str, kind: str, scale: int, depth: str) -> Path:
    """Sheet holding sprite `kind` for model `name` (e.g. re460_solo). depth: 8bpp|32bpp|mask."""
    stem = f"{name}_{kind}" if kind in ("up", "down") else name
    return sheet_path(sprite_dir, stem, scale, depth)


OVERLAY_SUFFIX = "_ovl"


def overlay_sheet_name(overlay: str) -> str:
    """Sheet base name of a lamp overlay, e.g. re460_solo -> re460_solo_ovl."""
    return overlay + OVERLAY_SUFFIX


def _save_atomic(img: Image.Image, path: Path) -> None:
    """Write via a temp file: an interrupted build never leaves a half-written sheet that
    looks up to date."""
    tmp = path.with_name(path.name + ".tmp")
    img.save(tmp, format="PNG")
    tmp.replace(path)


def prune_sheets(sprite_dir: Path, plans: dict, road: bool, extra: tuple[str, ...] = ()) -> list[Path]:
    """Delete sheets of models that are no longer in the vehicle's plans (renamed or removed
    variants would otherwise stay in build/sprites/ forever). extra: other sheet names to keep."""
    keep = set(extra)
    for plan in plans.values():
        names = list(plan.bodies) + list(plan.overlays) + [overlay_sheet_name(o) for o in plan.overlays]
        keep |= {
            name if kind in ("normal", "road") else f"{name}_{kind}" for name in names for kind in sheet_kinds(road)
        }
    removed = []
    for p in sprite_dir.glob("*x/*.png"):
        stem = p.stem.rsplit("_", 1)[0]  # strip _8bpp / _32bpp / _mask
        if stem not in keep:
            p.unlink()
            removed.append(p)
    return removed


def make_overlay(
    sprite_dir: Path,
    lit: str,
    body: str,
    force: bool = False,
    road: bool = False,
    scales: tuple[int, ...] = SCALES,
) -> list[Path]:
    """Write `<lit>_ovl` sheets: the pixels where the lit render differs from its dark
    body render (lamps), transparent elsewhere. GoRender is deterministic, so unchanged
    pixels are bit-identical. Drawn in-game as a second sprite layer over the body.
    Sheets newer than both inputs are left alone."""
    written = []
    out = overlay_sheet_name(lit)
    for kind in sheet_kinds(road):  # the normal sheet also holds the turn views
        for scale in scales:
            depths = ("32bpp", "mask") + (("8bpp",) if scale == 1 else ())
            outs = [sheet_for(sprite_dir, out, kind, scale, d) for d in depths]
            ins = [sheet_for(sprite_dir, n, kind, scale, d) for n in (lit, body) for d in depths]
            if not force and all(o.exists() for o in outs):
                newest_in = max(i.stat().st_mtime for i in ins)
                if min(o.stat().st_mtime for o in outs) >= newest_in:
                    continue
            a32 = np.array(Image.open(sheet_for(sprite_dir, lit, kind, scale, "32bpp")).convert("RGBA"))
            b32 = np.array(Image.open(sheet_for(sprite_dir, body, kind, scale, "32bpp")).convert("RGBA"))
            diff = (a32 != b32).any(axis=2)
            p = sheet_for(sprite_dir, out, kind, scale, "32bpp")
            _save_atomic(Image.fromarray(np.where(diff[..., None], a32, 0).astype(np.uint8), "RGBA"), p)
            written.append(p)
            for depth in ("mask",) + (("8bpp",) if scale == 1 else ()):
                src = Image.open(sheet_for(sprite_dir, lit, kind, scale, depth))
                a = np.array(src)
                if depth == "mask":
                    d = diff
                else:
                    d = a != np.array(Image.open(sheet_for(sprite_dir, body, kind, scale, depth)))
                o = Image.fromarray(np.where(d, a, 0).astype(np.uint8), "P")
                o.putpalette(src.getpalette())
                p = sheet_for(sprite_dir, out, kind, scale, depth)
                _save_atomic(o, p)
                written.append(p)
    return written


PURCHASE_DIRECTION = 6  # W: the side view OpenTTD shows in the buy menu, front at the left
PURCHASE_MAX_CARS = 3


def purchase_sheet_name(vehicle_id: str) -> str:
    return f"{vehicle_id}_purchase"


def purchase_layout(lengths: list[int]) -> list[tuple[int, int]]:
    """(car index, OpenTTD length) of the cars shown in a multiple unit's buy-menu sprite:
    the whole unit up to three cars, otherwise front car, second car and rear car, so it reads
    as a complete train with both cab ends without filling the buy menu."""
    n = len(lengths)
    picks = list(range(n)) if n <= PURCHASE_MAX_CARS else [0, 1, n - 1]
    return [(i, lengths[i]) for i in picks]


def _purchase_geometry(scale: int, layout: list[tuple[int, int]]) -> tuple[int, int, list[tuple[SpriteRect, int]]]:
    """Sheet width, height and per car (source rect, x to paste it at). A car's rect is the
    full canvas view with the model centred, so the rects overlap by their empty margins."""
    rects = [sprite_layout(scale, length, "normal")[PURCHASE_DIRECTION] for _, length in layout]
    w, h = rects[0].w, max(r.h for r in rects)
    placed, x = [], 0.0
    for r, (_, length) in zip(rects, layout, strict=True):
        placed.append((r, round(x + length * 2 * scale)))  # 4 px per 1/8 at 1x: half the car = 2 px per unit
        x += length * 4 * scale
    return round(x) + w, h, placed


def purchase_rect(scale: int, layout: list[tuple[int, int]]) -> SpriteRect:
    """The buy-menu sprite in its sheet, centred on the cars it shows."""
    width, height, placed = _purchase_geometry(scale, layout)
    return SpriteRect(270, 0, 0, width, height, -(width // 2), placed[0][0].yrel)


def make_purchase_sheet(
    sprite_dir: Path,
    vehicle_id: str,
    bodies: list[str],
    lengths: list[int],
    force: bool = False,
    scales: tuple[int, ...] = SCALES,
) -> list[Path]:
    """Compose `<id>_purchase` sheets for a multiple unit from the side views of its cars
    (`bodies`: default body per car, front to rear). Skipped when newer than the car sheets."""
    layout = purchase_layout(lengths)
    name = purchase_sheet_name(vehicle_id)
    written = []
    for scale in scales:
        width, height, placed = _purchase_geometry(scale, layout)
        depths = ("32bpp", "mask") + (("8bpp",) if scale == 1 else ())
        outs = [sheet_path(sprite_dir, name, scale, d) for d in depths]
        ins = [sheet_for(sprite_dir, bodies[i], "normal", scale, d) for i, _ in layout for d in depths]
        fresh = all(o.exists() for o in outs) and min(o.stat().st_mtime for o in outs) >= max(
            i.stat().st_mtime for i in ins
        )
        if fresh and not force:
            continue
        canvases = {"32bpp": np.zeros((height, width, 4), np.uint8)}
        canvases |= {d: np.zeros((height, width), np.uint8) for d in depths if d != "32bpp"}
        palettes = {}
        for (r, x0), (car, _) in zip(placed, layout, strict=True):
            box = (r.x, r.y, r.x + r.w, r.y + r.h)
            rgba = np.array(Image.open(sheet_for(sprite_dir, bodies[car], "normal", scale, "32bpp")).convert("RGBA"))
            rgba = rgba[box[1] : box[3], box[0] : box[2]]
            solid = rgba[..., 3] > 0
            for depth in depths:
                if depth == "32bpp":
                    src = rgba
                else:
                    img = Image.open(sheet_for(sprite_dir, bodies[car], "normal", scale, depth))
                    palettes[depth] = img.getpalette()
                    src = np.array(img)[box[1] : box[3], box[0] : box[2]]
                view = canvases[depth][: r.h, x0 : x0 + r.w]
                view[solid] = src[solid]
        for depth, out in zip(depths, outs, strict=True):
            if depth == "32bpp":
                img = Image.fromarray(canvases[depth], "RGBA")
            else:
                img = Image.fromarray(canvases[depth], "P")
                img.putpalette(palettes[depth])
            out.parent.mkdir(parents=True, exist_ok=True)
            _save_atomic(img, out)
            written.append(out)
    return written


def _views(
    sprite_dir: Path,
    name: str,
    kind: str,
    scale: int,
    length: int,
    only: tuple[int, ...] | None = None,
    mask_vis: bool = False,
    overlay: str | None = None,
    overlay_cc1: str | None = None,
    cc: tuple[str | None, str | None] = (None, None),
) -> Image.Image:
    """The 8 (or 4 for hills) direction views of one sheet, cropped and laid out in a row."""
    p32 = sheet_for(sprite_dir, name, kind, scale, "32bpp")
    pm = sheet_for(sprite_dir, name, kind, scale, "mask")
    mask = Image.open(pm) if pm.exists() else None
    if mask_vis and mask is not None:
        m = np.array(mask)
        vis = np.zeros((*m.shape, 4), dtype=np.uint8)
        vis[(m >= CC1[0]) & (m <= CC1[1])] = (255, 0, 255, 255)
        vis[(m >= CC2[0]) & (m <= CC2[1])] = (0, 255, 255, 255)
        img = Image.fromarray(vis, "RGBA")
    else:
        img = composite_cc(Image.open(p32), mask, *cc)
        if overlay is not None:  # what the game shows: body, then the lamp layer on top
            o32 = sheet_for(sprite_dir, overlay_sheet_name(overlay), kind, scale, "32bpp")
            om = sheet_for(sprite_dir, overlay_sheet_name(overlay), kind, scale, "mask")
            img = img.copy()
            # lamp overlays wear the livery; recolourable cargo wears its cargo colour
            ocols = (overlay_cc1, None) if overlay_cc1 else cc
            img.alpha_composite(composite_cc(Image.open(o32), Image.open(om), *ocols))
    crops = []
    for i, r in enumerate(sprite_layout(scale, length, kind)):
        if r.w <= 1 or (only is not None and i not in only):
            continue
        crops.append(img.crop((r.x, r.y, r.x + r.w, r.y + r.h)))
    gap = 6 * scale
    row = Image.new("RGBA", (sum(c.width for c in crops) + gap * len(crops), max(c.height for c in crops)))
    x = 0
    for c in crops:
        row.alpha_composite(c, (x, 0))
        x += c.width + gap
    return row


def contact_sheet(vehicle, sprite_dir: Path, out: Path, scales: tuple[int, ...] = SCALES) -> Path:
    """Review sheet in the colours of the vehicle's first livery: normal views at 1x/2x/4x
    (upscaled nearest-neighbour to the same size), a magnified 4x detail row, curve (±15°) and
    hill views, every light variant and the company-colour mask."""
    from puenktlich.models import car_plans  # local: avoid import cycle

    rows: list[tuple[str, Image.Image]] = []
    livery = vehicle.liveries[0]
    cc = (livery.cc1, livery.cc2)
    colours = f"{livery.name['en']} livery: {livery.cc1 or _DEFAULT_CC1}/{livery.cc2 or _DEFAULT_CC2}".lower()

    def up(img: Image.Image, f: int) -> Image.Image:
        return img.resize((img.width * f, img.height * f), Image.Resampling.NEAREST)

    def views(name: str, kind: str, scale: int, length: int, **kw) -> Image.Image:
        return _views(sprite_dir, name, kind, scale, length, cc=cc, **kw)

    plans = list(car_plans(vehicle).values())
    for car, plan in plans:
        length = car.ottd_length
        base = "road" if car.road else "normal"
        tag = f"car {car.index}: " if len(plans) > 1 else ""
        main, main_ovl = plan.mapping[next(iter(plan.mapping))]
        if car.index == 0 or car.road:
            for scale in scales:
                label = f"{tag}{scale}x normal, {colours} (shown x{4 // scale})"
                rows.append((label, up(views(main, base, scale, length, overlay=main_ovl), 4 // scale)))
        if car.index == 0:  # what the model really looks like: side, three-quarter front and rear
            label = f"{tag}4x detail (shown x2): NE, E, SW"
            rows.append((label, up(views(main, base, 4, length, only=(1, 2, 5), overlay=main_ovl), 2)))
        if car.index == 0 and not car.road:
            for kind, label in (
                ("turn_1", "turn_1 (+15°, curves)"),
                ("turn_2", "turn_2 (-15°, curves)"),
                ("up", "up (hill)"),
                ("down", "down (hill)"),
            ):
                rows.append((f"{tag}4x {label}", views(main, kind, 4, length, overlay=main_ovl)))
        elif not car.road:
            rows.append((f"{tag}4x normal", views(main, "normal", 4, length, overlay=main_ovl)))
        if len(plan.mapping) > 1:
            for var, (body, ovl) in plan.mapping.items():
                label = (
                    f"{tag}4x lights: {var} = {body} + {ovl or 'no overlay'} (left: NE = rear end, right: SW = front)"
                )
                rows.append((label, views(body, base, 4, length, only=(5, 1), overlay=ovl)))
        if plan.cargo:
            for look, colour in plan.cargo_looks.items():
                for stage, ovl in plan.cargo.items():
                    label = f"{tag}4x cargo: {look} ({colour or 'own colours'}), stage {stage} = {main} + {ovl}"
                    rows.append((label, views(main, base, 4, length, only=(1, 2, 5), overlay=ovl, overlay_cc1=colour)))
    for car, plan in plans if plans[0][0].road else plans[:1]:
        main = plan.mapping[next(iter(plan.mapping))][0]
        kind = "road" if car.road else "normal"
        label = "4x mask (magenta = CC1, cyan = CC2)"
        rows.append((label, views(main, kind, 4, car.ottd_length, mask_vis=True)))

    label_h, pad = 14, 6
    width = max(r.width for _, r in rows) + 2 * pad
    height = sum(r.height + label_h + pad for _, r in rows) + pad
    sheet = Image.new("RGBA", (width, height), _BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    y = pad
    for label, img in rows:
        draw.text((pad, y), label, fill=(255, 255, 255, 255))
        y += label_h
        sheet.alpha_composite(img, (pad, y))
        y += img.height + pad
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def lint_sheets(sprite_dir: Path, name: str, length: int, allow_empty: bool = False, road: bool = False) -> list[str]:
    """Problems with one model's sheets (all kinds, scales, depths). Empty = OK.
    allow_empty: overlays legitimately have views without any lamp pixel."""
    problems: list[str] = []
    for scale in SCALES:
        # several kinds share a sheet (normal + turn views): collect their rectangles per file
        # so every sheet is opened and decoded once
        by_sheet: dict[str, list[tuple[str, SpriteRect]]] = {}
        for kind in layout_kinds(road):
            stem = sheet_for(sprite_dir, name, kind, scale, "32bpp").name.removesuffix("_32bpp.png")
            by_sheet.setdefault(stem, []).extend((kind, r) for r in sprite_layout(scale, length, kind) if r.w > 1)
        for stem, rects in by_sheet.items():
            need_w = max(r.x + r.w for _, r in rects)
            need_h = max(r.h for _, r in rects)
            for depth in ("32bpp", "mask") + (("8bpp",) if scale == 1 else ()):
                p = sheet_path(sprite_dir, stem, scale, depth)
                if not p.exists():
                    problems.append(f"missing {p}")
                    continue
                im = Image.open(p)
                if im.width < need_w or im.height < need_h:
                    problems.append(f"{p}: {im.size} smaller than layout {need_w}x{need_h}")
                if depth in ("8bpp", "mask") and im.mode != "P":
                    problems.append(f"{p}: expected palette image, got {im.mode}")
                if depth == "32bpp" and not allow_empty:
                    alpha = np.array(im.convert("RGBA"))[..., 3]
                    for kind, r in rects:
                        if not alpha[r.y : r.y + r.h, r.x : r.x + r.w].any():
                            problems.append(f"{p}: {kind} view {r.angle}° is empty")
    return problems


def lint_vehicle(vehicle) -> list[str]:
    from puenktlich.models import car_plans
    from puenktlich.paths import BUILD_SPRITES

    out: list[str] = []
    for car, plan in car_plans(vehicle).values():
        for body in plan.bodies:
            out += lint_sheets(BUILD_SPRITES / vehicle.id, body, car.ottd_length, road=car.road)
        for ovl in plan.overlays:
            name = overlay_sheet_name(ovl)
            out += lint_sheets(BUILD_SPRITES / vehicle.id, name, car.ottd_length, allow_empty=True, road=car.road)
    return out
