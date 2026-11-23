"""SBB RABe 503 "Astoro" (Alstom ETR 610, New Pendolino) in true proportions.

`build_etr_car(spec, lights)` builds one car on the train canvas from an `EtrSpec`. Sizes are
measured from the ETR 610 glTF props, the Lima H0 model photos, Wikimedia photos and the GDL
brochure (models/sbb/rabe503/REFERENCE.md). Positions along the car are *real* metres from the
car's front end (cab cars: from the nose tip), scaled to the modelled 25.6 m (8/8): the real
cars are longer (end cars 27.7 m, intermediates 26.2 m). Heights and widths are 12.2 voxels per
metre (roof 4.10 m = z 50, the 2.83 m body 34 voxels wide), so the recipe's BODY_WIDTH_M keeps
the authored width when rendered (docs/SCALE.md).

Structure: single-deck high-floor cars on bogies near the ends, the body tapering above the
window band (tilting profile). End cars have a long, low nose (measured top, bottom and plan
tables) with a steep windscreen. Livery: white body CC2, dark window band with framed windows,
thin red (CC1) cant line under the anthracite roof, dark skirt, red end panels with a blue class
marker at the car ends (1st class: yellow top third), red nose top with a black windscreen,
round lamps either side of the white bumper tip. Restaurant car: red window band on the dining
half, plain kitchen half with a service door.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    side_skin,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

ZM = 12.2  # voxels per metre across and up (true proportions)

# heights (z), REFERENCE.md "Measurements"
FLOOR = 6  # body underside between the bogies, 0.46 m
FLOOR_BOGIE = 12  # over the bogies, 1.0 m (bogies exposed under the body)
NOSE_FLOOR = 4  # under the nose, 0.30 m
SKIRT_TOP = 13  # dark skirt below 1.05 m
BAND = (22, 34)  # dark window band 1.80–2.75 m
WINDOW_Z = (23, 33)
YELLOW_FROM = 31  # 1st class: yellow top third of the red end panels
RED_LINE = (45, 47)  # thin red cant line 3.70–3.85 m
ROOF_FROM = 47  # anthracite roof above
ROOF = 50  # 4.10 m
DOOR_Z = (12, 38)  # plug doors 1.0–3.1 m
DOOR_WINDOW_Z = (25, 32)
LOGO_Z = (18, 21)
LETTERING_Z = (37, 39)  # "Restaurant" over the band, 3.0–3.2 m
HALF_WIDTH = 17  # 1.415 m

# tilting profile: vertical sides to 2.7 m, tapering inwards above, round roof (measured
# half-widths 16.5 at 3.06 m, 15.5 at 3.45 m, 14.1 at 3.68 m, 11.7 at 3.83 m); skirt 0.93 wide
SECTION = CrossSection(
    floor=FLOOR,
    roof=ROOF,
    half_width=HALF_WIDTH,
    roof_radius=13,
    tumblehome=1,
    tumble_from=11,
    chamfer_from=33,
    chamfer_inset=3,
)
END = EndShape(rake=0, corner_radius=3)
FLAT = EndShape(rake=0, corner_radius=0)  # the nose is cut by nose_mask()

# nose (real metres from the tip), REFERENCE.md "Nose": silhouette top and bottom, plan half-width
NOSE_TOP = (
    (0.0, 1.18), (0.25, 1.33), (0.5, 1.46), (0.75, 1.59), (1.0, 1.69), (1.5, 1.87), (2.0, 2.03),
    (2.5, 2.18), (3.0, 2.34), (3.5, 2.52), (3.75, 2.72), (4.0, 2.98), (4.25, 3.24), (4.5, 3.39),
    (5.0, 3.65), (5.5, 3.83), (6.0, 3.96), (6.5, 4.05), (6.9, 4.10),
)  # fmt: skip
NOSE_BOTTOM = ((0.0, 0.95), (0.25, 0.66), (0.5, 0.55), (0.75, 0.30))
NOSE_HALF = (
    (0.0, 0.15), (0.25, 0.50), (0.5, 0.76), (0.75, 0.89), (1.0, 1.03), (1.5, 1.14), (2.0, 1.22),
    (2.5, 1.27), (3.0, 1.33), (3.5, 1.38), (4.0, 1.415),
)  # fmt: skip
NOSE_LEN = 6.9  # roof height reached
NOSE_ROUND = 4  # voxel radius of the rounded top edges of the nose
RED_TOP_TO = 2.9  # red nose top back to the windscreen
WINDSCREEN = (3.0, 4.7)
CAB_WINDOW = ((3.6, 5.75), (2.05, 2.75), ((3.6, 2.2), (4.0, 2.55), (5.4, 3.3), (5.75, 2.95)))
SEAM = ((4.3, 0.95), (7.0, 3.85))  # cab module joint, a thin dark diagonal on the side
# depth (voxels) of the black windscreen/roof cap below the nose silhouette, seen from the side
SIDE_BLACK = ((0.0, 0.0), (2.9, 0.0), (4.0, 2.0), (5.5, 4.0), (6.9, 3.0))

WHITE = P.BODY_CC2
RED = P.BODY_CC1
BLACK = P.BLACK
DARK = P.DARK
ROOF_GREY = P.ROOF_DARK
CLASS_BLUE = P.ramp(P.BRIGHT_BLUE, 0.35)
FIRST_YELLOW = P.YELLOW
SEAM_GREY = P.MID_GREY


@dataclass(frozen=True)
class Panto:
    u: float  # real metres from the car's front end
    facing_front: bool  # knee towards the front (high x)
    raised: bool = False
    main_switch: bool = False  # SBB 15 kV pantographs: main switch inboard


@dataclass
class EtrSpec:
    kind: Literal["cab", "intermediate", "dining"] = "intermediate"
    first_class: bool = False
    real_m: float = 26.2
    length_m: float = 25.6  # modelled (8/8)
    bogies: tuple[float, float] = (3.7, 22.5)
    pantographs: tuple[Panto, ...] = ()
    roof_line: bool = False  # 25/15 kV roof line through cars 3–6
    mu_role: Literal["front", "middle", "rear"] = "middle"
    # intermediate cars: 10 windows at 1.95 m round the car centre, doors at both ends
    windows: tuple[float, ...] = field(default_factory=lambda: tuple(13.1 + (k - 4.5) * 1.95 for k in range(10)))
    window_width: float = 1.4


def end_car(**kw) -> EtrSpec:
    """Cab end car (27.7 m): nose, door behind the cab, 8 windows, door and red panel at the rear."""
    base = EtrSpec(
        kind="cab",
        real_m=27.7,
        bogies=(5.6, 23.65),
        windows=tuple(8.85 + k * 1.88 for k in range(8)),
    )
    return replace(base, **kw)


def dining_car(**kw) -> EtrSpec:
    """Restaurant car (car 3, WR + A): 1st-class end at the front (towards car 2), red band with
    5 windows over the dining room, plain kitchen half with a service door; DB pantograph at
    the rear end (towards car 4)."""
    base = EtrSpec(
        kind="dining",
        first_class=True,
        windows=tuple(4.55 + k * 2.03 for k in range(5)),
        window_width=1.45,
        pantographs=(Panto(26.2 - 5.5, facing_front=True),),
        roof_line=True,
    )
    return replace(base, **kw)


def nose_mask(mdl: Model, ur: np.ndarray, dy: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """The nose from the measured tables: plan half-width, top and bottom by distance from the
    tip, with rounded top edges. Behind NOSE_LEN everything (the body section does the rest)."""
    top = np.interp(ur, *zip(*NOSE_TOP, strict=True)) * ZM
    bottom = np.interp(ur, *zip(*NOSE_BOTTOM, strict=True)) * ZM
    half = np.interp(ur, *zip(*NOSE_HALF, strict=True)) * HALF_WIDTH / NOSE_HALF[-1][1]
    r = NOSE_ROUND
    inside = (dy <= half) & (bottom <= Z) & (top >= Z)
    corner = (dy > half - r) & (top - r < Z)
    inside &= ~corner | ((dy - (half - r)) ** 2 + (Z - (top - r)) ** 2 <= r * r)
    return (ur >= 0) & (inside | (ur >= NOSE_LEN))


def build_etr_car(spec: EtrSpec, lights: Lights) -> Model:
    turn_round = spec.mu_role == "rear" and spec.kind == "cab"
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    scale = spec.length_m / spec.real_m
    L = spec.real_m
    cab = spec.kind == "cab"

    def at(u: float) -> float:
        """Real metres from the front end -> x."""
        return x_front - u * 10 * scale

    def span(a: float, b: float) -> tuple[float, float]:
        """x-range of real metres a..b from the front (a < b)."""
        return at(b), at(a)

    def floor_at(X: np.ndarray) -> np.ndarray:
        ur = (x_front - X) / 10 / scale
        floor = np.full_like(X, FLOOR, dtype=float)
        for b in spec.bogies:
            floor = np.where(abs(ur - b) < 2.1, FLOOR_BOGIE, floor)
        if cab:
            floor = np.where(ur < 3.4, NOSE_FLOOR, floor)
        return floor

    shell = Shell(x_rear, x_front, SECTION, front=FLAT if cab else END, rear=END, floor_at=floor_at)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    ur = (x_front - X) / 10 / scale  # real metres from the front
    body = shell.mask(mdl)
    if cab:
        body &= nose_mask(mdl, ur, dy, Z)
    nose = ur < NOSE_LEN if cab else np.zeros_like(body)

    # --- body colours ---------------------------------------------------------
    mdl.solid(body, WHITE)
    mdl.paint(Z >= ROOF_FROM, ROOF_GREY)
    mdl.paint((RED_LINE[0] <= Z) & (RED_LINE[1] > Z) & ~nose, RED)
    mdl.paint((Z < SKIRT_TOP) & ((ur >= 7.2) if cab else True), DARK)
    if cab:
        mdl.paint(nose & (Z < 7), DARK)  # dark lower lip under the nose

    # --- window band, end panels, doors ---------------------------------------------------
    def end_panel(a: float, b: float, door: tuple[float, float] | None) -> None:
        mdl.paint(side_band(mdl, *span(a, b), *BAND), RED)
        if spec.first_class:
            mdl.paint(side_band(mdl, *span(a, b), YELLOW_FROM, BAND[1]), FIRST_YELLOW)
        if door is not None:
            plug_door(*door)

    def marker(a: float) -> None:  # blue class marker with the class numeral
        mdl.paint(side_band(mdl, *span(a, a + 0.25), *BAND), CLASS_BLUE)
        mdl.paint(side_band(mdl, *span(a + 0.05, a + 0.2), BAND[1] - 4, BAND[1] - 1), P.OFF_WHITE)

    def plug_door(a: float, b: float, window: bool = True) -> None:
        x0, x1 = span(a, b)
        mdl.paint(side_band(mdl, x0, x1, *DOOR_Z), WHITE)
        door_outline(mdl, x0, x1, *DOOR_Z, P.MID_GREY, sill=0)
        if window:
            rounded_window(mdl, x0 + 2, x1 - 2, *DOOR_WINDOW_Z, frame=DARK)

    def windows(band_colour: int, a: float, b: float) -> None:
        mdl.paint(side_band(mdl, *span(a, b), *BAND), band_colour)
        for c in spec.windows:
            rounded_window(mdl, *span(c, c + spec.window_width), *WINDOW_Z, frame=BLACK)

    if spec.kind == "intermediate":
        windows(DARK, 2.85, L - 2.85)
        end_panel(0, 2.6, (0.35, 1.35))
        end_panel(L - 2.6, L, (L - 1.35, L - 0.35))
        marker(2.6)
        marker(L - 2.85)
    elif spec.kind == "dining":
        windows(RED, 2.85, 14.1)
        mdl.paint(side_band(mdl, *span(2.85, 14.1), BAND[0], BAND[0] + 2), RED)
        end_panel(0, 2.6, (0.35, 1.35))
        marker(2.6)
        plug_door(16.6, 17.7, window=False)
        mdl.inset(side_band(mdl, *span(16.85, 17.45), 30, 35), P.GLASS)  # high service-door window
        # "Restaurant": letter strokes over the dining room
        for k in range(10):
            a = 8.9 + k * 0.5
            mdl.paint(side_band(mdl, *span(a, a + 0.3), *LETTERING_Z), RED)
    else:  # cab end car
        windows(DARK, 8.75, 23.6)
        plug_door(7.55, 8.55)
        marker(24.7)
        end_panel(24.95, L, (25.55, 26.75))

    # SBB logo and lettering under the band, near the rear end (dining car: near the front)
    lu = 4.0 if spec.kind == "dining" else L - 5.0
    mdl.paint(side_band(mdl, *span(lu, lu + 1.0), *LOGO_Z), RED)
    mdl.paint(side_band(mdl, *span(lu + 0.4, lu + 0.6), LOGO_Z[0] + 1, LOGO_Z[1] - 1), P.OFF_WHITE)
    la = lu + 1.2 if spec.kind == "dining" else L - 7.9
    for k in range(6):
        a = la + k * 0.45
        mdl.paint(side_band(mdl, *span(a, a + 0.3), LOGO_Z[0] + 1, LOGO_Z[1]), DARK)

    # skirt: louvred panels between the bogies
    b0, b1 = spec.bogies
    louvres(mdl, *span(b0 + 2.4, b1 - 2.4), FLOOR + 1, SKIRT_TOP - 1, back=BLACK, slat=P.DARK_GREY)

    # --- nose ---------------------------------------------------------------------------
    if cab:
        _nose(mdl, ur, dy, Z)
        lamp_cluster(
            mdl, shell, True, lights.state("front"), low_z=(19, 22), top_z=None, spacing=11, lamp_half_width=1.5,
            face=True,
        )  # fmt: skip

    # --- ends: gangway bellows ------------------------------------------------------------
    for front in (False,) if cab else (False, True):
        skin = face_mask(mdl, front, depth=2) & (Z >= FLOOR_BOGIE)
        mdl.paint(skin & (dy <= 9) & (ROOF - 4 > Z), BLACK)

    # --- roof -----------------------------------------------------------------------------
    if cab:
        roof_box(mdl, *span(12.0, 19.5), 8, ROOF - 1, 2, P.MID_GREY)
    else:
        roof_box(mdl, *span(L / 2 - 4.3, L / 2 + 4.3), 9, ROOF - 1, 3, ROOF_GREY)
    if spec.roof_line:
        roof_cable(mdl, x_rear + 2, x_front - 2, ROOF)
    for p in spec.pantographs:
        px = at(p.u)
        pantograph(mdl, px, ROOF - 1, raised=p.raised, facing_front=p.facing_front, raise_height=16)
        if p.main_switch:
            main_switch(mdl, px + (14 if p.facing_front else -14), ROOF - 1)

    # --- running gear ---------------------------------------------------------------------
    for b in spec.bogies:
        bogie(mdl, at(b), wheelbase=2.7 * 10 * scale, wheel_diameter=9, top=FLOOR_BOGIE, style="coach")

    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose(mdl: Model, ur: np.ndarray, dy: np.ndarray, Z: np.ndarray) -> None:
    """Nose livery: red top from the bumper to the windscreen, black windscreen and roof cap
    with red edges, white bumper tip, black cab side window, the cab module seam."""
    nose = ur < NOSE_LEN
    top = np.interp(ur, *zip(*NOSE_TOP, strict=True)) * ZM
    half = np.interp(ur, *zip(*NOSE_HALF, strict=True)) * HALF_WIDTH / NOSE_HALF[-1][1]
    skin = nose & (top - 2 <= Z)  # the nose's upper surface
    mdl.paint(skin & (ur < RED_TOP_TO) & (Z >= 18), RED)
    mdl.paint(skin & (ur >= RED_TOP_TO), BLACK)
    mdl.paint(skin & (ur >= RED_TOP_TO) & (dy >= half - 2.5) & (Z < ROOF_FROM), RED)
    mdl.paint(skin & (ur >= WINDSCREEN[0]) & (ur < WINDSCREEN[1]) & (dy <= half - 4), P.GLASS)
    # seen from the side: the black windscreen/roof cap reaches down the nose flank as a wedge,
    # with a thin red line under it that runs on into the cant line
    side = side_skin(mdl) & nose
    depth = np.interp(ur, *zip(*SIDE_BLACK, strict=True))
    mdl.paint(side & (ur >= RED_TOP_TO) & (top - depth <= Z), BLACK)
    mdl.paint(side & (ur >= 0.6) & (top - depth - 1.5 <= Z) & (top - depth > Z), RED)
    mdl.paint(side & (ur >= RED_TOP_TO) & (Z >= ROOF_FROM), ROOF_GREY)

    # cab side window: a slanted black parallelogram with two panes
    (u0, u1), lo, up = CAB_WINDOW
    lower = np.interp(ur, (u0, u1), lo) * ZM
    upper = np.interp(ur, *zip(*up, strict=True)) * ZM
    win = side & (ur >= u0) & (ur < u1) & (lower <= Z) & (upper > Z)
    mdl.paint(win, BLACK)
    mdl.inset(win & (ur >= 4.3) & (ur < 5.2) & (lower + 1 <= Z) & (upper - 1 > Z), P.GLASS)

    # cab module seam
    (sa, za), (sb, zb) = SEAM
    zl = (za + (ur - sa) * (zb - za) / (sb - sa)) * ZM
    mdl.paint(side_skin(mdl) & (ur >= sa) & (ur < sb) & (abs(Z - zl) < 0.6), SEAM_GREY)
