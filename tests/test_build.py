"""End-to-end smoke test: recipes -> Cargopositor -> GoRender -> NML -> nmlc. Skipped without tools."""

import shutil

import pytest

from puenktlich import paths
from puenktlich.nml.generate import compile_grf, generate
from puenktlich.pipeline import render_vehicle
from puenktlich.schema import vehicles

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not (paths.GORENDER.exists() and paths.CARGOPOSITOR.exists()), reason="run tools/install.sh first"
    ),
]


def _assert_sprites_fit_length(v) -> None:
    """In the 1x 90° view OpenTTD advances 4 px per 1/8 unit: a wider sprite overlaps the
    neighbouring vehicles (and the depot window's next wagon)."""
    import numpy as np
    from PIL import Image

    from puenktlich.models import car_plans
    from puenktlich.render import sprite_layout
    from puenktlich.sprites import sheet_for

    for car, plan in car_plans(v).values():
        kind = "road" if car.road else "normal"
        rect = next(r for r in sprite_layout(1, car.ottd_length, kind) if r.angle == 90)
        for body in plan.bodies:
            img = Image.open(sheet_for(paths.BUILD_SPRITES / v.id, body, kind, 1, "32bpp")).convert("RGBA")
            alpha = np.array(img)[rect.y : rect.y + rect.h, rect.x : rect.x + rect.w, 3] > 0
            cols = np.flatnonzero(alpha.any(axis=0))
            width = cols.max() - cols.min() + 1
            assert width <= 4 * car.ottd_length + 2, f"{body}: {width} px for length {car.ottd_length}"


def test_full_build(tmp_path) -> None:
    if shutil.which("nmlc") is None:
        pytest.skip("nmlc not installed")
    for v in vehicles().values():
        _, problems, _ = render_vehicle(v)
        assert problems == []
        _assert_sprites_fit_length(v)
    nml = generate(tmp_path / "nml")
    text = nml.read_text()
    # 3-part articulation with invisible ends, curve and hill sprites
    assert "articulated_part: sw_re460_sbb_articulated" in text
    assert "ss_invisible" in text
    for kind in ("turn_1", "turn_2", "up", "down"):
        assert f"ss_re460_body0_{kind}" in text  # body, lamps dark
        assert f"ss_re460_solo_ovl_{kind}" in text  # lamp overlay layer
    # lamps are a second sprite layer, not separate full sprite sets
    assert "TRAIN_FLAG_SPRITE_STACK" in text
    assert "sw_re460_mid" in text and "sw_re460_lights_overlay" in text
    assert "ss_re460_head_normal" not in text
    # multiple unit: one stacking switch per car; freight: per-cargo looks recolour the cargo layer
    assert "sw_npz_c0_mid" in text and "sw_npz_c2_mid" in text and "sw_npz_c1_mid" not in text
    assert "COAL: sw_eanos_parts_coal" in text and "palette_1cc(COLOUR_GREY)" in text
    assert "sw_sgns_load" in text
    # road vehicles: 8-view road sprites, articulated bus parts with their own lengths
    assert "item(FEAT_ROADVEHS, citaro_postauto," in text and "ss_citaro_body0_road" in text
    assert "sw_citaro_g_length" in text and "sw_citaro_g_postauto_articulated" in text
    grf = compile_grf(nml, tmp_path / "test.grf")
    # budget per vehicle: a light-variant loco is ~0.8 MB in the GRF, a duplicated full
    # sprite set per light variant would be ~3x that
    budget = 1.2 * 1024 * 1024 * len(vehicles())
    assert 1000 < grf.stat().st_size < budget, "GRF size regression (overlays not used?)"


def test_body_plus_overlay_equals_lit_render() -> None:
    """The lamp overlay must reproduce the fully lit render exactly when drawn over the body."""
    import numpy as np
    from PIL import Image

    from puenktlich.sprites import overlay_sheet_name, sheet_for

    d = paths.BUILD_SPRITES / "re460"
    if not sheet_for(d, "re460_solo", "normal", 4, "32bpp").exists():
        pytest.skip("run the full build first")
    for kind in ("normal", "up"):
        lit = np.array(Image.open(sheet_for(d, "re460_solo", kind, 4, "32bpp")).convert("RGBA"))
        body = np.array(Image.open(sheet_for(d, "re460_body0", kind, 4, "32bpp")).convert("RGBA"))
        ovl = np.array(Image.open(sheet_for(d, overlay_sheet_name("re460_solo"), kind, 4, "32bpp")).convert("RGBA"))
        assert 0 < (ovl[..., 3] > 0).sum() < 0.01 * ovl[..., 3].size  # a few lamp pixels only
        composite = np.where((ovl[..., 3] > 0)[..., None], ovl, body)
        assert ((composite != lit).any(axis=2)).sum() == 0
