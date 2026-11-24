"""SBB RABe 511 Regio-Dosto (Stadler KISS): every car of the 6-car (511 001–069) and 4-car
(511 101–124) units, in true proportions. Measurements, sources and livery: REFERENCE.md in this
directory; builder: puenktlich.voxel.parts.regio_dosto.

    build(lights, car=..., role=...)
    car:  cab           cab car (Bt), pantograph lowered in the roof well at its inner end
          cab_panto_up  the same with the pantograph raised
          first         car 2 (AB): first class upstairs and in the rear half of the lower deck
          multi         car 3 (B): multi-purpose area and wheelchair toilet
          second        car 4 (B)
          first_b       car 5 (AB): car 2's counterpart
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

Cab cars are 24.92 m from the nose tip to the coupling plane, the intermediate cars 24.72 m between
coupling planes (type sketch, scaled to 150,000 mm); modelled at 24.9 and 24.7 m.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.regio_dosto import (
    build_regio_car,
    cab_car,
    first_car,
    first_car_b,
    multi_car,
    second_car,
)
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.8  # 2,800 mm, authored at its real width (34 voxels at 12.2 per metre)

CARS = {
    "cab": lambda: cab_car(),
    "cab_panto_up": lambda: cab_car(pantograph_raised=True),
    "first": first_car,
    "multi": multi_car,
    "second": second_car,
    "first_b": first_car_b,
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_regio_car(spec, lights)
