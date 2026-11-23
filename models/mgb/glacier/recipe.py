"""Glacier Express panorama coaches (Stadler, 2006–2009, RhB and MGB). Measurements, photos
and livery: REFERENCE.md in this directory.

    build(lights, kind=...)
    kind: first       Ap, 1st class (36 seats, 2+1)
          second      Bp, 2nd class (48 seats, 2+2)
          bar         WRp, kitchen and panorama bar car (red all over)
          excellence  Aps Excellence Class (converted 2019, gold stripes, 20 seats)

18.5 m over buffers -> OpenTTD length 6 (19.2 m), modelled at full length.
"""

from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.panorama import PanoramaSpec, build_panorama_car
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

BODY_WIDTH_M = 2.68  # 2,680 mm (docs/SCALE.md)
Z_PER_M = 12.5  # height scale of this model (REFERENCE.md)


def build(lights: Lights = LIGHT_VARIANTS["solo"], kind: str = "second") -> Model:
    return build_panorama_car(PanoramaSpec(kind=kind), lights)  # type: ignore[arg-type]
