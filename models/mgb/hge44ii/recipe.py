"""MGB HGe 4/4 II — metre-gauge Bo'Bo' rack and adhesion electric locomotive (SLM/BBC, 1985–1990).

Approximate prototype data (from memory, to be cross-checked against de.wikipedia
"HGe 4/4 II"): about 14.8 m over buffers, 64 t, 1932 kW, 90 km/h on adhesion and about
35–40 km/h on the Abt rack, 11 kV 16.7 Hz. Built for the Furka-Oberalp (now MGB), the BVZ
and the SBB Brünig line (now zb). Boxy body with flat, slightly raked cab fronts, two
single-arm pantographs, and a rack drive in each bogie.

The `rack_drive` under each bogie is the visible difference to an adhesion loco. In game,
rack track (NRA*) can only be entered by trains with a rack engine (data/tracks.yaml).
"""

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model, m
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_band, end_span, side_band
from puenktlich.voxel.parts.lights import lamps
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie, buffers, rack_drive, skirt
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

LENGTH_OVER_BUFFERS_M = 14.8
BUFFER_DEPTH = 5
BOGIE_CENTRES_M = 3.7  # each side of the middle
WHEELBASE = m(2.5)

BODY = P.ramp(P.CC1, 0.6)
SEAM = P.ramp(P.CC1, 0.25)
BAND = P.ramp(P.CC2, 0.85)
ROOF = P.ramp(P.GREY, 0.45)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    mdl = Model.new()
    mid_canvas = mdl.d.shape[0] / 2
    lob = m(LENGTH_OVER_BUFFERS_M)
    x_rear = mid_canvas - lob / 2 + BUFFER_DEPTH
    x_front = mid_canvas + lob / 2 - BUFFER_DEPTH

    section = CrossSection(floor=14, roof=46, half_width=18, roof_radius=4, tumblehome=0.5, tumble_from=26)
    nose = EndShape(rake=4, rake_from=30, rake_curve=1.0, corner_radius=3, undercut=2, undercut_height=4)
    shell = Shell(x_rear, x_front, section, front=nose)
    mid = shell.mid
    X, Y, Z = mdl.coords()

    mdl.solid(shell.mask(mdl), BODY)
    mdl.paint((section.roof - 2 <= Z) & (abs(Y - CENTRE_Y) <= 13) & (x_rear + 12 < X) & (x_front - 12 > X), ROOF)
    # white band along the sides at waist height (CC2: white in the MGB livery)
    mdl.paint(side_band(mdl, x_rear + 2, x_front - 1, 25, 27), BAND)

    for front in (True, False):
        # two-pane windscreen in a black frame, centre pillar
        mdl.paint(end_band(mdl, shell, 30, 44, 16, front=front, depth=12), P.BLACK)
        mdl.inset(end_band(mdl, shell, 32, 42, 14.5, front=front, depth=12), P.GLASS)
        mdl.paint(end_band(mdl, shell, 32, 42, 0.8, front=front, depth=12), P.BLACK)
        mdl.inset(side_band(mdl, *end_span(shell, front, 6, 13), 32, 42), P.GLASS)  # cab side window
        x0, x1 = end_span(shell, front, 14, 21)  # cab door
        door = side_band(mdl, x0, x1, 16, 43) & ~side_band(mdl, x0 + 1, x1 - 1, 17, 42)
        mdl.inset(door, SEAM)
    lamps(mdl, shell, lights, low_z=(19, 23), top_z=(44, 46), spacing=11)

    # machine room: a row of louvred grilles and two small windows per side
    for c in (mid - 26, mid, mid + 26):
        panel = side_band(mdl, c - 9, c + 9, 31, 41)
        mdl.inset(panel, P.DARK_GREY)
        mdl.paint(panel & ((Z.astype(int) % 2) == 0), P.MID_GREY)
    for c in (mid - 13, mid + 13):
        mdl.inset(side_band(mdl, c - 2, c + 2, 33, 39), P.GLASS)

    for c in (mid - m(BOGIE_CENTRES_M), mid + m(BOGIE_CENTRES_M)):
        bogie(mdl, c, wheelbase=WHEELBASE, wheel_diameter=10, top=section.floor, gauge="metre")
        rack_drive(mdl, c, wheelbase=WHEELBASE)
    skirt(mdl, mid - m(BOGIE_CENTRES_M) + 18, mid + m(BOGIE_CENTRES_M) - 18, 6, section.floor, 13)
    buffers(mdl, x_front, front=True, z=section.floor, length=BUFFER_DEPTH, spacing=10)
    buffers(mdl, x_rear, front=False, z=section.floor, length=BUFFER_DEPTH, spacing=10)

    roof_z = section.roof + 1
    pantograph(mdl, mid - 24, roof_z, raised=True, facing_front=False)
    pantograph(mdl, mid + 24, roof_z, raised=False, facing_front=True)
    main_switch(mdl, mid, roof_z)
    roof_box(mdl, mid - 12, mid - 5, 7, roof_z, 2)
    roof_cable(mdl, mid - 24, mid + 24, roof_z)
    return mdl
