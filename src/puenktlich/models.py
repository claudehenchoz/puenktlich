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

import ast
import functools
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from puenktlich import paths
from puenktlich.schema import CarSpec, Vehicle
from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.palette import rgb_palette
from puenktlich.voxel.squash import (
    Z_PER_M,
    authored_body_width,
    body_split,
    colour_counts,
    for_road_render,
    squash_x,
    true_width_factor,
    widen_y,
)
from puenktlich.voxel.variants import DEFAULT_VARIANT, LIGHT_VARIANTS
from puenktlich.voxel.vox import VoxelGrid, read_vox, write_vox


def _car(target: Vehicle | CarSpec) -> CarSpec:
    """Single-car vehicles may be passed directly; multiple units need a CarSpec."""
    if isinstance(target, CarSpec):
        return target
    specs = target.car_specs
    if len(specs) != 1:
        raise ValueError(f"{target.id} has {len(specs)} cars; pass a CarSpec")
    return specs[0]


def model_dir(target: Vehicle | CarSpec) -> Path:
    return paths.MODELS / _car(target).model.path


def variants(target: Vehicle | CarSpec) -> list[str]:
    """Light variants selectable in-game (always starts with the default)."""
    return list(LIGHT_VARIANTS) if _car(target).model.lights else [DEFAULT_VARIANT]


