"""Head/tail lamp clusters (Swiss pattern: two low lamps + one high centre lamp).

Leading end: all three white. Trailing end: the two low lamps red, top off.
Unlit lamps are dark glass so the lamp housings still read at 4x zoom.
"""

from __future__ import annotations

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model
from puenktlich.voxel.parts.body import Shell, end_band
from puenktlich.voxel.variants import Lights

LAMP_WHITE = P.WHITE
LAMP_RED = 184  # brightest pure red in the TTD palette
LAMP_OFF = P.GLASS_DARK


def lamp_cluster(
    model: Model,
    shell: Shell,
    front: bool,
    state: str,
    low_z: tuple[float, float] = (20, 25),
    top_z: tuple[float, float] = (49, 51),
    spacing: float = 12,
    lamp_half_width: float = 2,
) -> None:
    """Paint one end's lamps. state: 'white' | 'red' | 'off'."""
    _, Y, _ = model.coords()
    low = {"white": LAMP_WHITE, "red": LAMP_RED, "off": LAMP_OFF}[state]
    top = LAMP_WHITE if state == "white" else LAMP_OFF
    z0, z1 = low_z
    for dy in (-spacing, spacing):
        # dark housing one voxel larger than the lamp, so a red lamp reads on a red body
        housing = end_band(model, shell, z0 - 1, z1 + 1, spacing + lamp_half_width + 2, front=front, depth=8)
        model.paint(housing & (abs(Y - (CENTRE_Y + dy)) <= lamp_half_width + 1), P.BLACK)
        band = end_band(model, shell, z0, z1, spacing + lamp_half_width + 1, front=front, depth=8)
        model.paint(band & (abs(Y - (CENTRE_Y + dy)) <= lamp_half_width), low)
    model.paint(end_band(model, shell, *top_z, lamp_half_width, front=front, depth=26), top)


def lamps(model: Model, shell: Shell, lights: Lights, **kw) -> None:
    """Both ends according to `lights` (front = high x = direction of travel)."""
    lamp_cluster(model, shell, True, lights.front, **kw)
    lamp_cluster(model, shell, False, lights.rear, **kw)
