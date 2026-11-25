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


def test_fv_dosto_true_proportions() -> None:
    """FV-Dosto (REFERENCE.md, measured from the 3D model and the factsheets): body 34 voxels wide
    for 2.80 m against the 4.59 m roof at z 56 (true width:height), lower deck down to z 3 between
    the doors, intermediate levels at z 9, end car 25.32 m with a lower cab roof and a nose that
    is narrower in plan than the body."""
    from puenktlich.voxel.parts.fv_dosto import (
        CAB_ROOF,
        HALF_WIDTH,
        HIGH_FLOOR,
        LOW_FLOOR,
        ROOF,
        FvSpec,
        build_fv_car,
        end_car,
    )
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    none = LIGHT_VARIANTS["none"]
    d = build_fv_car(FvSpec(), none).grid.data
    mid = d.shape[0] // 2
    width = np.flatnonzero(d[mid, :, 30]).size
    assert width == 2 * HALF_WIDTH and abs(width / ROOF - 2.80 / 4.59) < 0.02
    side = d[:, 21 - HALF_WIDTH + 2, :]  # inside the tumblehome
    assert np.flatnonzero(side[mid])[0] == LOW_FLOOR
    body = np.flatnonzero(d[:, 20, ROOF])  # roof line: the body without the gangway bellows
    assert np.flatnonzero(side[body[0] + 4])[0] >= HIGH_FLOOR  # intermediate level, in front of the bogie
    assert np.flatnonzero(d[mid, 20, :])[-1] == ROOF

    cab = build_fv_car(end_car(mu_role="front"), none).grid.data
    xs = np.flatnonzero(cab[:, 20, :].any(axis=1))
    assert abs((xs[-1] - xs[0] + 1) - 253) <= 2  # 25.32 m
    assert np.flatnonzero(cab[xs[-1] - 50, 20, :])[-1] <= CAB_ROOF  # cab section roof
    tip_width = np.flatnonzero(cab[xs[-1] - 3, :, 14]).size
    assert 0 < tip_width < 2 * HALF_WIDTH - 10  # tapered in plan


def test_regio_dosto_proportions() -> None:
    """RABe 511 in true proportions (models/sbb/rabe511/REFERENCE.md): body 34 voxels wide
    (2.80 m), roof z 56 (4.595 m), intermediate cars at their real length (24.7 m); the skirt is
    the dark CC2 shade, so the S-Bahn Zürich (blue) and RegioExpress (grey) schemes are only a cc2
    change; the cab car's roof drops into a well at its inner end with the pantograph in it, and
    the windscreen has glass."""
    from puenktlich import models
    from puenktlich.voxel import palette as P
    from puenktlich.voxel.parts.regio_dosto import (
        LOWER_WIN,
        ROOF,
        SKIRT_TOP,
        WELL_ROOF,
        build_regio_car,
        cab_car,
    )
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    none = LIGHT_VARIANTS["none"]
    recipe = models.load_recipe(models.paths.MODELS / "sbb" / "rabe511" / "recipe.py")
    mid_car = recipe.build(none, car="second").grid.data
    xs = np.flatnonzero(mid_car.any(axis=(1, 2)))
    assert abs(xs[-1] - xs[0] + 1 - 247) <= 1  # 24.7 m, centred on the canvas
    mid = mid_car.shape[0] // 2
    assert np.flatnonzero(mid_car[mid, :, 30]).size == 34
    assert np.flatnonzero(mid_car[mid, 20, :])[-1] == ROOF - 1  # top voxel up to 4.59 m
    skirt = mid_car[mid, :, :SKIRT_TOP][:, : LOWER_WIN[0]]  # below the lower-deck windows
    side = skirt[np.flatnonzero(skirt.any(axis=1))[0]]
    assert (side[side != 0] == P.DARK_CC2).all()

    d = build_regio_car(cab_car(mu_role="front"), none).grid.data
    xs = np.flatnonzero(d.any(axis=(1, 2)))
    front, rear = xs[-1], xs[0]
    assert np.flatnonzero(d[front - 60, 20, :])[-1] == ROOF - 1  # full-height cab
    assert np.flatnonzero(d[rear + 2, 20, :])[-1] < ROOF - 4  # roof well at the inner end
    panto = np.flatnonzero((d[:, :, WELL_ROOF + 1 :] == P.LIGHT_GREY).any(axis=(1, 2)))
    assert panto.size and panto.max() < front - 180  # in the well, over the inner end
    assert P.GLASS in d[front - 10 : front + 1, 12:30, 27:42]  # windscreen
    up = recipe.build(none, car="cab_panto_up").grid.data
    assert np.flatnonzero(up.any(axis=(0, 1)))[-1] > np.flatnonzero(d.any(axis=(0, 1)))[-1]  # raised


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


