"""SBB RABe 514 "DTZ" (Siemens Desiro Double Deck), S-Bahn Zürich: every car of the 4-car unit.
Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab        Bt, end car with cab, motor bogies and pantograph, 2nd class
          cab_first  At, the same with 1st class (yellow panels over the doors)
          second     B, 2nd-class intermediate car
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

≈100 m over couplers: 4 × 25.0 m (unverified split), modelled at 25.0 m (8/8).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.kiss import build_kiss_car, dtz_cab_car, dtz_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab": lambda role: dtz_cab_car(pantograph_raised=role == "rear"),
    "cab_first": lambda role: dtz_cab_car(first_class=True, pantograph_raised=role == "rear"),
    "second": lambda role: dtz_car(),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car](role)
    spec.mu_role = role  # type: ignore[assignment]
    return build_kiss_car(spec, lights)
