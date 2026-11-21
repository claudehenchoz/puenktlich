"""Road-vehicle parts (buses) on the road canvas `ROAD_CANVAS` = 126 x 40 x 48 voxels.

Same axes as trains: x along the vehicle (high x = front), y across (centre `model.cy`
= 19.5), z up with z = 0 the road surface. 10 voxels per metre along x; width and height
are exaggerated like the trains (docs/SCALE.md): a 2.55 m bus body is 34 voxels wide and
the roof sits at z ≈ 40.

Livery convention: body CC1 (PostAuto yellow), a thin CC2 line below the windows.
Doors are on the right-hand side of the bus (`DOOR_SIDE`), as on Swiss roads.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_band, side_band

BODY = P.ramp(P.CC1, 0.6)
STRIPE = P.ramp(P.CC2, 0.55)
SKIRT = P.DARK_GREY
ROOF = P.ramp(P.GREY, 0.7)
FRAME = P.BLACK
TYRE = P.BLACK
HUB = P.MID_GREY
LAMP_WHITE = P.WHITE
LAMP_RED = 184
# right-hand side when looking forward (+x) is high y on the canvas (seen in the 90° view)
DOOR_SIDE = 1

BUS_SECTION = CrossSection(floor=4, roof=40, half_width=17, roof_radius=5, tumblehome=0.5, tumble_from=14)
FRONT = EndShape(rake=3, rake_from=18, rake_curve=1.4, corner_radius=4)
REAR = EndShape(rake=1, rake_from=30, rake_curve=1.0, corner_radius=4)
JOINT = EndShape(rake=0, corner_radius=2)  # articulation end (bellows)


@dataclass
class BusBody:
    shell: Shell
    window_z: tuple[float, float] = (19, 35)

    @property
    def cs(self) -> CrossSection:
        return self.shell.section


def side_mask(model: Model, x0: float, x1: float, z0: float, z1: float, side: int) -> np.ndarray:
    """One body side only (side -1 = low y, +1 = high y)."""
    band = side_band(model, x0, x1, z0, z1)
    _, Y, _ = model.coords()
    return band & ((model.cy > Y) if side < 0 else (model.cy < Y))


def bus_body(model: Model, length_m: float, front: EndShape | None, rear: EndShape | None) -> BusBody:
    """Centred low-floor bus body of `length_m`: yellow (CC1) shell, dark skirt, grey roof,
    continuous window band. `front`/`rear` None = articulation joint at that end."""
    sx = model.d.shape[0]
    lob = length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    shell = Shell(x_rear, x_front, BUS_SECTION, front=front or JOINT, rear=rear or JOINT)
    body = BusBody(shell)
    cs = BUS_SECTION
    X, Y, Z = model.coords()
    model.solid(shell.mask(model), BODY)
    model.paint(cs.floor + 4 > Z, SKIRT)  # dark lower skirt
    model.paint((cs.roof - 3 <= Z) & (abs(Y - model.cy) <= cs.half_width - 3), ROOF)
    w0, w1 = body.window_z
    model.paint(side_band(model, x_rear + 3, x_front - 3, w0 - 3, w0 - 2), STRIPE)
    # continuous glazing with thin pillars
    band = side_band(model, x_rear + 4, x_front - 4, w0, w1)
    model.paint(band, FRAME)
    pitch = 13
    glass = band & (((X - x_rear) % pitch) > 1.5)
    model.inset(glass, P.GLASS)
    # roof equipment: air-conditioning pod and an escape hatch
    mid = shell.mid
    model.solid(model.centred_box(mid - 14, mid + 10, 10, cs.roof - 1, cs.roof + 3), ROOF)
    model.solid(model.centred_box(mid - 12, mid + 8, 8, cs.roof + 3, cs.roof + 4), P.ramp(P.GREY, 0.55))
    return body


def windscreen(model: Model, body: BusBody) -> None:
    """Large front windscreen with destination display on top."""
    shell, cs = body.shell, body.cs
    model.paint(end_band(model, shell, 10, cs.roof - 1, cs.half_width - 1, front=True, depth=6), FRAME)
    model.inset(end_band(model, shell, 12, cs.roof - 7, cs.half_width - 3, front=True, depth=6), P.GLASS)
    # destination display (amber text on black)
    disp = end_band(model, shell, cs.roof - 5, cs.roof - 3, 9, front=True, depth=6)
    model.paint(disp, 66)
    # driver's side window directly behind the windscreen
    model.inset(side_band(model, shell.x_front - 12, shell.x_front - 4, 17, cs.roof - 6), P.GLASS)


def rear_end(model: Model, body: BusBody) -> None:
    """Rear window above the engine compartment, red tail lamps."""
    shell, cs = body.shell, body.cs
    model.paint(end_band(model, shell, 24, cs.roof - 3, cs.half_width - 3, front=False, depth=4), FRAME)
    model.inset(end_band(model, shell, 26, cs.roof - 5, cs.half_width - 5, front=False, depth=4), P.GLASS)
    grille = end_band(model, shell, 7, 15, cs.half_width - 6, front=False, depth=4)
    model.inset(grille, P.DARK_GREY)
    lamps(model, body, front=False)


def lamps(model: Model, body: BusBody, front: bool) -> None:
    """Head lamps (white) or tail lamps (red) at the lower corners of one end."""
    shell, cs = body.shell, body.cs
    _, Y, _ = model.coords()
    z0, z1 = (6, 10) if front else (9, 20)
    colour = LAMP_WHITE if front else LAMP_RED
    band = end_band(model, shell, z0, z1, cs.half_width + 1, front=front, depth=7)
    model.paint(band & (abs(Y - model.cy) >= cs.half_width - 5), colour)


def door(model: Model, body: BusBody, x0: float, width: float = 12) -> None:
    """Double glazed door on the kerb side, from floor to the top of the window band."""
    top = body.window_z[1]
    leaf = side_mask(model, x0, x0 + width, 4, top + 1, DOOR_SIDE)
    model.paint(leaf, FRAME)
    model.inset(side_mask(model, x0 + 1, x0 + width - 1, 6, top - 1, DOOR_SIDE), P.GLASS)
    model.paint(side_mask(model, x0 + width / 2 - 0.5, x0 + width / 2 + 0.5, 5, top, DOOR_SIDE), FRAME)


def wheel(model: Model, x: float, diameter: float = 11, twin: bool = False) -> None:
    """Wheel arch cut into the skirt and a tyre with a grey hub on both sides."""
    r = diameter / 2
    zc = r
    cs = BUS_SECTION
    hw = cs.half_width
    y_out = model.cy + hw + 0.5
    arch = model.cylinder_y(x, zc, r + 1.5, 0, model.d.shape[1]) & (abs(model.coords()[1] - model.cy) > hw - 6)
    model.carve(arch & (model.coords()[2] < zc + r + 1.5))
    width = 6 if twin else 4
    tyre = model.cylinder_y(x, zc, r, y_out - width, y_out - 0.5)
    model.solid(model.mirror_y(tyre), TYRE)
    hub = model.cylinder_y(x, zc, r * 0.45, y_out - 1.5, y_out - 0.5)
    model.solid(model.mirror_y(hub), HUB)


def bellows(model: Model, body: BusBody, front: bool) -> None:
    """Half of the articulation bellows (black concertina) at one end, inside the body
    length: OpenTTD butts articulated parts together at their length boundaries."""
    shell, cs = body.shell, body.cs
    x0, x1 = (shell.x_front - 2, shell.x_front + 1) if front else (shell.x_rear, shell.x_rear + 3)
    model.carve(model.centred_box(x0, x1, cs.half_width + 1, 0, model.d.shape[2]))
    box = model.centred_box(x0, x1, cs.half_width - 2, cs.floor + 1, cs.roof - 2)
    model.solid(box, P.BLACK)
    model.paint(box & ((model.coords()[2].astype(int) % 3) == 0), P.DARK_GREY)
