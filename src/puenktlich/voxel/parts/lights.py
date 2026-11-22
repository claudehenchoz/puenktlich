"""Head/tail lamp clusters (Swiss pattern: two low lamps + one high centre lamp).

Leading end: all three white. Trailing end: the two low lamps red, top off.
Unlit lamps are dark glass so the lamp housings still read at 4x zoom.
"""

from __future__ import annotations

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model
from puenktlich.voxel.parts.body import Shell, end_band, face_mask
from puenktlich.voxel.variants import Lights

LAMP_WHITE = P.WHITE
LAMP_RED = P.LAMP_RED
LAMP_OFF = P.GLASS_DARK


def lamp_cluster(
    model: Model,
    shell: Shell,
    front: bool,
    state: str,
    low_z: tuple[float, float] = (20, 25),
    top_z: tuple[float, float] | None = (49, 51),
    spacing: float = 12,
    lamp_half_width: float = 2,
    face: bool = False,
) -> None:
    """Paint one end's lamps. state: 'white' | 'red' | 'off'. top_z=None: no top lamp (coach ends).
    face=True: paint the end's front skin (face_mask) instead of a fixed depth, for raked noses."""
    _, Y, Z = model.coords()
    low = {"white": LAMP_WHITE, "red": LAMP_RED, "off": LAMP_OFF}[state]
    top = LAMP_WHITE if state == "white" else LAMP_OFF
    z0, z1 = low_z
    skin = face_mask(model, front, depth=3) if face else None

    def region(za: float, zb: float, hw: float, depth: float):
        if skin is not None:
            return skin & (za <= Z) & (zb > Z) & (abs(Y - CENTRE_Y) <= hw)
        return end_band(model, shell, za, zb, hw, front=front, depth=depth)

    for dy in (-spacing, spacing):
        # dark housing one voxel larger than the lamp, so a red lamp reads on a red body
        housing = region(z0 - 1, z1 + 1, spacing + lamp_half_width + 2, 8)
        model.paint(housing & (abs(Y - (CENTRE_Y + dy)) <= lamp_half_width + 1), P.BLACK)
        band = region(z0, z1, spacing + lamp_half_width + 1, 8)
        model.paint(band & (abs(Y - (CENTRE_Y + dy)) <= lamp_half_width), low)
    if top_z is not None:
        # only as deep as the nose is raked: on a steep cab front a deeper box would also
        # paint a strip along the roof behind the lamp
        shape = shell.front if front else (shell.rear or shell.front)
        model.paint(region(*top_z, lamp_half_width, shape.rake + 4), top)


def lamps(model: Model, shell: Shell, lights: Lights, **kw) -> None:
    """Both ends according to `lights` (front = high x = direction of travel).
    Always paint lamps through this module so `Lights.dark` bodies stay lamp-free."""
    lamp_cluster(model, shell, True, lights.state("front"), **kw)
    lamp_cluster(model, shell, False, lights.state("rear"), **kw)


def mu_lights(role: str, lights: Lights) -> Lights:
    """Lamps of one car of a multiple unit, which is drawn as a whole with its front leading.

    front   first car: the unit's front lamps at its front end
    rear    last car: built cab-first and then turned round by the builder, so the unit's
            rear lamps go on its (built) front end
    middle  no lamps
    """
    if role == "rear":
        return Lights(front=lights.rear, rear="off", dark=lights.dark)  # type: ignore[arg-type]
    if role == "front":
        return Lights(front=lights.front, rear="off", dark=lights.dark)
    return Lights(front="off", rear="off", dark=lights.dark)
