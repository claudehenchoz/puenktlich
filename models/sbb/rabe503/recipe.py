"""SBB RABe 503 "Astoro" (Alstom ETR 610, New Pendolino): every car of the 7-car tilting unit.
Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab_first   car 1, cab, 1st class, powered
          first       car 2, 1st class, powered
          dining      car 3, restaurant and 1st class, pantograph
          second_pan  car 4/5, 2nd class, pantograph (car 4 raised)
          second      car 6, 2nd class, powered
          cab         car 7, cab, 2nd class, powered
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

187.4 m over couplers: end cars ≈27.6 m and intermediates ≈26.4 m (unverified), all modelled
at 25.6 m (8/8).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.tilting import TiltSpec, build_tilting_car, cab_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab_first": lambda: cab_car("etr610", first_class=True),
    "first": lambda: TiltSpec(first_class=True),
    "dining": lambda: TiltSpec(dining=True),
    "second_pan_up": lambda: TiltSpec(pantograph=True, pantograph_raised=True),
    "second_pan": lambda: TiltSpec(pantograph=True),
    "second": lambda: TiltSpec(),
    "cab": lambda: cab_car("etr610"),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_tilting_car(spec, lights)
