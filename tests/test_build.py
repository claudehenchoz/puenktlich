"""End-to-end smoke test: recipes -> gorender -> NML -> nmlc. Skipped without GoRender."""

import shutil

import pytest

from puenktlich import paths
from puenktlich.models import write_model
from puenktlich.nml.generate import compile_grf, generate
from puenktlich.render import gorender
from puenktlich.schema import vehicles
from puenktlich.sprites import lint_sheets

pytestmark = pytest.mark.skipif(not paths.GORENDER.exists(), reason="run tools/install.sh first")


def test_full_build(tmp_path) -> None:
    if shutil.which("nmlc") is None:
        pytest.skip("nmlc not installed")
    for v in vehicles().values():
        vox = write_model(v)
        out = paths.BUILD_SPRITES / v.id
        gorender([vox], out)
        assert lint_sheets(out, v.id, v.ottd_length) == []
    nml = generate(tmp_path / "nml")
    grf = compile_grf(nml, tmp_path / "test.grf")
    assert grf.stat().st_size > 1000
