"""Model checks: the modelling conventions of CLAUDE.md and docs/STYLE.md, as code.

`pk lint` and the tests both run `check_all()`, so the rules can't drift apart. Each check
looks at the voxel models as the recipes build them (before the render squash) and returns
readable problems; an empty list means the model follows the conventions.
"""

from __future__ import annotations

import numpy as np

from puenktlich.models import build_grid, load_recipe, model_dir, variants
from puenktlich.schema import CarSpec, Vehicle, vehicles
from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CANVAS, ROAD_CANVAS, VOX_PER_M
from puenktlich.voxel.parts.lights import LAMP_RED, LAMP_WHITE
from puenktlich.voxel.parts.running_gear import COUPLING_Z

MAX_Z = 68  # the 10° hill tilt needs headroom under the 72-voxel canvas
SYMMETRIC_BELOW_Z = 44  # above: pantographs and roof gear may sit off-centre
MIN_FILL = 0.85  # a model much shorter than its OpenTTD length leaves gaps in the train
SPECIAL_INDICES = range(215, 253)  # process pink and animated colours (docs/STYLE.md)
BUFFERED_KINDS = ("locomotive", "coach", "control_car", "wagon")


def _is_cargo_wagon(car: CarSpec) -> bool:
    return car.model.kind == "recipe" and hasattr(load_recipe(model_dir(car) / "recipe.py"), "CARGO")


def check_shape(v: Vehicle, car: CarSpec) -> list[str]:
    """Canvas, hill-tilt headroom, centring, symmetry and length."""
    out: list[str] = []
    grid = build_grid(car, "none", dark=True) if car.model.lights else build_grid(car)
    d = grid.data
    canvas = ROAD_CANVAS if car.road else CANVAS
    if d.shape != canvas:
        return [f"{car.key}: canvas {d.shape}, expected {canvas}"]
    (x0, x1), _, (_, z1) = grid.bounds()
    if not car.road and z1 > MAX_Z:
        out.append(f"{car.key}: z {z1} > {MAX_Z} leaves too little headroom for the hill tilt")
    off = (x0 + x1) / 2 - (canvas[0] - 1) / 2
    if abs(off) > 0.5:
        out.append(f"{car.key}: off-centre in x by {off:+.1f} voxels (bounds {x0}..{x1})")
    per_unit = 14 if car.road else 3.2 * VOX_PER_M  # voxels per 1/8 unit, before the squash
    length, allowed = x1 - x0 + 1, car.ottd_length * per_unit
    if length > allowed:
        out.append(f"{car.key}: {length} voxels long, OpenTTD length {car.ottd_length} allows {allowed:.0f}")
    elif length < MIN_FILL * allowed:
        out.append(f"{car.key}: only {length} of {allowed:.0f} voxels long: gaps between vehicles")
    if not car.road:  # buses have doors on one side
        occ = d != 0
        asym = int((occ != occ[:, ::-1, :])[:, :, :SYMMETRIC_BELOW_Z].sum())
        if asym:
            out.append(f"{car.key}: {asym} voxels below z {SYMMETRIC_BELOW_Z} are not left/right symmetric")
    return out


def check_palette(v: Vehicle, car: CarSpec) -> list[str]:
    """No special palette ranges; company colours stay out of recolourable cargo wagons."""
    out: list[str] = []
    d = build_grid(car).data
    used = set(np.unique(d).tolist())
    special = sorted(used & set(SPECIAL_INDICES))
    if special:
        out.append(f"{car.key}: uses animated/special palette indices {special}")
    cargo = _is_cargo_wagon(car)
    mask = sorted(used & set(range(P.CARGO_MASK[0], P.CARGO_MASK[1] + 1)))
    if mask and not cargo:
        out.append(f"{car.key}: cargo mask indices {mask} without a CARGO spec")
    if cargo:
        looks = load_recipe(model_dir(car) / "recipe.py").CARGO.looks
        cc = (d >= P.CC1[0]) & (d <= P.CC1[1]) | (d >= P.CC2[0]) & (d <= P.CC2[1])
        if any(colour for colour in looks.values()) and cc.any():
            out.append(
                f"{car.key}: {int(cc.sum())} company-colour voxels on a wagon with recolourable cargo "
                "(the cargo palette would recolour them, see voxel/cargo.py)"
            )
    return out


def check_lamps(v: Vehicle, car: CarSpec) -> list[str]:
    """Dark bodies carry no lit lamps; coaches and wagons never show white headlamps."""
    if not car.model.lights:
        return []
    out: list[str] = []
    for var in variants(car):
        dark = build_grid(car, var, dark=True).data
        if ((dark == LAMP_WHITE) | (dark == LAMP_RED)).any():
            out.append(f"{car.key}/{var}: lit lamp voxels in the dark body (paint lamps via parts.lights only)")
        if v.kind in ("coach", "wagon") and (build_grid(car, var).data == LAMP_WHITE).any():
            out.append(f"{car.key}/{var}: white headlamps on a {v.kind} (it never leads a train)")
    return out


def check_coupling(v: Vehicle, car: CarSpec) -> list[str]:
    """Buffer plates at the gauge's coupling height at both ends, so coupled vehicles line up."""
    if v.cars or v.is_road or v.kind not in BUFFERED_KINDS:
        return []  # multiple units couple inside the unit
    gauge = "metre" if (v.railtype or "").startswith("metre") else "standard"
    want = (COUPLING_Z[gauge] - 2, COUPLING_Z[gauge] + 3)  # running_gear.buffers plate
    grid = build_grid(car, "none", dark=True) if car.model.lights else build_grid(car)
    occ = grid.data != 0
    (x0, x1), _, _ = grid.bounds()
    out = []
    for name, x in (("rear", x0), ("front", x1)):
        zs = set(np.flatnonzero(occ[x].any(axis=0)).tolist())
        # the plate is the lowest thing at the very end (a gangway may stand above it)
        if min(zs) != want[0] or not set(range(want[0], want[1] + 1)) <= zs:
            out.append(
                f"{car.key}: no buffer plate at z {want[0]}..{want[1]} at the {name} end "
                f"(lowest voxel there: z {min(zs)}); use running_gear.buffers for the {gauge} gauge"
            )
    return out


def check_width(v: Vehicle, car: CarSpec) -> list[str]:
    """Train recipes give their real body width; the render step scales the body to it."""
    if car.road or car.model.kind != "recipe":
        return []
    if getattr(load_recipe(model_dir(car) / "recipe.py"), "BODY_WIDTH_M", None) is None:
        return [f"{car.key}: recipe sets no BODY_WIDTH_M, so the body renders at its authored width"]
    return []


CHECKS = (check_shape, check_palette, check_lamps, check_coupling, check_width)


def check_vehicle(v: Vehicle) -> list[str]:
    return [p for car in v.car_specs for check in CHECKS for p in check(v, car)]


def check_all() -> list[str]:
    return [p for v in vehicles().values() for p in check_vehicle(v)]
