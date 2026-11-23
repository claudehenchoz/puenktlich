"""SBB IC2000 double-deck InterCity coaches (FIAT-SIG/Schindler, 1997–2004) and the Bt control
car. Measurements, photos and livery: REFERENCE.md in this directory.

    build(lights, car=...)
    car:  a    A, 1st class (yellow line over the mid band)
          ad   AD, 1st class with luggage compartment
          b    B, 2nd class
          bt   Bt, 2nd-class control car with the Re 460-style cab

26.8 m over buffers, compressed to 25.6 m (8/8). Stand-alone coaches: tail lamps when last; the
Bt turns its cab outward when it is the last vehicle (as the EW IV Bt).
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.kiss import build_kiss_car, ic2000_bt, ic2000_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.825  # 2,825 mm (fr.wikipedia) (docs/SCALE.md)

CARS = {
    "a": lambda: ic2000_coach(first_class=True),
    "ad": lambda: ic2000_coach(first_class=True, lower_windows=4),
    "b": lambda: ic2000_coach(),
    "bt": lambda: ic2000_bt(),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "b") -> Model:
    return build_kiss_car(CARS[car](), lights)
