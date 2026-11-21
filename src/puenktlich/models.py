"""Locate and build vehicle models (recipe.py or hand-made model.vox), per light variant.

Light variants differ only in lamp colours (and, for control cars, orientation), so
they are not rendered as full sprite sets each. `variant_plan` splits them into:

    bodies    the variant built with all lamps dark (`Lights.dark`), deduplicated:
              `<id>_body0`, `<id>_body1`, ... (a control car has two: cab front / turned)
    overlays  the lit variant, when it differs from its body, deduplicated by content:
              `<id>_<variant>`; only the pixels that differ from the body are kept
              (sprites.make_overlay) and drawn as a second sprite layer in-game.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path

from puenktlich import paths
from puenktlich.schema import Vehicle
from puenktlich.voxel.model import Model
from puenktlich.voxel.palette import rgb_palette
from puenktlich.voxel.variants import DEFAULT_VARIANT, LIGHT_VARIANTS
from puenktlich.voxel.vox import VoxelGrid, read_vox, write_vox


def model_dir(vehicle: Vehicle) -> Path:
    return paths.MODELS / vehicle.model.path


def variants(vehicle: Vehicle) -> list[str]:
    """Light variants selectable in-game (always starts with the default)."""
    return list(LIGHT_VARIANTS) if vehicle.model.lights else [DEFAULT_VARIANT]


def load_recipe(path: Path):
    spec = importlib.util.spec_from_file_location(f"recipe_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_grid(vehicle: Vehicle, variant: str = DEFAULT_VARIANT, dark: bool = False) -> VoxelGrid:
    d = model_dir(vehicle)
    if vehicle.model.kind == "vox":
        return read_vox(d / "model.vox")
    build = load_recipe(d / "recipe.py").build
    takes_lights = "lights" in inspect.signature(build).parameters
    if takes_lights:
        lights = LIGHT_VARIANTS[variant]
        result = build(lights=lights.darkened() if dark else lights)
    else:
        result = build()
    return result.grid if isinstance(result, Model) else result


def _digest(grid: VoxelGrid) -> str:
    return hashlib.sha1(grid.data.tobytes() + repr(grid.size).encode()).hexdigest()


@dataclass(frozen=True)
class VariantPlan:
    bodies: dict[str, VoxelGrid]  # body name -> dark grid
    overlays: dict[str, tuple[str, VoxelGrid]]  # overlay name -> (its body, lit grid)
    mapping: dict[str, tuple[str, str | None]]  # variant -> (body name, overlay name or None)

    @property
    def default_body(self) -> str:
        return self.mapping[next(iter(self.mapping))][0]


_PLANS: dict[str, VariantPlan] = {}


def _plan(vehicle_id: str, vehicle: Vehicle) -> VariantPlan:
    bodies: dict[str, VoxelGrid] = {}
    body_by_digest: dict[str, str] = {}
    overlays: dict[str, tuple[str, VoxelGrid]] = {}
    overlay_by_digest: dict[str, str] = {}
    mapping: dict[str, tuple[str, str | None]] = {}
    for var in variants(vehicle):
        dark = build_grid(vehicle, var, dark=True)
        dd = _digest(dark)
        if dd not in body_by_digest:
            body_by_digest[dd] = f"{vehicle_id}_body{len(body_by_digest)}"
            bodies[body_by_digest[dd]] = dark
        body = body_by_digest[dd]
        lit = build_grid(vehicle, var)
        ld = _digest(lit)
        overlay = None
        if ld != dd:
            if ld not in overlay_by_digest:
                overlay_by_digest[ld] = f"{vehicle_id}_{var}"
                overlays[overlay_by_digest[ld]] = (body, lit)
            overlay = overlay_by_digest[ld]
        mapping[var] = (body, overlay)
    return VariantPlan(bodies, overlays, mapping)


def variant_plan(vehicle: Vehicle) -> VariantPlan:
    """Cached per process (recipes are rebuilt by each new `pk` run)."""
    if vehicle.id not in _PLANS:
        _PLANS[vehicle.id] = _plan(vehicle.id, vehicle)
    return _PLANS[vehicle.id]


def write_models(vehicle: Vehicle, out_dir: Path | None = None) -> tuple[VariantPlan, list[Path]]:
    """Write body and lit-overlay models to `build/vox/<id>/base/` (stale files removed)."""
    out_dir = out_dir or paths.BUILD_VOX / vehicle.id / "base"
    plan = variant_plan(vehicle)
    grids = dict(plan.bodies) | {name: lit for name, (_, lit) in plan.overlays.items()}
    files = []
    for name, grid in grids.items():
        p = out_dir / f"{name}.vox"
        write_vox(grid, p, rgb_palette())
        files.append(p)
    for stale in out_dir.glob("*.vox"):
        if stale not in files:
            stale.unlink()
    return plan, files
