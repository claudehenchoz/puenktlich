"""TTD palette access and named colour ramps for voxel modelling.

Every voxel colour is a TTD (DOS/Win-neutral) palette index. Ramps are dark -> light.
Use the *middle* of a ramp for flat surfaces; GoRender shades along the ramp itself.
See docs/STYLE.md for the rules on when to use which ramp.
"""

from __future__ import annotations

import json
from functools import cache

from puenktlich.paths import PALETTE_JSON

# --- Ramps (inclusive start, end) — from render/palettes/ttd_palette.json ---
GREY = (1, 15)  # flat greys (bogies, underframe, roof gear)
BLUE_GREY = (16, 23)
REDDISH_BROWN = (70, 79)
CC2 = (80, 87)  # secondary company colour
MAUVE_WINDOWS = (128, 135)  # glass
BRIGHT_BLUE = (144, 153)
PALE_RED = (162, 169)
DEEP_RED_YELLOW = (178, 191)
CC1 = (198, 205)  # primary company colour
ICY_BLUE = (210, 214)
CARGO_MASK = (253, 255)  # Cargopositor replacement area; never rendered

# --- Single named indices commonly used in recipes ---
# index 1 (the darkest grey) renders transparent in GoRender, so black is index 2
UNRENDERABLE_BLACK = 1
BLACK = 2
DARK_GREY = 3
MID_GREY = 6
LIGHT_GREY = 10
WHITE = 15
GLASS = 131
GLASS_DARK = 129
CC1_MID = 202
CC2_MID = 84
# TTD "deep red" — SBB red when a fixed (non company-colour) livery is wanted
SBB_RED = 181
LAMP = 15  # headlights read as white


def ramp(r: tuple[int, int], t: float) -> int:
    """Pick a colour along ramp `r` with t in [0, 1] (0 = darkest)."""
    lo, hi = r
    i = int(round(lo + max(0.0, min(1.0, t)) * (hi - lo)))
    return BLACK if i == UNRENDERABLE_BLACK else i


@cache
def rgb_palette() -> list[tuple[int, int, int]]:
    entries = json.loads(PALETTE_JSON.read_text())["entries"]
    return [tuple(e) for e in entries]  # type: ignore[misc]
