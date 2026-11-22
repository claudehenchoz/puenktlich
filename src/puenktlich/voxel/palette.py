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
GOLDEN_BROWN = (32, 39)
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
YELLOW = 66  # first-class stripes, destination displays
LAMP_RED = 184  # tail lamps: brightest pure red in the TTD palette (parts/lights.py, parts/road.py)


def ramp(r: tuple[int, int], t: float) -> int:
    """Pick a colour along ramp `r` with t in [0, 1] (0 = darkest)."""
    lo, hi = r
    i = int(round(lo + max(0.0, min(1.0, t)) * (hi - lo)))
    return BLACK if i == UNRENDERABLE_BLACK else i


@cache
def rgb_palette() -> list[tuple[int, int, int]]:
    entries = json.loads(PALETTE_JSON.read_text())["entries"]
    return [tuple(e) for e in entries]  # type: ignore[misc]


# --- Shade table: the one place that says which shade a kind of surface gets (docs/STYLE.md).
# Builders and recipes use these names, so every vehicle shares the same roof, underframe,
# seam and stripe shades and sits in one family next to the others.
BODY_CC1 = ramp(CC1, 0.6)  # livery colour on flat body surfaces (doors on white coaches too)
SEAM_CC1 = ramp(CC1, 0.25)  # door seams and panel lines on CC1 surfaces (always inset)
BODY_CC2 = ramp(CC2, 0.75)  # large secondary-colour surfaces (white coach sides)
STRIPE_CC2 = ramp(CC2, 0.85)  # stripes, bands and logo panels: a step brighter, to read at 1x
DARK_CC2 = ramp(CC2, 0.4)  # dark secondary-colour bands: skirts of regional units (RABe 511)
ROOF = ramp(GREY, 0.45)  # silver-grey roofs: locomotives, coaches
ROOF_DARK = ramp(GREY, 0.3)  # anthracite roofs of modern multiple units (FV-Dosto, Giruno)
ROOF_LIGHT = ramp(GREY, 0.7)  # light roofs of buses
DARK = ramp(GREY, 0.2)  # car ends, gangways, dark window bands: dark grey, never pure black
UNDERFRAME = DARK_GREY  # bogie frames, skirts, underfloor equipment, buffers

RAMPS = (GREY, BLUE_GREY, GOLDEN_BROWN, REDDISH_BROWN, CC2, MAUVE_WINDOWS, BRIGHT_BLUE, PALE_RED)
RAMPS += (DEEP_RED_YELLOW, CC1, ICY_BLUE)


def shade(index: int, steps: int) -> int:
    """`index` moved `steps` along its own ramp (negative = darker), clamped to the ramp:
    for seams, corrugation and frames in the colour of the surface they sit on."""
    for lo, hi in RAMPS:
        if lo <= index <= hi:
            i = max(lo, min(hi, index + steps))
            return BLACK if i == UNRENDERABLE_BLACK else i
    raise ValueError(f"palette index {index} is not on a named ramp")


# Painted white (stripes, logos, lettering). Not WHITE: that index is reserved for lit
# headlamps, which the light variants and their tests look for.
OFF_WHITE = ramp(GREY, 0.93)
