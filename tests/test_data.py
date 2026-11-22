import pytest
from pydantic import ValidationError

from puenktlich.schema import Livery, validate_all, vehicles


def test_all_data_validates() -> None:
    assert validate_all() == []


def test_vehicle_ids_and_grf_ids_unique() -> None:
    vs = list(vehicles().values())
    assert len({v.grf_id for v in vs}) == len(vs)


def test_lengths_are_sane() -> None:
    for v in vehicles().values():
        assert 1 <= v.ottd_length <= 8, v.id


def test_fixed_livery_requires_colours() -> None:
    with pytest.raises(ValidationError):
        Livery(id="x", name={"en": "x"}, company_colours=False)


def test_wagons_have_capacity_and_no_power() -> None:
    for v in vehicles().values():
        if v.kind in ("coach", "wagon"):
            assert v.power_kw == 0, v.id
            assert v.capacity, v.id


def test_control_cars_are_nominal_engines() -> None:
    """Control cars carry a nominal power so they can lead a train (OpenTTD needs an
    engine in front); it must stay token-sized."""
    for v in vehicles().values():
        if v.kind == "control_car":
            assert 0 < v.power_kw <= 10, v.id
            assert v.capacity, v.id


def test_rail_and_road_vehicles_have_the_right_track() -> None:
    for v in vehicles().values():
        if v.is_road:
            assert v.railtype is None and v.road_type in ("road", "tram"), v.id
            assert all(c.road for c in v.car_specs), v.id
        else:
            assert v.railtype is not None, v.id


def test_road_vehicle_lengths() -> None:
    vs = vehicles()
    assert vs["citaro"].ottd_length == 8  # 12 m solo bus fills the 12.6 m road canvas
    assert [c.ottd_length for c in vs["citaro_g"].car_specs] == [6, 4]  # Timberwolf's Citaro G


def test_rack_track_needs_a_rack_engine() -> None:
    """OpenTTD lets a train enter track on which one of its engines has power, so adhesion
    railtypes must not be powered on rack railtypes, and rack railtypes power everywhere."""
    import yaml

    from puenktlich import paths

    tracks = {t["label"]: t for t in yaml.safe_load((paths.DATA / "tracks.yaml").read_text(encoding="utf-8"))}
    rack = {lab for lab, t in tracks.items() if t["style"] == "metre_rack"}
    for lab, t in tracks.items():
        if lab in rack:
            assert {"NAAN", "NAAE"} & set(t["powered"]), lab
        else:
            assert not rack & set(t["powered"]), f"{lab} is powered on rack track"


def test_saved_game_ids_are_locked() -> None:
    """data/ids.lock pins grf_ids and livery order (item id = grf_id * 8 + livery index)."""
    from puenktlich import lock

    assert lock.problems() == []
    vs = dict(vehicles())
    re460 = vs["re460"]
    moved = re460.model_copy(update={"grf_id": re460.grf_id + 900})
    assert any("grf_id changed" in p for p in lock.problems(vs | {"re460": moved}))
    swapped = re460.model_copy(update={"liveries": list(reversed(re460.liveries))})
    assert any("append-only" in p for p in lock.problems(vs | {"re460": swapped}))
    removed = {k: v for k, v in vs.items() if k != "re460"}
    assert any("no longer in data/vehicles" in p for p in lock.problems(removed))
    reused = re460.model_copy(update={"id": "other"})
    assert any("can't be reused" in p for p in lock.problems(removed | {"other": reused}, lock.load()))


def test_schema_rejects_data_that_would_break_the_build() -> None:
    """Rules that used to surface only at build time (or not at all)."""
    from puenktlich.schema import MAX_GRF_ID, Track, Vehicle

    base = vehicles()["re460"].model_dump()
    coach = vehicles()["ew4_a"].model_dump()

    def bad(data: dict, **changes) -> None:
        with pytest.raises(ValidationError):
            Vehicle(**(data | changes))

    Vehicle(**(base | {"grf_id": MAX_GRF_ID}))
    bad(base, grf_id=MAX_GRF_ID + 1)  # item id grf_id * 8 + 7 would not fit 16 bits
    bad(base, liveries=base["liveries"] * 5)  # more than 8 liveries: outside the item-id block
    bad(base, retire_year=base["intro_year"])
    bad(coach, capacity={"PASS": 60, "MAIL": 5})  # one default cargo
    bad(coach, capacity={"WOOD": 30})  # unknown label without refit_classes
    Vehicle(**(coach | {"capacity": {"WOOD": 30}, "refit_classes": ["CC_PIECE_GOODS"]}))
    bad(coach, refit_classes=["CC_NONSENSE"])
    bad(coach, power_kw=500)
    bad(coach, capacity={})
    track = next(iter(__import__("puenktlich.schema", fromlist=["tracks"]).tracks().values())).model_dump()
    with pytest.raises(ValidationError):
        Track(**(track | {"powered": ["XXXX"]}))  # powered must be a subset of compatible
    with pytest.raises(ValidationError):
        Track(**(track | {"style": "narrow"}))
