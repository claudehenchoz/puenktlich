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
