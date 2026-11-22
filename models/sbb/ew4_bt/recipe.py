"""SBB Bt IC — EW IV control car (driving trailer, 1996–2004, 90 built).

Prototype: EuroCity Apm/Bpm-based body with the cab of the Re 460 "Lok 2000",
200 km/h, open 2nd-class saloon, door right behind the cab. Pushed by an Re 460.
Source: de.wikipedia "Einheitswagen (Schweiz, Normalspur)".

Push-pull: when the car is last in the train (`tail` light variant) the model is
turned round so the cab faces outward with red lamps — see parts/coach.py.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.coach import CabSpec, CoachSpec, build_coach
from puenktlich.voxel.parts.loco import LOK2000_NOSE  # the Bt has the cab of the Re 460
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

# windscreen ends below the roof crown so the top headlamp sits above it, as on the Re 460
SPEC = CoachSpec(windows=10, cab=CabSpec(nose=LOK2000_NOSE, windscreen_z=(33, 46)))


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
