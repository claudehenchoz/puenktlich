"""RhB EW IV — Einheitswagen IV of the Rhaetian Railway (metre gauge, 1980s–90s).

Approximate prototype data (from memory, to be cross-checked against de.wikipedia
"Einheitswagen IV (RhB)"): about 18.5 m over couplers, about 17 t, 90 km/h, plug doors at
both ends, all-red body with a grey roof. The 1st-class car (A) carries a yellow band at the
roof edge. One recipe builds both classes via `params: {cls: A|B}`.

Metre gauge: narrower, lower body (docs/SCALE.md) and metre-gauge wheel positions, like
the Ge 4/4 III.
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape
from puenktlich.voxel.parts.coach import CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.65  # 2,650 mm (docs/SCALE.md)
Z_PER_M = 13.3  # height scale of this model: roof z 46 = 3.45 m

SECTION = CrossSection(floor=13, roof=45, half_width=17.5, roof_radius=7, tumblehome=1, tumble_from=23)


def spec(cls: str) -> CoachSpec:
    return CoachSpec(
        windows=8 if cls == "A" else 9,
        first_class=cls == "A",
        first_class_z=(42, 43),
        section=SECTION,
        end=EndShape(rake=0, corner_radius=2),
        door_from_end=(14, 24),
        window_z=(27, 40),
        pillar=2.5,
        length_m=18.5,
        gauge="metre",
        body_colour=P.BODY_CC1,
        roof_line=False,
        bogie_centres_m=6.3,
        wheel_diameter=8,
        wheelbase=18,
        buffer_spacing=10,
        gangway_half_width=8,
        roof_half_width=13,
        skirt_half_width=13,
    )


def build(cls: str = "B", lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(spec(cls), lights)
