"""SBB EW IV B — 2nd class Einheitswagen IV (1983–1990, 293 built).

Prototype: 26.4 m, 40–43 t, 200 km/h, eleven windows per side between the doors.
Source: de.wikipedia "Einheitswagen (Schweiz, Normalspur)". Compressed to 8/8.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.coach import CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = CoachSpec(windows=11)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
