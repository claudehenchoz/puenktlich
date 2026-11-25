"""VBZ Hess lighTram 10 Plug (battery Quartierbus 340-354), 10.8 m, 8/8 at its true length.
Measured from the side press photo (bus = 10.80 m): front overhang 2.5 m, wheelbase 4.8 m;
single front door, double middle door; batteries along the roof. REFERENCE.md; builder:
puenktlich.voxel.parts.citybus.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.citybus import Car, CityBus, build_city_bus

BODY_WIDTH_M = 2.55
Z_PER_M = 13.9

BUS = CityBus(
    "lightram",
    cars=[Car(0, 10.8, 10.8)],
    axles=[(2.6, False), (7.3, True)],
    doors=[(0.67, 1.59), (4.85, 6.25)],
    roof=[(1.6, 9.6, 3)],
    height_m=3.3,
)


def build() -> Model:
    return build_city_bus(BUS)
