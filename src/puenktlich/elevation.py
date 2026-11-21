"""Orthographic elevations of a vehicle's models, for comparing proportions with photos.

`pk elevation <id>` writes build/previews/<id>_elevation.png: per car the side view (front at
the left, like most reference photos), the front view and the rear view, in the first
livery's colours. It projects the authoring voxel grids directly (no GoRender, a few seconds),
at the authoring scale (10 voxels per metre along x).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from puenktlich import paths
from puenktlich.models import build_grid
from puenktlich.schema import Vehicle
from puenktlich.sprites import COLOUR_RAMPS
from puenktlich.voxel.palette import CC1, CC2, rgb_palette

SCALE = 4  # pixels per voxel
SKY = (196, 214, 230)


def _colour_table(vehicle: Vehicle) -> np.ndarray:
    liv = vehicle.liveries[0]
    cc1 = liv.cc1 or "RED"
    cc2 = liv.cc2 or "WHITE"
    remap = np.arange(256)
    remap[CC1[0] : CC1[1] + 1] = np.arange(COLOUR_RAMPS[cc1], COLOUR_RAMPS[cc1] + 8)
    remap[CC2[0] : CC2[1] + 1] = np.arange(COLOUR_RAMPS[cc2], COLOUR_RAMPS[cc2] + 8)
    return np.array(rgb_palette(), dtype=np.float64)[remap]


def _project(d: np.ndarray, axis: int, reverse: bool, table: np.ndarray) -> Image.Image:
    """First filled voxel along `axis` (from the low or high end), lightly shaded by depth.
    Returns an image with z up."""
    occ = d != 0
    if reverse:
        d, occ = np.flip(d, axis), np.flip(occ, axis)
    hit = occ.any(axis=axis)
    idx = np.argmax(occ, axis=axis)
    col = np.take_along_axis(d, np.expand_dims(idx, axis), axis).squeeze(axis)
    rgb = table[col] * (1 - 0.006 * np.minimum(idx, 60))[..., None]
    rgb = np.where(hit[..., None], rgb, np.array(SKY))
    img = np.transpose(rgb, (1, 0, 2))[::-1]  # rows = z from the top
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def elevation(vehicle: Vehicle, out: Path | None = None) -> Path:
    out = out or paths.BUILD_PREVIEWS / f"{vehicle.id}_elevation.png"
    table = _colour_table(vehicle)
    rows: list[tuple[str, list[Image.Image]]] = []
    for car in vehicle.car_specs:
        d = build_grid(car, "solo").data
        side = _project(d, 1, False, table).transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # front left
        front = _project(d, 0, True, table)
        rear = _project(d, 0, False, table).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        rows.append((f"{car.key}  (side: front at left | front | rear)", [side, front, rear]))
    pad, label_h = 10, 16
    width = max(sum(i.width * SCALE + pad for i in imgs) for _, imgs in rows) + pad
    height = sum(max(i.height for i in imgs) * SCALE + label_h + pad for _, imgs in rows) + pad
    sheet = Image.new("RGB", (width, height), (40, 44, 52))
    draw = ImageDraw.Draw(sheet)
    y = pad
    for label, imgs in rows:
        draw.text((pad, y), label, fill=(255, 255, 255))
        y += label_h
        x = pad
        for img in imgs:
            big = img.resize((img.width * SCALE, img.height * SCALE), Image.Resampling.NEAREST)
            sheet.paste(big, (x, y))
            x += big.width + pad
        y += max(i.height for i in imgs) * SCALE + pad
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
