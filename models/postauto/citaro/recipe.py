"""PostAuto Mercedes-Benz Citaro — low-floor city/regional bus (solo 12 m and articulated G).

Approximate prototype data (from memory, to be cross-checked): Citaro O 530 solo 12.0 m,
2.55 m wide, about 3.1 m high, three double doors; Citaro G O 530 G 18.1 m with four doors.
PostAuto livery: yellow body (CC1), here with a thin red line (CC2) below the windows.

One recipe builds every car via `params: {car: solo|front|rear}` on the road canvas:
    solo   12.0 m, doors front / middle / rear, two axles
    front   9.5 m of the Citaro G: front door, middle door, two axles, joint at the rear
    rear    6.5 m of the Citaro G: joint at the front, a door behind it, driven rear axle
The Citaro G is compressed from 18.1 m to 16 m so it fits OpenTTD road lengths 6 + 4.
"""

from puenktlich.voxel.model import ROAD_CANVAS, Model
from puenktlich.voxel.parts import road as R


def build(car: str = "solo") -> Model:
    mdl = Model.new(ROAD_CANVAS)
    if car == "solo":
        body = R.bus_body(mdl, 12.0, front=R.FRONT, rear=R.REAR)
        s = body.shell
        R.windscreen(mdl, body)
        R.lamps(mdl, body, front=True)
        R.rear_end(mdl, body)
        R.door(mdl, body, s.x_front - 25)
        R.door(mdl, body, s.mid - 2)
        R.door(mdl, body, s.x_rear + 22)
        R.wheel(mdl, s.x_front - 27)
        R.wheel(mdl, s.x_rear + 31, twin=True)
    elif car == "front":
        body = R.bus_body(mdl, 9.5, front=R.FRONT, rear=None)
        s = body.shell
        R.windscreen(mdl, body)
        R.lamps(mdl, body, front=True)
        R.door(mdl, body, s.x_front - 25)
        R.door(mdl, body, s.mid - 8)
        R.wheel(mdl, s.x_front - 27)
        R.wheel(mdl, s.x_rear + 14, twin=True)
        R.bellows(mdl, body, front=False)
    elif car == "rear":
        body = R.bus_body(mdl, 6.5, front=None, rear=R.REAR)
        s = body.shell
        R.rear_end(mdl, body)
        R.door(mdl, body, s.x_front - 18)
        R.wheel(mdl, s.x_rear + 22, twin=True)
        R.bellows(mdl, body, front=True)
    else:
        raise ValueError(f"unknown car {car!r}")
    return mdl
