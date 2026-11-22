"""SBB RABe 512 IR-Dosto (Stadler KISS, second generation): every car of the 6-car unit.
Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab         end car with cab and motor bogie (Bt)
          first       intermediate car with the 1st-class section (yellow lines over the doors)
          second      2nd-class intermediate car
          panto       2nd-class intermediate car, pantograph in a roof well at its front
          panto_rear  the same, turned round: pantograph at its rear, lowered
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

151.88 m over couplers = 6 × ≈25.3 m, each modelled at 25.3 m (8/8).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.kiss import build_kiss_car, kiss2_cab_car, kiss2_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab": lambda: kiss2_cab_car(),
    "first": lambda: kiss2_car(first_class=True),
    "second": lambda: kiss2_car(),
    "panto": lambda: kiss2_car(pantograph=True),
    "panto_rear": lambda: kiss2_car(pantograph=True, pantograph_raised=False, turned=True),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_kiss_car(spec, lights)