def test_flirt_cars_jakobs_and_generations() -> None:
    """FLIRT: an intermediate car draws only its halves of the Jakobs bogies, a cab car adds
    the motor bogie under the cab; generation 1 has the black skirt, generation 3 is white to
    the sill, and the two noses differ."""
    from puenktlich.voxel import palette as P
    from puenktlich.voxel.parts.flirt import SKIRT_TOP, FlirtSpec, build_flirt_car, end_car
    from puenktlich.voxel.parts.running_gear import GAUGES
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    none = LIGHT_VARIANTS["none"]
    d = build_flirt_car(FlirtSpec(), none).grid.data
    body = np.flatnonzero(d[:, 20, :].any(axis=1))
    x0, x1 = body[0], body[-1]
    occ = np.flatnonzero(d.any(axis=(1, 2)))
    assert occ[0] >= x0 and occ[-1] <= x1
    wheels = np.flatnonzero(d[:, GAUGES["standard"] + 1, 1])
    assert wheels.min() < x0 + 20 and wheels.max() > x1 - 20
    assert not ((wheels > x0 + 30) & (wheels < x1 - 30)).any()

    cab1 = build_flirt_car(end_car(generation=1, mu_role="front"), none).grid.data
    cab3 = build_flirt_car(end_car(generation=3, mu_role="front"), none).grid.data
    cab_wheels = np.flatnonzero(cab1[:, GAUGES["standard"] + 1, 1])
    front = np.flatnonzero(cab1.any(axis=(1, 2)))[-1]
    assert ((cab_wheels > front - 60) & (cab_wheels < front - 20)).any()  # motor bogie under the cab
    mid = d.shape[0] // 2
    skirt1 = cab1[mid, 1, : SKIRT_TOP - 1]
    skirt3 = cab3[mid, 1, : SKIRT_TOP - 1]
    assert (skirt1[skirt1 != 0] == P.BLACK).all()
    assert P.BLACK not in skirt3[skirt3 != 0]
    assert (cab1[front - 30 :] != cab3[front - 30 :]).any()


def test_ir_dosto_proportions() -> None:
    """RABe 512 in true proportions (models/sbb/rabe512/REFERENCE.md): body 34 voxels wide
    (2.80 m), roof z 56 (4.595 m) and the cab section's lower roof; intermediate cars at their
    real length (24.8 m); upper-deck windows only over the double-deck section of the cab car;
    glass in the windscreen; the pantograph on the cab car over its inner end."""
    from puenktlich import models
    from puenktlich.voxel import palette as P
    from puenktlich.voxel.parts.ir_dosto import CAB_ROOF, ROOF, UPPER_WIN, build_ir_car, cab_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    none = LIGHT_VARIANTS["none"]
    recipe = models.load_recipe(models.paths.MODELS / "sbb" / "rabe512" / "recipe.py")
    mid_car = recipe.build(none, car="second").grid.data
    xs = np.flatnonzero(mid_car.any(axis=(1, 2)))
    assert xs[-1] - xs[0] + 1 == 248  # 24.8 m
    mid = mid_car.shape[0] // 2
    assert np.flatnonzero(mid_car[mid, :, 30]).size == 34
    assert np.flatnonzero(mid_car[mid, 20, :])[-1] == ROOF

    spec = cab_car(mu_role="front")
    d = build_ir_car(spec, none).grid.data
    front = np.flatnonzero(d.any(axis=(1, 2)))[-1]
    assert np.flatnonzero(d[front - 30, 20, :])[-1] == CAB_ROOF  # cab section, 3 m behind the tip
    scale = spec.length_m / spec.real_m
    door1 = int(front - spec.doors[0][0] * 10 * scale)
    side = d[:, 0:6, UPPER_WIN[0] + 1 : UPPER_WIN[1] - 1]
    assert P.GLASS not in side[door1 + 10 : front - 40]  # no upper deck over the cab section
    assert P.GLASS in side[door1 - 100 : door1]
    assert P.GLASS in d[front - 30 : front + 1, 12:30, 34:48]  # windscreen
    panto = np.flatnonzero((d[:, :, ROOF + 1 :] == P.LIGHT_GREY).any(axis=(1, 2)))
    assert panto.size and panto.max() < front - 200  # over the inner end


