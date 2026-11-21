"""SBB RBDe 560 "NPZ" in the Domino look — 3-car multiple unit (one recipe, three cars).

Prototype (de.wikipedia "SBB RBDe 4/4"): motor car 25.0 m, 2.86 m wide, 3.75 m high,
Bo'Bo', wheels 950 mm, 1650 kW, 140 km/h, 70 t; built 1984–1996 (126 + 2). NPZ sets ran
motor car + converted EW I/II intermediate coaches + control car (Bt). The Domino
refurbishment (from 2006) gave white bodies, an anthracite window band, red doors and a
red front — modelled here: body CC2 (white), doors and fronts CC1 (red).
Not in the source: car-by-car window counts, baggage-door position (approximated).

    build(lights, car="motor")        front car: cab + pantograph + baggage door
    build(lights, car="intermediate") middle car
    build(lights, car="control")      rear car: control car (turned round, cab outward)
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_span, side_band
from puenktlich.voxel.parts.coach import DOOR, DOOR_SEAM, CabSpec, CoachSpec, build_coach
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SECTION = CrossSection(floor=15, roof=47, half_width=19, roof_radius=8, tumblehome=1, tumble_from=24)
NOSE = EndShape(rake=8, rake_from=30, rake_curve=1.2, corner_radius=6, undercut=2, undercut_height=4)
CAB = CabSpec(nose=NOSE, windscreen_z=(31, 43), windscreen_half_width=16, door_from_end=(24, 32))


def _motor_extras(mdl: Model, shell: Shell) -> None:
    """Pantograph + roof gear towards the rear, double baggage door behind the cab."""
    roof_z = shell.section.roof + 1
    mid = shell.mid
    pantograph(mdl, mid - 50, roof_z, raised=True, facing_front=False)
    main_switch(mdl, mid - 22, roof_z)
    roof_box(mdl, mid - 10, mid + 30, 9, roof_z - 1, 3)
    x0, x1 = end_span(shell, True, 46, 64)  # baggage compartment door
    leaf = side_band(mdl, x0, x1, shell.section.floor + 1, 42)
    mdl.paint(leaf, DOOR)
    mdl.inset(leaf & ~side_band(mdl, x0 + 1, x1 - 1, shell.section.floor + 2, 41), DOOR_SEAM)
    mdl.inset(side_band(mdl, (x0 + x1) / 2 - 0.5, (x0 + x1) / 2 + 0.5, shell.section.floor + 2, 41), DOOR_SEAM)


def _spec(car: str) -> CoachSpec:
    common = dict(section=SECTION, window_band=True, roof_line=False, wheel_diameter=10, bogie_centres_m=9.0)
    if car == "motor":
        return CoachSpec(
            windows=7,
            cab=CAB,
            mu_role="front",
            cab_colour=P.ramp(P.CC1, 0.6),
            door_from_end=(24, 36),
            extras=_motor_extras,
            wheelbase=26,
            **common,
        )
    if car == "intermediate":
        return CoachSpec(windows=10, mu_role="middle", **common)
    if car == "control":
        return CoachSpec(windows=9, cab=CAB, mu_role="rear", cab_colour=P.ramp(P.CC1, 0.6), **common)
    raise ValueError(f"unknown NPZ car {car!r}")


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "motor") -> Model:
    return build_coach(_spec(car), lights)
