"""SBB RABe 501 "Giruno" (Stadler SMILE, EC250): every car of the 11-car unit.
Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab_first   L  At2, end car with cab, 1st class
          first       K/J A3/A4, 1st class
          first_2d    H  A5, 1st class, two doors, pantograph
          dining      G  WR6, restaurant (red band)
          second_2d   F  B7, 2nd class, two doors, pantograph
          second      E/C B8/B10, 2nd class
          second_pan  D/B B9/B11, 2nd class, pantograph (B: raised)
          cab         A  Bt1, end car with cab, 2nd class
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

End cars (22.25 m) are modelled at 22.4 m (7/8), intermediate cars (17.5 m) compressed to
16.0 m (5/8). Door positions are real metres from the car end facing car L.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.smile import SmileSpec, build_smile_car, end_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab_first": lambda: end_car(first_class=True),
    "first": lambda: SmileSpec(first_class=True, doors=(12.1,)),
    "first_2d": lambda: SmileSpec(first_class=True, doors=(6.6, 11.0), pantograph=True),
    "dining": lambda: SmileSpec(dining=True, doors=(5.6,), door_width=1.0, window_pitch=1.6, window_width=1.0),
    "second_2d": lambda: SmileSpec(doors=(7.9, 12.3), pantograph=True),
    "second": lambda: SmileSpec(doors=(8.0,)),
    "second_pan": lambda: SmileSpec(doors=(8.0,), pantograph=True),
    "second_pan_up": lambda: SmileSpec(doors=(8.0,), pantograph=True, pantograph_raised=True),
    "cab": lambda: end_car(),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_smile_car(spec, lights)
