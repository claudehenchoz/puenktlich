"""MGB HGe 4/4 II — metre-gauge Bo'Bo' rack and adhesion electric locomotive (SLM/BBC, 1985–1990).

Approximate prototype data (from memory, to be cross-checked against de.wikipedia
"HGe 4/4 II"): about 14.8 m over buffers, 64 t, 1932 kW, 90 km/h on adhesion and about
35–40 km/h on the Abt rack, 11 kV 16.7 Hz. Built for the Furka-Oberalp (now MGB), the BVZ
and the SBB Brünig line (now zb). Boxy body with flat, slightly raked cab fronts, two
single-arm pantographs, and a rack drive in each bogie.

The `rack_drive` under each bogie is the visible difference to an adhesion loco. In game,
rack track (NRA*) can only be entered by trains with a rack engine (data/tracks.yaml).
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape
from puenktlich.voxel.parts.loco import LocoSpec, Louvres, Panel, Windscreen, build_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = LocoSpec(
    length_m=14.8,
    section=CrossSection(floor=14, roof=46, half_width=18, roof_radius=4, tumblehome=0.5, tumble_from=26),
    nose=EndShape(rake=4, rake_from=30, rake_curve=1.0, corner_radius=3, undercut=2, undercut_height=4),
    # two-pane windscreen in a black frame, centre pillar
    windscreen=Windscreen(
        frame_z=(30, 44), frame_half_width=16, glass_z=(32, 42), glass_half_width=14.5, depth=12, centre_pillar=0.8
    ),
    cab_window=(6, 13),
    cab_window_z=(32, 42),
    door=(14, 21),
    door_z=(16, 43),
    lamps=dict(low_z=(19, 23), top_z=(44, 46), spacing=11),
    # machine room: a row of louvred grilles and two small windows per side
    louvres=Louvres(offsets=(-26, 0, 26), half_length=9, z=(31, 41), horizontal=True, pitch=2),
    side_windows=(-13, 13),
    # white band along the sides at waist height (CC2: white in the MGB livery)
    panels=(Panel(z=(25, 27), colour=P.STRIPE_CC2),),
    bogie_centres_m=3.7,
    wheelbase_m=2.5,
    wheel_diameter=10,
    gauge="metre",
    rack=True,  # rack drive under each bogie: the visible difference to an adhesion loco
    buffer_depth=5,
    buffer_spacing=10,
    skirt_gap=18,
    skirt_half_width=13,
    roof_depth=2,
    roof_setback=12,
    pantograph_offset=24,
    roof_boxes=((-12, -5, 7),),
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_loco(SPEC, lights)
