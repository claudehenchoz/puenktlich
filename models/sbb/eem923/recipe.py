"""SBB Eem 923 (Stadler, "Butler"): electro-diesel two-axle shunting locomotive for SBB Cargo.
Measurements, photos and livery: REFERENCE.md.

Front (high x) = the red short hood end. 9.13 m over buffers = 3/8.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.hood import Block, HoodSpec, build_hood_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 3.1  # 3,100 mm (docs/SCALE.md)

SPEC = HoodSpec(
    length_m=9.13,
    frame_z=(5, 16),
    hoods=(Block(0.3, 2.75, top=36, half_width=16), Block(5.2, 7.6, top=36, half_width=16)),
    cab=Block(2.75, 5.2, top=50, half_width=19),
    cab_windows=(37, 46),
    axles=(1.8, 6.1),
    wheel=11,
    livery="cargo",
    cargo_split=2.45,
    pantograph_u=4.0,
    roof_overhang=1,
    lamps={"low_z": (19, 22), "top_z": (31, 33), "spacing": 11},
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_hood_loco(SPEC, lights)
