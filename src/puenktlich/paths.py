"""Canonical repository paths. Everything else should import from here."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
VEHICLES = DATA / "vehicles"
REFERENCE = DATA / "reference"
MODELS = ROOT / "models"
OVERRIDES = ROOT / "overrides"
LANG = ROOT / "lang"

RENDER = ROOT / "render"
MANIFESTS = RENDER / "manifests"
PALETTE_JSON = RENDER / "palettes" / "ttd_palette.json"

TOOLS_BIN = ROOT / ".tools" / "bin"
EXE = ".exe" if os.name == "nt" else ""  # `go build` names Windows binaries *.exe (tools/install.sh)
GORENDER = TOOLS_BIN / f"gorender{EXE}"
CARGOPOSITOR = TOOLS_BIN / f"cargopositor{EXE}"

BUILD = ROOT / "build"
BUILD_VOX = BUILD / "vox"
BUILD_SPRITES = BUILD / "sprites"
BUILD_SPRITES_DRAFT = BUILD / "sprites_draft"  # `pk preview --draft` (4x only, fast sampler)
BUILD_PREVIEWS = BUILD / "previews"
BUILD_NML = BUILD / "nml"
CACHE = BUILD / ".cache"  # content-addressed caches (voxel grids, Cargopositor output)
GRF_NAME = "puenktlich"


def rel(path: Path) -> str:
    """Path as shown to the user: relative to the repository when it is inside it."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)
