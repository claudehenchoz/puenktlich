"""Build plumbing: cache keys, stamps, overrides, in-game shot plans. No renders."""

import os
import time

from puenktlich import paths


def test_recipe_cache_key_follows_imports() -> None:
    """A recipe's cache key covers the modules it imports (directly or not), not the whole
    voxel library: editing the bus parts must not rebuild the trains."""
    from puenktlich.models import _imported_files, _source_digest

    voxel = paths.ROOT / "src" / "puenktlich" / "voxel"
    re460 = paths.MODELS / "sbb" / "re460" / "recipe.py"
    direct = _imported_files(re460.read_text())
    assert voxel / "palette.py" in direct and voxel / "model.py" in direct
    assert voxel / "parts" / "road.py" not in direct
    assert _source_digest(re460) != _source_digest(paths.MODELS / "postauto" / "citaro" / "recipe.py")

    def closure(recipe):
        seen, todo = set(), [recipe]
        while todo:
            f = todo.pop()
            if f not in seen:
                seen.add(f)
                todo += _imported_files(f.read_text())
        return seen

    assert voxel / "parts" / "road.py" not in closure(re460)
    assert voxel / "vox.py" in closure(re460)  # through voxel/model.py


def test_prune_caches_drops_unused_entries(tmp_path, monkeypatch) -> None:
    from puenktlich import models

    monkeypatch.setattr(paths, "CACHE", tmp_path)
    vox = tmp_path / "vox"
    vox.mkdir()
    old, new, legacy = vox / "old.npz", vox / "new.npz", vox / "legacy.npy"
    for f in (old, new, legacy):
        f.write_bytes(b"x" * 10)
    month_ago = time.time() - 30 * 86400
    os.utime(old, (month_ago, month_ago))
    assert models.prune_caches() == 20
    assert new.exists() and not old.exists() and not legacy.exists()


def test_overrides_are_copied_once_with_a_fresh_mtime(tmp_path, monkeypatch) -> None:
    """An override must look newer than the render it replaces (GoRender and nmlc compare
    mtimes), and an unchanged override must not be touched again."""
    from puenktlich.render import apply_overrides

    monkeypatch.setattr(paths, "OVERRIDES", tmp_path / "overrides")
    src = tmp_path / "overrides" / "re460" / "4x" / "re460_body0_32bpp.png"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"hand-made")
    os.utime(src, (1_000_000, 1_000_000))  # an old file
    out = tmp_path / "sprites"
    dst = out / "4x" / src.name
    assert apply_overrides("re460", "re460", out) == [dst]
    assert dst.read_bytes() == b"hand-made" and dst.stat().st_mtime > 2_000_000
    os.utime(dst, (3_000_000, 3_000_000))
    assert apply_overrides("re460", "re460", out) == [dst]
    assert dst.stat().st_mtime == 3_000_000  # identical bytes: left alone


def test_render_stamp_covers_renderer_palette_and_scales() -> None:
    import pytest

    from puenktlich.render import render_stamp

    if not paths.GORENDER.exists():
        pytest.skip("run tools/install.sh first")
    assert render_stamp("train") == render_stamp("train")
    assert render_stamp("train") != render_stamp("train_hill")
    assert render_stamp("train") != render_stamp("train", (4,))


def test_partial_grf_is_only_used_for_its_own_vehicles(tmp_path, monkeypatch) -> None:
    import json

    from puenktlich.nml import generate as gen

    monkeypatch.setattr(paths, "BUILD", tmp_path)
    assert gen.grf_for(["re460"]) is None
    full = tmp_path / "puenktlich.grf"
    full.write_bytes(b"full")
    assert gen.grf_for(["re460"]) == full
    partial = gen.partial_grf()
    partial.write_bytes(b"partial")
    partial.with_suffix(".json").write_text(json.dumps(["re460"]))
    os.utime(full, (1_000_000, 1_000_000))
    assert gen.grf_for(["re460"]) == partial
    assert gen.grf_for(["re460", "giruno"]) == full  # giruno is not in the partial build
    os.utime(full)
    os.utime(partial, (1_000_000, 1_000_000))
    assert gen.grf_for(["re460"]) == full  # a newer full build wins


def test_ingame_shot_plan_shares_one_run_between_zooms() -> None:
    from puenktlich.ingame import STOP_TILES, run_timeout, shot_plan

    plan = shot_plan(["1x", "2x", "4x"], shots=2)
    assert [z for z, _ in plan] == ["1x", "2x", "4x"] * 2
    x, y = STOP_TILES[0]
    assert plan[0][1] == f"1x_1_at_{x}_{y}" and plan[2][1] == f"4x_1_at_{x}_{y}"
    assert len({name for _, name in plan}) == 6
    assert [name for _, name in shot_plan(["2x"], 2, "infra")] == ["infra_1_2x", "infra_2_4x"]
    # 8 shots used to exceed a fixed 600 s limit and lose screenshots without an error
    assert run_timeout(8 + 1) > 9 * 67


