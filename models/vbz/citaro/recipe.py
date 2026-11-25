"""VBZ Mercedes-Benz Citaro (O 530 facelift, 12 m) and Citaro G (O 530 G, 18 m, 4 doors).
Positions from Daimler's type drawings and data sheets (REFERENCE.md); builder:
puenktlich.voxel.parts.citybus.

    build(type=solo|g, car=0..)

Fitted to 8 (12 m -> 11.2 m) and 6 + 5 (18 m -> 15.4 m) OpenTTD units.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.citybus import Car, CityBus, build_city_bus

BODY_WIDTH_M = 2.55
Z_PER_M = 13.9

TYPES = {
    "solo": CityBus(
        "citaro",
        cars=[Car(0, 12.0, 11.2)],
        axles=[(2.7, False), (8.55, True)],
        doors=[(0.5, 1.85), (4.4, 5.7), (9.8, 11.1)],
        roof=[(4.5, 7.5, 3)],
        height_m=3.1,
        rear_window=False,
    ),
    "g": CityBus(
        "citaro",
        cars=[Car(0, 10.5, 8.4), Car(10.5, 18.0, 7.0)],
        axles=[(2.85, False), (8.72, True), (14.7, True)],
        doors=[(0.55, 1.94), (6.4, 7.8), (12.4, 13.8), (16.0, 17.3)],
        roof=[(3.0, 6.5, 3), (11.2, 12.4, 2)],
        height_m=3.1,
        rear_window=False,
    ),
}


def build(type: str = "solo", car: int = 0) -> Model:
    return build_city_bus(TYPES[type], car)
