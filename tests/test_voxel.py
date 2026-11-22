from pathlib import Path

import numpy as np
import pytest

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CANVAS, Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell
from puenktlich.voxel.vox import VoxelGrid, read_vox, write_vox


def test_vox_roundtrip(tmp_path: Path) -> None:
    g = VoxelGrid.empty(16, 8, 12)
    g.data[1:5, 2:4, 3:9] = 202
    g.data[0, 0, 0] = 1
    write_vox(g, tmp_path / "t.vox", P.rgb_palette())
    back = read_vox(tmp_path / "t.vox")
    assert back.size == g.size
    assert np.array_equal(back.data, g.data)


def test_palette_has_256_entries() -> None:
    assert len(P.rgb_palette()) == 256
    assert P.ramp(P.CC1, 0) == 198 and P.ramp(P.CC1, 1) == 205


def test_shell_is_symmetric_and_inside_canvas() -> None:
    mdl = Model.new()
    shell = Shell(60, 196, CrossSection(), EndShape(rake=10, corner_radius=6))
    mask = np.broadcast_to(shell.mask(mdl), CANVAS)
    assert mask.any()
    # left/right symmetric
    assert np.array_equal(mask, mask[:, ::-1, :])
    # front/rear symmetric for a symmetric shell (about x = 128)
    assert np.array_equal(mask[60:197], mask[60:197][::-1])


def test_inset_recesses_surface() -> None:
    mdl = Model.new()
    mdl.solid(mdl.centred_box(50, 200, 19.5, 15, 50), 202)
    before = mdl.grid.count()
    band = mdl.box(100, 120, 0, 42, 30, 40)
    mdl.inset(band, P.GLASS)
    assert mdl.grid.count() < before
    assert (mdl.d == P.GLASS).any()


def test_light_variants_differ_at_lamps() -> None:
    from puenktlich.models import build_grid, variants
    from puenktlich.schema import vehicles
    from puenktlich.voxel.parts.lights import LAMP_RED, LAMP_WHITE

    v = vehicles()["re460"]
    assert variants(v) == ["solo", "head", "tail", "none"]
    grids = {var: build_grid(v, var).data for var in variants(v)}
    mid = grids["solo"].shape[0] // 2
    front, rear = (slice(mid, None),), (slice(0, mid),)
    assert (grids["solo"][front] == LAMP_WHITE).any() and (grids["solo"][rear] == LAMP_RED).any()
    assert (grids["head"][front] == LAMP_WHITE).any() and not (grids["head"] == LAMP_RED).any()
    assert (grids["tail"] == LAMP_RED).any() and not (grids["tail"][front] == LAMP_WHITE).any()
    assert not (grids["none"] == LAMP_RED).any()
    # only the lamp clusters differ (painted through their depth, so a few hundred voxels)
    diff = grids["solo"] != grids["none"]
    assert 0 < diff.sum() < 2000


def test_control_car_turns_cab_outward_when_last() -> None:
    """Push-pull: the Bt's cab (windscreen glass) is at the front normally and at the
    rear (low x) in the `tail` variant, i.e. when it is the last vehicle of the train."""
    from puenktlich.models import build_grid
    from puenktlich.schema import vehicles

    v = vehicles()["ew4_bt"]

    def windscreen_glass(var: str) -> tuple[int, int]:
        d = build_grid(v, var).data
        mid = d.shape[0] // 2
        upper = d[:, :, 33:48] == P.GLASS
        return int(upper[mid + 100 :].sum()), int(upper[: mid - 100].sum())  # (front end, rear end)

    front, rear = windscreen_glass("head")
    assert front > 3 * max(rear, 1)
    front, rear = windscreen_glass("tail")
    assert rear > 3 * max(front, 1)


def test_cabs_have_a_top_headlamp() -> None:
    """Swiss three-lamp pattern: a leading cab shows a white lamp above the windscreen
    (the default lamp height once missed the lower NPZ roof entirely)."""
    from puenktlich.models import build_grid
    from puenktlich.schema import vehicles
    from puenktlich.voxel.parts.lights import LAMP_WHITE

    vs = vehicles()
    for car in (vs["ew4_bt"].car_specs[0], vs["npz"].car_specs[0], vs["re460"].car_specs[0]):
        white = build_grid(car, "head").data == LAMP_WHITE
        assert white[:, :, 40:].sum() >= 8, car.key


