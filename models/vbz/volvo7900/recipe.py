"""VBZ Volvo 7900 hybrids: Electric Hybrid (12.13 m, OppCharge roof rails), Hybrid
articulated LAH (18.04 m) and its 18.74 m HA version. Positions from Volvo's drawings and
rescue sheets (REFERENCE.md); builder: puenktlich.voxel.parts.citybus.

    build(type=eh|lah|ha, car=0..)

Fitted to 8 (12 m -> 11.2 m) and 6 + 5 (18 m -> 15.4 m) OpenTTD units.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.citybus import Car, CityBus, build_city_bus

BODY_WIDTH_M = 2.55
Z_PER_M = 13.9

FRONT_CAR = Car(0, 9.9, 8.4)
TYPES = {
    "eh": CityBus(
        "volvo",
        cars=[Car(0, 12.13, 11.2)],
        axles=[(2.66, False), (8.61, True)],
        doors=[(0.4, 1.6), (4.6, 5.9), (9.8, 11.0)],
        roof=[(6.6, 10.6, 3)],
        opp_charge=(4.4, 6.0),
        height_m=3.3,
    ),
    "lah": CityBus(
        "volvo",
        cars=[FRONT_CAR, Car(9.9, 18.04, 7.0)],
        axles=[(2.66, False), (8.4, True), (15.0, True)],
        doors=[(0.4, 1.6), (4.6, 5.9), (11.0, 12.3), (16.3, 17.5)],
        roof=[(11.2, 13.4, 3), (14.4, 17.2, 4)],
        height_m=3.28,
    ),
    "ha": CityBus(
        "volvo",
        cars=[FRONT_CAR, Car(9.9, 18.74, 7.0)],
        axles=[(2.66, False), (8.4, True), (15.6, True)],
        doors=[(0.4, 1.6), (4.6, 5.9), (11.0, 12.3), (17.0, 18.2)],
        roof=[(11.2, 13.4, 3), (14.8, 17.8, 4)],
        height_m=3.3,
    ),
}


def build(type: str = "lah", car: int = 0) -> Model:
    return build_city_bus(TYPES[type], car)
