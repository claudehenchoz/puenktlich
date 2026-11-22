"""Hood-unit locomotives: a cab between two hoods on a dark frame (SBB Aem 940, Eem 923).

`build_hood_loco(spec, lights)` builds one locomotive on the train canvas from a `HoodSpec`.
Positions along the frame are metres from the front buffer beam (`u`), heights are z.
Photos and measurements: models/sbb/aem940/REFERENCE.md, models/sbb/eem923/REFERENCE.md.

Livery
    "sbb":   hoods and cab CC1 (SBB red), white SBB crosses, dark frame.
    "cargo": SBB Cargo: long hood and cab CC1 (blue), short hood CC2 (red) from a diagonal
             split at the cab, white "cargo" lettering with red dashes, dark frame.
Lamps: two low lamps and a top lamp on each end's hood face; front white / rear red by the
light variant (`voxel/variants.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, side_band
from puenktlich.voxel.parts.lights import lamp_cluster
from puenktlich.voxel.parts.roof import pantograph
from puenktlich.voxel.parts.running_gear import bogie, buffers, wheelset
from puenktlich.voxel.variants import Lights


@dataclass(frozen=True)
class Block:
    """A box-shaped body part from u0 to u1 (m from the front) up to `top`, `half_width` wide,
    with rounded roof edges."""

    u0: float
    u1: float
    top: float
    half_width: float
    roof_radius: float = 3


@dataclass
class HoodSpec:
    length_m: float  # over buffer beams (buffers stick out 0.6 m at each end)
    frame_z: tuple[float, float]  # dark frame
    cab: Block
    hoods: tuple[Block, ...]
    cab_windows: tuple[float, float]  # z range of the cab windows
    bogies: tuple[float, ...] = ()  # bogie centres (m from the front)
    axles: tuple[float, ...] = ()  # single axles in the frame (m from the front)
    bogie_wheelbase: float = 2.6
    wheel: float = 9
    livery: Literal["sbb", "cargo"] = "sbb"
    cargo_split: float = 0.0  # cargo: red short hood in front of this (m), diagonal on the cab
    pantograph_u: float | None = None  # on the cab roof
    roof_overhang: float = 0  # cab roof canopy wider than the cab by this (voxels per side)
    lamps: dict = field(default_factory=dict)  # lamp_cluster keyword arguments


BODY = P.BODY_CC1
SECOND = P.BODY_CC2
FRAME = P.UNDERFRAME
WHITE = P.OFF_WHITE


def build_hood_loco(spec: HoodSpec, lights: Lights) -> Model:
    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10 - 12  # body/frame between the buffer beams
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2

    def at(u: float) -> float:
        return x_front - u * 10

    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)

    # --- frame and body blocks ----------------------------------------------------------
    f0, f1 = spec.frame_z
    mdl.solid(mdl.centred_box(x_rear, x_front, 19.5, f0, f1), FRAME)
    shells = []
    for b in (*spec.hoods, spec.cab):
        cs = CrossSection(floor=f1, roof=b.top, half_width=b.half_width, roof_radius=b.roof_radius, tumblehome=0)
        sh = Shell(at(b.u1), at(b.u0), cs, front=EndShape(corner_radius=2), rear=EndShape(corner_radius=2))
        mdl.solid(sh.mask(mdl), BODY)
        shells.append(sh)
    cab = spec.cab
    if spec.roof_overhang:
        hw = cab.half_width + spec.roof_overhang
        mdl.solid(mdl.centred_box(at(cab.u1) - 1, at(cab.u0) + 1, min(hw, 20), cab.top, cab.top + 2), P.DARK)

    # --- cab windows: all round above the hoods --------------------------------------------
    w0, w1 = spec.cab_windows
    cx0, cx1 = at(cab.u1), at(cab.u0)
    cab_side = side_band(mdl, cx0 + 2, cx1 - 2, w0, w1)
    mdl.paint(cab_side, P.BLACK)
    panes = side_band(mdl, cx0 + 2, cx1 - 2, w0 + 1, w1 - 1) & ((X.astype(int) - int(cx0)) % 9 != 0)
    mdl.inset(panes, P.GLASS)
    for xe, inward in ((cx1, -1), (cx0, 1)):  # cab end faces over the hoods
        face = (np.abs(X - (xe + inward * 0.5)) <= 1) & (dy <= cab.half_width - 2) & (w0 <= Z) & (w1 > Z)
        mdl.paint(face, P.BLACK)
        mdl.inset(face & (dy <= cab.half_width - 3) & (w0 + 1 <= Z) & (w1 - 1 > Z), P.GLASS)

    # --- livery ---------------------------------------------------------------------------
    body = mdl.d == BODY
    if spec.livery == "cargo":
        split = spec.cargo_split + (cab.top - Z) * 0.025  # diagonal: red reaches further back low down
        mdl.paint(body & (at(split) < X) & (f1 <= Z), SECOND)
        long_hood = max(spec.hoods, key=lambda b: b.u0)  # the rear (CC1) hood carries the lettering
        lx0, lx1 = at(long_hood.u1), at(long_hood.u0)
        side = (dy >= long_hood.half_width - 0.5) & (dy <= long_hood.half_width)
        letters = side & (lx0 + 8 <= X) & (lx1 - 4 > X) & (f1 + 8 <= Z) & (f1 + 13 > Z)
        mdl.paint(letters & ((X.astype(int) % 6) != 0) & ~(((X.astype(int) % 6) == 3) & (f1 + 10 == Z)), WHITE)
        for k in range(3):  # red dashes at the rear end of the long hood
            zc = f1 + 6 + k * 5
            mdl.paint(side & (lx0 <= X) & (lx0 + 5 > X) & (zc <= Z) & (zc + 2 > Z), SECOND)
    else:
        # white SBB cross on the cab sides
        cxm = (cx0 + cx1) / 2
        zc = (f1 + w0) / 2
        side = (dy >= cab.half_width - 0.5) & (dy <= cab.half_width)
        cross = (np.abs(X - cxm) <= 1) & (np.abs(Z - zc) <= 4) | (np.abs(X - cxm) <= 4) & (np.abs(Z - zc) <= 1)
        mdl.paint(side & cross & (f1 <= Z), WHITE)

    # --- lamps (hood end faces), buffers ---------------------------------------------------
    lamp_args = {"low_z": (f1 + 2, f1 + 5), "top_z": None, "spacing": 11, "lamp_half_width": 1.5} | spec.lamps
    lamp_cluster(mdl, shells[0], True, lights.state("front"), face=True, **lamp_args)
    lamp_cluster(mdl, shells[0], False, lights.state("rear"), face=True, **lamp_args)
    buffers(mdl, x_front, front=True)
    buffers(mdl, x_rear, front=False)

    # --- running gear and roof --------------------------------------------------------------
    for b in spec.bogies:
        bogie(mdl, at(b), wheelbase=spec.bogie_wheelbase * 10, wheel_diameter=spec.wheel, top=f0, style="loco")
    for a in spec.axles:
        wheelset(mdl, at(a), spec.wheel)
        r = spec.wheel / 2
        mdl.solid(mdl.box(at(a) - 3, at(a) + 4, 1, 4, r - 1, f0), FRAME)  # axle box guide
        mdl.solid(mdl.box(at(a) - 3, at(a) + 4, 37, 40, r - 1, f0), FRAME)
    if spec.pantograph_u is not None:
        top = cab.top + (2 if spec.roof_overhang else 0)
        pantograph(mdl, at(spec.pantograph_u), top, raised=True, facing_front=False, raise_height=66 - top)
    return mdl
