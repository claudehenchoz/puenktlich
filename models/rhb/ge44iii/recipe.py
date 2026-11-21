"""RhB Ge 4/4 III — metre-gauge Bo'Bo' universal electric locomotive (SLM/ABB, 1993–1999).

Prototype (de.wikipedia "RhB Ge 4/4 III"): 16.0 m over buffers, 2.80 m wide, 3.86 m high,
62 t, 2400 kW (max 3100 kW), 100 km/h, wheels 1070 mm, two single-arm pantographs,
11 kV 16.7 Hz, 12 + 1 built (641–653). Livery: RhB red with a large "RhB" logo, many
units with advertising liveries.

Metre gauge: narrower, lower body (docs/SCALE.md) and wheels at the metre-gauge positions
of the companion track GRF (running_gear.GAUGES["metre"]).
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model, m
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_band, end_span, side_band
from puenktlich.voxel.parts.lights import lamps
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie, buffers, skirt
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

LENGTH_OVER_BUFFERS_M = 16.0
BUFFER_DEPTH = 5

BODY = P.ramp(P.CC1, 0.6)
SEAM = P.ramp(P.CC1, 0.25)
LOGO = P.ramp(P.CC2, 0.85)
ROOF = P.ramp(P.GREY, 0.45)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    mdl = Model.new()
    mid_canvas = mdl.d.shape[0] / 2
    lob = m(LENGTH_OVER_BUFFERS_M)
    x_rear = mid_canvas - lob / 2 + BUFFER_DEPTH
    x_front = mid_canvas + lob / 2 - BUFFER_DEPTH

    section = CrossSection(floor=13, roof=46, half_width=18, roof_radius=6, tumblehome=1, tumble_from=24)
    nose = EndShape(rake=7, rake_from=31, rake_curve=1.2, corner_radius=5, undercut=2, undercut_height=4)
    shell = Shell(x_rear, x_front, section, front=nose)
    mid = shell.mid
    X, Y, Z = mdl.coords()

    mdl.solid(shell.mask(mdl), BODY)
    mdl.paint((section.roof - 3 <= Z) & (abs(Y - CENTRE_Y) <= 12) & (x_rear + 16 < X) & (x_front - 16 > X), ROOF)

    for front in (True, False):
        mdl.paint(end_band(mdl, shell, 29, 45, 16, front=front, depth=14), P.BLACK)
        mdl.inset(end_band(mdl, shell, 31, 43, 14, front=front, depth=14), P.GLASS)
        mdl.inset(side_band(mdl, *end_span(shell, front, 8, 16), 32, 42), P.GLASS)  # cab side window
        x0, x1 = end_span(shell, front, 18, 25)  # cab door
        door = side_band(mdl, x0, x1, 15, 43) & ~side_band(mdl, x0 + 1, x1 - 1, 16, 42)
        mdl.inset(door, SEAM)
    lamps(mdl, shell, lights, low_z=(19, 23), top_z=(45, 47), spacing=11)

    # machine-room grilles and the big RhB logo panel (CC2: white in the RhB livery)
    for c in (mid - 30, mid + 30):
        panel = side_band(mdl, c - 10, c + 10, 34, 42)
        mdl.inset(panel, P.DARK_GREY)
        mdl.paint(panel & ((X.astype(int) % 3) == 0), P.MID_GREY)
    mdl.paint(side_band(mdl, mid - 16, mid + 16, 22, 30), LOGO)

    for c in (mid - m(4.3), mid + m(4.3)):
        bogie(mdl, c, wheelbase=m(2.5), wheel_diameter=11, top=section.floor, gauge="metre")
    skirt(mdl, mid - m(4.3) + 20, mid + m(4.3) - 20, 6, section.floor, 13)
    buffers(mdl, x_front, front=True, z=section.floor, length=BUFFER_DEPTH, spacing=10)
    buffers(mdl, x_rear, front=False, z=section.floor, length=BUFFER_DEPTH, spacing=10)

    roof_z = section.roof + 1
    pantograph(mdl, mid - 30, roof_z, raised=True, facing_front=False)
    pantograph(mdl, mid + 30, roof_z, raised=False, facing_front=True)
    main_switch(mdl, mid, roof_z)
    roof_box(mdl, mid - 14, mid - 6, 7, roof_z, 2)
    roof_cable(mdl, mid - 30, mid + 30, roof_z)
    return mdl