def test_variant_plan_dedupes_bodies_and_overlays() -> None:
    from puenktlich.models import variant_plan
    from puenktlich.schema import vehicles

    vs = vehicles()
    coach = variant_plan(vs["ew4_b"])
    assert len(coach.bodies) == 1 and len(coach.overlays) == 1  # only "rear red" differs
    assert coach.mapping["head"][1] is None and coach.mapping["none"][1] is None
    assert coach.mapping["solo"][1] == coach.mapping["tail"][1]
    bt = variant_plan(vs["ew4_bt"])
    assert len(bt.bodies) == 2  # cab-front body and turned-round body
    assert bt.mapping["tail"][0] != bt.mapping["head"][0]
    loco = variant_plan(vs["re460"])
    assert len(loco.bodies) == 1 and len(loco.overlays) == 3


def test_multiple_unit_car_plans() -> None:
    from puenktlich.models import car_plans
    from puenktlich.schema import vehicles

    plans = car_plans(vehicles()["npz"])
    assert list(plans) == ["npz_c0", "npz_c1", "npz_c2"]
    (_, front), (_, middle), (_, rear) = plans.values()
    assert front.overlays and rear.overlays  # lamps only at the unit's ends
    assert not middle.overlays
    assert front.mapping["head"][1] is not None and front.mapping["tail"][1] is None
    assert rear.mapping["tail"][1] is not None and rear.mapping["head"][1] is None


def test_cargo_plan_from_cargopositor() -> None:
    from puenktlich import paths

    if not paths.CARGOPOSITOR.exists():
        import pytest

        pytest.skip("cargopositor not installed")
    from puenktlich.models import variant_plan
    from puenktlich.schema import vehicles

    plan = variant_plan(vehicles()["eanos"])
    assert len(plan.bodies) == 1 and set(plan.cargo) == {1, 2}
    body = next(iter(plan.bodies.values())).data
    assert not (body == 255).any()  # Cargopositor removed the mask
    for name in plan.cargo.values():
        loaded = plan.overlays[name][1].data
        assert ((body != 0) & (loaded != body)).sum() == 0  # cargo only adds voxels
        assert (loaded != 0).sum() > (body != 0).sum()
    assert plan.cargo_labels["COAL"] == "coal" and plan.cargo_looks["coal"] == "GREY"


def test_cargo_spec_validates() -> None:
    import pytest

    from puenktlich.voxel.cargo import CargoSpec, CargoState

    with pytest.raises(ValueError):
        CargoSpec(shapes={}, stages={1: CargoState("x"), 2: CargoState("x")}, looks={"a": None}, default_look="a")
    with pytest.raises(ValueError):
        CargoSpec(
            shapes={"x": Model.new},
            stages={1: CargoState("x"), 2: CargoState("x")},
            looks={"a": "TEAL"},
            default_look="a",
        )


def test_metre_gauge_wheels() -> None:
    from puenktlich.models import build_grid
    from puenktlich.schema import vehicles
    from puenktlich.voxel.parts.running_gear import GAUGES

    d = build_grid(vehicles()["ge44iii"]).data
    wy = GAUGES["metre"]
    wheels = d[:, :, 0:3]  # rail level: only wheel rims touch z 0..2
    ys = sorted(set(int(y) for y in wheels.nonzero()[1]))
    assert ys and min(ys) >= wy and max(ys) <= d.shape[1] - wy - 1


def test_cargo_models_are_stable_between_builds() -> None:
    """Cargopositor's `scale` is not deterministic; its cached output must make repeated
    plans identical, or every build would re-render the wagon."""
    from puenktlich import paths

    if not paths.CARGOPOSITOR.exists():
        import pytest

        pytest.skip("cargopositor not installed")
    import puenktlich.models as M
    from puenktlich.schema import vehicles

    car = vehicles()["eanos"].car_specs[0]
    first = M._plan("eanos", car)
    second = M._plan("eanos", car)
    for name in first.overlays:
        assert np.array_equal(first.overlays[name][1].data, second.overlays[name][1].data), name


def test_voxel_cache_hits(tmp_path, monkeypatch) -> None:
    import time

    from puenktlich import paths
    from puenktlich.models import build_grid
    from puenktlich.schema import vehicles

    monkeypatch.setattr(paths, "CACHE", tmp_path)
    v = vehicles()["re460"]
    a = build_grid(v, "solo")
    t = time.perf_counter()
    b = build_grid(v, "solo")
    assert time.perf_counter() - t < 0.05 and np.array_equal(a.data, b.data)
    assert list(tmp_path.glob("vox/*.npz"))


