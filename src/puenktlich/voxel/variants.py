"""Model variants rendered per vehicle.

Direction-aware lights: OpenTTD always draws a vehicle front-first, so the model's
front (high x) is the end facing the direction of travel. The game picks one of these
variants from the vehicle's position in the train (see nml/templates/procedures.nml.j2):

    solo  front white, rear red    the vehicle is both first and last
    head  front white, rear off    leading a longer train
    tail  front off,   rear red    last vehicle of the train
    none  both off                 somewhere in the middle
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Front = Literal["white", "off"]
Rear = Literal["red", "off"]


@dataclass(frozen=True)
class Lights:
    front: Front = "white"
    rear: Rear = "red"


LIGHT_VARIANTS: dict[str, Lights] = {
    "solo": Lights("white", "red"),
    "head": Lights("white", "off"),
    "tail": Lights("off", "red"),
    "none": Lights("off", "off"),
}
DEFAULT_VARIANT = "solo"
