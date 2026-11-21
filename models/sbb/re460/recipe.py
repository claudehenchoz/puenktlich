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
from puenktlich.voxel.model import CENTRE_Y, Model, m
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, end_band, end_span, side_band
from puenktlich.voxel.parts.roof import main_switch, pantograph, roof_box, roof_cable
from puenktlich.voxel.parts.running_gear import bogie, buffers, skirt

LENGTH_OVER_BUFFERS_M = 18.5
BUFFER_DEPTH = 6

BODY = P.ramp(P.CC1, 0.6)
BODY_SEAM = P.ramp(P.CC1, 0.25)
ROOF = P.ramp(P.GREY, 0.45)


def build() -> Model:
    mdl = Model.new()
    canvas_mid = mdl.d.shape[0] / 2
    lob = m(LENGTH_OVER_BUFFERS_M)
    x_rear = canvas_mid - lob / 2 + BUFFER_DEPTH
    x_front = canvas_mid + lob / 2 - BUFFER_DEPTH

    section = CrossSection(floor=15, roof=51, half_width=19.5, roof_radius=7, tumblehome=1.5, tumble_from=26)
    nose = EndShape(rake=19, rake_from=29, rake_curve=1.35, corner_radius=10, undercut=3, undercut_height=5)
    shell = Shell(x_rear, x_front, section, front=nose)
    mid = shell.mid

    # --- body ---------------------------------------------------------------
    mdl.solid(shell.mask(mdl), BODY)

    # roof: grey walkway area between the pantographs
    X, Y, Z = mdl.coords()
    roof_area = (section.roof - 3 <= Z) & (abs(Y - CENTRE_Y) <= 13) & (x_rear + 22 < X) & (x_front - 22 > X)
    mdl.paint(roof_area, ROOF)

    # windscreens (both ends): black frame, then glass
    for front in (True, False):
        mdl.paint(end_band(mdl, shell, 31, 50, 18, front=front, depth=26), P.BLACK)
        mdl.inset(end_band(mdl, shell, 33, 48, 16, front=front, depth=26), P.GLASS)
        # headlights: two low, one high
        for dy in (-12, 12):
            lamp = end_band(mdl, shell, 21, 24, 2, front=front, depth=8)
            lamp = lamp & (abs(Y - (CENTRE_Y + dy)) <= 1.5)
            mdl.paint(lamp, P.LAMP)
        mdl.paint(end_band(mdl, shell, 49, 51, 1.5, front=front, depth=26), P.LAMP)

    # cab side windows and doors, both ends
    for front in (True, False):
        mdl.inset(side_band(mdl, *end_span(shell, front, 14, 24), 35, 45), P.GLASS)
        # door outline
        x0, x1 = end_span(shell, front, 26, 34)
        door = side_band(mdl, x0, x1, 17, 47) & ~side_band(mdl, x0 + 1, x1 - 1, 18, 46)
        mdl.inset(door, BODY_SEAM)
        mdl.inset(side_band(mdl, x0 + 2, x1 - 2, 38, 44), P.GLASS)

    # machine-room louvre panels: four groups high on the side, smooth body between
    for c in (mid - 40, mid - 16, mid + 16, mid + 40):
        panel = side_band(mdl, c - 9, c + 9, 38, 46)
        mdl.inset(panel, P.DARK_GREY)
        mdl.paint(panel & ((X.astype(int) % 3) == 0), P.MID_GREY)

    # "SBB CFF FFS" logo panel (CC2) on the side, centre
    mdl.paint(side_band(mdl, mid - 14, mid + 14, 25, 30), P.CC2_MID)

    # --- running gear ---------------------------------------------------------
    bogie_offset = m(5.5)
    for c in (mid - bogie_offset, mid + bogie_offset):
        bogie(mdl, c, wheelbase=m(2.8), wheel_diameter=11, top=section.floor)
    skirt(mdl, mid - bogie_offset + 22, mid + bogie_offset - 22, 6, section.floor, 15)
    buffers(mdl, x_front, front=True, z=section.floor, length=BUFFER_DEPTH)
    buffers(mdl, x_rear, front=False, z=section.floor, length=BUFFER_DEPTH)

    # --- roof equipment -------------------------------------------------------
    roof_z = section.roof + 1
    pantograph(mdl, mid - 38, roof_z, raised=True, facing_front=False)
    pantograph(mdl, mid + 38, roof_z, raised=False, facing_front=True)
    main_switch(mdl, mid, roof_z)
    roof_box(mdl, mid - 18, mid - 8, 8, roof_z, 2)
    roof_box(mdl, mid + 8, mid + 18, 8, roof_z, 2)
    roof_cable(mdl, mid - 38, mid + 38, roof_z)
    return mdl
