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


def _remap_table() -> np.ndarray:
    t = np.arange(256, dtype=np.uint8)
    t[CC1[0] : CC1[1] + 1] = _PREVIEW_CC1
    t[CC2[0] : CC2[1] + 1] = _PREVIEW_CC2
    return t


def composite_cc(rgba: Image.Image, mask: Image.Image | None) -> Image.Image:
    """Approximate OpenTTD's 32bpp+mask blitter: masked pixels take the remapped
    palette colour scaled by the 32bpp pixel's brightness (128 = unchanged)."""
    out = np.array(rgba.convert("RGBA")).astype(np.int32)
    if mask is None:
        return rgba
    m = np.array(mask)
    pal = np.array(rgb_palette(), dtype=np.int32)
    remap = _remap_table()
    sel = m != 0
    if sel.any():
        bright = out[..., :3].max(axis=2)[sel]
        col = pal[remap[m[sel]]] * bright[:, None] // 128
        out[..., :3][sel] = np.clip(col, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def sheet_for(sprite_dir: Path, name: str, kind: str, scale: int, depth: str) -> Path:
    """Sheet holding sprite `kind` for model `name` (e.g. re460_solo). depth: 8bpp|32bpp|mask."""
    stem = f"{name}_{kind}" if kind in ("up", "down") else name
    return sheet_path(sprite_dir, stem, scale, depth)


def _views(
    sprite_dir: Path,
    name: str,
    kind: str,
    scale: int,
    length: int,
    only: tuple[int, ...] | None = None,
    mask_vis: bool = False,
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
    from puenktlich.models import sprite_name, variants  # local: avoid import cycle

    length = vehicle.ottd_length
    names = {v: sprite_name(vehicle, v) for v in variants(vehicle)}
    main = names.get("solo", next(iter(names.values())))
    rows: list[tuple[str, Image.Image]] = []

    def up(img: Image.Image, f: int) -> Image.Image:
        return img.resize((img.width * f, img.height * f), Image.Resampling.NEAREST)

    for scale in SCALES:
        label = f"{scale}x normal, CC red/white (shown x{4 // scale})"
        rows.append((label, up(_views(sprite_dir, main, "normal", scale, length), 4 // scale)))
    rows.append(("4x turn_1 (+15°, curves)", _views(sprite_dir, main, "turn_1", 4, length)))
    rows.append(("4x turn_2 (-15°, curves)", _views(sprite_dir, main, "turn_2", 4, length)))
    rows.append(("4x up (hill)", _views(sprite_dir, main, "up", 4, length)))
    rows.append(("4x down (hill)", _views(sprite_dir, main, "down", 4, length)))
    if len(names) > 1:
        for var, name in names.items():
            label = f"4x lights: {var} (SW view = front end, NE view = rear end)"
            rows.append((label, _views(sprite_dir, name, "normal", 4, length, only=(5, 1))))
    rows.append(("4x mask (magenta = CC1, cyan = CC2)", _views(sprite_dir, main, "normal", 4, length, mask_vis=True)))

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


def lint_sheets(sprite_dir: Path, name: str, length: int) -> list[str]:
    """Problems with one model's sheets (all kinds, scales, depths). Empty = OK."""
    problems: list[str] = []
    for kind in ("normal", "turn_1", "turn_2", "up", "down"):
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
                if depth == "32bpp":
                    alpha = np.array(im.convert("RGBA"))[..., 3]
                    for r in rects:
                        if not alpha[r.y : r.y + r.h, r.x : r.x + r.w].any():
                            problems.append(f"{p}: {kind} view {r.angle}° is empty")
    return problems


def lint_vehicle(vehicle) -> list[str]:
    from puenktlich.models import sprite_name, variants
    from puenktlich.paths import BUILD_SPRITES

    out: list[str] = []
    for var in variants(vehicle):
        out += lint_sheets(BUILD_SPRITES / vehicle.id, sprite_name(vehicle, var), vehicle.ottd_length)
    return out
