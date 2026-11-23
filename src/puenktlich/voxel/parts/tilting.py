"""Single-deck tilting multiple-unit cars: SBB RABDe 500 (ICN). Measurements and photos:
models/sbb/rabde500/REFERENCE.md. (The RABe 503 / ETR 610 has its own builder, parts/etr610.py.)

`build_tilting_car(spec, lights)` builds one 8/8 car on the train canvas from a `TiltSpec`.
Positions along the car are *real* metres from the car's front end (cab cars: from the nose
tip), scaled to the modelled 25.6 m like `parts/smile.py`. Cars run on ordinary bogies near the
ends. The bodies taper above the window band (tilting profile: `CrossSection.chamfer_*`).

style "icn": white body CC2, dark window band, black skirt, dark roof; blunter nose: silver lower
    nose, red (CC1) mask round the black windscreen.
Multiple-unit lamp roles work like `DostoSpec.mu_role`.
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
    side_band,
)
from puenktlich.voxel.parts.lights import lamp_cluster, mu_lights
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box
from puenktlich.voxel.parts.running_gear import bogie
from puenktlich.voxel.variants import Lights

FLOOR = 12  # body underside (high-floor cars)
WHEEL = 9  # 820–890 mm
WHEELBASE = 2.7  # m


@dataclass(frozen=True)
class Style:
    roof: float  # roof top (z)
    band: tuple[float, float]  # dark window band (z)
    roof_from: float  # dark roof above
    skirt_top: float  # black skirt below (0: none)
    red_line: tuple[float, float] | None  # cant line (z), CC1
    nose: EndShape
    nose_len: float  # nose section, modelled m from the tip
    door_z: tuple[float, float]
    roof_colour: int = P.ROOF_DARK


STYLES = {
    # REFERENCE.md (RABDe 500): height 3.95 m -> roof z 48
    "icn": Style(
        roof=48,
        band=(18, 30),
        roof_from=44,
        skirt_top=15,
        red_line=None,
        nose=EndShape(rake=34, rake_from=22, corner_radius=14, undercut=5, undercut_height=10, profile="ellipse"),
        nose_len=4.2,
        door_z=(9, 34),
        roof_colour=P.ROOF,
    ),
}

WHITE = P.BODY_CC2
RED = P.BODY_CC1
BLACK = P.BLACK
DARK = P.DARK
SILVER = P.ramp(P.GREY, 0.72)
FIRST_YELLOW = P.YELLOW
DISPLAY = P.YELLOW


@dataclass
class TiltSpec:
    style: Literal["icn"] = "icn"
    cab: bool = False  # cab at the front (high x)
    real_m: float = 26.4
    length_m: float = 25.6  # modelled length
    doors: tuple[float, ...] = (1.6, 24.8)  # door centres, real metres from the front end
    door_width: float = 0.9
    bogies: tuple[float, float] = (3.6, 22.8)  # bogie centres, real metres
    first_class: bool = False  # yellow line over the window band
    dining: bool = False  # red band in the window band
    pantograph: bool = False  # on the roof over the rear bogie
    pantograph_raised: bool = False
    mu_role: Literal["front", "middle", "rear"] = "middle"
    window_pitch: float = 1.9
    window_width: float = 1.4


def cab_car(style: str, **kw) -> TiltSpec:
    """Cab end car: long nose, one door behind the cab and one at the rear end."""
    base = {
        "icn": TiltSpec(style="icn", cab=True, real_m=28.4, doors=(6.2, 26.8), bogies=(5.6, 25.4)),
    }[style]
    return replace(base, **kw)


def build_tilting_car(spec: TiltSpec, lights: Lights) -> Model:
    st = STYLES[spec.style]
    turn_round = spec.mu_role == "rear" and spec.cab
    lights = mu_lights(spec.mu_role, lights)

    mdl = Model.new()
    sx = mdl.d.shape[0]
    lob = spec.length_m * 10
    x_rear, x_front = sx / 2 - lob / 2 + 1, sx / 2 + lob / 2 - 2
    scale = spec.length_m / spec.real_m

    def at(u: float) -> float:
        """Real metres from the front end -> x."""
        return x_front - u * 10 * scale

    section = CrossSection(
        floor=FLOOR,
        roof=st.roof,
        half_width=19.5,
        roof_radius=8,
        tumblehome=1.0,
        tumble_from=16,
        chamfer_from=st.band[1] + 2,
        chamfer_inset=3,
    )
    end = EndShape(rake=0, corner_radius=3)
    shell = Shell(x_rear, x_front, section, front=st.nose if spec.cab else end, rear=end)
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    u = (x_front - X) / 10  # modelled metres from the front
    nose_end = st.nose_len if spec.cab else 0.0

    # --- body colours ---------------------------------------------------------
    mdl.solid(shell.mask(mdl), WHITE)
    mdl.paint(st.roof_from <= Z, st.roof_colour)
    if st.skirt_top:
        mdl.paint((st.skirt_top > Z) & (u >= nose_end - 1), BLACK)
    if st.red_line is not None:
        mdl.paint((st.red_line[0] <= Z) & (st.red_line[1] > Z) & (u >= nose_end - 0.5), RED)
    band = side_band(mdl, x_rear + 3, at(nose_end / scale + 0.6) if spec.cab else x_front - 3, *st.band)
    mdl.paint(band, RED if spec.dining else DARK)
    if spec.dining:
        mdl.paint(band & (st.band[0] + 2 <= Z) & (st.band[1] - 2 > Z), DARK)
    if spec.first_class:
        mdl.paint(
            side_band(
                mdl, x_rear + 3, at(nose_end / scale + 0.6) if spec.cab else x_front - 3, st.band[1], st.band[1] + 1
            ),
            FIRST_YELLOW,
        )

    # --- windows in the band: glass panes at a regular pitch ---------------------------
    door_x = [(at(c + spec.door_width / 2), at(c - spec.door_width / 2)) for c in spec.doors]
    pitch, ww = spec.window_pitch * 10 * scale, spec.window_width * 10 * scale
    x = x_rear + 8
    stop = at(nose_end / scale + 1.4) if spec.cab else x_front - 8
    while x + ww <= stop:
        if not any(x + ww > a - 3 and x < b + 3 for a, b in door_x):
            mdl.inset(side_band(mdl, x, x + ww, st.band[0] + 1, st.band[1] - 1), P.GLASS)
        x += pitch

    # --- doors (both sides): white plug doors with a seam and a narrow window ------------
    for x0, x1 in door_x:
        z0, z1 = st.door_z
        mdl.paint(side_band(mdl, x0, x1, z0, z1), WHITE)
        door_outline(mdl, x0, x1, z0, z1, P.MID_GREY, sill=0)
        mdl.inset(side_band(mdl, x0 + 2, x1 - 2, st.band[0] + 1, st.band[1] - 1), P.GLASS)

    # --- nose ---------------------------------------------------------------------------
    if spec.cab:
        _nose_icn(mdl, at, scale, u, dy, st)
        lamp_cluster(
            mdl,
            shell,
            True,
            lights.state("front"),
            low_z=(21, 24),
            top_z=(44, 46),
            spacing=12,
            lamp_half_width=2,
            face=True,
        )

    # SBB logo and lettering under the band near the rear end
    lx = at(spec.real_m - 3.5)
    lz = max(st.band[0] - 5, st.skirt_top + 1)
    mdl.paint(side_band(mdl, lx, lx + 8, lz, lz + 3), RED)
    mdl.paint(side_band(mdl, lx + 3, lx + 5, lz + 1, lz + 2), P.OFF_WHITE)
    mdl.paint(side_band(mdl, lx + 10, lx + 26, lz + 1, lz + 2), DARK)

    # --- ends: gangway bellows ------------------------------------------------------------
    for front in (False, True) if not spec.cab else (False,):
        skin = face_mask(mdl, front, depth=2) & (Z >= FLOOR)
        mdl.paint(skin & (dy <= 9) & (st.roof - 3 > Z), BLACK)

    # --- roof -----------------------------------------------------------------------------
    roof_box(mdl, at(spec.real_m / 2 + 2.0), at(spec.real_m / 2 - 2.0), 8, st.roof - 1, 2, P.MID_GREY)
    if spec.pantograph:
        px = at(spec.bogies[1])
        pantograph(mdl, px, st.roof - 1, raised=spec.pantograph_raised, facing_front=False, raise_height=16)
        main_switch(mdl, px + 14, st.roof - 1)

    # --- running gear ---------------------------------------------------------------------
    for b in spec.bogies:
        bogie(mdl, at(b), wheelbase=WHEELBASE * 10 * scale, wheel_diameter=WHEEL, top=FLOOR)

    if turn_round:
        mdl.rotate_180()
    return mdl


def _nose_icn(mdl: Model, at, scale: float, u: np.ndarray, dy: np.ndarray, st: Style) -> None:
    """ICN nose: silver lower nose, red mask round the black windscreen, black skirt."""
    _, _, Z = mdl.coords()
    nose = u < st.nose_len
    red_lo = 24 + (st.roof_from - 24) * np.clip((u - 1.6) / (st.nose_len - 1.6), 0, 1)
    mdl.paint(nose & (st.skirt_top <= Z) & (red_lo > Z) & (u < 3.2), SILVER)
    mdl.paint(nose & (red_lo <= Z) & (st.roof_from > Z), RED)
    mdl.paint(nose & (st.skirt_top > Z), BLACK)
    wrap = 32 + 7 * np.clip((u - 0.8) / 1.6, 0, 1)  # black windscreen wrap on the sides
    mdl.paint(nose & (u < 2.4) & (wrap <= Z), BLACK)
    cab_win = side_band(mdl, at(3.8 / scale), at(2.7 / scale), 28, 35)
    mdl.paint(cab_win, BLACK)
    mdl.inset(cab_win & side_band(mdl, at(3.7 / scale), at(2.8 / scale), 29, 34), P.GLASS)
    face = face_mask(mdl, True, depth=3) & (u < 3.0) & (dy <= 17)
    mdl.paint(face & (st.skirt_top <= Z) & (Z < 24), SILVER)
    mdl.paint(face & (Z >= 24), RED)
    mdl.paint(face & (Z >= 28) & (Z < 44) & (dy <= 13), BLACK)
    mdl.inset(face & (Z >= 30) & (Z < 41) & (dy <= 12), P.GLASS)
    mdl.paint(face & (Z >= 41) & (Z < 43) & (dy <= 7), DISPLAY)
    mdl.paint(face & (Z >= 45) & (dy <= 10), BLACK)
    mdl.paint(face & (st.skirt_top > Z), BLACK)