def load_recipe(path: Path):
    spec = importlib.util.spec_from_file_location(f"recipe_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_SRC = Path(__file__).parents[1]  # .../src
CACHE_MAX_AGE_DAYS = 14


def _imported_files(source: str) -> set[Path]:
    """Files of the `puenktlich` modules a source file imports (packages: their __init__)."""
    found: set[Path] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            # `from pkg import name`: name may be a submodule
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        else:
            continue
        for name in names:
            if name.split(".")[0] != "puenktlich":
                continue
            base = _SRC.joinpath(*name.split("."))
            for f in (base.with_suffix(".py"), base / "__init__.py"):
                if f.exists():
                    found.add(f)
    return found


@functools.cache
def _source_digest(recipe: Path) -> str:
    """Digest of a recipe and of every `puenktlich` module it imports, directly or not: a
    change to one part only rebuilds the models that use it."""
    seen: dict[Path, bytes] = {}
    todo = [recipe]
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen[f] = f.read_bytes()
        todo += _imported_files(seen[f].decode("utf-8"))
    h = hashlib.sha1(inspect.getsource(_renderable).encode() + inspect.getsource(_run_recipe).encode())
    for f in sorted(seen):
        h.update(f.as_posix().encode())
        h.update(seen[f])
    return h.hexdigest()


def build_grid(target: Vehicle | CarSpec, variant: str = DEFAULT_VARIANT, dark: bool = False) -> VoxelGrid:
    """Run the car's recipe for one variant. Cached in build/.cache/vox/ by the source of the
    recipe and of the modules it imports, params, variant and dark flag."""
    car = _car(target)
    d = model_dir(car)
    if car.model.kind == "vox":
        return _renderable(read_vox(d / "model.vox"))
    recipe = d / "recipe.py"
    key = hashlib.sha1(
        _source_digest(recipe).encode() + json.dumps([sorted(car.model.params.items()), variant, dark]).encode()
    ).hexdigest()
    cached = paths.CACHE / "vox" / f"{key}.npz"
    if cached.exists():
        os.utime(cached)  # last use, for prune_caches
        with np.load(cached) as z:
            return VoxelGrid(z["grid"])
    grid = _renderable(_run_recipe(car, recipe, variant, dark))
    cached.parent.mkdir(parents=True, exist_ok=True)
    tmp = cached.with_suffix(f".{os.getpid()}.tmp.npz")  # parallel renders may build the same grid
    np.savez_compressed(tmp, grid=grid.data)
    tmp.replace(cached)
    return grid


def prune_caches(max_age_days: float = CACHE_MAX_AGE_DAYS) -> int:
    """Delete cache entries that no build has used for `max_age_days` (every hit touches its
    entry), plus grids in the old uncompressed format. Returns the bytes freed."""
    limit = time.time() - max_age_days * 86400
    freed = 0
    for f in (paths.CACHE / "vox").glob("*"):
        if f.suffix == ".npy" or f.stat().st_mtime < limit:
            freed += f.stat().st_size
            f.unlink()
    for d in (paths.CACHE / "cargopositor").glob("*"):
        if d.is_dir() and d.stat().st_mtime < limit:
            freed += sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            shutil.rmtree(d)
    return freed


def _renderable(grid: VoxelGrid) -> VoxelGrid:
    """GoRender renders palette index 1 transparent: map it to black (P.BLACK)."""
    grid.data[grid.data == P.UNRENDERABLE_BLACK] = P.BLACK
    return grid


def _run_recipe(car: CarSpec, recipe: Path, variant: str, dark: bool) -> VoxelGrid:
    build = load_recipe(recipe).build
    kwargs: dict = dict(car.model.params)
    if "lights" in inspect.signature(build).parameters:
        lights = LIGHT_VARIANTS[variant]
        kwargs["lights"] = lights.darkened() if dark else lights
    result = build(**kwargs)
    return result.grid if isinstance(result, Model) else result


def _digest(grid: VoxelGrid) -> str:
    return hashlib.sha1(grid.data.tobytes() + repr(grid.size).encode()).hexdigest()


@dataclass(frozen=True)
class VariantPlan:
    bodies: dict[str, VoxelGrid]  # body name -> dark grid
    overlays: dict[str, tuple[str, VoxelGrid]]  # overlay name -> (its body, lit grid)
    mapping: dict[str, tuple[str, str | None]]  # variant -> (body name, overlay name or None)
    # freight (voxel/cargo.py): stage -> overlay name, look -> TTD colour, label -> look
    cargo: dict[int, str] = field(default_factory=dict)
    cargo_looks: dict[str, str | None] = field(default_factory=dict)
    cargo_labels: dict[str, str] = field(default_factory=dict)
    default_look: str = ""

    @property
    def default_body(self) -> str:
        return self.mapping[next(iter(self.mapping))][0]


_PLANS: dict[str, VariantPlan] = {}


def _cargo_plan(car: CarSpec, recipe) -> VariantPlan:
    """Freight wagon: Cargopositor turns the masked wagon into an empty body plus one model
    per cargo look and load stage; each loaded model becomes an overlay of the empty body."""
    from puenktlich.render import cargopositor

    spec = recipe.CARGO
    grid = build_grid(car)
    factor = width_factor(recipe, grid)
    masked = widen_y(squash_x(grid), factor=factor)  # render scale
    with tempfile.TemporaryDirectory(prefix=f"pk_cargo_{car.key}_") as tmp:
        src, out = Path(tmp) / "in", Path(tmp) / "out"
        write_vox(masked, src / f"{car.key}.vox", rgb_palette())
        for name, make in spec.shapes.items():
            shape = make()
            shape = squash_x(shape.grid if isinstance(shape, Model) else shape, centre=False)
            shape = widen_y(shape, full=True, factor=factor)  # same scale as the wagon body
            write_vox(shape, src / f"{name}.vox", rgb_palette())
        batch = Path(tmp) / "batch.json"
        batch.write_text(json.dumps({"files": [f"{car.key}.vox"], "operations": spec.batch_operations()}))
        cargopositor(batch, src, out)

        def load(stem: str) -> VoxelGrid:
            """Cargopositor trims trailing empty space (origin kept): pad back to the canvas
            so every state renders in exactly the same frame as the body."""
            g = read_vox(out / f"{stem}.vox")
            canvas = np.zeros(masked.data.shape, dtype=np.uint8)
            sx, sy, sz = (min(a, b) for a, b in zip(g.size, canvas.shape, strict=True))
            canvas[:sx, :sy, :sz] = g.data[:sx, :sy, :sz]
            return VoxelGrid(canvas)

        body_name = f"{car.key}_body0"
        bodies = {body_name: load(f"{car.key}_empty")}
        overlays: dict[str, tuple[str, VoxelGrid]] = {}
        cargo: dict[int, str] = {}
        for stage in spec.stages:
            name = f"{car.key}_{spec.stage_name(stage)}"
            overlays[name] = (body_name, load(name))
            cargo[stage] = name
    return VariantPlan(
        bodies=bodies,
        overlays=overlays,
        mapping={DEFAULT_VARIANT: (body_name, None)},
        cargo=cargo,
        cargo_looks=dict(spec.looks),
        cargo_labels=dict(spec.labels),
        default_look=spec.default_look,
    )


def width_factor(recipe, grid: VoxelGrid) -> float:
    """Across-scale that renders the body of `grid` at the recipe's real BODY_WIDTH_M (metres)
    on its height scale Z_PER_M (voxels per metre, default 12.2); docs/SCALE.md."""
    width_m = getattr(recipe, "BODY_WIDTH_M", None) if recipe is not None else None
    z_per_m = getattr(recipe, "Z_PER_M", Z_PER_M) if recipe is not None else Z_PER_M
    return true_width_factor(authored_body_width(grid), width_m, z_per_m)


def _plan(vehicle_id: str, vehicle: CarSpec) -> VariantPlan:
    recipe = None
    if vehicle.model.kind == "recipe":
        recipe = load_recipe(model_dir(vehicle) / "recipe.py")
        if hasattr(recipe, "CARGO"):
            return _cargo_plan(vehicle, recipe)
    bodies: dict[str, VoxelGrid] = {}
    body_by_digest: dict[str, str] = {}
    overlays: dict[str, tuple[str, VoxelGrid]] = {}
    overlay_by_digest: dict[str, str] = {}
    mapping: dict[str, tuple[str, str | None]] = {}
    for var in variants(vehicle):
        dark = build_grid(vehicle, var, dark=True)
        lit = build_grid(vehicle, var)
        if not vehicle.road:  # trains: half length, body at its real width (voxel/squash.py, docs/SCALE.md)
            factor = width_factor(recipe, dark)
            counts = colour_counts(dark)
            dark, lit = squash_x(dark, counts), squash_x(lit, counts)
            # same split, factor and colour ranking for lit and dark: overlays stay lamp diffs
            split = body_split(dark)
            dark = widen_y(dark, split, factor=factor, counts=counts)
            lit = widen_y(lit, split, factor=factor, counts=counts)
        else:  # buses: rescaled as a whole to their real width (voxel/squash.py)
            factor, counts = width_factor(recipe, dark), colour_counts(dark)
            dark, lit = for_road_render(dark, factor, counts), for_road_render(lit, factor, counts)
        dd = _digest(dark)
        if dd not in body_by_digest:
            body_by_digest[dd] = f"{vehicle_id}_body{len(body_by_digest)}"
            bodies[body_by_digest[dd]] = dark
        body = body_by_digest[dd]
        ld = _digest(lit)
        overlay = None
        if ld != dd:
            if ld not in overlay_by_digest:
                overlay_by_digest[ld] = f"{vehicle_id}_{var}"
                overlays[overlay_by_digest[ld]] = (body, lit)
            overlay = overlay_by_digest[ld]
        mapping[var] = (body, overlay)
    return VariantPlan(bodies, overlays, mapping)


def variant_plan(target: Vehicle | CarSpec) -> VariantPlan:
    """Plan for one car (names prefixed with the car key). Cached per process."""
    car = _car(target)
    if car.key not in _PLANS:
        _PLANS[car.key] = _plan(car.key, car)
    return _PLANS[car.key]


def car_plans(vehicle: Vehicle) -> dict[str, tuple[CarSpec, VariantPlan]]:
    """car key -> (car, plan) for every car of the vehicle, front to rear."""
    return {c.key: (c, variant_plan(c)) for c in vehicle.car_specs}


def write_models(vehicle: Vehicle, out_dir: Path | None = None) -> tuple[dict[str, VariantPlan], list[Path]]:
    """Write body and lit-overlay models of every car to `build/vox/<id>/base/`
    (stale files removed). Returns ({car key: plan}, files)."""
    out_dir = out_dir or paths.BUILD_VOX / vehicle.id / "base"
    plans = {key: plan for key, (_, plan) in car_plans(vehicle).items()}
    grids: dict[str, VoxelGrid] = {}
    for plan in plans.values():
        grids |= dict(plan.bodies) | {name: lit for name, (_, lit) in plan.overlays.items()}
    files = []
    for name, grid in grids.items():
        p = out_dir / f"{name}.vox"
        write_vox(grid, p, rgb_palette())
        files.append(p)
    for stale in out_dir.glob("*.vox"):
        if stale not in files:
            stale.unlink()
    return plans, files
