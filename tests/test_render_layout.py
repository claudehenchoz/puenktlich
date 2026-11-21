from puenktlich.render import load_manifest, sprite_layout


def test_layout_matches_timberwolf_reference() -> None:
    """Offsets must equal temporarily_late's output for the same geometry.
    Reference: timberwolfs_trains templates/static/sprite_templates.nml,
    template_auto_6_1x (centre unit of length 2)."""
    got = [(r.w, r.h, r.xrel, r.yrel) for r in sprite_layout(1, 2)]
    assert got == [
        (7, 45, -2, -32),
        (36, 31, -15, -21),
        (62, 17, -19, -13),
        (36, 31, -9, -16),
        (7, 45, -2, -20),
        (36, 31, -27, -15),
        (62, 17, -43, -13),
        (36, 31, -21, -22),
    ]


def test_layout_scales_linearly() -> None:
    one, four = sprite_layout(1, 8), sprite_layout(4, 8)
    for a, b in zip(one, four, strict=True):
        assert (b.x, b.w, b.h) == (a.x * 4, a.w * 4, a.h * 4)


def test_manifest_has_eight_directions() -> None:
    angles = [s["angle"] for s in load_manifest()["sprites"]]
    assert angles == [0, 45, 90, 135, 180, 225, 270, 315]
