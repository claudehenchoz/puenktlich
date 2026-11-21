"""Locate and build vehicle models (recipe.py or hand-made model.vox)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from puenktlich import paths
from puenktlich.schema import Vehicle
from puenktlich.voxel.model import Model
from puenktlich.voxel.palette import rgb_palette
from puenktlich.voxel.vox import VoxelGrid, read_vox, write_vox


def model_dir(vehicle: Vehicle) -> Path:
    return paths.MODELS / vehicle.model.path


def load_recipe(path: Path):
    spec = importlib.util.spec_from_file_location(f"recipe_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_grid(vehicle: Vehicle) -> VoxelGrid:
    d = model_dir(vehicle)
    if vehicle.model.kind == "vox":
        return read_vox(d / "model.vox")
    result = load_recipe(d / "recipe.py").build()
    return result.grid if isinstance(result, Model) else result


def write_model(vehicle: Vehicle, out_dir: Path | None = None) -> Path:
    """Build the vehicle's model and write `build/vox/<id>.vox`."""
    out = (out_dir or paths.BUILD_VOX) / f"{vehicle.id}.vox"
    write_vox(build_grid(vehicle), out, rgb_palette())
    return out
