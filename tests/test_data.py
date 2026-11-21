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
