"""SBB EW IV A — 1st class Einheitswagen IV (1981–1992, 220 built).

Prototype: 26.4 m, 40–43 t, 200 km/h (after modernisation), ten windows per side
between the sliding-plug doors, modern IC livery with red doors, black end bands and
the SBB yellow 1st-class stripe. Source: de.wikipedia "Einheitswagen (Schweiz, Normalspur)".
The 26.4 m body is compressed slightly to fit the 25.6 m (8/8) canvas.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.coach import CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = CoachSpec(windows=10, first_class=True)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