def test_tilting_icn_taper_and_nose() -> None:
    """ICN: the body narrows above the window band (tilting profile), and the cab car's nose is
    pointed (the roof far behind the tip)."""
    from puenktlich.voxel.parts.tilting import STYLES, TiltSpec, build_tilting_car, cab_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    none = LIGHT_VARIANTS["none"]
    st = STYLES["icn"]
    d = build_tilting_car(TiltSpec(style="icn"), none).grid.data
    mid = d.shape[0] // 2
    widths = [np.flatnonzero(d[mid, :, z]).size for z in (st.band[0], st.roof - 4)]
    assert widths[0] > widths[1]  # tapered upper body
    assert np.flatnonzero(d[mid, 20, :])[-1] == st.roof
    cab = build_tilting_car(cab_car("icn", mu_role="front"), none).grid.data
    front = np.flatnonzero(cab.any(axis=(1, 2)))[-1]
    tip_z = np.flatnonzero(cab[front, 20, :])
    assert tip_z.size and tip_z.max() < st.roof - 15


def test_etr610_proportions() -> None:
    """RABe 503 / ETR 610 in true proportions (models/sbb/rabe503/REFERENCE.md): body 34 voxels
    wide (2.83 m), roof z 50 (4.10 m), tilting taper above the window band, a long low nose
    (tip at the bumper height, roof reached ~10.35 m back: the measured 6.9 m stretched 1.5x so it
    reads long at half-length rendering), pantographs as in the GDL brochure."""
    from puenktlich import models
    from puenktlich.voxel.parts.etr610 import BAND, ROOF, build_etr_car, end_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    recipe = models.load_recipe(models.paths.MODELS / "sbb" / "rabe503" / "recipe.py")
    none = LIGHT_VARIANTS["none"]
    d = recipe.build(none, car="second_db").grid.data
    mid = d.shape[0] // 2
    assert np.flatnonzero(d[mid, :, BAND[0]]).size == 34
    assert np.flatnonzero(d[mid, :, ROOF - 4]).size < 34  # tilting taper
    assert np.flatnonzero(d[mid - 60, 20, :])[-1] == ROOF  # beside the roof hump
    cab = build_etr_car(end_car(mu_role="front"), none).grid.data
    front = np.flatnonzero(cab.any(axis=(1, 2)))[-1]
    assert np.flatnonzero(cab[front, 20, :]).max() < 18  # tip at ~1.2 m
    roof_x = np.flatnonzero(cab[:, 20, ROOF])
    assert front - roof_x.max() > 85  # the roof starts ~9.6 modelled metres behind the tip

    def pantographs(car: str) -> int:  # pantograph bases: light-grey insulator clusters on the roof
        g = recipe.build(none, car=car).grid.data
        roof_top = g[:, :, ROOF : ROOF + 3]
        cols = np.flatnonzero((roof_top == models.P.LIGHT_GREY).any(axis=(1, 2)))
        return int((np.diff(cols) > 20).sum() + 1) if cols.size else 0

    assert [pantographs(c) for c in ("first", "dining", "second_pan_up", "second_pan", "second_db")] == [0, 1, 2, 2, 1]


def test_dtz_end_car() -> None:
    """RABe 514: red (CC1) front, S-Bahn Zürich dark CC2 skirt, a pantograph over the cab section
    (raised on request), no KISS roof well."""
    from puenktlich.voxel import palette as P
    from puenktlich.voxel.parts.dosto import ROOF
    from puenktlich.voxel.parts.kiss import SKIRT_TOP, build_kiss_car, dtz_cab_car
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    d = build_kiss_car(dtz_cab_car(mu_role="front", pantograph_raised=True), LIGHT_VARIANTS["none"]).grid.data
    front = np.flatnonzero(d.any(axis=(1, 2)))[-1]
    assert P.BODY_CC1 in d[front - 3 : front + 1, 10:30, 20:30]
    mid = d.shape[0] // 2
    skirt = d[mid, 1, :SKIRT_TOP]
    assert (skirt[skirt != 0] == P.DARK_CC2).all()
    assert d[front - 60 : front - 40, 18:23, ROOF + 6 :].any()  # raised pantograph
    assert np.flatnonzero(d[mid, 20, :])[-1] == ROOF


