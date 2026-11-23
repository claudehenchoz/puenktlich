"""SBB RABe 523 (Stadler FLIRT): the 4-car FLIRT 1 regional units (523 001–073) and the
FLIRT 3 "Mouette" InterRegio units (523 501–511). Measurements, photos, livery: REFERENCE.md.

    build(lights, car=..., role=..., generation=1|3)
    car:  cab_first  end car with cab, motor bogie, pantograph, 1st class behind the cab
          cab        end car with cab, motor bogie, pantograph, 2nd class
          second     intermediate car on Jakobs bogies
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

End cars (≈19.4 m, unverified) are modelled at 19.2 m (6/8), intermediate cars (≈17.6 m)
compressed to 16.0 m (5/8), as the Giruno's.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.flirt import FlirtSpec, build_flirt_car, end_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.88  # 2,880 mm, FLIRT for SBB (later units 2,820) (docs/SCALE.md)

CARS = {
    "cab_first": lambda g, role: end_car(generation=g, first_class=(4.2, 8.2), pantograph_raised=role == "front"),
    "cab": lambda g, role: end_car(generation=g, pantograph_raised=role == "front"),
    "second": lambda g, role: FlirtSpec(generation=g),
}


def build(
    lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle", generation: int = 1
) -> Model:
    spec = CARS[car](generation, role)
    spec.mu_role = role  # type: ignore[assignment]
    return build_flirt_car(spec, lights)
