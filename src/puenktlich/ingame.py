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

Windows: OpenTTD ignores XDG_* and has no SDL driver. The profile is isolated with `-c`
(the working directory becomes the personal dir), the win32 driver opens a window that
doesn't take the focus, and the debug log goes through the console (`developer = 2` plus
the `script` command in autoexec.scr), because `-d` would send it to a new console window.
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
WINDOWS = os.name == "nt"
NICE = ["nice", "-n", "10"] if not WINDOWS and shutil.which("nice") else []
DEBUG_LEVELS = "grf=1,script=4"
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


def personal_dir() -> Path:
    """The user's own OpenTTD data dir (content downloads)."""
    if WINDOWS:
        import ctypes

        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # type: ignore[attr-defined]  # Documents
        return Path(buf.value) / "OpenTTD"
    return Path.home() / ".local" / "share" / "openttd"


def openttd_exe() -> str | None:
    """PK_OPENTTD, else `openttd` on PATH, else the Windows installer's location."""
    found = os.environ.get("PK_OPENTTD") or shutil.which("openttd")
    if not found and WINDOWS:
        exe = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "OpenTTD" / "openttd.exe"
        found = str(exe) if exe.exists() else None
    return found


def find_baseset(name: str) -> Path:
    """A downloaded base graphics set tar by (part of) its file name, e.g. 'abase'."""
    root = personal_dir() / "content_download" / "baseset"
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
    # own file names: on Windows OpenTTD also searches Documents\OpenTTD (before this profile), where
    # `pk install` puts puenktlich.grf; the same name would load that copy instead of the build
    sources = [g for g in (paths.BUILD / "puenktlich_tracks.grf", grf) if g.exists()]  # tracks first
    grfs = [data / "newgrf" / f"pk_test_{g.name}" for g in sources]
    for src, dst in zip(sources, grfs, strict=True):
        shutil.copy2(src, dst)
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
    cfg = data if WINDOWS else root / "config" / "openttd"  # Windows: `-c`, see the module doc
    cfg.mkdir(parents=True, exist_ok=True)
    config = CONFIG.format(grfs="\n".join(f"{g.name} =" for g in grfs), graphicsset=graphicsset)
    if WINDOWS:
        config += "\n[gui]\ndeveloper = 2\n"  # copy debug output into the console
    (cfg / "openttd.cfg").write_text(config)
    scripts = data / "scripts"
    scripts.mkdir()
    if WINDOWS:
        log = (root / "openttd.log").as_posix()
        (scripts / "autoexec.scr").write_text(f'debug_level {DEBUG_LEVELS}\nscript "{log}"\n')
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
    log = root / "openttd.log"  # Windows: written by OpenTTD's console (autoexec.scr)
    cmd = [*NICE, openttd_exe() or "openttd", "-x", "-r", "1280x720", "-s", "null", "-m", "null", "-b", "32bpp-anim"]
    extra: dict = {}
    if WINDOWS:
        data = root / "data" / "openttd"
        cmd += ["-v", "win32", "-c", str(data / "openttd.cfg")]
        startup = subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=4)  # SW_SHOWNOACTIVATE
        extra = dict(cwd=data, startupinfo=startup, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    else:
        xdg = dict(XDG_DATA_HOME=str(root / "data"), XDG_CONFIG_HOME=str(root / "config"))
        cmd += ["-v", "sdl", "-d", DEBUG_LEVELS]
        extra = dict(env=dict(os.environ, SDL_VIDEODRIVER="offscreen", **xdg))
    cmd += ["-g", "-G", str(SEED)]  # the config's generation_seed is ignored for `-g`; pin the terrain
    timeout = run_timeout(len(plan) + 1)
    timed_out = False
    with (root / "stdout.log" if WINDOWS else log).open("w") as fh:
        try:  # run() kills the child on timeout
            subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout, check=False, **extra)
        except subprocess.TimeoutExpired:
            timed_out = True
    text = log.read_text(errors="replace") if log.exists() else ""
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
    if openttd_exe() is None:
        raise FileNotFoundError("openttd not found: put it on PATH or set PK_OPENTTD")
    if parallel and len(zooms) > 1:
        with ThreadPoolExecutor(len(zooms)) as pool:
            runs = pool.map(lambda z: _run(z, [z], grf, targets, shots, scene, extras, baseset), zooms)
            return [r for rs in runs for r in rs]
    name = zooms[0] if len(zooms) == 1 else "all"
    return _run(name, zooms, grf, targets, shots, scene, extras, baseset)
