"""Sprite post-processing: lint checks and human/AI review previews."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from puenktlich.render import SCALES, sheet_path, sprite_layout
from puenktlich.voxel.palette import CC1, CC2, rgb_palette

# Preview company colours: CC1 -> TTD "red" ramp, CC2 -> white/grey ramp.
_PREVIEW_CC1 = list(range(179, 187))
_PREVIEW_CC2 = list(range(8, 16))
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


def _remap_table(cc1: str | None = None) -> np.ndarray:
    t = np.arange(256, dtype=np.uint8)
    t[CC1[0] : CC1[1] + 1] = list(range(COLOUR_RAMPS[cc1], COLOUR_RAMPS[cc1] + 8)) if cc1 else _PREVIEW_CC1
    t[CC2[0] : CC2[1] + 1] = _PREVIEW_CC2
    return t


def composite_cc(rgba: Image.Image, mask: Image.Image | None, cc1: str | None = None) -> Image.Image:
    """Approximate OpenTTD's 32bpp+mask blitter: masked pixels take the remapped
    palette colour scaled by the 32bpp pixel's brightness (128 = unchanged)."""
    out = np.array(rgba.convert("RGBA")).astype(np.int32)
    if mask is None:
        return rgba
    m = np.array(mask)
    pal = np.array(rgb_palette(), dtype=np.int32)
    remap = _remap_table(cc1)
    sel = m != 0
    if sel.any():
        bright = out[..., :3].max(axis=2)[sel]
        col = pal[remap[m[sel]]] * bright[:, None] // 128
        out[..., :3][sel] = np.clip(col, 0, 255)
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


def make_overlay(sprite_dir: Path, lit: str, body: str, force: bool = False, road: bool = False) -> list[Path]:
    """Write `<lit>_ovl` sheets: the pixels where the lit render differs from its dark
    body render (lamps), transparent elsewhere. GoRender is deterministic, so unchanged
    pixels are bit-identical. Drawn in-game as a second sprite layer over the body.
    Sheets newer than both inputs are left alone."""
    written = []
    out = overlay_sheet_name(lit)
    for kind in sheet_kinds(road):  # the normal sheet also holds the turn views
        for scale in SCALES:
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
            Image.fromarray(np.where(diff[..., None], a32, 0).astype(np.uint8), "RGBA").save(p)
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
                o.save(p)
                written.append(p)
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
        img = composite_cc(Image.open(p32), mask)
        if overlay is not None:  # what the game shows: body, then the lamp layer on top
            o32 = sheet_for(sprite_dir, overlay_sheet_name(overlay), kind, scale, "32bpp")
            om = sheet_for(sprite_dir, overlay_sheet_name(overlay), kind, scale, "mask")
            img = img.copy()
            img.alpha_composite(composite_cc(Image.open(o32), Image.open(om), overlay_cc1))
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


def contact_sheet(vehicle, sprite_dir: Path, out: Path) -> Path:
    """Review sheet: normal views at 1x/2x/4x, curve (±15°) and hill views, every light
    variant and the company-colour mask, upscaled nearest-neighbour to 4x."""
    from puenktlich.models import car_plans  # local: avoid import cycle

    rows: list[tuple[str, Image.Image]] = []

    def up(img: Image.Image, f: int) -> Image.Image:
        return img.resize((img.width * f, img.height * f), Image.Resampling.NEAREST)

    plans = list(car_plans(vehicle).values())
    for car, plan in plans:
        length = car.ottd_length
        base = "road" if car.road else "normal"
        tag = f"car {car.index}: " if len(plans) > 1 else ""
        main, main_ovl = plan.mapping[next(iter(plan.mapping))]
        if car.index == 0 or car.road:
            for scale in SCALES:
                label = f"{tag}{scale}x normal, CC red/white (shown x{4 // scale})"
                rows.append((label, up(_views(sprite_dir, main, base, scale, length, overlay=main_ovl), 4 // scale)))
        if car.index == 0 and not car.road:
            for kind, label in (
                ("turn_1", "turn_1 (+15°, curves)"),
                ("turn_2", "turn_2 (-15°, curves)"),
                ("up", "up (hill)"),
                ("down", "down (hill)"),
            ):
                rows.append((f"{tag}4x {label}", _views(sprite_dir, main, kind, 4, length, overlay=main_ovl)))
        elif not car.road:
            rows.append((f"{tag}4x normal", _views(sprite_dir, main, "normal", 4, length, overlay=main_ovl)))
        if len(plan.mapping) > 1:
            for var, (body, ovl) in plan.mapping.items():
                label = (
                    f"{tag}4x lights: {var} = {body} + {ovl or 'no overlay'} (left: NE = rear end, right: SW = front)"
                )
                rows.append((label, _views(sprite_dir, body, base, 4, length, only=(5, 1), overlay=ovl)))
        if plan.cargo:
            for look, colour in plan.cargo_looks.items():
                for stage, ovl in plan.cargo.items():
                    label = f"{tag}4x cargo: {look} ({colour or 'own colours'}), stage {stage} = {main} + {ovl}"
                    rows.append(
                        (
                            label,
                            _views(sprite_dir, main, base, 4, length, only=(1, 2, 5), overlay=ovl, overlay_cc1=colour),
                        )
                    )
    for car, plan in plans if plans[0][0].road else plans[:1]:
        main = plan.mapping[next(iter(plan.mapping))][0]
        kind = "road" if car.road else "normal"
        label = "4x mask (magenta = CC1, cyan = CC2)"
        rows.append((label, _views(sprite_dir, main, kind, 4, car.ottd_length, mask_vis=True)))

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
    for kind in layout_kinds(road):
        for scale in SCALES:
            rects = [r for r in sprite_layout(scale, length, kind) if r.w > 1]
            need_w = max(r.x + r.w for r in rects)
            need_h = max(r.h for r in rects)
            for depth in ("32bpp", "mask") + (("8bpp",) if scale == 1 else ()):
                p = sheet_for(sprite_dir, name, kind, scale, depth)
                if not p.exists():
                    if f"missing {p}" not in problems:
                        problems.append(f"missing {p}")
                    continue
                im = Image.open(p)
                if im.width < need_w or im.height < need_h:
                    problems.append(f"{p}: {im.size} smaller than layout {need_w}x{need_h}")
                if depth in ("8bpp", "mask") and im.mode != "P":
                    problems.append(f"{p}: expected palette image, got {im.mode}")
                if depth == "32bpp" and not allow_empty:
                    alpha = np.array(im.convert("RGBA"))[..., 3]
                    for r in rects:
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
