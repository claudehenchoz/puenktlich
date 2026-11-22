"""NML generation checks that need no rendered sprites."""

import pytest

from puenktlich import paths
from puenktlich.nml.generate import split_capacity
from puenktlich.render import parts_for
from puenktlich.schema import vehicles


def test_split_capacity_is_exact() -> None:
    assert split_capacity(422, [1] * 33) == [13] * 26 + [12] * 7
    assert split_capacity(58, [1, 1, 1]) == [20, 19, 19]
    assert split_capacity(60, [1, 1, 1]) == [20, 20, 20]
    assert split_capacity(100, [6, 4]) == [60, 40]
    assert split_capacity(2, [1, 1, 1]) == [1, 1, 0]


def test_every_vehicle_carries_exactly_its_capacity() -> None:
    """Articulated parts share one item, so capacity is split per part: the shares must
    add up to the capacity in the vehicle YAML (not round(total / parts) * parts)."""
    for v in vehicles().values():
        for total in v.capacity.values():
            if v.is_road:
                weights = [c.ottd_length for c in v.car_specs]
            else:
                weights = [1 for c in v.car_specs for _ in parts_for(c.ottd_length)]
            assert sum(split_capacity(total, weights)) == total, v.id


@pytest.fixture(scope="module")
def nml(tmp_path_factory) -> str:
    """The generated NML (no rendered sheets needed: sprite paths are only names here)."""
    if not paths.CARGOPOSITOR.exists():
        pytest.skip("cargopositor not installed (freight wagon plans)")
    from puenktlich.nml.generate import generate

    return generate(tmp_path_factory.mktemp("nml")).read_text(encoding="utf-8")


def _item(nml: str, ident: str) -> str:
    start = nml.index(f"item(FEAT_TRAINS, {ident},") if f"item(FEAT_TRAINS, {ident}," in nml else -1
    if start < 0:
        start = nml.index(f"item(FEAT_ROADVEHS, {ident},")
    return nml[start : nml.index("\n}\n", start)]


def test_nml_has_one_item_per_livery_with_locked_ids(nml) -> None:
    for v in vehicles().values():
        for i, livery in enumerate(v.liveries):
            feature = "FEAT_ROADVEHS" if v.is_road else "FEAT_TRAINS"
            assert f"item({feature}, {v.id}_{livery.id}, {v.grf_id * 8 + i})" in nml


def test_uneven_capacity_uses_the_per_part_callback(nml) -> None:
    giruno = _item(nml, "giruno_sbb")
    assert "cargo_capacity: sw_giruno_capacity;" in giruno
    assert "switch (FEAT_TRAINS, SELF, sw_giruno_capacity, position_in_articulated_veh)" in nml
    assert "sw_ew4_a_capacity" not in nml  # 60 seats / 3 parts divides evenly: property only


def test_livery_variants_share_news_and_reliability(nml) -> None:
    first, variant = _item(nml, "re460_sbb"), _item(nml, "re460_company")
    assert "extra_flags" not in first and "variant_group" not in first
    assert "variant_group: re460_sbb;" in variant
    for flag in ("DISABLE_NEW_VEHICLE_MESSAGE", "SYNC_VARIANT_EXCLUSIVE_PREVIEW", "SYNC_VARIANT_RELIABILITY"):
        assert f"VEHICLE_FLAG_{flag}" in variant


def test_badges_for_operator_gauge_and_traction(nml) -> None:
    from puenktlich.nml.generate import vehicle_badges

    vs = vehicles()
    assert vehicle_badges(vs["re460"]) == ["operator/sbb", "gauge/standard", "traction/electric"]
    assert vehicle_badges(vs["hge44ii"]) == ["operator/mgb", "gauge/metre", "traction/rack"]
    assert vehicle_badges(vs["ew4_rhb_a"]) == ["operator/rhb", "gauge/metre"]  # coaches have no traction
    assert vehicle_badges(vs["ew4_bt"])[1:] == ["gauge/standard"]  # nominal power only
    assert vehicle_badges(vs["citaro"]) == ["operator/postauto", "traction/diesel"]
    for label in ("gauge", "gauge/metre", "traction", "traction/rack"):
        assert f'label: "{label}";' in nml
    assert 'badges: ["operator/mgb", "gauge/metre", "traction/rack"];' in _item(nml, "hge44ii_mgb")


def test_multiple_units_get_a_whole_unit_purchase_sprite_and_the_mu_flag(nml) -> None:
    from puenktlich.sprites import purchase_layout, purchase_rect

    assert "purchase: ss_giruno_purchase;" in _item(nml, "giruno_sbb")
    assert "TRAIN_FLAG_MU" in _item(nml, "giruno_sbb") and "TRAIN_FLAG_MU" not in _item(nml, "re460_sbb")
    assert "purchase: ss_re460_body0_normal;" in _item(nml, "re460_sbb")
    assert purchase_layout([8, 8, 8]) == [(0, 8), (1, 8), (2, 8)]  # NPZ: the whole unit
    assert purchase_layout([7, 5, 5, 5, 7]) == [(0, 7), (1, 5), (4, 7)]  # front, second and rear car
    one, three = purchase_rect(1, [(0, 8)]), purchase_rect(1, [(0, 8), (1, 8), (2, 8)])
    assert three.w - one.w == 2 * 8 * 4  # 4 px per 1/8 unit at 1x
    assert purchase_rect(4, [(0, 8)]).w == 4 * one.w


def test_model_life_follows_retire_year() -> None:
    from puenktlich.nml.generate import model_life

    re460 = vehicles()["re460"]
    assert model_life(re460) == re460.model_life_years
    assert model_life(re460.model_copy(update={"retire_year": re460.intro_year + 45})) == 45
