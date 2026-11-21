"""Canonical repository paths. Everything else should import from here."""

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
GORENDER = TOOLS_BIN / "gorender"
CARGOPOSITOR = TOOLS_BIN / "cargopositor"

BUILD = ROOT / "build"
BUILD_VOX = BUILD / "vox"
BUILD_SPRITES = BUILD / "sprites"
BUILD_PREVIEWS = BUILD / "previews"
BUILD_NML = BUILD / "nml"
GRF_NAME = "puenktlich"
