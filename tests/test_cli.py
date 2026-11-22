"""Command-line smoke tests and the `pk new` scaffold."""

import pytest
from typer.testing import CliRunner

from puenktlich import paths, scaffold
from puenktlich.cli import app
from puenktlich.models import load_recipe
from puenktlich.schema import load_vehicle, operators, vehicles
from puenktlich.voxel.model import CANVAS, ROAD_CANVAS, Model

runner = CliRunner()


def test_list_shows_every_vehicle() -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    for vid in vehicles():
        assert vid in result.output


def test_vox_writes_models(tmp_path, monkeypatch) -> None:
    """`pk vox` once crashed on the (plans, files) tuple of write_models."""
    monkeypatch.setattr(paths, "BUILD_VOX", tmp_path)
    result = runner.invoke(app, ["vox", "citaro"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "citaro" / "base" / "citaro_body0.vox").exists()


def test_vox_rejects_unknown_ids() -> None:
    result = runner.invoke(app, ["vox", "no_such_vehicle"])
    assert result.exit_code != 0 and "unknown vehicle id" in result.output


def test_lint_data_and_lock_are_clean() -> None:
    assert runner.invoke(app, ["lint", "--no-sprites", "--no-models"]).exit_code == 0
    result = runner.invoke(app, ["lock"])
    assert result.exit_code == 0 and "0 new entries" in result.output  # nothing unlocked in the repo


def test_coverage_report() -> None:
    result = runner.invoke(app, ["coverage", "--no-write"])
    assert result.exit_code == 0 and "sbb" in result.output


def test_next_grf_id_stays_in_the_operator_block() -> None:
    ops = operators()
    used = {v.grf_id for v in vehicles().values()}
    for op in ops.values():
        nxt = scaffold.next_grf_id(op.id)
        assert op.grf_id_block <= nxt < op.grf_id_block + 100 and nxt not in used
    assert scaffold.next_grf_id("bls") == ops["bls"].grf_id_block  # no BLS vehicles yet


@pytest.mark.parametrize("kind", scaffold.KINDS)
def test_new_vehicle_stub_validates_and_builds(kind, tmp_path, monkeypatch) -> None:
    """Every `pk new` stub is valid data and its recipe builds on the right canvas."""
    monkeypatch.setattr(paths, "VEHICLES", tmp_path / "vehicles")
    monkeypatch.setattr(paths, "MODELS", tmp_path / "models")
    yaml_file, recipe, reference = scaffold.new_vehicle("bls", f"test_{kind}", kind, "BLS Test")
    assert reference.read_text().startswith("# BLS Test")
    v = load_vehicle(yaml_file)
    assert v.grf_id == operators()["bls"].grf_id_block and v.kind == kind
    assert [livery.id for livery in v.liveries] == ["bls", "company"]
    build = load_recipe(recipe).build
    for car in v.car_specs:
        model = build(**car.model.params)
        assert isinstance(model, Model) and (model.d != 0).any()
        assert model.d.shape == (ROAD_CANVAS if v.is_road else CANVAS)
    with pytest.raises(ValueError, match="already exists"):
        scaffold.new_vehicle("bls", f"test_{kind}", kind, "BLS Test")


def test_new_vehicle_refuses_bad_input() -> None:
    with pytest.raises(ValueError, match="unknown operator"):
        scaffold.new_vehicle("nobody", "x", "coach", "X")
    with pytest.raises(ValueError, match="already in use"):
        scaffold.new_vehicle("sbb", "re460", "locomotive", "X")
    with pytest.raises(ValueError, match="unknown kind"):
        scaffold.new_vehicle("sbb", "x", "zeppelin", "X")
