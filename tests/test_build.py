"""End-to-end smoke test: recipes -> Cargopositor -> GoRender -> NML -> nmlc. Skipped without tools."""

import shutil

import pytest

from puenktlich import paths
from puenktlich.nml.generate import compile_grf, generate
from puenktlich.pipeline import render_vehicle
from puenktlich.schema import vehicles

pytestmark = pytest.mark.skipif(
    not (paths.GORENDER.exists() and paths.CARGOPOSITOR.exists()), reason="run tools/install.sh first"
)


def test_full_build(tmp_path) -> None:
    if shutil.which("nmlc") is None:
        pytest.skip("nmlc not installed")
    for v in vehicles().values():
        _, problems, _ = render_vehicle(v)
        assert problems == []
    nml = generate(tmp_path / "nml")
    text = nml.read_text()
    # 3-part articulation with invisible ends, curve and hill sprites, light variants
    assert "articulated_part: sw_re460_sbb_articulated" in text
    assert "ss_invisible" in text
    for kind in ("turn_1", "turn_2", "up", "down"):
        assert f"ss_re460_solo_{kind}" in text
    assert "sw_re460_lights" in text
    grf = compile_grf(nml, tmp_path / "test.grf")
    assert grf.stat().st_size > 1000
