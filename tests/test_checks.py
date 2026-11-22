"""The modelling conventions (puenktlich/checks.py): every vehicle passes, and each check
really catches what it is for."""

import numpy as np
import pytest

from puenktlich import checks
from puenktlich.models import build_grid
from puenktlich.schema import vehicles
from puenktlich.voxel.vox import VoxelGrid


def test_all_models_follow_the_conventions() -> None:
    assert checks.check_all() == []


@pytest.fixture
def tampered(monkeypatch):
    """Run one check on a vehicle whose grid went through `edit` first."""

    def run(check, vehicle_id: str, edit) -> list[str]:
        v = vehicles()[vehicle_id]
        car = v.car_specs[0]

        def fake(target, variant="solo", dark=False):
            grid = VoxelGrid(build_grid(target, variant, dark).data.copy())
            edit(grid.data)
            return grid

        monkeypatch.setattr(checks, "build_grid", fake)
        return check(v, car)

    return run


def test_shape_check_catches_height_centring_and_asymmetry(tampered) -> None:
    def too_tall(d):
        d[128, 20, 70] = 5

    def lopsided(d):
        d[100:110, 0, 20] = 5

    def shifted(d):
        d[:] = np.roll(d, 3, axis=0)

    assert any("headroom" in p for p in tampered(checks.check_shape, "re460", too_tall))
    assert any("symmetric" in p for p in tampered(checks.check_shape, "re460", lopsided))
    assert any("off-centre" in p for p in tampered(checks.check_shape, "re460", shifted))


def test_shape_check_catches_wrong_length(tampered) -> None:
    def stretched(d):
        d[2:254, 20, 20] = 5  # the Re 460 is 6/8 = 192 voxels

    def shortened(d):
        d[:80] = 0
        d[176:] = 0

    assert any("allows" in p for p in tampered(checks.check_shape, "re460", stretched))
    assert any("gaps" in p for p in tampered(checks.check_shape, "re460", shortened))


def test_coupling_check_catches_buffers_at_the_wrong_height(tampered) -> None:
    def raised(d):
        d[:, :, 3:] = d[:, :, :-3].copy()

    assert checks.check_coupling(vehicles()["re460"], vehicles()["re460"].car_specs[0]) == []
    assert len(tampered(checks.check_coupling, "re460", raised)) == 2  # both ends
    assert len(tampered(checks.check_coupling, "glacier_bp", raised)) == 2


def test_lamp_check_catches_white_lamps_on_a_coach(tampered) -> None:
    def headlamp(d):
        d[254, 20, 20] = checks.LAMP_WHITE

    problems = tampered(checks.check_lamps, "ew4_a", headlamp)
    assert any("white headlamps on a coach" in p for p in problems)
    assert any("dark body" in p for p in problems)


def test_palette_check_catches_special_colours_and_cc_in_cargo_wagons(tampered) -> None:
    def pink(d):
        d[128, 20, 30] = 220

    def company_colour(d):
        d[128, 20, 30] = 200

    assert any("special palette" in p for p in tampered(checks.check_palette, "re460", pink))
    assert any("company-colour" in p for p in tampered(checks.check_palette, "eanos", company_colour))
    assert tampered(checks.check_palette, "sgns", company_colour) == []  # containers keep their colours
