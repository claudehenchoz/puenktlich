"""SBB FV-Dosto (RABe 502 / RABDe 502, Twindexx Swiss Express): every car of the IR 100 and
IC 200 sets. Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab_first  end car with cab, 1st class (yellow door strips), pantograph
          cab        end car with cab, 2nd class, pantograph
          first      1st-class intermediate car (wider upper windows)
          second     2nd-class intermediate car
          dining     dining car (IC 200): red band around the upper windows
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

End cars (26.3 m) are compressed to 25.6 m (8/8), and intermediates (≈24.7 m) stretched to it.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.dosto import DostoSpec, build_dosto_car, end_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

CARS = {
    "cab_first": lambda: end_car(first_class=True, pantograph=True, lower_windows=3, lower_width=1.8),
    "cab": lambda: end_car(pantograph=True),
    "first": lambda: DostoSpec(first_class=True, lower_windows=5, lower_width=1.8, upper_pitch=2.4, upper_width=1.8),
    "second": lambda: DostoSpec(),
    "dining": lambda: DostoSpec(dining=True, lower_windows=4, lower_width=1.8, upper_pitch=2.2, upper_width=1.7),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_dosto_car(spec, lights)
