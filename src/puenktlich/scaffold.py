"""`pk new`: start a vehicle from a working stub.

Writes `data/vehicles/<operator>/<id>.yaml` (next free grf_id in the operator's block) and
`models/<operator>/<id>/recipe.py` + `REFERENCE.md`. The stub builds and previews as it is;
every value marked TODO is a placeholder to replace with the prototype's data.
"""

from __future__ import annotations

from pathlib import Path

from puenktlich import lock, paths
from puenktlich.schema import operators, vehicles

KINDS = ("locomotive", "coach", "control_car", "emu", "wagon", "bus")
COMPANY = (
    "  - id: company\n"
    "    name: { en: Company colours, de: Firmenfarben, fr: Couleurs de la société, it: Colori della compagnia }\n"
    "    company_colours: true\n"
)
#        kind: (railtype, speed, power, weight, length, capacity, model block)
DATA = {
    "locomotive": ("standard_ac", 140, 4000, 80, 16.0, None, "model:\n  path: {path}\n  lights: true\n"),
    "coach": ("standard", 160, 0, 40, 25.6, 60, "model:\n  path: {path}\n  lights: true\n"),
    "control_car": ("standard", 160, 5, 42, 25.6, 50, "model:\n  path: {path}\n  lights: true\n"),
    "emu": (
        "standard_ac",
        160,
        2000,
        150,
        76.8,
        200,
        "cars:   # front to rear; one recipe builds every car\n"
        "  - model: {{ path: {path}, lights: true, params: {{ car: front }} }}\n    length_m: 25.6\n"
        "  - model: {{ path: {path}, lights: true, params: {{ car: middle }} }}\n    length_m: 25.6\n"
        "  - model: {{ path: {path}, lights: true, params: {{ car: rear }} }}\n    length_m: 25.6\n",
    ),
    "wagon": ("standard", 100, 0, 20, 12.8, 40, "model:\n  path: {path}\n"),
    "bus": (None, 80, 220, 18, 12.0, 90, "model:\n  path: {path}\n"),
}


def _after_imports(source: str, line: str) -> str:
    """`source` with `line` inserted after its last top-level import (multi-line imports too)."""
    lines = source.split("\n")
    last = max(i for i, ln in enumerate(lines) if ln.startswith(("from ", "import ")))
    if lines[last].rstrip().endswith("("):
        last = next(i for i in range(last, len(lines)) if lines[i].startswith(")"))
    return "\n".join([*lines[: last + 1], "", line, *lines[last + 1 :]])