def test_hood_locos() -> None:
    """Aem 940 / Eem 923: the cab stands above both hoods, cab glass on the sides, buffers at both
    ends, lamps white at the front and red at the rear; the Eem's short hood is CC2 (cargo)."""
    import importlib.util

    from puenktlich import paths
    from puenktlich.voxel import palette as P
    from puenktlich.voxel.parts.hood import build_hood_loco
    from puenktlich.voxel.parts.lights import LAMP_RED, LAMP_WHITE
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    for name in ("aem940", "eem923", "ee922"):
        path = paths.ROOT / "models" / "sbb" / name / "recipe.py"
        mod = importlib.util.module_from_spec(spec := importlib.util.spec_from_file_location(name, path))
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        s = mod.SPEC
        d = build_hood_loco(s, LIGHT_VARIANTS["solo"]).grid.data
        assert s.cab.top > max(h.top for h in s.hoods)
        assert P.GLASS in d
        occ = np.flatnonzero(d.any(axis=(1, 2)))
        front, rear = d[occ[-1] - 14 :], d[: occ[0] + 15]  # buffers stick out ~6, hoods start 3 behind
        assert LAMP_WHITE in front and LAMP_RED in rear
        if s.livery == "cargo":
            assert P.BODY_CC2 in d[occ[-1] - 25 :, :, s.frame_z[1] : s.hoods[0].top]


def test_ic2000_coaches() -> None:
    """IC2000: coaches have buffers at both ends and red tail lamps when last; the Bt turns its
    cab outward with red lamps when it is the last vehicle."""
    from puenktlich.voxel.parts.kiss import build_kiss_car, ic2000_bt, ic2000_coach
    from puenktlich.voxel.parts.lights import LAMP_RED, LAMP_WHITE
    from puenktlich.voxel.parts.running_gear import COUPLING_Z
    from puenktlich.voxel.variants import LIGHT_VARIANTS

    d = build_kiss_car(ic2000_coach(), LIGHT_VARIANTS["tail"]).grid.data
    occ = np.flatnonzero(d.any(axis=(1, 2)))
    for x in (occ[0], occ[-1]):  # buffer plates stick out at coupling height
        assert d[x, :, COUPLING_Z["standard"]].any()
    assert LAMP_RED in d[: occ[0] + 12] and LAMP_WHITE not in d  # behind the buffers
    head = build_kiss_car(ic2000_bt(), LIGHT_VARIANTS["head"]).grid.data
    tail = build_kiss_car(ic2000_bt(), LIGHT_VARIANTS["tail"]).grid.data
    hx, tx = np.flatnonzero(head.any(axis=(1, 2))), np.flatnonzero(tail.any(axis=(1, 2)))
    assert LAMP_WHITE in head[hx[-1] - 14 :]  # cab leading: white
    assert LAMP_RED in tail[: tx[0] + 14]  # last: cab turned to the rear, red


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


def test_vbz_city_buses() -> None:
    """VBZ buses: blue (CC1) skirt and white (CC2) sides, doors only on the kerb side, trolley
    poles only on the last section of a trolleybus, axles where the layout puts them."""
    from puenktlich.models import load_recipe
    from puenktlich.voxel.parts.citybus import CANTRAIL, SECTION, SKIRT_TOP, WINDOW, build_city_bus

    root = Path(__file__).parent.parent / "models" / "vbz"
    trolley = load_recipe(root / "hess_trolley" / "recipe.py").TYPES["lt3"]
    cars = [build_city_bus(trolley, k) for k in range(3)]
    for mdl in cars:
        d = mdl.d
        assert (d[:, :, : SKIRT_TOP + 1] == P.BODY_CC1).sum() > 200  # blue skirt
        assert (d[:, :, SKIRT_TOP + 1 : WINDOW[0]] == P.BODY_CC2).sum() > 200  # white below the windows
        assert (d[:, :, CANTRAIL] == P.BODY_CC1).any()  # blue cantrail line
    poles = [int((m.d[:, :, SECTION.roof + 2 :] == P.DARK_GREY).sum()) for m in cars]
    assert poles[0] == poles[1] == 0 and poles[2] > 20
    # doors (glass from the floor up) on the kerb side (high y) only
    d = cars[0].d
    low = d[:, :, SECTION.floor + 3]
    assert (low[:, 20:] == P.GLASS).any() and not (low[:, :20] == P.GLASS).any()
    # the solo bus fills its OpenTTD length and has two axles
    man = load_recipe(root / "lions_city" / "recipe.py").TYPES["12e"]
    mdl = build_city_bus(man)
    xs = np.nonzero((mdl.d != 0).any(axis=(1, 2)))[0]
    assert 108 <= xs.max() - xs.min() + 1 <= 112
    tyres = np.nonzero((mdl.d[:, :8, 2:8] == P.BLACK).any(axis=(1, 2)))[0]
    assert len(np.split(tyres, np.nonzero(np.diff(tyres) > 1)[0] + 1)) == 2
