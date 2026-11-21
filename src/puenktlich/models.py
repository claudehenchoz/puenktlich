"""Locate and build vehicle models (recipe.py or hand-made model.vox), per variant."""

from __future__ import annotations

import importlib.util
import inspect
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
    """Model variants rendered for this vehicle (always starts with the default)."""
    return list(LIGHT_VARIANTS) if vehicle.model.lights else [DEFAULT_VARIANT]


def sprite_name(vehicle: Vehicle, variant: str) -> str:
    """Base name of rendered sheets / vox files: `<id>_<variant>`."""
    return f"{vehicle.id}_{variant}"


def load_recipe(path: Path):
    spec = importlib.util.spec_from_file_location(f"recipe_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_grid(vehicle: Vehicle, variant: str = DEFAULT_VARIANT) -> VoxelGrid:
    d = model_dir(vehicle)
    if vehicle.model.kind == "vox":
        return read_vox(d / "model.vox")
    build = load_recipe(d / "recipe.py").build
    takes_lights = "lights" in inspect.signature(build).parameters
    result = build(lights=LIGHT_VARIANTS[variant]) if takes_lights else build()
    return result.grid if isinstance(result, Model) else result


def write_models(vehicle: Vehicle, out_dir: Path | None = None) -> list[Path]:
    """Write every variant to `build/vox/<id>/base/<id>_<variant>.vox`."""
    out_dir = out_dir or paths.BUILD_VOX / vehicle.id / "base"
    files = []
    for var in variants(vehicle):
        p = out_dir / f"{sprite_name(vehicle, var)}.vox"
        write_vox(build_grid(vehicle, var), p, rgb_palette())
        files.append(p)
    return files
