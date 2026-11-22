"""SBB Ee 922 (Stadler): two-axle electric shunting locomotive (15/25 kV) for passenger-station
shunting. Measurements, photos and livery: REFERENCE.md.

Front (high x) = the low front hood with the railings; the cab with its roof canopy stands
behind it, followed by a short rear section. 8.8 m over buffers = 3/8.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.hood import Block, HoodSpec, build_hood_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = HoodSpec(
    length_m=8.8,
    frame_z=(5, 16),
    hoods=(Block(0.2, 2.3, top=33, half_width=16), Block(6.0, 7.4, top=32, half_width=17)),
    cab=Block(2.3, 6.0, top=50, half_width=19),
    cab_windows=(38, 48),
    axles=(1.8, 5.8),
    wheel=11,
    livery="sbb",
    pantograph_u=4.2,
    roof_overhang=1,
    lamps={"low_z": (18, 21), "top_z": (28, 30), "spacing": 11},
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_hood_loco(SPEC, lights)
