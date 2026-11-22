"""Bo'Bo' electric locomotives with a cab at each end.

`build_loco(LocoSpec, lights)` builds the whole locomotive: shell with the same nose at both
ends, grey roof walkway, windscreens, cab side windows and doors, machine-room louvres,
bogies, underframe, buffers, lamps, two pantographs (the rear one raised) and the roof gear.
A recipe is a `LocoSpec` with the prototype's measurements (see models/sbb/re460).

x positions are voxels: `mid ± offset` for things along the body, "from the end" spans
(`body.end_span`) for the cab, which is mirrored to both ends. Lengths over buffers and
bogie positions are metres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model, m
from puenktlich.voxel.parts.body import (
    CrossSection,
    EndShape,
    Shell,
    door_outline,
    end_band,
    end_span,
    louvres,
    side_band,
)
from puenktlich.voxel.parts.lights import lamps
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import LOCO_UNDERFRAME, bogie, buffers, rack_drive, underframe
from puenktlich.voxel.variants import Lights

BODY = P.BODY_CC1
SEAM = P.SEAM_CC1
ROOF = P.ROOF

# Cab front of the SBB "Lok 2000" family: Re 460 and the matching EW IV control car (Bt)
LOK2000_NOSE = EndShape(rake=19, rake_from=29, rake_curve=1.35, corner_radius=10, undercut=3, undercut_height=5)

Span = tuple[float, float]


@dataclass
class Windscreen:
    frame_z: Span
    frame_half_width: float
    glass_z: Span
    glass_half_width: float
    depth: float  # how far back from the nose tip the raked screen reaches
    centre_pillar: float | None = None  # half width of a black pillar (two-pane screens)


@dataclass
class Louvres:
    """Groups of grilles on both sides, centred at `mid + offset`."""

    offsets: tuple[float, ...]
    half_length: float
    z: Span
    horizontal: bool = False
    pitch: int = 3


@dataclass
class Panel:
    """A plain painted rectangle on both sides (logo panel, waist band)."""

    z: Span
    colour: int
    half_length: float | None = None  # None: the whole body length


@dataclass
class LocoSpec:
    length_m: float  # over buffers
    section: CrossSection
    nose: EndShape
    windscreen: Windscreen
    cab_window: Span  # from the end
    cab_window_z: Span
    door: Span  # from the end
    door_z: Span
    louvres: Louvres
    bogie_centres_m: float  # each side of the middle
    wheelbase_m: float
    pantograph_offset: float  # each side of the middle
    roof_boxes: tuple[tuple[float, float, float], ...]  # (from offset, to offset, half width)
    door_glass_z: Span | None = None
    side_windows: tuple[float, ...] = ()  # small machine-room windows at mid + offset
    side_window_half_length: float = 2
    side_window_z: Span = (33, 39)
    panels: tuple[Panel, ...] = ()
    lamps: dict = field(default_factory=dict)  # lights.lamp_cluster arguments
    wheel_diameter: float = 11
    gauge: Literal["standard", "metre"] = "standard"
    rack: bool = False
    buffer_depth: float = 6
    buffer_spacing: float = 13
    skirt_gap: float = 22  # between a bogie centre and the underframe box
    skirt_half_width: float = 15
    roof_half_width: float = 13  # grey walkway
    roof_depth: float = 3  # how far down from the crown the grey reaches
    roof_setback: float = 22  # body colour kept at each end of the roof


def build_loco(spec: LocoSpec, lights: Lights) -> Model:
    mdl = Model.new()
    canvas_mid = mdl.d.shape[0] / 2
    lob = m(spec.length_m)
    x_rear = canvas_mid - lob / 2 + spec.buffer_depth
    x_front = canvas_mid + lob / 2 - spec.buffer_depth
    cs = spec.section
    shell = Shell(x_rear, x_front, cs, front=spec.nose)
    mid = shell.mid
    X, Y, Z = mdl.coords()

    # --- body, roof walkway, painted bands ------------------------------------
    mdl.solid(shell.mask(mdl), BODY)
    walkway = (abs(Y - CENTRE_Y) <= spec.roof_half_width) & (x_rear + spec.roof_setback < X)
    mdl.paint(walkway & (cs.roof - spec.roof_depth <= Z) & (x_front - spec.roof_setback > X), ROOF)
    for panel in spec.panels:
        if panel.half_length is None:
            mdl.paint(side_band(mdl, x_rear + 2, x_front - 1, *panel.z), panel.colour)

    # --- cabs: windscreen (black frame, then glass), side window, door ----------
    ws = spec.windscreen
    for front in (True, False):
        mdl.paint(end_band(mdl, shell, *ws.frame_z, ws.frame_half_width, front=front, depth=ws.depth), P.BLACK)
        mdl.inset(end_band(mdl, shell, *ws.glass_z, ws.glass_half_width, front=front, depth=ws.depth), P.GLASS)
        if ws.centre_pillar is not None:
            mdl.paint(end_band(mdl, shell, *ws.glass_z, ws.centre_pillar, front=front, depth=ws.depth), P.BLACK)
        mdl.inset(side_band(mdl, *end_span(shell, front, *spec.cab_window), *spec.cab_window_z), P.GLASS)
        x0, x1 = end_span(shell, front, *spec.door)
        door_outline(mdl, x0, x1, *spec.door_z, SEAM)
        if spec.door_glass_z is not None:
            mdl.inset(side_band(mdl, x0 + 2, x1 - 2, *spec.door_glass_z), P.GLASS)
    # head/tail lamps: white at the leading end, red at the trailing end (variants.py)
    lamps(mdl, shell, lights, **spec.lamps)

    # --- machine room -----------------------------------------------------------
    lv = spec.louvres
    for off in lv.offsets:
        c = mid + off
        louvres(mdl, c - lv.half_length, c + lv.half_length, *lv.z, horizontal=lv.horizontal, pitch=lv.pitch)
    for off in spec.side_windows:
        c = mid + off
        mdl.inset(
            side_band(mdl, c - spec.side_window_half_length, c + spec.side_window_half_length, *spec.side_window_z),
            P.GLASS,
        )
    for panel in spec.panels:
        if panel.half_length is not None:
            mdl.paint(side_band(mdl, mid - panel.half_length, mid + panel.half_length, *panel.z), panel.colour)

    # --- running gear -----------------------------------------------------------
    bc = m(spec.bogie_centres_m)
    for c in (mid - bc, mid + bc):
        bogie(mdl, c, wheelbase=m(spec.wheelbase_m), wheel_diameter=spec.wheel_diameter, top=cs.floor, gauge=spec.gauge)
        if spec.rack:
            rack_drive(mdl, c, wheelbase=m(spec.wheelbase_m))
    underframe(
        mdl, mid - bc + spec.skirt_gap, mid + bc - spec.skirt_gap, cs.floor, spec.skirt_half_width, LOCO_UNDERFRAME
    )
    buffers(mdl, x_front, front=True, length=spec.buffer_depth, spacing=spec.buffer_spacing, gauge=spec.gauge)
    buffers(mdl, x_rear, front=False, length=spec.buffer_depth, spacing=spec.buffer_spacing, gauge=spec.gauge)

    # --- roof equipment ---------------------------------------------------------
    roof_z = cs.roof + 1
    po = spec.pantograph_offset
    pantograph(mdl, mid - po, roof_z, raised=True, facing_front=False)
    pantograph(mdl, mid + po, roof_z, raised=False, facing_front=True)
    main_switch(mdl, mid, roof_z)
    for a, b, half_width in spec.roof_boxes:
        roof_box(mdl, mid + a, mid + b, half_width, roof_z, 2)
    roof_cable(mdl, mid - po, mid + po, roof_z)
    return mdl
