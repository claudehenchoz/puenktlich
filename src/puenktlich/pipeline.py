"""Per-vehicle render pipeline: variants -> hill tilt -> GoRender -> overrides -> lint."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from puenktlich import paths
from puenktlich.models import write_models
from puenktlich.render import apply_overrides, cargopositor, gorender
from puenktlich.schema import Vehicle
from puenktlich.sprites import lint_vehicle

HILL_ANGLE = 10  # degrees, as in Timberwolf's Trains
HILL_BATCH = {
    "files": ["*.vox"],
    "operations": [
        {"name": "_up", "type": "rotate_y", "angle": HILL_ANGLE},
        {"name": "_down", "type": "rotate_y", "angle": -HILL_ANGLE},
    ],
}


def sprite_dir(vehicle: Vehicle) -> Path:
    return paths.BUILD_SPRITES / vehicle.id


def render_vehicle(vehicle: Vehicle, force: bool = False) -> tuple[Path, list[str], list[Path]]:
    """Render all sheets for one vehicle. Returns (sprite dir, lint problems, overrides applied)."""
    vox_root = paths.BUILD_VOX / vehicle.id
    base = write_models(vehicle, vox_root / "base")

    # hill models: every variant tilted ±10° (Cargopositor rotate_y -> <name>_up/_down.vox)
    hill_dir = vox_root / "hill"
    expected = [hill_dir / f"{p.stem}{op['name']}.vox" for p in base for op in HILL_BATCH["operations"]]
    newest_base = max(p.stat().st_mtime for p in base)
    if force or any(not h.exists() or h.stat().st_mtime < newest_base for h in expected):
        shutil.rmtree(hill_dir, ignore_errors=True)
        batch = vox_root / "hill_batch.json"
        batch.write_text(json.dumps(HILL_BATCH, indent=2))
        cargopositor(batch, vox_root / "base", hill_dir)
    hills = expected

    out = sprite_dir(vehicle)
    gorender(base, out, manifest="train", force=force)
    gorender(hills, out, manifest="train_hill", force=force)
    applied = apply_overrides(vehicle.id, vehicle.id, out)
    return out, lint_vehicle(vehicle), applied
