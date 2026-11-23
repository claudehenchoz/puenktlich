"""SBB RABe 512 IR-Dosto (Stadler KISS, second generation): every car of the 6-car unit, in
true proportions. Measurements (Stadler type sketch and datasheet), photos and livery:
REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab          cars 1 and 6: cab car (Bt) with the motor bogie, pantograph lowered
          cab_panto_up the same with the pantograph raised (car 6)
          multi        car 2: 2nd class, multi-purpose area and wheelchair toilet
          first_a      car 3: 1st class upstairs
          first_b      car 4: 1st class upstairs (car 3's counterpart)
          second       car 5: 2nd class
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

Real lengths (type sketch, 151.88 m over couplers): cab cars 25.74 m from the nose tip
(compressed to 25.6 m), intermediates 24.80–24.88 m (at their real length).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.ir_dosto import build_ir_car, cab_car, first_car_a, first_car_b, multi_car, second_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.8  # 2,800 mm, authored at this width (docs/SCALE.md)

CARS = {
    "cab": lambda: cab_car(),
    "cab_panto_up": lambda: cab_car(pantograph_raised=True),
    "multi": lambda: multi_car(),
    "first_a": lambda: first_car_a(),
    "first_b": lambda: first_car_b(),
    "second": lambda: second_car(),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_ir_car(spec, lights)
