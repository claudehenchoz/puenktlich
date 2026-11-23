"""Headless in-game test: run OpenTTD with the built GRF and take screenshots.

Runs use a throw-away profile (XDG_DATA_HOME/XDG_CONFIG_HOME under build/ingame/), so
the user's OpenTTD config is never touched. All zoom levels share one run.

    tools/ingame/pk_test/   Game Script: levels land, builds an electrified loop +
                            depot, builds one train from every engine whose name
                            matches TARGETS, runs it and stops it on the next
                            STOP_TILES tile for one month per zoom level.
    console scripts         on the 1st of each month take one viewport screenshot.

Rendering uses SDL's offscreen backend (no window). The null video driver can't
take screenshots. Only one screenshot per console script, because screenshots are
written on the next drawn frame.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tarfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from puenktlich import paths

GS_DIR = paths.ROOT / "tools" / "ingame" / "pk_test"
OUT = paths.BUILD / "ingame"
NICE = ["nice", "-n", "10"] if os.name != "nt" and shutil.which("nice") else []  # not on Windows
ZOOM_LEVELS = {"4x": 0, "2x": 1, "1x": 2}  # OpenTTD ZoomLevel: 0 = 4x in, 2 = normal

# A 4x4-tile loop around the map centre (64x64 map): the initial camera looks at
# the centre and the whole loop fits on a 1280x720 screen even at 4x zoom, so no
# scrolling is needed (`scrollto` does not move the null-input SDL viewport).
# The train is stopped on a different tile each month: straight sides give the
# diagonal-on-screen views, corners the N/E/S/W views.
LOOP = {"x0": 31, "x1": 34, "y0": 31, "y1": 34}
RAISE_X = 34  # vertices x >= 34 one level up: tiles (33, y0) and (33, y1) are ramps
SEED = 12345  # map seed: same terrain every run
STOP_DELAY = 4  # ticks after the head enters a stop tile
ALL_ZOOMS = ["1x", "2x", "4x"]
# Optionally reverse the whole train when restarting in this month (0 = never). Note that
# OpenTTD then swaps the vehicles end to end, so the locomotive still leads.
REVERSE_AT_MONTH = 0
# first three = straight, ramp (hill sprite), corner (curve sprite): the default --shots 3
STOP_TILES = [(32, 31), (33, 31), (34, 31), (34, 33), (33, 34), (31, 34)]

CONFIG = """\
[misc]
language = english.lng

[game_creation]
; 2025: every vehicle is introduced (never_expire_vehicles keeps the old ones)
starting_year = 2025
map_x = 6
map_y = 6
land_generator = original
generation_seed = 12345

[difficulty]
terrain_type = 0
quantity_sea_lakes = 0
industry_density = 0
vehicle_breakdowns = 0
number_towns = 0

[vehicle]
never_expire_vehicles = true

[news_display]
arrival_player = off
arrival_other = off
accident = off
company_info = off
open = off
close = off
economy = off
production_player = off
production_other = off
production_nobody = off
advice = off
new_vehicles = off
acceptance = off
subsidies = off
general = off

