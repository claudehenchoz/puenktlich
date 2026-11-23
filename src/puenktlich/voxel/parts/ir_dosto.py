"""SBB RABe 512 "IR-Dosto" (Stadler KISS, second generation) in true proportions.

`build_ir_car(spec, lights)` builds one car on the train canvas from an `IrSpec`. Every position is
measured from Stadler's type sketch in the datasheet (scaled to 151,880 mm over couplers), the
heights from the same sketch (rail to roof 4.595 m) and the livery from Wikimedia photos
(models/sbb/rabe512/REFERENCE.md). Positions are *real* metres from the car's front coupling
plane (cab cars: from the nose tip), scaled to the modelled length; heights and widths are 12.2
voxels per metre (roof 4.595 m = z 56, the 2.80 m body 34 voxels wide), so the recipe's
BODY_WIDTH_M keeps the authored width when rendered (docs/SCALE.md).

Structure: lower deck between the doors (body down to 0.49 m), intermediate levels over the
bogies (body bottom 1.33 m), upper deck along the double-deck section; cab cars have a single-level
cab section with a lower roof (4.41 m) and a raked nose (measured side and plan tables) over the
motor bogie. Livery: white body CC2, thin red (CC1) line under the anthracite roof, upper-deck
windows in a continuous dark band, framed lower-deck windows, red door leaves under a blue band
with the class numbers (1st class: a yellow line above), red SBB panel. Nose: red mask round a
black one-piece windscreen with a V-shaped lower edge, dark recess with the LED lamps, white
lower corners with dark grilles; on the side a red line rises along the windscreen edge into the
roof-edge line.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import (
    CrossSection,
    EndShape,
    Shell,
    door_outline,
    face_mask,
    louvres,
    rounded_window,
    side_band,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

ZM = 12.2  # voxels per metre across and up (true proportions)

# heights (z), REFERENCE.md "Measurements" (type sketch, rail to roof 4.595 m)
LOW_FLOOR = 6  # lower-deck body bottom, 0.49 m
HIGH_FLOOR = 16  # over the bogies, 1.33 m
LOWER_WIN = (15, 23)  # 1.20–1.90 m
DISPLAY_Z = (25, 27)  # small display over the lower windows next to the doors
MEZZ_WIN = (26, 35)  # 2.12–2.86 m
UPPER_BAND = (39, 50)
UPPER_WIN = (40, 49)  # 3.27–3.98 m
DOOR_Z = (6, 30)  # red leaves 0.45–2.45 m
DOOR_BAND = (30, 33)  # blue band with the class numbers
DOOR_GLASS = (11, 27)
LOGO_Z = (32, 36)
ROOF_LOUVRE_Z = (44, 50)  # louvred grilles at the roof edge over the intermediate levels
RED_LINE = (52, 54)  # 4.25–4.40 m
ROOF_FROM = 54
ROOF = 56  # 4.595 m
CAB_ROOF = 54  # cab section 4.41 m
HALF_WIDTH = 17  # 1.40 m

SECTION = CrossSection(
    floor=HIGH_FLOOR, roof=ROOF, half_width=HALF_WIDTH, roof_radius=8, tumblehome=0.5, tumble_from=20
)
FLAT = EndShape(rake=0, corner_radius=2)

# nose (REFERENCE.md "Nose"), metres from the tip: side setback by height, plan setback by
# half-width; the nose recedes by the larger of the two
NOSE_SIDE = (
    (0.0, 1.30), (0.6, 0.40), (0.75, 0.12), (0.9, 0.05), (1.35, 0.03), (1.95, 0.0), (2.1, 0.06),
    (2.25, 0.14), (2.4, 0.20), (2.55, 0.40), (2.7, 0.47), (2.85, 0.57), (3.0, 0.67), (3.15, 0.77),
    (3.3, 0.87), (3.45, 0.98), (3.6, 1.10), (3.75, 1.24), (3.9, 1.38), (4.05, 1.55), (4.2, 1.75),
    (4.35, 2.08), (4.41, 2.6), (4.6, 4.66),
)  # fmt: skip
NOSE_PLAN = ((0.0, 0.0), (1.08, 0.0), (1.27, 0.3), (1.40, 1.1))
CAB_ROOF_TO = 4.66  # cab section roof (4.41 m) up to here, then the full roof
# side view: the red line along the windscreen edge (m from the tip -> height), black wrap above
SIDE_LINE = ((0.0, 1.9), (0.47, 2.83), (1.1, 3.54), (1.77, 3.94), (2.4, 4.25))
CAB_WINDOW = (0.6, 2.7, 27, 38)  # black band behind the windscreen edge, cab side window 2.0–2.6 m

WHITE = P.BODY_CC2
RED = P.BODY_CC1
RED_DARK = P.SEAM_CC1
BLACK = P.BLACK
DARK = P.DARK
ROOF_GREY = P.ROOF_DARK
DOOR_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = P.YELLOW
HATCH = P.ramp(P.GREY, 0.72)

Span = tuple[float, float]


@dataclass
class IrSpec:
    cab: bool = False  # cab at the front (high x)
    real_m: float = 24.8  # coupling plane to coupling plane (cab cars: nose tip to coupling plane)
    length_m: float = 24.8  # modelled
    doors: tuple[Span, ...] = ((5.88, 7.54), (17.3, 18.95))
    bogies: tuple[float, float] = (3.0, 21.8)
    upper: tuple[Span, ...] = ()
    lower: tuple[Span, ...] = ()
    mezz: tuple[Span, ...] = ()
    roof_louvres: tuple[Span, ...] = ()
    roof_boxes: tuple[Span, ...] = ()
    first_class: bool = False  # yellow line over the door bands
    pantograph: float | None = None  # position (m) on the roof of a cab car's inner end
    pantograph_raised: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"


def _windows(start: float, widths_gaps: tuple[tuple[float, float], ...]) -> tuple[Span, ...]:
    out, a = [], start
    for w, gap in widths_gaps:
        out.append((round(a, 2), round(a + w, 2)))
        a += w + gap
    return tuple(out)


def cab_car(**kw) -> IrSpec:
    """Cab end car (cars 1 and 6, Bt with the motor bogie): cab section over the motor bogie,
    double-deck section between the doors, pantograph over the inner end."""
    base = IrSpec(
        cab=True,
        real_m=25.74,
        length_m=25.6,
        doors=((7.87, 9.53), (17.78, 19.43)),
        bogies=(4.76, 22.61),
        upper=((8.39, 9.04), (10.2, 11.46), (12.07, 13.33), (13.99, 15.2), (15.85, 17.11), (18.27, 18.93)),
        lower=((10.15, 11.36), (12.07, 13.28), (13.89, 15.2), (15.8, 17.11)),
        mezz=((5.72, 6.32), (20.94, 21.85)),
        roof_louvres=((4.6, 5.3), (21.3, 22.1), (23.97, 25.38)),
        roof_boxes=((23.97, 25.38),),
        pantograph=23.87,
    )
    return replace(base, **kw)


def multi_car(**kw) -> IrSpec:
    """Car 2: 2nd class with the multi-purpose area and wheelchair toilet on the lower deck
    (three lower windows)."""
    base = IrSpec(
        real_m=24.88,
        length_m=24.88,
        doors=((5.94, 7.6), (17.38, 19.05)),
        bogies=(3.06, 21.92),
        upper=((6.39, 7.1), (8.16, 9.42), (10.02, 11.28), (11.84, 13.15), (13.76, 14.97), (15.57, 16.78),
               (17.89, 18.54)),
        lower=((8.0, 8.96), (12.34, 13.85), (14.96, 16.53)),
        mezz=((1.05, 2.31), (2.76, 3.37), (21.62, 22.22), (22.62, 23.88)),
        roof_louvres=((1.1, 1.8), (23.0, 23.7)),
        roof_boxes=((22.14, 23.9),),
    )  # fmt: skip
    return replace(base, **kw)


def first_car_a(**kw) -> IrSpec:
    """Car 3: 1st class upstairs (2+1 seats, wider windows in pairs), 2nd class downstairs."""
    base = IrSpec(
        real_m=24.86,
        length_m=24.86,
        doors=((5.86, 7.52), (17.3, 18.99)),
        bogies=(2.9, 21.82),
        upper=((6.38, 7.03), (8.0, 9.54), (10.02, 11.59), (12.11, 12.76), (13.27, 14.84), (15.33, 16.86),
               (17.83, 18.45)),
        lower=((8.16, 9.39), (10.06, 11.3), (11.9, 13.14), (13.77, 15.0), (15.46, 16.7)),
        mezz=((3.23, 3.89), (21.3, 21.95), (22.35, 23.88)),
        roof_louvres=((1.1, 1.8), (23.0, 23.7)),
        first_class=True,
    )  # fmt: skip
    return replace(base, **kw)


def first_car_b(**kw) -> IrSpec:
    """Car 4: car 3's counterpart (1st class upstairs), its large intermediate-level window at the
    front end."""
    base = IrSpec(
        real_m=24.8,
        length_m=24.8,
        doors=((5.89, 7.51), (17.31, 18.96)),
        bogies=(2.97, 21.8),
        upper=((6.35, 7.0), (7.99, 9.51), (10.02, 11.57), (12.08, 12.73), (13.26, 14.78), (15.3, 16.82),
               (17.81, 18.45)),
        lower=((8.08, 9.32), (10.06, 11.61), (12.12, 13.64), (14.16, 15.69), (16.15, 16.79)),
        mezz=((0.95, 2.47), (2.9, 3.53), (20.96, 21.59)),
        roof_louvres=((1.1, 1.8), (23.0, 23.7)),
        roof_boxes=((1.0, 2.3),),
        first_class=True,
    )  # fmt: skip
    return replace(base, **kw)


def second_car(**kw) -> IrSpec:
    """Car 5: 2nd class, five windows on each deck."""
    base = IrSpec(
        real_m=24.8,
        length_m=24.8,
        doors=((5.88, 7.54), (17.3, 18.95)),
        bogies=(3.13, 22.04),
        upper=_windows(6.31, ((0.64, 1.07), (1.23, 0.6), (1.23, 0.62), (1.23, 0.62), (1.23, 0.62), (1.23, 1.09),
                              (0.64, 0))),
        lower=_windows(8.06, ((1.23, 0.47), (1.23, 0.61), (1.24, 0.61), (1.23, 0.65), (1.24, 0))),
        mezz=((0.99, 2.23), (2.68, 3.25), (21.58, 22.13), (22.58, 23.82)),
        roof_louvres=((1.1, 1.8), (23.0, 23.7)),
        roof_boxes=((2.7, 4.0), (20.85, 22.1)),
    )  # fmt: skip
    return replace(base, **kw)


def build_ir_car(spec: IrSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.cab
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    scale = spec.length_m / spec.real_m

    def at(u: float) -> float:
        """Real metres from the front -> x."""
        return x_front - u * 10 * scale

    def span(s: Span) -> tuple[float, float]:
        return at(s[1]), at(s[0])

    d0, d1 = spec.doors[0][0], spec.doors[-1][1]

    def floor_at(X: np.ndarray) -> np.ndarray:
        ur = (x_front - X) / 10 / scale
        # lower deck from 1.3 m before the first door to 1.6 m behind the last, 0.6 m ramps
        d = np.maximum((d0 - 1.3) - ur, ur - (d1 + 1.6))
        floor = np.clip(LOW_FLOOR + (HIGH_FLOOR - LOW_FLOOR) * d / 0.6, LOW_FLOOR, HIGH_FLOOR)
        if spec.cab:  # lower nose block down to 0.49 m, rising to the motor bogie
            floor = np.where(ur < 2.4, np.clip(LOW_FLOOR + (ur - 1.6) * 12, LOW_FLOOR, HIGH_FLOOR), floor)
        return floor

    def roof_at(X: np.ndarray) -> np.ndarray:
        if not spec.cab:
            return np.full_like(X, ROOF, dtype=float)
        ur = (x_front - X) / 10 / scale
        return np.where(ur < CAB_ROOF_TO, CAB_ROOF, ROOF)

    shell = Shell(x_rear, x_front, SECTION, front=FLAT, rear=FLAT, floor_at=floor_at, roof_at=roof_at)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    ur = (x_front - X) / 10 / scale
    body = shell.mask(mdl)
    if spec.cab:
        side_sb = np.interp(Z / ZM, *zip(*NOSE_SIDE, strict=True))
        plan_sb = np.interp(dy / ZM, *zip(*NOSE_PLAN, strict=True))
        body &= ur >= np.maximum(side_sb, plan_sb)

    # --- body colours -------------------------------------------------------------
    mdl.solid(body, WHITE)
    mdl.paint(Z >= ROOF_FROM, ROOF_GREY)
    mdl.paint((RED_LINE[0] <= Z) & (RED_LINE[1] > Z) & ((ur >= 2.4) if spec.cab else True), RED)

    # --- windows ------------------------------------------------------------------
    if spec.upper:
        mdl.paint(side_band(mdl, at(spec.upper[-1][1] + 0.15), at(spec.upper[0][0] - 0.15), *UPPER_BAND), DARK)
    for s in spec.upper:
        rounded_window(mdl, *span(s), *UPPER_WIN)
    for s in spec.lower:
        rounded_window(mdl, *span(s), *LOWER_WIN)
    for s in spec.mezz:
        rounded_window(mdl, *span(s), *MEZZ_WIN)

    # --- doors: red leaves, blue band with the class numbers, displays beside them ------------
    for i, (a, b) in enumerate(spec.doors):
        x0, x1 = span((a, b))
        mdl.paint(side_band(mdl, x0, x1, *DOOR_Z), RED)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_BAND), DOOR_BLUE)
        c = (x0 + x1) / 2
        for p in (x0 + 0.3 * (x1 - x0), x0 + 0.7 * (x1 - x0)):  # class numerals
            mdl.paint(side_band(mdl, p - 1, p + 1, DOOR_BAND[0] + 1, DOOR_BAND[1]), P.OFF_WHITE)
        if spec.first_class:
            mdl.paint(side_band(mdl, x0, x1, DOOR_BAND[1], DOOR_BAND[1] + 1), FIRST_YELLOW)
        door_outline(mdl, x0, x1, *DOOR_Z, RED_DARK, lintel=0)
        for g0, g1 in ((x0 + 2, c - 1), (c + 1, x1 - 2)):
            mdl.inset(side_band(mdl, g0, g1, *DOOR_GLASS), P.GLASS)
        inner = (b + 0.6, b + 1.6) if i == 0 else (a - 1.6, a - 0.6)  # display towards the car centre
        mdl.paint(side_band(mdl, *span(inner), *DISPLAY_Z), BLACK)

    # SBB panel behind the first door
    lg = (spec.doors[0][1] + 1.8, spec.doors[0][1] + 2.7)
    mdl.paint(side_band(mdl, *span(lg), *LOGO_Z), RED)
    lx0, lx1 = span(lg)
    mdl.paint(side_band(mdl, (lx0 + lx1) / 2 - 1.5, (lx0 + lx1) / 2 + 1.5, LOGO_Z[0] + 1, LOGO_Z[1] - 1), P.OFF_WHITE)

    # louvred grilles at the roof edge
    for s in spec.roof_louvres:
        louvres(mdl, *span(s), *ROOF_LOUVRE_Z, pitch=2, back=P.DARK_GREY, slat=P.MID_GREY)

    # --- cab car: equipment hatches, nose ------------------------------------------------
    if spec.cab:
        hatch = span((3.30, 4.20))
        mdl.paint(side_band(mdl, *hatch, 18, 35), HATCH)
        louvres(mdl, hatch[0] + 1, hatch[1] - 1, 19, 34, pitch=2, back=P.MID_GREY, slat=P.LIGHT_GREY)
        door_outline(mdl, *span((4.61, 5.21)), 30, 35, P.MID_GREY)  # service flap
        rear_hatch = span((23.97, 24.98))
        door_outline(mdl, *rear_hatch, 18, 35, P.MID_GREY)
        louvres(mdl, rear_hatch[0] + 2, rear_hatch[1] - 2, 31, 34, horizontal=True, back=P.MID_GREY, slat=HATCH)
        _nose(mdl, ur, dy, Z)
        lamp_cluster(
            mdl, shell, True, lights.state("front"), low_z=(21, 25), top_z=(51, 53), spacing=10, lamp_half_width=2,
            face=True,
        )  # fmt: skip

    # --- ends: gangway bellows ------------------------------------------------------------
    for front in (False,) if spec.cab else (False, True):
        skin = face_mask(mdl, front, depth=2) & (Z >= HIGH_FLOOR)
        mdl.paint(skin & (dy <= 8) & (ROOF - 4 > Z), BLACK)
        mdl.paint(skin & (dy <= 6) & (Z >= HIGH_FLOOR + 2) & (ROOF - 6 > Z), DARK)

    # --- roof -----------------------------------------------------------------------------
    for s in spec.roof_boxes:
        roof_box(mdl, *span(s), 10, ROOF - 1, 2, P.MID_GREY)
    if spec.pantograph is not None:
        px = at(spec.pantograph)
        pantograph(mdl, px, ROOF - 1, raised=spec.pantograph_raised, facing_front=True, raise_height=11)
        main_switch(mdl, px + 16, ROOF)
        roof_cable(mdl, px + 4, at(15.0), ROOF)

    # --- running gear: motor bogie under the cab (2.7 m), trailer bogies (2.5 m), 920 mm wheels --
    for i, b in enumerate(spec.bogies):
        motor = spec.cab and i == 0
        wb = (2.7 if motor else 2.5) * 10 * scale
        bogie(mdl, at(b), wheelbase=wb, wheel_diameter=9, top=HIGH_FLOOR - 3, style="loco" if motor else "coach")

    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose(mdl: Model, ur: np.ndarray, dy: np.ndarray, Z: np.ndarray) -> None:
    """Front (photo of the head-on view, REFERENCE.md "Nose"): red mask round the black
    windscreen with a V-shaped lower edge, roof cap, dark recess with the lamps, white lower
    corners with grilles. Side: red line along the windscreen edge, black wrap above it, black
    cab side window band."""
    nose = ur < 2.6
    edge = np.interp(ur, *zip(*SIDE_LINE, strict=True)) * ZM
    mdl.paint(nose & (edge + 2 <= Z) & (Z < ROOF_FROM), BLACK)
    mdl.paint(nose & (edge <= Z) & (edge + 2 > Z) & (Z < ROOF_FROM), RED)
    u0, u1, z0, z1 = CAB_WINDOW
    cab_win = (ur >= u0) & (ur < u1) & (z0 <= Z) & (z1 > Z) & (dy >= HALF_WIDTH - 2)
    mdl.paint(cab_win, BLACK)
    mdl.inset(cab_win & (ur >= 2.0) & (ur < 2.6) & (z0 + 1 <= Z) & (z1 - 1 > Z), P.GLASS)

    h = Z / ZM  # height (m)
    w = dy / ZM  # half-width (m)
    # the outermost columns (beyond 1.27 m) are the body sides wrapping round: they keep the
    # side livery above (white below the red line, black wrap above it)
    face = face_mask(mdl, True, depth=3) & (ur < 3.0) & (w <= 1.27)
    mdl.paint(face & (h >= 1.6), RED)
    v_bottom = 2.54 + 0.21 * np.clip(w / 1.15, 0, 1)  # V-shaped lower edge of the windscreen frame
    mdl.paint(face & (h >= v_bottom) & (w <= 1.15), BLACK)
    mdl.paint(face & (h >= 3.7) & (w > 1.15), BLACK)  # the frame reaches the edge at the top
    mdl.inset(face & (h >= v_bottom + 0.15) & (h < 3.95) & (w <= 1.0), P.GLASS)
    mdl.paint(face & (h >= 3.98) & (h < 4.31) & (w <= 0.7), DARK)  # destination display
    mdl.paint(face & (h < 1.61) & (w <= 0.7), DARK)  # recess with the coupler
    lower = face_mask(mdl, True, depth=3) & (ur < 3.0) & (h < 1.59)
    mdl.paint(lower & (w > 0.7), WHITE)  # white lower corners, round onto the sides
    mdl.paint(face & (h >= 0.74) & (h < 1.36) & (w >= 0.9) & (w < 1.3), DARK)  # grilles
    mdl.paint(face & (h >= 1.61) & (h < 2.12) & (w > 0.61) & (w <= 1.07), DARK)  # lamp recess
