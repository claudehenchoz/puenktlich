"""SBB RABe 511 Regio-Dosto (Stadler KISS): every car of the 6-car (511 001–069) and 4-car
(511 101–124) units. Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab        end car with cab and motor bogie (Bt / Bt with WC)
          first      intermediate car with the 1st-class section (yellow strips over the doors)
          second     2nd-class intermediate car
          panto      2nd-class intermediate car with the pantograph in a roof well at its front
          panto_first  pantograph car with the 1st-class section (4-car units)
          panto_rear the same as panto, turned round: pantograph at its rear, lowered
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

Cars are 25.0–25.4 m over couplers (Bt: 25.36 m), modelled at 25.0 m (8/8).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.kiss import KissSpec, build_kiss_car, cab_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.8  # 2,800 mm (docs/SCALE.md)

CARS = {
    "cab": lambda: cab_car(),
    "first": lambda: KissSpec(first_class=True),
    "second": lambda: KissSpec(),
    "panto": lambda: KissSpec(pantograph=True),
    "panto_first": lambda: KissSpec(pantograph=True, first_class=True),
    "panto_rear": lambda: KissSpec(pantograph=True, pantograph_raised=False, turned=True),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_kiss_car(spec, lights)
