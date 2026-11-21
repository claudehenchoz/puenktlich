"""Data model for vehicles, operators, railtypes and reference fleet lists.

YAML in data/ is the single source of truth; everything else (NML, docs, coverage)
is generated from these models. Validation errors are meant to be read by humans
and agents alike, so keep field descriptions precise.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from puenktlich import paths

Lang = Literal["en", "de", "fr", "it", "rm"]
TTD_COLOURS = Literal[
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
]
METRES_PER_UNIT = 3.2  # 8/8 = 25.6 m — docs/SCALE.md
# road vehicles: OpenTTD draws 1/8 unit as 4 px (90° view) = 14 voxels on the road manifest
# (126 voxels -> 36 px), i.e. 1.4 m at 10 vox/m: 8/8 = 11.2 m
ROAD_METRES_PER_UNIT = 1.4
ROAD_KINDS = ("bus", "tram")


def units(length_m: float, road: bool = False) -> int:
    """Length in metres -> OpenTTD length in 1/8 units, clamped to 1..8."""
    return max(1, min(8, round(length_m / (ROAD_METRES_PER_UNIT if road else METRES_PER_UNIT))))


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Operator(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    full_name: dict[Lang, str]
    badge: str = Field(description="Badge label, e.g. 'operator/sbb'")
    founded: int | None = None


class Railtype(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str = Field(min_length=4, max_length=4)
    fallbacks: list[str] = Field(default_factory=list, description="Ordered fallback labels")
    description: str = ""


class Livery(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: dict[Lang, str]
    company_colours: bool = Field(
        False, description="True = use the player's company colours; False = fixed cc1/cc2 below"
    )
    cc1: TTD_COLOURS | None = None
    cc2: TTD_COLOURS | None = None
    model_variant: str | None = Field(None, description="Alternative recipe variant / vox file")

    @model_validator(mode="after")
    def _fixed_needs_colours(self) -> Livery:
        if not self.company_colours and (self.cc1 is None or self.cc2 is None):
            raise ValueError(f"livery {self.id}: fixed liveries need cc1 and cc2")
        return self


class ModelRef(Strict):
    path: str = Field(description="Directory under models/, e.g. 'sbb/re460'")
    kind: Literal["recipe", "vox"] = "recipe"
    lights: bool = Field(
        False,
        description="Recipe takes build(lights=...); render solo/head/tail/none lamp variants (voxel/variants.py)",
    )
    params: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Keyword arguments passed to the recipe's build(), e.g. {car: motor}"
    )


class Car(Strict):
    """One car of a multiple unit (sold and coupled as a single articulated vehicle)."""

    model: ModelRef
    length_m: float = Field(gt=0)

    @property
    def ottd_length(self) -> int:
        return units(self.length_m)


class CarSpec(BaseModel):
    """Resolved car: a single-model vehicle is one car keyed by the vehicle id."""

    key: str
    index: int
    model: ModelRef
    ottd_length: int
    road: bool = False  # road vehicle: road canvas/manifest, no articulation split, no hill sprites


class Vehicle(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]+$", description="Globally unique, stable forever")
    grf_id: int = Field(ge=0, lt=0xFFFF, description="NewGRF item ID — never reuse or change")
    name: dict[Lang, str]
    operator: str
    kind: Literal["locomotive", "emu", "dmu", "coach", "control_car", "wagon", "bus", "tram"]
    railtype: str | None = Field(None, description="Rail vehicles only (data/railtypes.yaml id)")
    roadtype: Literal["road", "tram"] | None = Field(None, description="Road vehicles only (bus: road)")
    intro_year: int = Field(ge=1847, le=2100)
    retire_year: int | None = None
    vehicle_life_years: int = 40
    model_life_years: int = 30
    max_speed_kmh: int = Field(gt=0)
    power_kw: int = Field(ge=0)
    tractive_effort_kn: float | None = None
    weight_t: float = Field(gt=0)
    length_m: float = Field(gt=0)
    capacity: dict[str, int] = Field(default_factory=dict, description="cargo label -> amount (the default cargo)")
    refit_classes: list[str] = Field(
        default_factory=list, description="Refittable cargo classes, e.g. [CC_BULK]; default: from the cargo label"
    )
    reliability_decay: int = 20
    cost_factor: int = Field(25, ge=0, le=255)
    running_cost_factor: int = Field(25, ge=0, le=255)
    liveries: list[Livery] = Field(min_length=1)
    model: ModelRef | None = Field(None, description="Single-model vehicle (or use `cars`)")
    cars: list[Car] = Field(default_factory=list, description="Multiple unit: cars from front to rear")
    reference: list[str] = Field(default_factory=list, description="IDs in data/reference/*.yaml")
    description: dict[Lang, str] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _has_english(cls, v: dict[str, str]) -> dict[str, str]:
        if "en" not in v:
            raise ValueError("name.en is required (fallback language)")
        return v

    @model_validator(mode="after")
    def _model_or_cars(self) -> Vehicle:
        if (self.model is None) == (not self.cars):
            raise ValueError(f"{self.id}: give exactly one of `model` or `cars`")
        if self.is_road:
            if self.railtype is not None:
                raise ValueError(f"{self.id}: road vehicles have a `roadtype`, not a `railtype`")
        elif self.railtype is None or self.roadtype is not None:
            raise ValueError(f"{self.id}: rail vehicles need a `railtype` (and no `roadtype`)")
        return self

    @property
    def is_road(self) -> bool:
        return self.kind in ROAD_KINDS

    @property
    def road_type(self) -> str:
        """Road vehicles: `roadtype`, defaulting to tram for trams and road otherwise."""
        return self.roadtype or ("tram" if self.kind == "tram" else "road")

    @property
    def ottd_length(self) -> int:
        """Length in 1/8 units (per car for multiple units / articulated buses), 1..8."""
        if self.cars:
            return max(units(c.length_m, self.is_road) for c in self.cars)
        return units(self.length_m, self.is_road)

    @property
    def car_specs(self) -> list[CarSpec]:
        if not self.cars:
            assert self.model is not None
            return [CarSpec(key=self.id, index=0, model=self.model, ottd_length=self.ottd_length, road=self.is_road)]
        return [
            CarSpec(
                key=f"{self.id}_c{i}",
                index=i,
                model=c.model,
                ottd_length=units(c.length_m, self.is_road),
                road=self.is_road,
            )
            for i, c in enumerate(self.cars)
        ]


class ReferenceEntry(Strict):
    id: str
    name: str
    category: Literal["locomotive", "emu", "dmu", "coach", "control_car", "wagon", "bus", "tram", "railcar"]
    gauge: Literal["standard", "metre", "rack_metre", "other"] = "standard"
    built: str | None = None
    in_scope: bool = True
    notes: str = ""


class ReferenceList(Strict):
    operator: str
    source: str
    retrieved: str
    entries: list[ReferenceEntry]


# --- loaders -------------------------------------------------------------------


def _yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@cache
def operators() -> dict[str, Operator]:
    return {o["id"]: Operator(**o) for o in _yaml(paths.DATA / "operators.yaml")}


@cache
def railtypes() -> dict[str, Railtype]:
    return {r["id"]: Railtype(**r) for r in _yaml(paths.DATA / "railtypes.yaml")}


def load_vehicle(path: Path) -> Vehicle:
    return Vehicle(**_yaml(path))


@cache
def vehicles() -> dict[str, Vehicle]:
    out: dict[str, Vehicle] = {}
    for p in sorted(paths.VEHICLES.rglob("*.yaml")):
        v = load_vehicle(p)
        if v.id in out:
            raise ValueError(f"duplicate vehicle id {v.id} ({p})")
        out[v.id] = v
    return out


@cache
def references() -> dict[str, ReferenceList]:
    return {p.stem: ReferenceList(**_yaml(p)) for p in sorted(paths.REFERENCE.glob("*.yaml"))}


def validate_all() -> list[str]:
    """Cross-file checks that pydantic can't do per file. Returns problems."""
    problems: list[str] = []
    ops, rts, vs = operators(), railtypes(), vehicles()
    all_refs = [e.id for r in references().values() for e in r.entries]
    ref_ids = set(all_refs)
    for rid in sorted(ref_ids):
        if all_refs.count(rid) > 1:
            problems.append(f"reference id {rid} listed {all_refs.count(rid)} times")
    seen_grf: dict[int, str] = {}
    for v in vs.values():
        if v.operator not in ops:
            problems.append(f"{v.id}: unknown operator {v.operator}")
        if not v.is_road and v.railtype not in rts:
            problems.append(f"{v.id}: unknown railtype {v.railtype}")
        if v.grf_id in seen_grf:
            problems.append(f"{v.id}: grf_id {v.grf_id} already used by {seen_grf[v.grf_id]}")
        seen_grf[v.grf_id] = v.id
        for r in v.reference:
            if r not in ref_ids:
                problems.append(f"{v.id}: reference {r} not found in data/reference/")
        for car in v.car_specs:
            mdir = paths.MODELS / car.model.path
            need = mdir / ("recipe.py" if car.model.kind == "recipe" else "model.vox")
            if not need.exists():
                problems.append(f"{v.id}: missing model {need.relative_to(paths.ROOT)}")
        ids = [livery.id for livery in v.liveries]
        if len(set(ids)) != len(ids):
            problems.append(f"{v.id}: duplicate livery ids")
    return problems
