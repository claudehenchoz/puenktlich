"""SBB Bt IC — EW IV control car (driving trailer, 1996–2004, 90 built).

Prototype: EuroCity Apm/Bpm-based body with the cab of the Re 460 "Lok 2000",
200 km/h, open 2nd-class saloon, door right behind the cab. Pushed by an Re 460.
Source: de.wikipedia "Einheitswagen (Schweiz, Normalspur)".

Push-pull: when the car is last in the train (`tail` light variant) the model is
turned round so the cab faces outward with red lamps — see parts/coach.py.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import EndShape
from puenktlich.voxel.parts.coach import CabSpec, CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

# same nose as models/sbb/re460/recipe.py
RE460_NOSE = EndShape(rake=19, rake_from=29, rake_curve=1.35, corner_radius=10, undercut=3, undercut_height=5)

SPEC = CoachSpec(windows=10, cab=CabSpec(nose=RE460_NOSE))


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
