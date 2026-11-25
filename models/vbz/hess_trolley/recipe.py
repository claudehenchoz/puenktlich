"""VBZ Hess trolleybuses: Swisstrolley 3 and 4, lighTram 19 DC (articulated, 18.7 m) and the
double-articulated lighTram 3 and lighTram 25 DC (24.7 m). Measurements and sources:
REFERENCE.md in this directory; builder: puenktlich.voxel.parts.citybus.

    build(type=st3|st4|lt19|lt3|lt25, car=0..)   car 0 is the front section

Positions are metres behind the front tip: the lighTram 3 from VBZ type drawing 1-2441
(24,660 mm), the 18.7 m buses from the Hess side view of the lighTram 19 DC. The sections
are fitted to 6 + 5 (18.7 m -> 15.4 m) and 6 + 5 + 4 (24.7 m -> 21 m) OpenTTD units.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.citybus import Car, CityBus, build_city_bus

BODY_WIDTH_M = 2.55
Z_PER_M = 13.9

ARTIC = dict(
    cars=[Car(0, 10.47, 8.4), Car(10.47, 18.7, 7.0)],
    axles=[(2.72, False), (8.6, True), (15.35, True)],
    doors=[(0.9, 1.7), (5.0, 6.4), (12.6, 14.0), (16.4, 17.8)],
    poles_at=14.6,
)
DOUBLE = dict(
    cars=[Car(0, 10.4, 8.4), Car(10.4, 17.84, 7.0), Car(17.84, 24.66, 5.6)],
    axles=[(2.8, False), (8.65, True), (15.3, True), (22.0, False)],
    doors=[(0.5, 1.3), (4.9, 6.2), (11.5, 12.8), (19.8, 21.1), (23.0, 24.3)],
    poles_at=19.6,
)
TYPES = {
    "st3": CityBus("hess", **ARTIC, roof=[(3.0, 5.0, 3), (5.6, 9.4, 5), (11.6, 13.6, 4)], height_m=3.45),
    "st4": CityBus("hess", **ARTIC, roof=[(2.6, 9.4, 4), (11.6, 13.6, 4)], height_m=3.45),
    "lt19": CityBus("lightram", **ARTIC, roof=[(2.2, 9.6, 3), (11.4, 14.0, 3)], height_m=3.5),
    "lt3": CityBus(
        "hess", **DOUBLE, roof=[(1.4, 4.6, 3), (5.3, 8.3, 5), (11.6, 12.5, 4), (15.6, 16.3, 3)], height_m=3.45
    ),
    "lt25": CityBus("lightram", **DOUBLE, roof=[(1.4, 9.6, 3), (11.2, 16.8, 3)], height_m=3.5),
}


def build(type: str = "lt19", car: int = 0) -> Model:
    return build_city_bus(TYPES[type], car)
