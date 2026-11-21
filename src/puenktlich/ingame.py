"""Headless in-game test: run OpenTTD with the built GRF and take screenshots.

Each zoom level runs in its own throw-away profile (XDG_DATA_HOME/XDG_CONFIG_HOME
under build/ingame/), so the user's OpenTTD config is never touched.

    tools/ingame/pk_test/   Game Script: levels land, builds an electrified loop +
                            depot, builds one train from every engine whose name
                            matches TARGETS, runs it and stops it on day 20 of each
                            month with every viewport scrolled onto it.
    console scripts         on the 1st of each month take one viewport screenshot.

Rendering uses SDL's offscreen backend (no window). The null video driver can't
take screenshots. Only one screenshot per console script, because screenshots are
written on the next drawn frame.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from puenktlich import paths

GS_DIR = paths.ROOT / "tools" / "ingame" / "pk_test"
OUT = paths.BUILD / "ingame"
ZOOM_LEVELS = {"4x": 0, "2x": 1, "1x": 2}  # OpenTTD ZoomLevel: 0 = 4x in, 2 = normal

# A 4x4-tile loop around the map centre (64x64 map): the initial camera looks at
# the centre and the whole loop fits on a 1280x720 screen even at 4x zoom, so no
# scrolling is needed (`scrollto` does not move the null-input SDL viewport).
# The train is stopped on a different tile each month: straight sides give the
# diagonal-on-screen views, corners the N/E/S/W views.
LOOP = {"x0": 31, "x1": 34, "y0": 31, "y1": 34}
RAISE_X = 34  # vertices x >= 34 one level up: tiles (33, y0) and (33, y1) are ramps
STOP_DELAY = 4  # ticks after the head enters a stop tile
# Optionally reverse the whole train when restarting in this month (0 = never). Note that
# OpenTTD then swaps the vehicles end to end, so the locomotive still leads.
REVERSE_AT_MONTH = 0
STOP_TILES = [(32, 31), (33, 31), (34, 31), (34, 33), (33, 34), (31, 34)]

CONFIG = """\
[misc]
language = english.lng

[game_creation]
starting_year = 2000
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


def _profile(zoom_name: str, grf: Path, targets: list[str], shots: int) -> Path:
    root = OUT / zoom_name
    shutil.rmtree(root, ignore_errors=True)
    data = root / "data" / "openttd"
    (data / "newgrf").mkdir(parents=True)
    grfs = [g for g in (paths.BUILD / "puenktlich_tracks.grf", grf) if g.exists()]  # tracks first
    for g in grfs:
        shutil.copy2(g, data / "newgrf" / g.name)
    gs = data / "game" / "pk_test"
    shutil.copytree(GS_DIR, gs)
    stops = ", ".join(f"[{x}, {y}]" for x, y in STOP_TILES)
    loop = ", ".join(f"{k} = {v}" for k, v in LOOP.items())
    (gs / "targets.nut").write_text(
        f"TARGETS <- {json.dumps(targets)};\nLOOP <- {{{loop}}};\nSTOP_TILES <- [{stops}];\n"
        f"RAISE_X <- {RAISE_X};\nSTOP_DELAY <- {STOP_DELAY};\nREVERSE_AT_MONTH <- {REVERSE_AT_MONTH};\n"
    )
    cfg = root / "config" / "openttd"
    cfg.mkdir(parents=True)
    (cfg / "openttd.cfg").write_text(CONFIG.format(grfs="\n".join(f"{g.name} =" for g in grfs)))
    scripts = data / "scripts"
    scripts.mkdir()
    (scripts / "game_start.scr").write_text("schedule on-next-calendar-month scripts/m1.scr\n")
    for i in range(1, shots + 1):
        x, y = STOP_TILES[(i - 1) % len(STOP_TILES)]
        (scripts / f"m{i}.scr").write_text(
            f"zoomto {ZOOM_LEVELS[zoom_name]}\n"
            f"screenshot viewport no_con {zoom_name}_{i}_at_{x}_{y}\n"
            f"schedule on-next-calendar-month scripts/m{i + 1}.scr\n"
        )
    (scripts / f"m{shots + 1}.scr").write_text("quit\n")
    return root


def _run(zoom_name: str, grf: Path, targets: list[str], shots: int, timeout: int) -> Result:
    root = _profile(zoom_name, grf, targets, shots)
    env = dict(
        os.environ, SDL_VIDEODRIVER="offscreen", XDG_DATA_HOME=str(root / "data"), XDG_CONFIG_HOME=str(root / "config")
    )
    log = root / "openttd.log"
    with log.open("w") as fh, contextlib.suppress(subprocess.TimeoutExpired):  # run() kills the child on timeout
        subprocess.run(
            [
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
            ],
            env=env,
            stdout=fh,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    text = log.read_text(errors="replace")
    lines = [ln.split("[I] ", 1)[1] for ln in text.splitlines() if "PKTEST" in ln and "[I] " in ln]
    errors = [
        ln
        for ln in text.splitlines()
        if "puenktlich" in ln.lower() and ("error" in ln.lower() or "warning" in ln.lower())
    ]
    errors += [ln for ln in text.splitlines() if "[S]" in ln or "ERROR" in ln]
    errors += [ln for ln in lines if re.search(r"\b(rail|depot|attach) fail\b", ln)]
    shots_dir = root / "data" / "openttd" / "screenshot"
    found = sorted(shots_dir.glob("*.png")) if shots_dir.exists() else []
    return Result(zoom_name, found, log, lines, errors)


def run(grf: Path, targets: list[str], zooms: list[str], shots: int = 6, timeout: int = 600) -> list[Result]:
    if shutil.which("openttd") is None:
        raise FileNotFoundError("openttd not found on PATH")
    with ThreadPoolExecutor(len(zooms)) as pool:
        return list(pool.map(lambda z: _run(z, grf, targets, shots, timeout), zooms))
