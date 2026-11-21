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


@pytest.mark.slow
def test_track_grf_compiles(tmp_path) -> None:
    if shutil.which("nmlc") is None:
        pytest.skip("nmlc not installed")
    from puenktlich.tracks.build import build_tracks

    grf = build_tracks(tmp_path / "tracks.grf")
    assert grf.stat().st_size > 10_000


def test_infra_groups_have_openttd_counts() -> None:
    from puenktlich.tracks.infra import infra_sprites

    counts = {k: len(v) for k, v in infra_sprites(METRE_GAUGE, 1).items()}
    assert counts == {
        "level_crossings": 10,
        "bridge_surfaces": 6,
        "tunnels": 4,
        "tunnel_overlay": 4,
        "depots": 6,
        "gui": 16,
    }


def test_crossing_rails_match_track_rails() -> None:
    """The crossing's rail sprites are the track overlay's rails (same gauge, same place)."""
    import numpy as np

    from puenktlich.tracks.infra import crossing_sprites

    crossing = crossing_sprites(METRE_GAUGE, 4)[0]
    rails = track_sprites(METRE_GAUGE, 4)["track_overlay"][0]
    assert (crossing.xofs, crossing.yofs) == (rails.xofs, rails.yofs)
    assert np.array_equal(np.array(crossing.image), np.array(rails.image))


def test_rack_style_adds_a_rack_bar() -> None:
    import numpy as np

    from puenktlich.tracks.raster import METRE_GAUGE_RACK

    plain = np.array(track_sprites(METRE_GAUGE, 4)["track_overlay"][0].image)
    rack = np.array(track_sprites(METRE_GAUGE_RACK, 4)["track_overlay"][0].image)
    assert (rack[..., 3] > 0).sum() > (plain[..., 3] > 0).sum()


def test_depots_sit_on_their_tile() -> None:
    """Each depot part is drawn at its own tile offset; re-adding that offset must put the
    building inside the tile diamond's horizontal extent (-32..32 px at 1x)."""
    from puenktlich.tracks.infra import depot_sprites
    from puenktlich.tracks.raster import _project

    origins = [(2, 2), (13, 2), (2, 2), (2, 13), (2, 13), (13, 2)]
    for sprite, (dx, dy) in zip(depot_sprites(1), origins, strict=True):
        ox, _ = _project(dx, dy, 0)
        left, right = ox + sprite.xofs, ox + sprite.xofs + sprite.image.width
        assert left >= -33 and right <= 33
