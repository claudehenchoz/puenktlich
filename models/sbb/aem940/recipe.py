"""SBB Aem 940 (Alstom Prima H4): bi-mode (15/25 kV electric + diesel) Bo'Bo' hood unit for
infrastructure and shunting work. Measurements, photos and livery: REFERENCE.md.

Front (high x) = the end with the taller grilled hood; the lower hood with the railings is at
the rear. 18.75 m over buffers = 6/8.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.hood import Block, HoodSpec, build_hood_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = HoodSpec(
    length_m=18.75,
    frame_z=(12, 25),
    hoods=(Block(0.3, 7.8, top=45, half_width=15), Block(11.8, 17.3, top=40, half_width=15)),
    cab=Block(7.8, 11.8, top=54, half_width=18),
    cab_windows=(41, 51),
    bogies=(4.3, 13.3),
    bogie_wheelbase=2.6,
    wheel=9,
    livery="sbb",
    pantograph_u=9.8,
    lamps={"low_z": (27, 30), "top_z": (39, 41), "spacing": 11},
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_hood_loco(SPEC, lights)
