"""Per-vehicle render pipeline: variants -> hill tilt -> GoRender -> overrides -> lint."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from puenktlich import paths
from puenktlich.models import write_models
from puenktlich.render import GORENDER_MEMORY_MB, SCALES, apply_overrides, cargopositor, gorender, sprite_layout
from puenktlich.schema import Vehicle, vehicles
from puenktlich.sprites import lint_vehicle, make_overlay, make_purchase_sheet, prune_sheets, purchase_sheet_name

HILL_ANGLE = 10  # degrees, as in Timberwolf's Trains
HILL_BATCH = {
    "files": ["*.vox"],
    "operations": [
        {"name": "_up", "type": "rotate_y", "angle": HILL_ANGLE},
        {"name": "_down", "type": "rotate_y", "angle": -HILL_ANGLE},
    ],
}
DRAFT_SCALES = (4,)  # `pk preview --draft`: 4x only, GoRender's fast sampler


@dataclass
class RenderResult:
    vehicle_id: str
    sprite_dir: Path
    problems: list[str]
    overrides: list[Path]
    sheets_rendered: int  # sheets (re)written by this render
    timings: dict[str, float] = field(default_factory=dict)  # stage -> seconds


def sprite_dir(vehicle: Vehicle, draft: bool = False) -> Path:
    """Draft renders live apart from the real sheets, so they never look up to date to a build."""
    return (paths.BUILD_SPRITES_DRAFT if draft else paths.BUILD_SPRITES) / vehicle.id


def _sheet_mtimes(out: Path) -> dict[Path, float]:
    return {p: p.stat().st_mtime for p in out.glob("*x/*.png")}


@contextmanager
def _timed(timings: dict[str, float], stage: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        timings[stage] = timings.get(stage, 0.0) + time.perf_counter() - start


def render_vehicle(vehicle: Vehicle, force: bool = False, draft: bool = False) -> RenderResult:
    """Render all sheets for one vehicle.
    Unchanged inputs are skipped at every step (vox bytes, cached Cargopositor output, GoRender
    up-to-date check, overlay mtimes), so a no-op build does no rendering.
    draft: quick look for the model-edit loop (4x only, fast sampler) in build/sprites_draft/."""
    t: dict[str, float] = {}
    scales = DRAFT_SCALES if draft else SCALES
    vox_root = paths.BUILD_VOX / vehicle.id
    with _timed(t, "models"):
        plans, base = write_models(vehicle, vox_root / "base")
    out = sprite_dir(vehicle, draft)
    before = _sheet_mtimes(out)
    if vehicle.is_road:  # 8 views, no hill sprites
        with _timed(t, "gorender"):
            gorender(base, out, manifest="road", scales=scales, force=force, fast=draft)
    else:
        # hill models: every variant tilted ±10° (Cargopositor rotate_y -> <name>_up/_down.vox);
        # cached by content, files are only rewritten when they change
        hill_dir = vox_root / "hill"
        hills = [hill_dir / f"{p.stem}{op['name']}.vox" for p in base for op in HILL_BATCH["operations"]]
        batch = vox_root / "hill_batch.json"
        text = json.dumps(HILL_BATCH, indent=2)
        if not batch.exists() or batch.read_text() != text:
            batch.write_text(text)
        with _timed(t, "hills"):
            cargopositor(batch, vox_root / "base", hill_dir)
        for stale in hill_dir.glob("*.vox"):
            if stale not in hills:
                stale.unlink()
        with _timed(t, "gorender"):
            gorender(base, out, manifest="train", scales=scales, force=force, fast=draft)
            gorender(hills, out, manifest="train_hill", scales=scales, force=force, fast=draft)
    # lamp / cargo overlays: lit render minus its dark body render
    with _timed(t, "overlays"):
        for plan in plans.values():
            for ovl, (body, _) in plan.overlays.items():
                make_overlay(out, ovl, body, force=force, road=vehicle.is_road, scales=scales)
        extra: tuple[str, ...] = ()
        if not vehicle.is_road and len(plans) > 1:  # multiple unit: buy-menu sprite of the whole unit
            cars = vehicle.car_specs
            bodies = [plans[c.key].default_body for c in cars]
            make_purchase_sheet(out, vehicle.id, bodies, [c.ottd_length for c in cars], force=force, scales=scales)
            extra = (purchase_sheet_name(vehicle.id),)
        prune_sheets(out, plans, vehicle.is_road, extra)
    applied = [] if draft else apply_overrides(vehicle.id, vehicle.id, out)
    rendered = sum(1 for p, mtime in _sheet_mtimes(out).items() if before.get(p) != mtime)
    problems: list[str] = []
    if not draft:
        # sheets are only decoded and checked again when one of them (or the layout) changed
        lint_ok = out / ".lint_ok"
        want = _lint_stamp(vehicle, plans)
        if rendered or not lint_ok.exists() or lint_ok.read_text() != want:
            lint_ok.unlink(missing_ok=True)
            with _timed(t, "lint"):
                problems = lint_vehicle(vehicle)
            if not problems:
                lint_ok.write_text(want)
    return RenderResult(vehicle.id, out, problems, applied, rendered, t)


def _lint_stamp(vehicle: Vehicle, plans: dict) -> str:
    cars = [
        (c.key, c.ottd_length, sorted(plans[c.key].bodies), sorted(plans[c.key].overlays)) for c in vehicle.car_specs
    ]
    return json.dumps([cars, [[r.nml() for r in sprite_layout(s, 8, k)] for s in SCALES for k in ("normal", "road")]])


def _render_by_id(args: tuple[str, bool, bool]) -> RenderResult:
    vehicle_id, force, draft = args
    return render_vehicle(vehicles()[vehicle_id], force=force, draft=draft)


def _available_memory_mb() -> int | None:
    if os.name == "nt":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
                (n, ctypes.c_ulonglong)
                for n in ("total", "avail", "total_page", "avail_page", "total_virt", "avail_virt", "avail_ext")
            ]

        status = MemoryStatus(dwLength=ctypes.sizeof(MemoryStatus))
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.avail // (1024 * 1024)
        return None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    return None  # not Linux or Windows: no limit from memory


def default_jobs() -> int:
    """Vehicles rendered at once. GoRender is multi-threaded itself, so half the cores; and
    each GoRender needs up to GORENDER_MEMORY_MB, so no more jobs than fit into the memory
    that is free right now (two of them once exhausted a 12 GB desktop). PK_JOBS or `--jobs`
    override both."""
    env = os.environ.get("PK_JOBS")
    if env:
        return max(1, int(env))
    jobs = max(1, (os.cpu_count() or 2) // 2)
    available = _available_memory_mb()
    if available is not None:
        jobs = min(jobs, max(1, (available - 1024) // GORENDER_MEMORY_MB))  # keep 1 GB for the desktop
    return jobs


def render_vehicles(
    vs: list[Vehicle], force: bool = False, draft: bool = False, jobs: int | None = None
) -> Iterator[RenderResult]:
    """Render several vehicles, `jobs` at a time, yielding results in the order given."""
    jobs = min(jobs or default_jobs(), len(vs))
    if jobs <= 1:
        for v in vs:
            yield render_vehicle(v, force=force, draft=draft)
        return
    with ProcessPoolExecutor(jobs) as pool:
        yield from pool.map(_render_by_id, [(v.id, force, draft) for v in vs])
