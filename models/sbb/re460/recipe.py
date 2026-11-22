"""SBB Re 460 ("Lok 2000") — parametric voxel recipe.

Prototype: 18.5 m over buffers, Bo'Bo', 4.3 m high, wheel Ø 1.1 m.
Canvas: 256 x 42 x 72, high x = cab 1 (front). See docs/SCALE.md.

Colour plan (docs/STYLE.md):
    body            CC1 (company colour 1)  -> SBB red in the "SBB" livery
    logo / stripe   CC2                     -> white in the "SBB" livery
    roof, bogies    greys (fixed)
    glass           mauve window ramp
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection
from puenktlich.voxel.parts.loco import LOK2000_NOSE, LocoSpec, Louvres, Panel, Windscreen, build_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = LocoSpec(
    length_m=18.5,
    section=CrossSection(floor=15, roof=51, half_width=19.5, roof_radius=7, tumblehome=1.5, tumble_from=26),
    nose=LOK2000_NOSE,
    windscreen=Windscreen(frame_z=(31, 50), frame_half_width=18, glass_z=(33, 48), glass_half_width=16, depth=26),
    cab_window=(14, 24),
    cab_window_z=(35, 45),
    door=(26, 34),
    door_z=(17, 47),
    door_glass_z=(38, 44),
    # machine-room louvre panels: four groups high on the side, smooth body between
    louvres=Louvres(offsets=(-40, -16, 16, 40), half_length=9, z=(38, 46)),
    # "SBB CFF FFS" logo panel (CC2) on the side, centre
    panels=(Panel(z=(25, 30), colour=P.STRIPE_CC2, half_length=14),),
    bogie_centres_m=5.5,
    wheelbase_m=2.8,
    pantograph_offset=38,
    roof_boxes=((-18, -8, 8), (8, 18, 8)),
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_loco(SPEC, lights)
