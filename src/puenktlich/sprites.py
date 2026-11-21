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


def _only_sprites(img: Image.Image, scale: int) -> Image.Image:
    """Blank everything outside the manifest's sprite rectangles (GoRender fills the
    rest of the sheet with opaque white / index 255, which the game never sees)."""
    a = np.array(img.convert("RGBA"))
    keep = np.zeros(a.shape[:2], dtype=bool)
    for r in sprite_layout(scale, 8):
        keep[r.y : r.y + r.h, r.x : r.x + r.w] = True
    a[~keep] = 0
    return Image.fromarray(a, "RGBA")


def contact_sheet(sprite_dir: Path, name: str, out: Path) -> Path:
    """All 8 views x 3 zooms with company colours applied, plus the 1x 8bpp sheet and the
    raw mask, upscaled with nearest-neighbour so pixels stay readable."""
    rows: list[tuple[str, Image.Image]] = []

    def up(img: Image.Image, f: int) -> Image.Image:
        return img.resize((img.width * f, img.height * f), Image.Resampling.NEAREST)

    for scale in SCALES:
        p32 = sheet_path(sprite_dir, name, scale, "32bpp")
        if not p32.exists():
            continue
        pm = sheet_path(sprite_dir, name, scale, "mask")
        img = composite_cc(Image.open(p32), Image.open(pm) if pm.exists() else None)
        rows.append((f"{scale}x 32bpp + CC red/white (shown x{4 // scale})", up(_only_sprites(img, scale), 4 // scale)))
    p8 = sheet_path(sprite_dir, name, 1, "8bpp")
    if p8.exists():
        pal8 = Image.open(p8)
        img = pal8.convert("RGBA")
        a = np.array(img)
        a[np.array(pal8) == 0, 3] = 0  # index 0 is transparent in TTD
        rows.append(("1x 8bpp fallback (shown x4)", up(_only_sprites(Image.fromarray(a), 1), 4)))
    pm = sheet_path(sprite_dir, name, 4, "mask")
    if pm.exists():
        m = np.array(Image.open(pm))
        vis = np.zeros((*m.shape, 4), dtype=np.uint8)
        vis[(m >= CC1[0]) & (m <= CC1[1])] = (255, 0, 255, 255)
        vis[(m >= CC2[0]) & (m <= CC2[1])] = (0, 255, 255, 255)
        rows.append(("4x mask (magenta = CC1, cyan = CC2)", _only_sprites(Image.fromarray(vis, "RGBA"), 4)))
    if not rows:
        raise FileNotFoundError(f"no rendered sheets for {name} in {sprite_dir}")

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
    """Return a list of problems (empty = OK)."""
    problems: list[str] = []
    for scale in SCALES:
        rects = sprite_layout(scale, length)
        need_w = rects[-1].x + rects[-1].w
        need_h = max(r.h for r in rects)
        for kind in ("32bpp", "mask") + (("8bpp",) if scale == 1 else ()):
            p = sheet_path(sprite_dir, name, scale, kind)
            if not p.exists():
                problems.append(f"missing {p}")
                continue
            im = Image.open(p)
            if im.width < need_w or im.height < need_h:
                problems.append(f"{p}: {im.size} smaller than layout {need_w}x{need_h}")
            if kind in ("8bpp", "mask") and im.mode != "P":
                problems.append(f"{p}: expected palette image, got {im.mode}")
            if kind == "32bpp":
                alpha = np.array(im.convert("RGBA"))[..., 3]
                for r in rects:
                    if not alpha[r.y : r.y + r.h, r.x : r.x + r.w].any():
                        problems.append(f"{p}: view {r.angle}° is empty")
    return problems
