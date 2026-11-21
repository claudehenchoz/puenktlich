"""Passenger coaches and control cars (driving trailers).

`build_coach(spec, lights)` builds a full coach from a `CoachSpec`: shell, doors,
window row, gangways, roof, bogies, buffers and lamps. A spec with a `cab` becomes a
control car: the cab end is built at the front (high x).

Push-pull: OpenTTD draws every vehicle front-first, so a control car at the *end* of
a train would show its cab leading. The light variant tells us where the car sits
(variants.py): for `tail` (last in the train) the control car is built with red cab
lamps and then turned 180°, so its cab faces outward at the rear of the train.
OpenTTD keeps the locomotive in front when a train reverses (it swaps the vehicles
end to end), and wagons can't lead a train, so in practice the control car always
rides last with its cab facing outward. The `head` variant (cab leading, white lamps)
is there for completeness.

Colour plan (docs/STYLE.md):
    body sides            CC2  (SBB: white/light grey)
    doors, roof-edge line CC1  (SBB: red)
    window band at ends, car ends, skirt   black / dark grey (fixed)
    1st class             yellow stripe at roof level (fixed, SBB convention)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_band, end_span, side_band
from puenktlich.voxel.parts.lights import lamp_cluster
from puenktlich.voxel.parts.running_gear import bogie, buffers, skirt
from puenktlich.voxel.variants import Lights

BODY = P.ramp(P.CC2, 0.75)
DOOR = P.ramp(P.CC1, 0.6)
DOOR_SEAM = P.ramp(P.CC1, 0.25)
LINE = P.ramp(P.CC1, 0.55)
ROOF = P.ramp(P.GREY, 0.5)
DARK = P.ramp(P.GREY, 0.08)
FIRST_CLASS_YELLOW = 66
BUFFER_DEPTH = 6


@dataclass
class CabSpec:
    """Driving cab at the front end (control cars)."""

    nose: EndShape
    windscreen_z: tuple[float, float] = (33, 48)
    windscreen_half_width: float = 16
    door_from_end: tuple[float, float] = (26, 34)  # cab/vestibule door right behind the cab


@dataclass
class CoachSpec:
    windows: int  # passenger windows per side between the doors
    door_from_end: tuple[float, float] = (24, 36)  # door x-range measured inwards from each end face
    window_z: tuple[float, float] = (30, 42)
    pillar: float = 3  # width of the body between windows
    first_class: bool = False
    section: CrossSection = field(
        default_factory=lambda: CrossSection(
            floor=15, roof=49, half_width=19.5, roof_radius=9, tumblehome=1.5, tumble_from=24
        )
    )
    end: EndShape = field(default_factory=lambda: EndShape(rake=0, corner_radius=2))
    cab: CabSpec | None = None
    bogie_centres_m: float = 9.5  # each side of the middle
    wheel_diameter: float = 9
    wheelbase: float = 25
    # multiple-unit car role: which end carries the unit's lamps.
    #   None    stand-alone coach / control car (default behaviour above)
    #   "front" first car: lamps at its front only (cab front if it has a cab)
    #   "middle" no lamps
    #   "rear"  last car: built cab-first, then always turned round; cab lamps = unit's rear lamps
    mu_role: Literal["front", "middle", "rear"] | None = None
    window_band: bool = False  # continuous dark band along the window row (NPZ/Domino, ICN…)
    cab_colour: int | None = None  # paint the cab nose (e.g. CC1 for a red front)
    roof_line: bool = True  # red line at the roof edge (EW IV IC livery)
    extras: Callable[[Model, Shell], None] | None = None  # car-specific details (pantograph…)


def _door(mdl: Model, shell: Shell, front: bool, span: tuple[float, float], top: float) -> None:
    x0, x1 = end_span(shell, front, *span)
    leaf = side_band(mdl, x0, x1, shell.section.floor + 1, top)
    mdl.paint(leaf, DOOR)
    seam = leaf & ~side_band(mdl, x0 + 1, x1 - 1, shell.section.floor + 2, top - 1)
    mdl.inset(seam, DOOR_SEAM)
    mdl.inset(side_band(mdl, x0 + 2, x1 - 2, 31, top - 4), P.GLASS)


def build_coach(spec: CoachSpec, lights: Lights) -> Model:
    if spec.mu_role == "rear":
        # last car of a multiple unit: cab built at the front, carrying the unit's rear lamps
        turn_round = True
        lights = Lights(front=lights.rear, rear="off", dark=lights.dark)  # type: ignore[arg-type]
    elif spec.mu_role == "front":
        turn_round = False
        lights = Lights(front=lights.front, rear="off", dark=lights.dark)
    elif spec.mu_role == "middle":
        turn_round = False
        lights = Lights(front="off", rear="off", dark=lights.dark)
    else:
        # stand-alone control car at the end of the train: build cab-first with red lamps, turn round
        turn_round = spec.cab is not None and lights.front == "off" and lights.rear == "red"
        if turn_round:
            lights = Lights(front="red", rear="off", dark=lights.dark)  # type: ignore[arg-type]

    mdl = Model.new()
    sx = mdl.d.shape[0]
    x_rear, x_front = BUFFER_DEPTH, sx - BUFFER_DEPTH - 1
    cs = spec.section
    shell = Shell(x_rear, x_front, cs, front=spec.cab.nose if spec.cab else spec.end, rear=spec.end)
    mid = shell.mid
    X, Y, Z = mdl.coords()

    # --- body ---------------------------------------------------------------
    mdl.solid(shell.mask(mdl), BODY)
    roof = (cs.roof - 4 <= Z) & (abs(Y - CENTRE_Y) <= 15)
    mdl.paint(roof, ROOF)
    if spec.roof_line:
        mdl.paint(side_band(mdl, x_rear, x_front + 1, cs.roof - 6, cs.roof - 5), LINE)  # red line at the roof edge
    if spec.first_class:
        mdl.paint(side_band(mdl, x_rear + 40, x_front - 40, cs.roof - 8, cs.roof - 7), FIRST_CLASS_YELLOW)

    # car ends black (not the cab nose)
    for front in (True, False):
        if front and spec.cab:
            continue
        mdl.paint(end_band(mdl, shell, cs.floor, cs.roof + 1, cs.half_width, front=front, depth=2), DARK)

    # --- doors + vestibule window bands -------------------------------------
    w0, w1 = spec.window_z
    if spec.window_band:
        mdl.paint(side_band(mdl, x_rear, x_front + 1, w0 - 2, w1 + 2), DARK)
    for front in (True, False):
        door_span = spec.cab.door_from_end if (front and spec.cab) else spec.door_from_end
        band_x0, band_x1 = end_span(shell, front, 2 if not (front and spec.cab) else 22, door_span[0])
        mdl.paint(side_band(mdl, band_x0, band_x1, w0 - 1, w1 + 1), DARK)  # black window band at the ends
        _door(mdl, shell, front, door_span, top=w1 + 3)

    # --- passenger windows between the doors --------------------------------
    rear_door = end_span(shell, False, *spec.door_from_end)
    front_door = end_span(shell, True, *(spec.cab.door_from_end if spec.cab else spec.door_from_end))
    span0, span1 = rear_door[1] + 4, front_door[0] - 4
    pitch = (span1 - span0) / spec.windows
    for i in range(spec.windows):
        a = span0 + i * pitch + spec.pillar / 2
        mdl.inset(side_band(mdl, a, a + pitch - spec.pillar, w0, w1), P.GLASS)

    # --- cab (control cars) ---------------------------------------------------
    if spec.cab:
        if spec.cab_colour is not None:
            nose = end_band(mdl, shell, cs.floor, cs.roof + 1, cs.half_width, front=True, depth=22)
            mdl.paint(nose, spec.cab_colour, only=(P.CC2[0], P.CC2[1]))
        z0, z1 = spec.cab.windscreen_z
        mdl.paint(
            end_band(mdl, shell, z0 - 2, z1 + 2, spec.cab.windscreen_half_width + 2, front=True, depth=26), P.BLACK
        )
        mdl.inset(end_band(mdl, shell, z0, z1, spec.cab.windscreen_half_width, front=True, depth=26), P.GLASS)
        mdl.inset(side_band(mdl, *end_span(shell, True, 12, 22), 35, 45), P.GLASS)  # cab side window

    # --- gangways (not at the cab end) ----------------------------------------
    for front in (True, False):
        if front and spec.cab:
            continue
        xe = x_front if front else x_rear
        xa, xb = (xe + 1, xe + 4) if front else (xe - 3, xe)
        mdl.solid(mdl.centred_box(xa, xb, 9, cs.floor + 1, cs.roof - 6), DARK)

    # --- lamps ----------------------------------------------------------------
    if spec.cab:
        lamp_cluster(mdl, shell, True, lights.state("front"))
    else:
        lamp_cluster(mdl, shell, True, "off", low_z=(18, 22), top_z=None, spacing=13, lamp_half_width=1.5)
    lamp_cluster(mdl, shell, False, lights.state("rear"), low_z=(18, 22), top_z=None, spacing=13, lamp_half_width=1.5)

    if spec.extras is not None:
        spec.extras(mdl, shell)

    # --- running gear ----------------------------------------------------------
    off = spec.bogie_centres_m * 10
    for c in (mid - off, mid + off):
        bogie(mdl, c, wheelbase=spec.wheelbase, wheel_diameter=spec.wheel_diameter, top=cs.floor)
    skirt(mdl, mid - off + 22, mid + off - 22, 7, cs.floor, 16, colour=DARK)
    buffers(mdl, x_front, front=True, z=cs.floor, length=BUFFER_DEPTH)
    buffers(mdl, x_rear, front=False, z=cs.floor, length=BUFFER_DEPTH)

    if turn_round:
        mdl.rotate_180()
    return mdl