def test_rendered_length_fits_ottd_length() -> None:
    """OpenTTD draws 1/8 unit as 4 px at 1x (90° view) = 16 rendered train voxels (after
    voxel/squash.py) or 14 road voxels: a longer model overlaps its neighbours in the
    train and in the depot window."""
    from puenktlich import paths
    from puenktlich.models import car_plans
    from puenktlich.schema import vehicles

    if not paths.CARGOPOSITOR.exists():
        pytest.skip("cargopositor not installed (freight wagon plans)")
    for v in vehicles().values():
        for car, plan in car_plans(v).values():
            per_unit = 14 if car.road else 16
            for name, grid in plan.bodies.items():
                (x0, x1), _, _ = grid.bounds()
                assert x1 - x0 + 1 <= car.ottd_length * per_unit + 2, (
                    f"{name}: {x1 - x0 + 1} voxels long, OpenTTD length {car.ottd_length} "
                    f"allows {car.ottd_length * per_unit}"
                )


def test_double_deck_floor_profile() -> None:
    """FV-Dosto: lower deck reaches down to z 3 between the bogies, the intermediate levels
    over the bogies start at z 12, and the double-deck roof is at z 56 (REFERENCE.md)."""
    from puenktlich.voxel.parts.dosto import HIGH_FLOOR, LOW_FLOOR, ROOF, DostoSpec, build_dosto_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    d = build_dosto_car(DostoSpec(), LIGHT_VARIANTS["none"]).grid.data
    side = d[:, 2, :]  # body side (y 2: inside the tumblehome, outside the bogie frames)
    mid, end = d.shape[0] // 2, 20
    assert np.flatnonzero(side[mid])[0] == LOW_FLOOR
    assert np.flatnonzero(side[end])[0] >= HIGH_FLOOR
    assert np.flatnonzero(d[mid, 20, :])[-1] == ROOF


def test_face_mask_only_touches_the_front_skin() -> None:
    from puenktlich.voxel.parts.body import face_mask

    m = Model.new()
    m.solid(m.centred_box(10, 50, 10, 5, 20), 6)
    f = face_mask(m, True, depth=2)
    X, _, _ = m.coords()
    assert f.any() and (np.broadcast_to(X, f.shape)[f] >= 48).all()


def test_jakobs_half_bogies() -> None:
    """Giruno intermediate car: one wheelset under each end (the car's half of the shared
    Jakobs bogie), nothing beyond the body ends, and the low skirt between the bogies."""
    from puenktlich.voxel.parts.running_gear import GAUGES
    from puenktlich.voxel.parts.smile import SKIRT_FLOOR, SmileSpec, build_smile_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    d = build_smile_car(SmileSpec(), LIGHT_VARIANTS["none"]).grid.data
    body = np.flatnonzero(d[:, 20, :].any(axis=1))  # centre line: body, not running gear
    x0, x1 = body[0], body[-1]
    occ = np.flatnonzero(d.any(axis=(1, 2)))
    assert occ[0] >= x0 and occ[-1] <= x1  # half bogies stay under this car
    wheels = np.flatnonzero(d[:, GAUGES["standard"] + 1, 1])  # wheel rims just above the rail head
    assert wheels.size and wheels.min() < x0 + 20 and wheels.max() > x1 - 20
    assert not ((wheels > x0 + 30) & (wheels < x1 - 30)).any()
    mid = (x0 + x1) // 2
    assert np.flatnonzero(d[mid, 3, :])[0] == SKIRT_FLOOR


def test_no_unrenderable_black() -> None:
    """Palette index 1 renders transparent in GoRender: ramps and P.BLACK avoid it."""
    from puenktlich.voxel import palette as P

    assert P.BLACK != P.UNRENDERABLE_BLACK
    assert all(P.ramp(P.GREY, t / 20) != P.UNRENDERABLE_BLACK for t in range(21))


def test_chamfered_section() -> None:
    """Panorama coaches: full width up to `chamfer_from`, then a straight bevel inwards."""
    from puenktlich.voxel.parts.panorama import SECTION

    _, Y, Z = Model.new().coords()
    inside = np.broadcast_to(SECTION.mask(Y, Z), (1, *np.broadcast(Y, Z).shape[1:]))[0]
    width = inside.sum(axis=0)  # voxels across, per z
    cf = int(SECTION.chamfer_from)
    assert width[cf] == width[SECTION.floor + 8]
    roof_w = width[int(SECTION.roof) - 1]
    assert roof_w < width[cf] - 2 * SECTION.chamfer_inset + 6
    assert np.all(np.diff(width[cf : int(SECTION.roof)]) <= 0)
