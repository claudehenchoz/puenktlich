"""SBB FV-Dosto (RABe 502 / RABDe 502, Bombardier TWINDEXX Swiss Express): every car of the IR100
and IC200 sets, in true proportions. Measurements (3D model + Bombardier factsheets), livery and
car layouts: REFERENCE.md in this directory.

    build(lights, car=..., role=...)
    car:  cab_first      1st-class end car (IR100), passenger door behind the cab, pantograph
          cab_first_lug  1st-class end car (IC200) with the luggage room's loading door
          cab            2nd-class end car, pantograph
          first          1st-class intermediate car (yellow door headers)
          second         2nd-class intermediate car
          dining         IC200 restaurant car (restaurant upstairs, red band)
    role: front | middle | rear (multiple-unit lamps; a rear cab car is turned round)

Real lengths in their 8/8 slots: end cars 25.32 m, intermediates 24.28 m (bellows out to the
slot ends). The 2.80 m body is authored at its real width (BODY_WIDTH_M), so rendering keeps it.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.fv_dosto import FvSpec, build_fv_car, end_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.8  # 2,800 mm, authored at this width (docs/SCALE.md)

CARS = {
    "cab_first": lambda: end_car(first_class=True, pantograph=True),
    "cab_first_lug": lambda: end_car(first_class=True, pantograph=True, luggage_door=True),
    "cab": lambda: end_car(pantograph=True),
    "first": lambda: FvSpec(first_class=True),
    "second": lambda: FvSpec(),
    "dining": lambda: FvSpec(dining=True),
}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "second", role: str = "middle") -> Model:
    spec = CARS[car]()
    spec.mu_role = role  # type: ignore[assignment]
    return build_fv_car(spec, lights)
