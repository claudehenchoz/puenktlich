"""Track GRF: projection, sprite sets, compilation."""

import shutil

import pytest

from puenktlich.tracks.raster import (
    METRE_GAUGE,
    OVERLAY_ORDER,
    STANDARD_HALF_GAUGE,
    UNDERLAY_ORDER,
    _project,
    track_sprites,
)


def test_projection_matches_openttd_tile_diamond() -> None:
    # north, west, south, east corners of a flat tile at normal zoom
    assert _project(0, 0, 0) == (0, 0)
    assert _project(16, 0, 0) == (-32, 16)
    assert _project(16, 16, 0) == (0, 32)
    assert _project(0, 16, 0) == (32, 16)
    assert _project(0, 0, 8) == (0, -8)  # one height level up


def test_sprite_counts_and_order() -> None:
    assert len(UNDERLAY_ORDER) == 16 and len(OVERLAY_ORDER) == 10
    for zoom in (1, 4):
        sp = track_sprites(METRE_GAUGE, zoom)
        assert len(sp["underlay"]) == 16 and len(sp["track_overlay"]) == 10


def test_flat_x_piece_spans_tile_edges() -> None:
    """The X piece runs from the NE edge midpoint (32, 16 at 4x: 64, 32) to the SW edge
    midpoint (-64, 96 at 4x); its rails reach both tile edges."""
    rail = track_sprites(METRE_GAUGE, 4)["track_overlay"][0]
    assert rail.xofs <= -64 + 2 and rail.xofs + rail.image.width >= 64 - 2


def test_slopes_rise_above_flat_pieces() -> None:
    sp = track_sprites(METRE_GAUGE, 1)["underlay"]
    flat_x, slope_ne = sp[0], sp[6]
    assert slope_ne.yofs < flat_x.yofs  # raised NE side is drawn higher


def test_metre_gauge_is_narrower() -> None:
    assert METRE_GAUGE.half_gauge == pytest.approx(STANDARD_HALF_GAUGE * 1000 / 1435)


def test_track_grf_compiles(tmp_path) -> None:
    if shutil.which("nmlc") is None:
        pytest.skip("nmlc not installed")
    from puenktlich.tracks.build import build_tracks

    grf = build_tracks(tmp_path / "tracks.grf")
    assert grf.stat().st_size > 10_000
