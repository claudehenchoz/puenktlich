"""VBZ MAN Lion's City: 12 E (12.2 m), 18 E (18.06 m) battery buses and the diesel
Lion's City GL (A40, 18.75 m). Positions from MAN's drawings and datasheets (REFERENCE.md);
builder: puenktlich.voxel.parts.citybus.

    build(type=12e|18e|gl, car=0..)

Fitted to 8 (12.2 m -> 11.2 m) and 6 + 5 (18 m -> 15.4 m) OpenTTD units.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.citybus import Car, CityBus, build_city_bus

BODY_WIDTH_M = 2.55
Z_PER_M = 13.9

TYPES = {
    "12e": CityBus(
        "man",
        cars=[Car(0, 12.2, 11.2)],
        axles=[(2.75, False), (8.82, True)],
        doors=[(0.45, 1.83), (5.73, 7.1), (9.7, 11.1)],
        roof=[(1.2, 4.6, 3), (5.4, 8.2, 4), (8.8, 11.4, 3)],
        height_m=3.32,
    ),
    "18e": CityBus(
        "man",
        cars=[Car(0, 9.79, 8.4), Car(9.79, 18.06, 7.0)],
        axles=[(2.74, False), (8.0, True), (14.7, True)],
        doors=[(0.45, 1.81), (4.9, 6.3), (11.6, 13.0)],
        roof=[(1.2, 4.4, 3), (5.0, 8.0, 4), (11.0, 17.2, 3)],
        height_m=3.32,
    ),
    "gl": CityBus(
        "man",
        cars=[Car(0, 10.2, 8.4), Car(10.2, 18.75, 7.0)],
        axles=[(2.75, False), (8.63, True), (15.4, True)],
        doors=[(0.45, 1.8), (5.0, 6.3), (12.2, 13.5)],
        roof=[(4.0, 7.0, 3), (12.0, 14.0, 2)],
        height_m=2.98,
        rear_window=False,
    ),
}


def build(type: str = "12e", car: int = 0) -> Model:
    return build_city_bus(TYPES[type], car)
