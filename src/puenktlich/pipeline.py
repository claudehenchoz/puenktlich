"""Per-vehicle render pipeline: variants -> hill tilt -> GoRender -> overrides -> lint."""

from __future__ import annotations

import json
from pathlib import Path

from puenktlich import paths
from puenktlich.models import write_models
from puenktlich.render import apply_overrides, cargopositor, gorender
from puenktlich.schema import Vehicle
from puenktlich.sprites import lint_vehicle, make_overlay

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


def _sheet_mtimes(out: Path) -> dict[Path, float]:
    return {p: p.stat().st_mtime for p in out.glob("*x/*.png")}


def render_vehicle(vehicle: Vehicle, force: bool = False) -> tuple[Path, list[str], list[Path]]:
    """Render all sheets for one vehicle. Returns (sprite dir, lint problems, overrides applied).
    Unchanged inputs are skipped at every step (vox bytes, cached Cargopositor output, GoRender
    up-to-date check, overlay mtimes), so a no-op build does no rendering."""
    vox_root = paths.BUILD_VOX / vehicle.id
    plans, base = write_models(vehicle, vox_root / "base")

    # hill models: every variant tilted ±10° (Cargopositor rotate_y -> <name>_up/_down.vox);
    # cached by content, files are only rewritten when they change
    hill_dir = vox_root / "hill"
    hills = [hill_dir / f"{p.stem}{op['name']}.vox" for p in base for op in HILL_BATCH["operations"]]
    batch = vox_root / "hill_batch.json"
    text = json.dumps(HILL_BATCH, indent=2)
    if not batch.exists() or batch.read_text() != text:
        batch.write_text(text)
    cargopositor(batch, vox_root / "base", hill_dir)
    for stale in hill_dir.glob("*.vox"):
        if stale not in hills:
            stale.unlink()

    out = sprite_dir(vehicle)
    before = _sheet_mtimes(out)
    gorender(base, out, manifest="train", force=force)
    gorender(hills, out, manifest="train_hill", force=force)
    # lamp / cargo overlays: lit render minus its dark body render
    for plan in plans.values():
        for ovl, (body, _) in plan.overlays.items():
            make_overlay(out, ovl, body, force=force)
    after = _sheet_mtimes(out)
    LAST_RENDER_STATS[vehicle.id] = sum(1 for p, t in after.items() if before.get(p) != t)
    applied = apply_overrides(vehicle.id, vehicle.id, out)
    return out, lint_vehicle(vehicle), applied


LAST_RENDER_STATS: dict[str, int] = {}  # vehicle id -> sheets (re)written by the last render
