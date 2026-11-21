"""GoRender / Cargopositor wrappers and sprite-sheet geometry.

GoRender writes one sheet per bit depth and zoom: `<scale>x/<name>_{8bpp,32bpp,mask}.png`.
The 8 views sit side by side in manifest order (angle 0, 45, … 315 = OpenTTD direction
N, NE, E, SE, S, SW, W, NW), separated by 8 px (× scale) spacing.

Sprite offsets follow the formula of Timberwolf's `temporarily_late` template
generator (github.com/mattkimber/temporarily_late, MIT), simplified to single-unit
vehicles: the model is centred in the 8/8 canvas and OpenTTD's shortened-vehicle
position shift is compensated with `(8 - length) / 2` units.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from puenktlich import paths

SCALES = (1, 2, 4)
SPRITE_SPACING = 8  # GoRender constant
Y_JOGGLE = 4

# Screen shift (px at 1x) per vehicle-length unit, by direction angle.
UNIT_SHIFTS = {
    0: (0, -2),
    45: (2, -1),
    90: (4, 0),
    135: (2, 1),
    180: (0, 2),
    225: (-2, 1),
    270: (-4, 0),
    315: (-2, -1),
}
# Centre OpenTTD's bounding boxes, by direction angle.
BBOX_JOGGLES = {
    0: (1, 0),
    45: (-3, 1.5),
    90: (0, -0.5),
    135: (3, 0.5),
    180: (1, 0),
    225: (-3, 1.5),
    270: (0, -0.5),
    315: (3, 0.5),
}


@dataclass(frozen=True)
class SpriteRect:
    angle: int
    x: int
    y: int
    w: int
    h: int
    xrel: int
    yrel: int

    def nml(self) -> str:
        return f"[{self.x}, {self.y}, {self.w}, {self.h}, {self.xrel}, {self.yrel}]"


@cache
def load_manifest(name: str = "train") -> dict:
    m = json.loads((paths.MANIFESTS / f"{name}.json").read_text())
    elev = m["render_elevation"]
    size = m["size"]
    for spr in m["sprites"]:
        if not spr.get("height"):
            spr["height"] = _auto_height(size, elev, spr)
    return m


def _auto_height(size: dict, render_elevation: float, spr: dict) -> int:
    """Port of GoRender's getCalculatedSpriteHeight."""
    a = math.radians(spr["angle"])
    cos, sin = math.cos(a), math.sin(a)
    horizontal = (abs(size["x"] * cos) + abs(size["y"] * sin)) * math.sin(math.radians(render_elevation))
    ratio = (horizontal + size["z"]) / (abs(size["x"] * sin) + abs(size["y"] * cos))
    return math.ceil(ratio * spr["width"])


def canvas_size(manifest: str = "train") -> tuple[int, int, int]:
    s = load_manifest(manifest)["size"]
    return int(s["x"]), int(s["y"]), int(s["z"])


def sprite_layout(scale: int, length: int, manifest: str = "train") -> list[SpriteRect]:
    """NML real-sprite rectangles + offsets for one vehicle sheet."""
    m = load_manifest(manifest)
    rects: list[SpriteRect] = []
    x = 0
    diff = (8 - length) / 2
    for spr in m["sprites"]:
        ang = int(spr["angle"])
        w = spr["width"] * scale
        h = spr["height"] * scale
        xrel = -(w / 2) + (UNIT_SHIFTS[ang][0] * diff + BBOX_JOGGLES[ang][0]) * scale
        yrel = -(h / 2) - Y_JOGGLE * scale + (UNIT_SHIFTS[ang][1] * diff + BBOX_JOGGLES[ang][1]) * scale
        rects.append(SpriteRect(ang, x * scale, 0, w, h, int(xrel), int(yrel)))
        x += spr["width"] + SPRITE_SPACING
    return rects


def sheet_path(sprite_dir: Path, name: str, scale: int, kind: str) -> Path:
    """kind: '8bpp' | '32bpp' | 'mask'."""
    return sprite_dir / f"{scale}x" / f"{name}_{kind}.png"


def gorender(
    vox_files: list[Path],
    out_dir: Path,
    *,
    manifest: str = "train",
    scales: tuple[int, ...] = SCALES,
    force: bool = False,
) -> None:
    """Render `vox_files` into `out_dir/<scale>x/`. GoRender skips up-to-date outputs."""
    if not paths.GORENDER.exists():
        raise FileNotFoundError(f"{paths.GORENDER} missing — run tools/install.sh")
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(paths.GORENDER),
        "-m",
        str(paths.MANIFESTS / f"{manifest}.json"),
        "-palette",
        str(paths.PALETTE_JSON),
        "-s",
        ",".join(str(s) for s in scales),
        "-u",
        "-r",
    ]
    if force:
        cmd.append("-overwrite")
    cmd += [str(p.resolve()) for p in vox_files]
    subprocess.run(cmd, cwd=out_dir, check=True, stdout=subprocess.DEVNULL)


def cargopositor(batch: Path, voxel_dir: Path, out_dir: Path) -> None:
    """Run a Cargopositor batch (JSON) — composites cargo/variants onto base models."""
    if not paths.CARGOPOSITOR.exists():
        raise FileNotFoundError(f"{paths.CARGOPOSITOR} missing — run tools/install.sh")
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(paths.CARGOPOSITOR), "-o", str(out_dir), "-v", str(voxel_dir), str(batch)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def apply_overrides(vehicle_id: str, name: str, sprite_dir: Path) -> list[Path]:
    """Copy hand-touched sheets from overrides/<id>/<scale>x/ over rendered ones."""
    applied = []
    src_root = paths.OVERRIDES / vehicle_id
    if not src_root.exists():
        return applied
    for src in src_root.glob("*x/*.png"):
        if not src.stem.startswith(name):
            continue
        dst = sprite_dir / src.parent.name / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        applied.append(dst)
    return applied