def test_ingame_targets_keep_non_ascii_names(tmp_path, monkeypatch) -> None:
    """Squirrel has no \\u escapes and OpenTTD reads script files without a BOM as Latin-1:
    a livery such as "S-Bahn Zürich" must reach the game script as UTF-8 with a BOM, or no
    engine matches and the screenshots show an empty map."""
    from puenktlich import ingame

    monkeypatch.setattr(ingame, "OUT", tmp_path)
    grf = tmp_path / "x.grf"
    grf.write_bytes(b"")
    root = ingame._profile("t", ["4x"], grf, ["SBB RABe 511 Regio-Dosto (S-Bahn Zürich)"], shots=1)
    raw = (root / "data" / "openttd" / "game" / "pk_test" / "targets.nut").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM: OpenTTD reads files without one as Latin-1
    text = raw.decode("utf-8-sig")
    assert '"SBB RABe 511 Regio-Dosto (S-Bahn Zürich)"' in text and "\\u" not in text


def test_default_jobs_fit_into_free_memory(monkeypatch) -> None:
    """Each GoRender needs ~3 GB: parallel jobs must not exceed the memory that is free."""
    from puenktlich import pipeline

    monkeypatch.delenv("PK_JOBS", raising=False)
    monkeypatch.setattr(pipeline.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(pipeline, "_available_memory_mb", lambda: 64_000)
    assert pipeline.default_jobs() == 8  # half the cores
    monkeypatch.setattr(pipeline, "_available_memory_mb", lambda: 8_500)
    assert pipeline.default_jobs() == 2
    monkeypatch.setattr(pipeline, "_available_memory_mb", lambda: 3_000)
    assert pipeline.default_jobs() == 1  # never zero
    monkeypatch.setattr(pipeline, "_available_memory_mb", lambda: None)
    assert pipeline.default_jobs() == 8
    monkeypatch.setenv("PK_JOBS", "3")
    assert pipeline.default_jobs() == 3


def test_preview_recolour_matches_openttd_brightness() -> None:
    """Masked pixels: palette colour scaled by brightness / 128; overbright red goes towards
    white (pink), never towards orange."""
    import numpy as np
    from PIL import Image

    from puenktlich.sprites import COLOUR_RAMPS, composite_cc
    from puenktlich.voxel.palette import CC1, rgb_palette

    red = np.array(rgb_palette()[COLOUR_RAMPS["RED"] + 4])
    rgba = np.zeros((1, 3, 4), np.uint8)
    rgba[0, :, 3] = 255
    rgba[0, 0, :3] = 128  # neutral
    rgba[0, 1, :3] = 64  # half as bright
    rgba[0, 2, :3] = 250  # overbright
    mask = Image.fromarray(np.full((1, 3), CC1[0] + 4, np.uint8), "P")
    out = np.array(composite_cc(Image.fromarray(rgba, "RGBA"), mask)).astype(int)[0, :, :3]
    assert (out[0] == red).all()
    assert (out[1] == red // 2).all()
    r, g, b = out[2]
    assert r == 255 and g > red[1] * 250 // 128 and abs(int(g) - int(b)) <= abs(int(red[1]) - int(red[2])) * 2 + 2


def test_render_widen_opt_out() -> None:
    """Trains are widened 1.5x for rendering unless the recipe sets RENDER_WIDEN = False
    (true-proportion models, docs/SCALE.md): then the body keeps its authored width."""
    import numpy as np

    from puenktlich import models, schema
    from puenktlich.voxel.squash import RENDER_WIDTH

    def body_width(vehicle_id: str) -> int:
        v = schema.vehicles()[vehicle_id]
        car = v.car_specs[1]  # an intermediate car
        plan = models._plan(vehicle_id, car)
        grid = next(iter(plan.bodies.values())).data
        assert grid.shape[1] == RENDER_WIDTH
        mid = grid.shape[0] // 2
        return np.flatnonzero(grid[mid, :, 30]).size

    assert models.load_recipe(models.paths.MODELS / "sbb" / "fv_dosto" / "recipe.py").RENDER_WIDEN is False
    assert body_width("fv_dosto_ir100") == 34  # authored width kept
    assert body_width("rabe512") >= 55  # widened 1.5x from 40