RECIPES = {
    "locomotive": """from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import CrossSection, EndShape
from puenktlich.voxel.parts.loco import LocoSpec, Louvres, Panel, Windscreen, build_loco
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = LocoSpec(  # TODO: every measurement below is a placeholder
    length_m={length},
    section=CrossSection(floor=15, roof=50, half_width=19.5, roof_radius=7, tumblehome=1.5, tumble_from=26),
    nose=EndShape(rake=8, rake_from=30, rake_curve=1.2, corner_radius=6, undercut=2, undercut_height=4),
    windscreen=Windscreen(frame_z=(31, 48), frame_half_width=17, glass_z=(33, 46), glass_half_width=15, depth=16),
    cab_window=(10, 19),
    cab_window_z=(34, 44),
    door=(21, 28),
    door_z=(17, 45),
    louvres=Louvres(offsets=(-28, 28), half_length=10, z=(36, 44)),
    panels=(Panel(z=(24, 29), colour=P.STRIPE_CC2, half_length=14),),
    bogie_centres_m=4.5,
    wheelbase_m=2.6,
    pantograph_offset=30,
    roof_boxes=((-14, -6, 7),),
)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_loco(SPEC, lights)
""",
    "coach": """from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.coach import CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

SPEC = CoachSpec(windows=10)  # TODO: windows, doors, section, length_m (see CoachSpec)


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
""",
    "control_car": """from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import EndShape
from puenktlich.voxel.parts.coach import CabSpec, CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

# TODO: nose shape and windscreen of the prototype's cab; push-pull orientation is automatic
NOSE = EndShape(rake=8, rake_from=30, rake_curve=1.2, corner_radius=6, undercut=2, undercut_height=4)
SPEC = CoachSpec(windows=9, cab=CabSpec(nose=NOSE, windscreen_z=(32, 45)))


def build(lights: Lights = LIGHT_VARIANTS["solo"]) -> Model:
    return build_coach(SPEC, lights)
""",
    "emu": """from puenktlich.voxel.model import Model
from puenktlich.voxel.parts.body import EndShape
from puenktlich.voxel.parts.coach import CabSpec, CoachSpec, build_coach
from puenktlich.voxel.variants import LIGHT_VARIANTS, Lights

# TODO: nose, windows and doors of the prototype. For double-deck units see parts/dosto.py,
# for articulated units on Jakobs bogies parts/smile.py.
NOSE = EndShape(rake=8, rake_from=30, rake_curve=1.2, corner_radius=6, undercut=2, undercut_height=4)
CAB = CabSpec(nose=NOSE, windscreen_z=(32, 45))
CARS = {{
    "front": lambda: CoachSpec(windows=8, cab=CAB, mu_role="front", motor_bogies=True),
    "middle": lambda: CoachSpec(windows=10, mu_role="middle"),
    "rear": lambda: CoachSpec(windows=8, cab=CAB, mu_role="rear"),
}}


def build(lights: Lights = LIGHT_VARIANTS["solo"], car: str = "front") -> Model:
    return build_coach(CARS[car](), lights)
""",
    "wagon": '''from puenktlich.voxel import palette as P
from puenktlich.voxel.model import Model, m
from puenktlich.voxel.parts.running_gear import bogie, buffers

LENGTH_M = {length}
BUFFER_DEPTH = 6
FLOOR = 15
BODY = P.ramp(P.REDDISH_BROWN, 0.45)  # TODO: wagons keep their own colours (no CC1 with recolourable cargo)


def build() -> Model:
    """TODO: a plain box van. For cargo graphics paint the load space with CARGO_MASK and
    define CARGO = CargoSpec(...): see models/sbb/eanos and voxel/cargo.py."""
    mdl = Model.new()
    mid = mdl.d.shape[0] / 2
    x0, x1 = mid - m(LENGTH_M) / 2 + BUFFER_DEPTH, mid + m(LENGTH_M) / 2 - BUFFER_DEPTH
    mdl.solid(mdl.centred_box(x0, x1, 18.5, FLOOR - 3, FLOOR), P.UNDERFRAME)
    mdl.solid(mdl.centred_box(x0, x1, 19.5, FLOOR, 44), BODY)
    for c in (x0 + 18, x1 - 18):
        bogie(mdl, c, wheelbase=m(1.8), wheel_diameter=9, top=FLOOR - 2, style="freight")
    buffers(mdl, x1, front=True, length=BUFFER_DEPTH, beam=False)
    buffers(mdl, x0, front=False, length=BUFFER_DEPTH, beam=False)
    return mdl
''',
    "bus": '''from puenktlich.voxel.model import ROAD_CANVAS, Model
from puenktlich.voxel.parts import road as R


def build() -> Model:
    """TODO: a 12 m low-floor bus fitted to 8/8 = 11.2 m (docs/SCALE.md); doors are on the
    right-hand side. Articulated buses: `cars:` with one recipe car each (models/postauto/citaro)."""
    mdl = Model.new(ROAD_CANVAS)
    body = R.bus_body(mdl, 11.2, front=R.FRONT, rear=R.REAR)
    s = body.shell
    R.windscreen(mdl, body)
    R.lamps(mdl, body, front=True)
    R.rear_end(mdl, body)
    R.door(mdl, body, s.x_front - 25)
    R.door(mdl, body, s.mid - 2)
    R.wheel(mdl, s.x_front - 27)
    R.wheel(mdl, s.x_rear + 28, twin=True)
    return mdl
''',
}

