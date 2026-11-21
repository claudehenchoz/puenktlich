"""GoRender / Cargopositor wrappers and sprite-sheet geometry.

GoRender writes one sheet per bit depth and zoom: `<scale>x/<name>_{8bpp,32bpp,mask}.png`,
with the manifest's views side by side, separated by 8 px (x scale).

- `train.json` has 24 views every 15°. Angles 0, 45, … 315 are OpenTTD's 8 directions
  (N, NE, E, SE, S, SW, W, NW). Direction ±15° are the curve sprites `turn_1`/`turn_2`.
- `train_hill.json` has the 4 diagonal views of a model tilted ±10° (hill sprites).
- `road.json` has the 8 views of a road vehicle (canvas 126x40x48; kind "road"). Road
  vehicles are not split into parts and have no curve or hill sprites.

Vehicles are split into 3 articulated parts (`PARTS`); only the middle part draws the
full-length sprite. Sprite rectangles and offsets are a straight port of Timberwolf's
`temporarily_late` template generator (github.com/mattkimber/temporarily_late, MIT);
tests pin the output to his generated templates.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from puenktlich import paths

SCALES = (1, 2, 4)
# renderers run at lower priority so a build never freezes the desktop
NICE = ["nice", "-n", "10"] if shutil.which("nice") else []
SPRITE_SPACING = 8  # GoRender constant
Y_JOGGLE = 4
KINDS = ("normal", "turn_1", "turn_2", "up", "down")

# OpenTTD length -> (front, middle, rear) articulated part lengths. The middle part
# carries the sprite; the short invisible ends let it lag behind on curves and slopes.
PARTS: dict[int, tuple[int, int, int]] = {
    3: (1, 1, 1),
    4: (1, 1, 2),
    5: (2, 1, 2),
    6: (2, 2, 2),
    7: (2, 3, 2),
    8: (2, 4, 2),
}

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
UPHILL_JOGGLES = {45: -1, 135: 0, 225: 0, 315: -1}
DOWNHILL_JOGGLES = {45: 0, 135: -1, 225: -1, 315: 0}
PLACEHOLDER_ANGLE = -1  # hill templates have no N/E/S/W views
# road vehicles (temporarily_late -road)
ROAD_Y_JOGGLE = 3
ROAD_BBOX_JOGGLES = {
    0: (1, 1),
    45: (-2.5, 2),
    90: (0, 2),
    135: (2.5, 0.5),
    180: (0, 1),
    225: (-2, 3),
    270: (0, 2),
    315: (3, 2),
}
MANIFEST_FOR_KIND = {
    "normal": "train",
    "turn_1": "train",
    "turn_2": "train",
    "up": "train_hill",
    "down": "train_hill",
    "road": "road",
}


def parts_for(length: int) -> tuple[int, ...]:
    """Articulated part lengths for an OpenTTD length; (length,) = not articulated."""
    return PARTS.get(length, (length,))


def is_articulated(length: int) -> bool:
    return len(parts_for(length)) == 3


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


def _sprite_x(manifest: dict) -> dict[int, tuple[int, dict]]:
    """angle -> (unscaled x position in the sheet, sprite definition)."""
    out, x = {}, 0
    for spr in manifest["sprites"]:
        out[int(spr["angle"])] = (x, spr)
        x += spr["width"] + SPRITE_SPACING
    return out


def _rels(w: float, h: float, scale: int, length: int, direction: int) -> tuple[float, float]:
    """Port of temporarily_late getRels (unitOffset 0)."""
    xrel = -(w / 2)
    yrel = -(h / 2) - Y_JOGGLE * scale
    mid = parts_for(length)[1] if is_articulated(length) else length
    diff = (8 - mid) / 2
    if length == 4:
        diff -= 0.5
    xrel += UNIT_SHIFTS[direction][0] * diff * scale + BBOX_JOGGLES[direction][0] * scale
    yrel += UNIT_SHIFTS[direction][1] * diff * scale + BBOX_JOGGLES[direction][1] * scale
    return xrel, yrel


def _road_rels(w: float, h: float, scale: int, length: int, direction: int) -> tuple[float, float]:
    """Port of temporarily_late getRoadRels."""
    diff = (8 - length) / 2
    xrel = -(w / 2) + UNIT_SHIFTS[direction][0] * diff * scale + ROAD_BBOX_JOGGLES[direction][0] * scale
    yrel = -(h / 2) - ROAD_Y_JOGGLE * scale + UNIT_SHIFTS[direction][1] * diff * scale
    yrel += ROAD_BBOX_JOGGLES[direction][1] * scale
    return xrel, yrel


def sprite_layout(scale: int, length: int, kind: str = "normal") -> list[SpriteRect]:
    """NML real-sprite rectangles + offsets (8 directions) for one sheet.

    kind: normal / turn_1 (+15°) / turn_2 (-15°) read the 24-view `train` sheet;
    up / down read the 4-view `train_hill` sheet (other directions are 1x1 placeholders).
    """
    rects: list[SpriteRect] = []
    if kind == "road":
        sprites = _sprite_x(load_manifest("road"))
        for d in range(0, 360, 45):
            x, spr = sprites[d]
            w, h = spr["width"] * scale, spr["height"] * scale
            xrel, yrel = _road_rels(w, h, scale, length, d)
            rects.append(SpriteRect(d, x * scale, 0, w, h, int(xrel), int(yrel)))
        return rects
    if kind in ("up", "down"):
        sprites = _sprite_x(load_manifest("train_hill"))
        joggles = UPHILL_JOGGLES if kind == "up" else DOWNHILL_JOGGLES
        for d in range(0, 360, 45):
            if d not in sprites:
                rects.append(SpriteRect(PLACEHOLDER_ANGLE, 0, 0, 1, 1, 0, 0))
                continue
            x, spr = sprites[d]
            w, h = spr["width"] * scale, spr["height"] * scale
            xrel, yrel = _rels(w, h, scale, length, d)
            yrel += 0.25 * length * scale + joggles[d] * scale
            rects.append(SpriteRect(d, x * scale, 0, w, h, int(xrel), int(yrel)))
        return rects

    offset = {"normal": 0, "turn_1": 15, "turn_2": -15}[kind]
    sprites = _sprite_x(load_manifest("train"))
    for d in range(0, 360, 45):
        ang = (d + offset) % 360
        x, spr = sprites[ang]
        w, h = spr["width"] * scale, spr["height"] * scale
        xrel, yrel = _rels(w, h, scale, length, d)
        rects.append(SpriteRect(ang, x * scale, 0, w, h, int(xrel), int(yrel)))
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
        *NICE,
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


@cache
def _tool_digest(tool: Path) -> str:
    return hashlib.sha1(tool.read_bytes()).hexdigest()


def cargopositor(batch: Path, voxel_dir: Path, out_dir: Path) -> None:
    """Run a Cargopositor batch (JSON) — composites cargo/variants onto base models.

    Results are cached by content (batch + every input .vox + the binary): Cargopositor's
    `scale` operation is not deterministic, so re-running it on unchanged input would change
    the models, and with them every rendered sheet. The cache makes the first result stick.
    """
    if not paths.CARGOPOSITOR.exists():
        raise FileNotFoundError(f"{paths.CARGOPOSITOR} missing — run tools/install.sh")
    h = hashlib.sha1(batch.read_bytes())
    h.update(_tool_digest(paths.CARGOPOSITOR).encode())
    for vox in sorted(voxel_dir.glob("*.vox")):
        h.update(vox.name.encode())
        h.update(vox.read_bytes())
    cached = paths.CACHE / "cargopositor" / h.hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    if not cached.is_dir():
        tmp = cached.with_name(cached.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        subprocess.run(
            [*NICE, str(paths.CARGOPOSITOR), "-o", str(tmp), "-v", str(voxel_dir), str(batch)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        tmp.rename(cached)
    for f in cached.iterdir():
        dst = out_dir / f.name
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            shutil.copy2(f, dst)


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