[game_scripts]
PKTest =
{graphicsset}
[newgrf]
{grfs}
"""


@dataclass
class Result:
    zoom: str
    screenshots: list[Path]
    log: Path
    script_lines: list[str]
    errors: list[str]


def _baseset_name(tar: Path) -> str:
    """`name` from the .obg inside a base graphics set tar (e.g. aBase)."""
    with tarfile.open(tar) as tf:
        for m in tf.getmembers():
            if m.name.endswith(".obg"):
                text = tf.extractfile(m).read().decode("utf-8", "replace")  # type: ignore[union-attr]
                found = re.search(r"^name\s*=\s*(.+)$", text, re.M)
                if found:
                    return found.group(1).strip()
    raise ValueError(f"{tar}: no .obg with a name")


def find_baseset(name: str) -> Path:
    """A downloaded base graphics set tar by (part of) its file name, e.g. 'abase'."""
    root = Path.home() / ".local" / "share" / "openttd" / "content_download" / "baseset"
    for tar in sorted(root.glob("*.tar")):
        if name.lower() in tar.name.lower():
            return tar
    raise FileNotFoundError(f"no base set matching {name!r} in {root}")


def _sq(value: object) -> str:
    """A Squirrel literal for strings and lists of strings (JSON syntax, non-ASCII kept)."""
    return json.dumps(value, ensure_ascii=False)


def default_baseset() -> Path | None:
    """OpenGFX from OpenTTD's content downloads, if present. The isolated profile only sees
    the system base sets otherwise, and a system install may ship none that work (only the
    original TTD sets, which need the TTD data files)."""
    try:
        return find_baseset("opengfx")
    except FileNotFoundError:
        return None


def _profile(
    name: str,
    zooms: list[str],
    grf: Path,
    targets: list[str],
    shots: int,
    scene: str = "loop",
    extras: list[str] | None = None,
    baseset: Path | None = None,
) -> Path:
    root = OUT / name
    shutil.rmtree(root, ignore_errors=True)
    data = root / "data" / "openttd"
    (data / "newgrf").mkdir(parents=True)
    grfs = [g for g in (paths.BUILD / "puenktlich_tracks.grf", grf) if g.exists()]  # tracks first
    for g in grfs:
        shutil.copy2(g, data / "newgrf" / g.name)
    gs = data / "game" / "pk_test"
    shutil.copytree(GS_DIR, gs)
    graphicsset = ""
    if baseset is not None:  # e.g. aBase, to compare our sprites with its vehicles
        (data / "baseset").mkdir()
        shutil.copy2(baseset, data / "baseset" / baseset.name)
        graphicsset = f"\n[graphicsset]\nname = {_baseset_name(baseset)}\n"
    stops = ", ".join(f"[{x}, {y}]" for x, y in STOP_TILES)
    loop = ", ".join(f"{k} = {v}" for k, v in LOOP.items())
    hold = 1 if scene == "infra" else len(zooms)  # months the train waits at each stop
    # Squirrel string literals know no \u escapes, so names such as "Zürich" are written as
    # UTF-8; the BOM makes OpenTTD read the file as UTF-8 (without one it assumes Latin-1)
    (gs / "targets.nut").write_text(
        f"TARGETS <- {_sq(targets)};\nLOOP <- {{{loop}}};\nSTOP_TILES <- [{stops}];\n"
        f"RAISE_X <- {RAISE_X};\nSTOP_DELAY <- {STOP_DELAY};\nREVERSE_AT_MONTH <- {REVERSE_AT_MONTH};\n"
        f"SCENE <- {_sq(scene)};\nEXTRAS <- {_sq(extras or [])};\nHOLD_MONTHS <- {hold};\n",
        encoding="utf-8-sig",
    )
    cfg = root / "config" / "openttd"
    cfg.mkdir(parents=True)
    (cfg / "openttd.cfg").write_text(
        CONFIG.format(grfs="\n".join(f"{g.name} =" for g in grfs), graphicsset=graphicsset)
    )
    scripts = data / "scripts"
    scripts.mkdir()
    (scripts / "game_start.scr").write_text("schedule on-next-calendar-month scripts/m1.scr\n")
    plan = shot_plan(zooms, shots, scene)
    for i, (zoom, shot_name) in enumerate(plan, start=1):
        (scripts / f"m{i}.scr").write_text(
            f"zoomto {ZOOM_LEVELS[zoom]}\nscreenshot viewport no_con {shot_name}\n"
            f"schedule on-next-calendar-month scripts/m{i + 1}.scr\n"
        )
    (scripts / f"m{len(plan) + 1}.scr").write_text("quit\n")
    return root


def shot_plan(zooms: list[str], shots: int, scene: str = "loop") -> list[tuple[str, str]]:
    """(zoom, screenshot name) per game month. The train waits at each stop for one month per
    zoom level, so one OpenTTD run covers every zoom."""
    if scene == "infra":  # alternate an overview (2x) and a close-up (4x)
        return [(z, f"infra_{i}_{z}") for i in range(1, shots + 1) for z in ["2x" if i % 2 else "4x"]]
    plan = []
    for i in range(1, shots + 1):
        x, y = STOP_TILES[(i - 1) % len(STOP_TILES)]
        plan += [(z, f"{z}_{i}_at_{x}_{y}") for z in zooms]
    return plan


def run_timeout(months: int) -> int:
    """Seconds allowed for a run: world generation and scene building, then ~67 s per month."""
    return 180 + 80 * months


def _run(
    name: str,
    zooms: list[str],
    grf: Path,
    targets: list[str],
    shots: int,
    scene: str = "loop",
    extras: list[str] | None = None,
    baseset: Path | None = None,
) -> list[Result]:
    root = _profile(name, zooms, grf, targets, shots, scene, extras, baseset)
    plan = shot_plan(zooms, shots, scene)
    env = dict(
        os.environ, SDL_VIDEODRIVER="offscreen", XDG_DATA_HOME=str(root / "data"), XDG_CONFIG_HOME=str(root / "config")
    )
    log = root / "openttd.log"
    timeout = run_timeout(len(plan) + 1)
    timed_out = False
    with log.open("w") as fh:
        try:  # run() kills the child on timeout
            subprocess.run(
                [
                    *NICE,
                    "openttd",
                    "-x",
                    "-v",
                    "sdl",
                    "-r",
                    "1280x720",
                    "-s",
                    "null",
                    "-m",
                    "null",
                    "-b",
                    "32bpp-anim",
                    "-d",
                    "grf=1,script=4",
                    "-g",
                    "-G",  # the config's generation_seed is ignored for `-g`; pin the terrain
                    str(SEED),
                ],
                env=env,
                stdout=fh,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
    text = log.read_text(errors="replace")
    lines = [ln.split("[I] ", 1)[1] for ln in text.splitlines() if "PKTEST" in ln and "[I] " in ln]
    errors = [
        ln
        for ln in text.splitlines()
        if "puenktlich" in ln.lower() and ("error" in ln.lower() or "warning" in ln.lower())
    ]
    errors += [ln for ln in text.splitlines() if "[S]" in ln or "ERROR" in ln]
    errors += [ln for ln in lines if re.search(r"\b(rail|depot|attach) fail\b|infra FAIL|cargo FAIL|road fail", ln)]
    shots_dir = root / "data" / "openttd" / "screenshot"
    found = {p.stem: p for p in shots_dir.glob("*.png")} if shots_dir.exists() else {}
    missing = [shot for _, shot in plan if shot not in found]
    if timed_out:
        errors.append(f"OpenTTD did not finish within {timeout} s and was stopped; missing: {', '.join(missing)}")
    elif missing:
        errors.append(f"missing screenshots: {', '.join(missing)}")
    results = []
    for zoom in dict.fromkeys(z for z, _ in plan):
        results.append(
            Result(zoom, [found[shot] for z, shot in plan if z == zoom and shot in found], log, lines, errors)
        )
    return results


def run(
    grf: Path,
    targets: list[str],
    zooms: list[str],
    shots: int = 6,
    parallel: bool = False,
    scene: str = "loop",
    extras: list[str] | None = None,
    baseset: Path | None = None,
) -> list[Result]:
    """All zoom levels share one OpenTTD run by default (`build/ingame/all/`; a single zoom
    runs in `build/ingame/<zoom>/`): the train waits one month per zoom at each stop.
    `parallel=True` starts one OpenTTD per zoom level instead: faster, but several offscreen
    OpenTTDs can freeze a 4-core laptop."""
    if shutil.which("openttd") is None:
        raise FileNotFoundError("openttd not found on PATH")
    if parallel and len(zooms) > 1:
        with ThreadPoolExecutor(len(zooms)) as pool:
            runs = pool.map(lambda z: _run(z, [z], grf, targets, shots, scene, extras, baseset), zooms)
            return [r for rs in runs for r in rs]
    name = zooms[0] if len(zooms) == 1 else "all"
    return _run(name, zooms, grf, targets, shots, scene, extras, baseset)
