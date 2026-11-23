"""PostAuto Mercedes-Benz Citaro — low-floor city/regional bus (solo 12 m and articulated G).

Prototype data: Citaro O 530 solo 12.0 m, 2.55 m wide, 3.095 m high (3.12–3.13 m with air
conditioning; Mercedes-Benz "facts citaro" data sheet), three double doors; Citaro G O 530 G 18.1 m with four doors.
PostAuto livery: yellow body (CC1), here with a thin red line (CC2) below the windows.

One recipe builds every car via `params: {car: solo|front|rear}` on the road canvas:
    solo   11.2 m, doors front / middle / rear, two axles
    front   8.4 m of the Citaro G: front door, middle door, two axles, joint at the rear
    rear    5.6 m of the Citaro G: joint at the front, a door behind it, driven rear axle
Models are fitted to their OpenTTD road lengths (1/8 = 1.4 m, docs/SCALE.md): the solo bus
from 12 m to 8/8, the Citaro G from 18.1 m to 6 + 4.
"""

from puenktlich.voxel.model import ROAD_CANVAS, Model
from puenktlich.voxel.parts import road as R

BODY_WIDTH_M = 2.55  # 2,550 mm (Mercedes-Benz data sheet, docs/SCALE.md)
Z_PER_M = 13.9  # height 3,095 mm = roof equipment top z 43


def build(car: str = "solo") -> Model:
    mdl = Model.new(ROAD_CANVAS)
    if car == "solo":
        body = R.bus_body(mdl, 11.2, front=R.FRONT, rear=R.REAR)
        s = body.shell
        R.windscreen(mdl, body)
        R.lamps(mdl, body, front=True)
        R.rear_end(mdl, body)
        R.door(mdl, body, s.x_front - 25)
        R.door(mdl, body, s.mid - 2)
        R.door(mdl, body, s.x_rear + 18)
        R.wheel(mdl, s.x_front - 27)
        R.wheel(mdl, s.x_rear + 28, twin=True)
    elif car == "front":
        body = R.bus_body(mdl, 8.4, front=R.FRONT, rear=None)
        s = body.shell
        R.windscreen(mdl, body)
        R.lamps(mdl, body, front=True)
        R.door(mdl, body, s.x_front - 25)
        R.door(mdl, body, s.mid - 10)
        R.wheel(mdl, s.x_front - 27)
        R.wheel(mdl, s.x_rear + 12, twin=True)
        R.bellows(mdl, body, front=False)
    elif car == "rear":
        body = R.bus_body(mdl, 5.6, front=None, rear=R.REAR)
        s = body.shell
        R.rear_end(mdl, body)
        R.door(mdl, body, s.x_front - 16)
        R.wheel(mdl, s.x_rear + 18, twin=True)
        R.bellows(mdl, body, front=True)
    else:
        raise ValueError(f"unknown car {car!r}")
    return mdl
