"""SBB RABDe 500 ICN (InterCity-Neigezug): every car of the 7-car tilting unit.
Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab          Bt, end car with cab, 2nd class, powered
          second       B, 2nd class, powered
          dining_first WRA, restaurant and 1st class, pantograph (transformer car)
          first        A, 1st class
          first_pan    AD, 1st class and luggage, pantograph (transformer car)
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

188.8 m over buffers: end cars ≈28.4 m and intermediates ≈26.4 m (unverified), all modelled
at 25.6 m (8/8). Formation Bt B WRA A AD B Bt (data.sbb.ch via en.wikipedia).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.tilting import TiltSpec, build_tilting_car, cab_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab": lambda: cab_car("icn"),
    "second": lambda: TiltSpec(style="icn"),
    "dining_first": lambda: TiltSpec(style="icn", dining=True, first_class=True, pantograph=True),
    "first": lambda: TiltSpec(style="icn", first_class=True),
    "first_pan": lambda: TiltSpec(style="icn", first_class=True, pantograph=True, pantograph_raised=True),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_tilting_car(spec, lights)
