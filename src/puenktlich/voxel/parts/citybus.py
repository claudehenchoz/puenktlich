"""Modern low-floor city buses in the VBZ (Zürich) style, built from a real-metre layout.

A `CityBus` gives the real bus from its front tip backwards: the sections between the
articulation joints, with the OpenTTD length each is fitted to, the axles, the doors and the
roof equipment. `build_city_bus(bus, car)` builds one section on the road canvas
(126 x 40 x 48, 10 voxels per metre along x, 13.9 per metre across and up: docs/SCALE.md).
Each section is scaled to its fitted length on its own, so doors and axles keep their place
within it.

VBZ livery ("Züri-Linie", since 2004): white body (CC2, as on white coaches) with a blue
skirt (CC1) up to the wheel hubs, black glazing in one continuous band, a thin blue line
along the cantrail and a white roof with grey equipment. In company colours the skirt and
the line take the first colour and the body the second.

Front styles, the shape that tells the makes apart at OpenTTD's zoom levels:
    hess      upright Swisstrolley 3/4 and lighTram 3 front, black from the bumper to the roof
    lightram  the raked lighTram 10/19/25 front under a white roof peak
    man       the raked MAN Lion's City front with its long roof slope and white "V" on the side
    citaro    the rounded Mercedes-Benz Citaro front with a white mask under the windscreen
    volvo     the Volvo 7900 front with the domed roof cap above the windscreen
Trolleybuses (`poles_at`) get their two trolley poles on the last section, lowered onto
the rear hooks, as on the Hess drawings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import ROAD_CANVAS, Model
from puenktlich.voxel.parts import road as R
from puenktlich.voxel.parts.body import CrossSection, EndShape, Shell, face_mask, side_band

Z_PER_M = 13.9  # height and width scale of buses (docs/SCALE.md)

WHITE = P.BODY_CC2  # body sides (CC2: white in the VBZ livery)
BLUE = P.BODY_CC1  # skirt and cantrail line (CC1: VBZ blue)
FRAME = P.DARK  # window band, door frames, black front masks
EQUIPMENT = P.ramp(P.GREY, 0.85)  # light roof fairings (battery packs, trolley equipment, A/C)
EQUIPMENT_TOP = P.ROOF_LIGHT
POLE = P.DARK_GREY

SECTION = CrossSection(floor=4, roof=41, half_width=17, roof_radius=4, tumblehome=0.5, tumble_from=14)
SKIRT_TOP = 11  # blue up to 0.8 m
WINDOW = (14, 33)  # glazing 1.0 .. 2.4 m
CANTRAIL = 36  # blue line 2.6 m

FRONTS = {
    "hess": EndShape(rake=2, rake_from=14, rake_curve=1.2, corner_radius=3),
    "lightram": EndShape(rake=5, rake_from=12, rake_curve=1.5, corner_radius=4),
    "man": EndShape(rake=5, rake_from=14, rake_curve=1.3, corner_radius=4),
    "citaro": EndShape(rake=3, rake_from=16, rake_curve=1.4, corner_radius=4),
    "volvo": EndShape(rake=3, rake_from=12, rake_curve=1.2, corner_radius=5),
}
REAR = EndShape(rake=1, rake_from=32, rake_curve=1.0, corner_radius=4)


@dataclass(frozen=True)
class Car:
    """One section of the bus: real metres a..b behind the front tip, fitted to `fitted_m`."""

    a: float
    b: float
    fitted_m: float


@dataclass
class CityBus:
    style: str  # key of FRONTS
    cars: list[Car]
    axles: list[tuple[float, bool]]  # (metres behind the front, twin tyres)
    doors: list[tuple[float, float]]  # leaves from..to; wider than 1 m = double door
    roof: list[tuple[float, float, int]] = field(default_factory=list)  # equipment from..to, height (voxels)
    height_m: float = 3.3  # over the roof equipment
    poles_at: float | None = None  # trolleybus: base of the trolley poles (metres behind the front)
    opp_charge: tuple[float, float] | None = None  # OppCharge contact rails on the roof
    rear_window: bool = True  # glazed rear (no engine tower behind it)


@dataclass
class _Frame:
    """Real metres -> voxels of one car."""

    car: Car
    x_rear: float
    x_front: float

    def x(self, p: float) -> float:
        k = self.car.fitted_m / (self.car.b - self.car.a)
        return self.x_front - (p - self.car.a) * k * 10

    def has(self, p0: float, p1: float | None = None) -> bool:
        p1 = p0 if p1 is None else p1
        return p1 >= self.car.a and p0 <= self.car.b


def build_city_bus(bus: CityBus, car: int = 0) -> Model:
    mdl = Model.new(ROAD_CANVAS)
    c = bus.cars[car]
    first, last = car == 0, car == len(bus.cars) - 1
    sx = mdl.d.shape[0]
    lob = c.fitted_m * 10
    x_rear, x_front = sx / 2 - lob / 2, sx / 2 + lob / 2 - 1
    f = _Frame(c, x_rear, x_front)
    front, rear = FRONTS[bus.style] if first else R.JOINT, REAR if last else R.JOINT
    shell = Shell(x_rear, x_front, SECTION, front=front, rear=rear)
    body = R.BusBody(shell, window_z=WINDOW)
    cs = SECTION
    X, _, Z = mdl.coords()

    mdl.solid(shell.mask(mdl), WHITE)
    mdl.paint(SKIRT_TOP >= Z, BLUE)
    mdl.paint(side_band(mdl, x_rear, x_front + 1, CANTRAIL, CANTRAIL + 1), BLUE)

    # continuous window band, pillars about every 1.4 m of the real bus
    w0, w1 = WINDOW
    b0 = x_rear + (4 if last else 1)
    b1 = x_front - (7 if first else 1)
    band = side_band(mdl, b0, b1, w0, w1)
    mdl.paint(band, FRAME)
    pitch = 14 * c.fitted_m / (c.b - c.a)
    mdl.inset(band & (((X - b0) % pitch) > 1.5), P.GLASS)

    for p0, p1 in bus.doors:
        if f.has(p0, p1):
            _door(mdl, f.x(p1), f.x(p0), double=p1 - p0 > 1.0)
    for p, twin in bus.axles:
        if f.has(p):
            R.wheel(mdl, f.x(p), twin=twin)

    top = min(ROAD_CANVAS[2] - 2, round(bus.height_m * Z_PER_M))
    for p0, p1, h in bus.roof:
        if f.has(p0, p1):
            x0, x1 = max(f.x(p1), x_rear + 2), min(f.x(p0), x_front - 2)
            z1 = min(top, cs.roof + h)
            mdl.solid(mdl.centred_box(x0, x1, cs.half_width - 4, cs.roof - 1, z1), EQUIPMENT)
            mdl.paint(mdl.centred_box(x0 + 1, x1 - 1, cs.half_width - 5, z1 - 1, z1), EQUIPMENT_TOP)
    if bus.opp_charge and f.has(*bus.opp_charge):
        x0, x1 = f.x(bus.opp_charge[1]), f.x(bus.opp_charge[0])
        for s in (-1, 1):
            rail = mdl.box(x0, x1, mdl.cy + s * 5 - 0.5, mdl.cy + s * 5 + 0.5, cs.roof, cs.roof + 3)
            mdl.solid(rail, POLE)

    if first:
        _front(mdl, bus, body)
    else:
        R.bellows(mdl, body, front=True)
    if last:
        _rear(mdl, bus, body)
        if bus.poles_at is not None:
            _poles(mdl, f.x(bus.poles_at), x_rear, top)
    else:
        R.bellows(mdl, body, front=False)
    return mdl


def _door(mdl: Model, x0: float, x1: float, double: bool) -> None:
    """Glazed door on the kerb side from the floor to the top of the window band."""
    top = WINDOW[1]
    mdl.paint(R.side_mask(mdl, x0, x1, SECTION.floor, top + 1, R.DOOR_SIDE), FRAME)
    mdl.inset(R.side_mask(mdl, x0 + 1, x1 - 1, SECTION.floor + 2, top - 1, R.DOOR_SIDE), P.GLASS)
    if double:
        mid = (x0 + x1) / 2
        mdl.paint(R.side_mask(mdl, mid - 0.5, mid + 0.5, SECTION.floor + 1, top, R.DOOR_SIDE), FRAME)


def _front(mdl: Model, bus: CityBus, body: R.BusBody) -> None:
    shell, cs = body.shell, SECTION
    X, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    face = face_mask(mdl, front=True, depth=2)
    style = bus.style
    if style == "volvo":  # domed roof cap above the windscreen
        cap = mdl.centred_box(shell.x_front - 16, shell.x_front - 3, cs.half_width - 2, cs.roof - 2, cs.roof + 2)
        mdl.solid(cap, WHITE)
    if style == "lightram":  # white roof peak over the raked windscreen
        peak = mdl.centred_box(shell.x_front - 6, shell.x_front - 1, cs.half_width - 1, cs.roof - 4, cs.roof)
        mdl.solid(peak & (dy <= cs.half_width - 1), WHITE)
        face = face_mask(mdl, front=True, depth=2)
    # windscreen up to the destination display, which sits under the roof edge
    screen_top = {"hess": cs.roof - 2, "lightram": cs.roof - 5, "man": cs.roof - 3}.get(style, cs.roof - 3)
    screen_bottom = {"hess": 12, "citaro": 17, "volvo": 16}.get(style, 13)
    mask_bottom = 12 if style in ("hess", "lightram", "man") else screen_bottom
    mdl.paint(face & (mask_bottom <= Z) & (screen_top >= Z) & (dy <= cs.half_width - 1), FRAME)
    glass = face & (screen_bottom + 1 <= Z) & (screen_top - 4 >= Z) & (dy <= cs.half_width - 2)
    mdl.inset(glass, P.GLASS)
    disp = face & (screen_top - 3 <= Z) & (screen_top - 2 >= Z) & (dy <= 8)
    mdl.paint(disp, P.YELLOW)
    if style == "volvo":  # black grille band between the lamps
        mdl.paint(face & (Z >= 12) & (Z <= 14) & (dy <= cs.half_width - 5), FRAME)
    # driver's side window behind the windscreen (left side, low y)
    drv = R.side_mask(mdl, shell.x_front - 9, shell.x_front - 3, WINDOW[0], WINDOW[1], -R.DOOR_SIDE)
    mdl.paint(drv & (dy >= cs.half_width - 1.5), FRAME)
    if style == "man":  # the white "V" over the glazing behind the front door
        k = (WINDOW[1] - WINDOW[0]) / 10
        v = side_band(mdl, shell.x_front - 30, shell.x_front - 8, WINDOW[0], WINDOW[1] + 1)
        v &= abs((shell.x_front - 18 - X) - (WINDOW[1] - Z) / k) <= 1.2
        mdl.paint(v, WHITE)
    _lamps(mdl, front=True)


def _rear(mdl: Model, bus: CityBus, body: R.BusBody) -> None:
    cs = SECTION
    _, _, Z = mdl.coords()
    face = face_mask(mdl, front=False, depth=2)
    _, Y, _ = mdl.coords()
    dy = abs(Y - mdl.cy)
    if bus.rear_window:
        mdl.paint(face & (WINDOW[0] + 4 <= Z) & (cs.roof - 4 >= Z) & (dy <= cs.half_width - 3), FRAME)
        mdl.inset(face & (WINDOW[0] + 6 <= Z) & (cs.roof - 6 >= Z) & (dy <= cs.half_width - 5), P.GLASS)
    else:  # engine compartment: grille in the white rear
        mdl.inset(face & (Z >= 13) & (Z <= 19) & (dy <= cs.half_width - 6), P.DARK_GREY)
        mdl.paint(face & (Z >= 24) & (cs.roof - 5 >= Z) & (dy <= cs.half_width - 4), FRAME)
    _lamps(mdl, front=False)


def _lamps(mdl: Model, front: bool) -> None:
    """Head lamps (white, in the blue apron) or tail lamps (red, up the rear corners), on the
    end face only."""
    _, Y, Z = mdl.coords()
    dy = abs(Y - mdl.cy)
    face = face_mask(mdl, front=front, depth=1)
    hw = SECTION.half_width
    if front:
        mdl.paint(face & (Z >= 7) & (Z <= 9) & (dy >= hw - 5) & (dy <= hw - 1), R.LAMP_WHITE)
    else:
        mdl.paint(face & (Z >= 9) & (Z <= 20) & (dy >= hw - 3), R.LAMP_RED)


def _poles(mdl: Model, x_base: float, x_rear: float, top: int) -> None:
    """Trolley poles lowered onto the rear hooks: a base on the roof, from which the two poles
    fall gently back to the hooks at the rear end (Hess drawing 1-2441)."""
    roof = SECTION.roof
    z_base = min(top, roof + 5)
    mdl.solid(mdl.centred_box(x_base - 6, x_base, 6, roof - 1, roof + 2), EQUIPMENT)
    mdl.solid(mdl.centred_box(x_base - 4, x_base - 1, 4.5, roof + 2, z_base - 1), POLE)
    X, _, Z = mdl.coords()
    for s in (-1, 1):
        y0 = mdl.cy + s * 3.5
        pole = mdl.box(x_rear + 1, x_base - 2, y0 - 0.5, y0 + 0.5, roof + 1, z_base + 1)
        zp = z_base - (x_base - 2 - X) / max(1.0, x_base - x_rear - 3) * (z_base - roof - 2)
        mdl.solid(pole & (np.abs(Z - zp) <= 0.6), POLE)
        mdl.solid(mdl.box(x_rear + 1, x_rear + 2, y0 - 0.5, y0 + 0.5, roof - 1, roof + 2), POLE)  # hook
