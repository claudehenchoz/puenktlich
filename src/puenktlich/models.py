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

import functools
import hashlib
import importlib.util
import inspect
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from puenktlich import paths
from puenktlich.schema import CarSpec, Vehicle
from puenktlich.voxel.model import Model
from puenktlich.voxel.palette import rgb_palette
from puenktlich.voxel.squash import body_split, colour_counts, for_road_render, squash_x, widen_y
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


_VOXEL_SRC = Path(__file__).parent / "voxel"


@functools.cache
def _library_digest() -> str:
    """Digest of the modelling library: any change to it invalidates every cached grid."""
    h = hashlib.sha1()
    for f in sorted(_VOXEL_SRC.rglob("*.py")):
        h.update(f.relative_to(_VOXEL_SRC).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def build_grid(target: Vehicle | CarSpec, variant: str = DEFAULT_VARIANT, dark: bool = False) -> VoxelGrid:
    """Run the car's recipe for one variant. Cached in build/.cache/vox/ by the recipe source,
    the voxel library source, params, variant and dark flag."""
    car = _car(target)
    d = model_dir(car)
    if car.model.kind == "vox":
        return read_vox(d / "model.vox")
    recipe = d / "recipe.py"
    key = hashlib.sha1(
        recipe.read_bytes()
        + _library_digest().encode()
        + json.dumps([sorted(car.model.params.items()), variant, dark]).encode()
    ).hexdigest()
    cached = paths.CACHE / "vox" / f"{key}.npy"
    if cached.exists():
        return VoxelGrid(np.load(cached))
    grid = _run_recipe(car, recipe, variant, dark)
    cached.parent.mkdir(parents=True, exist_ok=True)
    tmp = cached.with_suffix(".tmp.npy")
    np.save(tmp, grid.data)
    tmp.replace(cached)
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
    kwargs = dict(car.model.params)
    masked = recipe.build(**kwargs)
    masked = widen_y(squash_x(masked.grid if isinstance(masked, Model) else masked))  # render scale
    with tempfile.TemporaryDirectory(prefix=f"pk_cargo_{car.key}_") as tmp:
        src, out = Path(tmp) / "in", Path(tmp) / "out"
        write_vox(masked, src / f"{car.key}.vox", rgb_palette())
        for name, make in spec.shapes.items():
            shape = make()
            shape = squash_x(shape.grid if isinstance(shape, Model) else shape, centre=False)
            shape = widen_y(shape, full=True)
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


def _plan(vehicle_id: str, vehicle: CarSpec) -> VariantPlan:
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
        if not vehicle.road:  # trains: half length, widened body (voxel/squash.py, docs/SCALE.md)
            counts = colour_counts(dark)
            dark, lit = squash_x(dark, counts), squash_x(lit, counts)
            split = body_split(dark)  # same widening for lit and dark: overlays stay lamp diffs
            dark, lit = widen_y(dark, split), widen_y(lit, split)
        else:  # buses: wider and taller (aBase proportions)
            dark, lit = for_road_render(dark), for_road_render(lit)
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
