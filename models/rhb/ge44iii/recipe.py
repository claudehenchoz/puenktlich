"""RhB Ge 4/4 III — metre-gauge Bo'Bo' universal electric locomotive (SLM/ABB, 1993–1999).

Prototype (de.wikipedia "RhB Ge 4/4 III"): 16.0 m over buffers, 2.80 m wide, 3.86 m high,
62 t, 2400 kW (max 3100 kW), 100 km/h, wheels 1070 mm, two single-arm pantographs,
11 kV 16.7 Hz, 12 + 1 built (641–653). Livery: RhB red with a large "RhB" logo, many
units with advertising liveries.

Metre gauge: narrower, lower body (docs/SCALE.md) and wheels at the metre-gauge positions
of the companion track GRF (running_gear.GAUGES["metre"]).
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape
from puenktlich.voxel.parts.loco import LocoSpec, Louvres, Panel, Windscreen, build_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = LocoSpec(
    length_m=16.0,
    section=CrossSection(floor=13, roof=46, half_width=18, roof_radius=6, tumblehome=1, tumble_from=24),
    nose=EndShape(rake=7, rake_from=31, rake_curve=1.2, corner_radius=5, undercut=2, undercut_height=4),
    windscreen=Windscreen(frame_z=(29, 45), frame_half_width=16, glass_z=(31, 43), glass_half_width=14, depth=14),
    cab_window=(8, 16),
    cab_window_z=(32, 42),
    door=(18, 25),
    door_z=(15, 43),
    lamps=dict(low_z=(19, 23), top_z=(45, 47), spacing=11),
    # machine-room grilles and the big RhB logo panel (CC2: white in the RhB livery)
    louvres=Louvres(offsets=(-30, 30), half_length=10, z=(34, 42)),
    panels=(Panel(z=(22, 30), colour=P.STRIPE_CC2, half_length=16),),
    bogie_centres_m=4.3,
    wheelbase_m=2.5,
    gauge="metre",
    buffer_depth=5,
    buffer_spacing=10,
    skirt_gap=20,
    skirt_half_width=13,
    roof_half_width=12,
    roof_setback=16,
    pantograph_offset=30,
    roof_boxes=((-14, -6, 7),),
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_loco(SPEC, lights)
