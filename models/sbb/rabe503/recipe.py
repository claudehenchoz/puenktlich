"""SBB RABe 503 "Astoro" (Alstom ETR 610, New Pendolino): every car of the 7-car tilting unit,
in true proportions. Measurements (3D model, Lima H0 model, photos, GDL brochure), livery and
car layouts: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab_first      car 1, cab, 1st class
          first          car 2, 1st class
          dining         car 3, restaurant + 1st class, DB pantograph (lowered)
          second_pan_up  car 4, 2nd class, SBB pantograph (raised) + DC pantograph
          second_pan     car 5, 2nd class, SBB + DC pantographs (lowered)
          second_db      car 6, 2nd class, DB pantograph (lowered)
          cab            car 7, cab, 2nd class
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

Real lengths: end cars 27.7 m, intermediates 26.2 m (187.4 m over couplers); every car is
compressed to its 8/8 slot (25.6 m).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.etr610 import EtrSpec, Panto, build_etr_car, dining_car, end_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.83  # 2,830 mm, authored at this width (docs/SCALE.md)

L = 26.2  # intermediate car, real metres
# GDL brochure: SBB/IT AC (1,450 mm) and DC (1,950 mm) pantographs on cars 4 and 5, DB on 3 and 6;
# the pantographs sit over the inner side of the bogies, knees towards the car centre
CARS = {
    "cab_first": lambda: end_car(first_class=True),
    "first": lambda: EtrSpec(first_class=True),
    "dining": lambda: dining_car(),
    "second_pan_up": lambda: EtrSpec(
        pantographs=(Panto(5.8, False), Panto(L - 5.8, True, raised=True, main_switch=True)), roof_line=True
    ),
    "second_pan": lambda: EtrSpec(
        pantographs=(Panto(5.8, False, main_switch=True), Panto(L - 5.8, True)), roof_line=True
    ),
    "second_db": lambda: EtrSpec(pantographs=(Panto(5.5, False),), roof_line=True),
    "cab": lambda: end_car(),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second_db", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_etr_car(spec, lights)