REFERENCE = """# {name} — reference

Facts the model is built from, each with its source. Mark anything from memory as unverified.

## Prototype
| | Value | Source |
|---|---|---|
| Length over buffers | TODO m | |
| Width / height | TODO | |
| Wheel arrangement, wheel diameter | TODO | |
| Bogie centres, wheelbase | TODO | |
| Power, top speed, weight, tractive effort | TODO | |
| Built (years, number) | TODO | |

## Photos
| Id | Photo | Author | Licence |
|---|---|---|---|

## Measurements taken from the photos
Heights in metres -> z voxels, positions along the body in metres from the front.

## Livery
Which surfaces follow CC1 / CC2 and which stay fixed.
"""


def next_grf_id(operator: str) -> int:
    """Next free id in the operator's block of 100, counting ids that were ever locked."""
    block = operators()[operator].grf_id_block
    used = {v.grf_id for v in vehicles().values()} | {e["grf_id"] for e in lock.load().values()}
    for grf_id in range(block, block + 100):
        if grf_id not in used:
            return grf_id
    raise ValueError(f"{operator}: all 100 grf_ids of the block {block}.. are used")


def new_vehicle(operator: str, vehicle_id: str, kind: str, name: str) -> list[Path]:
    """Write the stub files and return them. Refuses to overwrite anything."""
    if operator not in operators():
        raise ValueError(f"unknown operator {operator!r} (data/operators.yaml: {', '.join(operators())})")
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r} ({', '.join(KINDS)})")
    if vehicle_id in vehicles() or vehicle_id in lock.load():
        raise ValueError(f"vehicle id {vehicle_id!r} is already in use")
    railtype, speed, power, weight, length, capacity, model = DATA[kind]
    path = f"{operator}/{vehicle_id}"
    yaml_file = paths.VEHICLES / operator / f"{vehicle_id}.yaml"
    model_dir = paths.MODELS / operator / vehicle_id
    files = [yaml_file, model_dir / "recipe.py", model_dir / "REFERENCE.md"]
    for f in files:
        if f.exists():
            raise ValueError(f"{paths.rel(f)} already exists")
    op = operators()[operator]
    lines = [
        f"# {name} — TODO: one line on the prototype. Values marked TODO are placeholders.",
        f"id: {vehicle_id}",
        f"grf_id: {next_grf_id(operator)}          # never change — saved games reference this (`pk lock`)",
        "name:",
        *[f"  {lang}: {name}" for lang in ("en", "de", "fr", "it")],
        f"operator: {operator}",
        f"kind: {kind}",
        *([f"railtype: {railtype}       # data/railtypes.yaml"] if railtype else []),
        "intro_year: 2000        # TODO",
        f"max_speed_kmh: {speed}      # TODO",
        f"power_kw: {power}          # TODO"
        + ("  (nominal: lets the control car lead a train)" if kind == "control_car" else ""),
        *(["tractive_effort_kn: 200 # TODO"] if power > 10 else []),
        f"weight_t: {weight}           # TODO",
        f"length_m: {length}         # TODO: prototype length; OpenTTD length = round(length / 3.2), max 8",
        *([f"capacity:\n  {'COAL' if kind == 'wagon' else 'PASS'}: {capacity}             # TODO"] if capacity else []),
        "liveries:               # append-only: item id = grf_id * 8 + position",
        f"  - id: {operator}",
        f"    name: {{ en: {op.name}, de: {op.name}, fr: {op.name}, it: {op.name} }}",
        "    cc1: RED            # TODO",
        "    cc2: WHITE          # TODO",
        COMPANY.rstrip("\n"),
        model.format(path=path).rstrip("\n"),
        f"reference: []           # TODO: id in data/reference/{operator}.yaml",
    ]
    yaml_file.parent.mkdir(parents=True, exist_ok=True)
    yaml_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    model_dir.mkdir(parents=True, exist_ok=True)
    doc = f'"""{name} — TODO: prototype summary. Facts and sources: REFERENCE.md in this directory."""\n\n'
    recipe = RECIPES[kind].format(length=length)
    if kind != "bus":  # trains render at their real width (docs/SCALE.md)
        recipe = _after_imports(recipe, "BODY_WIDTH_M = 2.8  # TODO: real body width in metres (docs/SCALE.md)")
    (model_dir / "recipe.py").write_text(doc + recipe, encoding="utf-8")
    (model_dir / "REFERENCE.md").write_text(REFERENCE.format(name=name), encoding="utf-8")
    return files
