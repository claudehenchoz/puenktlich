"""Cargo graphics for freight wagons, composited by Cargopositor.

A wagon recipe paints its load space with `CARGO_MASK` (palette index 255) and exposes a
module-level `CARGO = CargoSpec(...)`:

    shapes   cargo objects built in Python (a bulk heap, a block of containers, ...)
    stages   load stage -> CargoState (1 = partly loaded, 2 = full)
    looks    look id -> TTD colour that recolours the cargo, or None to keep its colours
    labels   cargo label -> look id; anything else uses `default_look`

The pipeline (models.py) writes the masked wagon and the shapes, runs one Cargopositor
batch (`produce_empty` + one operation per stage) and uses the output: the empty wagon is
the body, each loaded stage becomes a sprite overlay (only the cargo pixels are stored).

Looks cost nothing extra: model recolourable cargo in the CC1 ramp, and the game draws the
cargo layer with `palette_1cc(COLOUR_<look>)` (built-in company-colour remaps). Such a wagon
must not use company colours itself: cargo changes the shading of nearby body pixels, those
end up in the overlay, and the cargo palette would recolour them too. In-game the
look follows the carried cargo and the stage follows the load:
stage = (cargo_count > 0) + (2 * cargo_count > cargo_capacity).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from puenktlich.voxel.model import Model

CARGO_MASK = 255  # Cargopositor: voxels with this colour are replaced by cargo
STAGES = (1, 2)  # 0 = empty (no overlay), 1 = partly loaded, 2 = full


@dataclass(frozen=True)
class CargoState:
    shape: str  # key in CargoSpec.shapes
    op: Literal["scale", "repeat"] = "scale"
    n: int = 0  # repeat: number of copies (0 = fill)
    input_ramp: str | None = None  # Cargopositor recolouring, e.g. "3,12" -> "72,79"
    output_ramp: str | None = None
    scale: dict[str, float] | None = None  # Cargopositor "scale" directive


TTD_COLOURS = (
    "DARK_BLUE",
    "PALE_GREEN",
    "PINK",
    "YELLOW",
    "RED",
    "LIGHT_BLUE",
    "GREEN",
    "DARK_GREEN",
    "BLUE",
    "CREAM",
    "MAUVE",
    "PURPLE",
    "ORANGE",
    "BROWN",
    "GREY",
    "WHITE",
)


@dataclass
class CargoSpec:
    shapes: dict[str, Callable[[], Model]]
    stages: dict[int, CargoState]  # stage -> how Cargopositor places the cargo
    looks: dict[str, str | None]  # look -> TTD colour for palette_1cc (None = no recolour)
    labels: dict[str, str] = field(default_factory=dict)  # cargo label -> look
    default_look: str = ""

    def __post_init__(self) -> None:
        if set(self.stages) != set(STAGES):
            raise ValueError(f"cargo needs stages {STAGES}")
        for st in self.stages.values():
            if st.shape not in self.shapes:
                raise ValueError(f"unknown shape {st.shape!r}")
        if self.default_look not in self.looks:
            raise ValueError(f"default look {self.default_look!r} not in looks")
        for look, colour in self.looks.items():
            if colour is not None and colour not in TTD_COLOURS:
                raise ValueError(f"look {look!r}: unknown TTD colour {colour!r}")
        for label, look in self.labels.items():
            if look not in self.looks:
                raise ValueError(f"label {label}: unknown look {look!r}")

    @staticmethod
    def stage_name(stage: int) -> str:
        return f"load{stage}"

    def batch_operations(self) -> list[dict]:
        ops: list[dict] = [{"name": "_empty", "type": "produce_empty", "file": ""}]
        for stage, st in sorted(self.stages.items()):
            op: dict = {"name": f"_{self.stage_name(stage)}", "type": st.op, "file": f"{st.shape}.vox"}
            if st.op == "repeat" and st.n:
                op["n"] = st.n
            if st.input_ramp and st.output_ramp:
                op["input_ramp"], op["output_ramp"] = st.input_ramp, st.output_ramp
            if st.scale:
                op["scale"] = st.scale
            ops.append(op)
        return ops
