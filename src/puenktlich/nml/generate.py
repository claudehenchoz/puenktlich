"""Generate NML + language files from data/, then compile with nmlc.

Item IDs: each vehicle owns the block `grf_id * 8 .. grf_id * 8 + 7`; livery N
(0-based, list order) becomes item `grf_id * 8 + N`. The liveries list is therefore
append-only — reordering breaks saved games.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from puenktlich import paths
from puenktlich.models import car_plans
from puenktlich.render import KINDS, SCALES, is_articulated, parts_for, sheet_path, sprite_layout
from puenktlich.schema import CARGO_CLASSES, MAX_LIVERIES, Livery, Vehicle, operators, railtypes, vehicles
from puenktlich.sprites import (
    overlay_sheet_name,
    purchase_layout,
    purchase_rect,
    purchase_sheet_name,
    sheet_for,
)

GRFID = "PK\\43\\48"  # "PKCH" — never change after the first public release
LANG_IDS = {"en": 0x01, "de": 0x02, "fr": 0x03, "it": 0x27}
LANG_FILES = {"en": "english", "de": "german", "fr": "french", "it": "italian"}
ZOOMS = {1: "ZOOM_LEVEL_NORMAL", 2: "ZOOM_LEVEL_IN_2X", 4: "ZOOM_LEVEL_IN_4X"}

ENGINE = {  # traction -> (engine_class, running_cost_base, visual effect)
    "electric": ("ENGINE_CLASS_ELECTRIC", "RUNNING_COST_ELECTRIC", "VISUAL_EFFECT_ELECTRIC"),
    "diesel": ("ENGINE_CLASS_DIESEL", "RUNNING_COST_DIESEL", "VISUAL_EFFECT_DIESEL"),
    "steam": ("ENGINE_CLASS_STEAM", "RUNNING_COST_STEAM", "VISUAL_EFFECT_STEAM"),
}

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


@dataclass
class Badge:
    label: str
    string: str

    @property
    def ident(self) -> str:
        return self.label.replace("/", "_")


@dataclass
class LiveryItem:
    livery: Livery
    ident: str
    item_id: int
    name_string: str
    variant_group: str | None


class Strings:
    """Collects strings per language and writes .lng files."""

    def __init__(self) -> None:
        self.table: dict[str, dict[str, str]] = {}

    def add(self, key: str, texts: dict[str, str]) -> str:
        if "en" not in texts:
            raise ValueError(f"{key}: English text required")
        self.table[key] = {k: v for k, v in texts.items() if k in LANG_IDS}
        return key

    def write(self, lang_dir: Path) -> None:
        lang_dir.mkdir(parents=True, exist_ok=True)
        for lang, fname in LANG_FILES.items():
            lines = [f"##grflangid 0x{LANG_IDS[lang]:02X}", ""]
            for key, texts in self.table.items():
                if lang in texts:
                    lines.append(f"{key:<40}:{texts[lang]}")
            (lang_dir / f"{fname}.lng").write_text("\n".join(lines) + "\n", encoding="utf-8")


def project_version() -> str:
    return tomllib.loads((paths.ROOT / "pyproject.toml").read_text())["project"]["version"]


def _rel(p: Path) -> str:
    return p.relative_to(paths.ROOT).as_posix()


def _traction(v: Vehicle) -> str:
    rt = railtypes()[v.railtype]
    return "diesel" if rt.label.endswith("N") else "electric"


def vehicle_badges(v: Vehicle) -> list[str]:
    """Badge labels of a vehicle: operator, gauge (rail) and traction (powered vehicles).
    Players filter and group the purchase list by them (OpenTTD 15+)."""
    out = [operators()[v.operator].badge]
    if not v.is_road:
        out.append("gauge/metre" if v.railtype.startswith("metre") else "gauge/standard")
    if v.is_road:
        out.append(f"traction/{v.traction or 'diesel'}")
    elif v.power_kw > 0 and v.kind != "control_car":
        out.append("traction/rack" if "rack" in v.railtype else f"traction/{_traction(v)}")
    return out


def model_life(v: Vehicle) -> int | str:
    """Years a model stays in the purchase list: until `retire_year` if the prototype's
    retirement is known, otherwise the vehicle's `model_life_years`."""
    return v.retire_year - v.intro_year if v.retire_year is not None else v.model_life_years


def _shape_proc(length: int) -> str:
    """Timberwolf: vehicles longer than 4/8 compare with the part in front only."""
    return "pk_shape_medium" if length > 4 else "pk_shape_short"


def _livery_items(v: Vehicle, strings: Strings) -> list[LiveryItem]:
    items: list[LiveryItem] = []
    for i, livery in enumerate(v.liveries):
        ident = f"{v.id}_{livery.id}"
        names = {lang: f"{v.name[lang]} ({livery.name.get(lang, livery.name['en'])})" for lang in v.name}
        items.append(
            LiveryItem(
                livery=livery,
                ident=ident,
                item_id=v.grf_id * MAX_LIVERIES + i,
                name_string=strings.add(f"STR_NAME_{ident.upper()}", names),
                variant_group=items[0].ident if i > 0 else None,
            )
        )
    return items


def split_capacity(total: int, weights: list[int]) -> list[int]:
    """Share `total` between parts in proportion to `weights` so that the shares add up to
    exactly `total` (largest remainder; ties go to the front)."""
    exact = [total * w / sum(weights) for w in weights]
    shares = [int(e) for e in exact]
    by_remainder = sorted(range(len(weights)), key=lambda i: (shares[i] - exact[i], i))
    for i in by_remainder[: total - sum(shares)]:
        shares[i] += 1
    return shares


def _cargo(v: Vehicle, weights: list[int]) -> dict | None:
    """`weights`: one entry per part that carries cargo (train: every articulated part,
    equally; road: the cars by length)."""
    if not v.capacity:
        return None
    label, total = next(iter(v.capacity.items()))
    parts = split_capacity(total, weights)
    return {
        "label": label,
        "total": total,
        # Every articulated part is the same item, so the property is one number for all
        # parts (the buy menu shows it times the part count); `parts` are the exact shares,
        # applied in-game by the cargo_capacity callback when they are not all equal.
        "per_part": max(1, round(total / len(weights))),
        "parts": parts,
        "uneven": len(set(parts)) > 1,
        "classes": ", ".join(v.refit_classes) if v.refit_classes else CARGO_CLASSES[label],
    }


def _te(v: Vehicle) -> float | None:
    if not v.tractive_effort_kn:
        return None
    return round(min(1.0, v.tractive_effort_kn / (v.weight_t * 9.81)), 3)


def road_vehicle_nml(v: Vehicle, strings: Strings) -> str:
    """Road vehicle: one part per car (`cars:` = articulated bus), 8 views, no light variants."""
    sprite_dir = paths.BUILD_SPRITES / v.id
    specs = car_plans(v)
    cargo = _cargo(v, [car.ottd_length for car, _ in specs.values()])  # capacity split by length
    cars = []
    for i, (car, plan) in enumerate(specs.values()):
        if len(plan.bodies) != 1 or plan.overlays:
            raise ValueError(f"{v.id}: road vehicles have one body per car (no light variants yet)")
        body = plan.default_body
        cars.append(
            {
                "key": car.key,
                "index": car.index,
                "length": car.ottd_length,
                "body": body,
                "rects": {s: sprite_layout(s, car.ottd_length, "road") for s in SCALES},
                "sheets": {
                    s: {d: _rel(sheet_for(sprite_dir, body, "road", s, d)) for d in ("8bpp", "32bpp", "mask")}
                    for s in SCALES
                },
                "capacity": cargo["parts"][i] if cargo else 0,
            }
        )
    up = v.id.upper()
    desc_string = strings.add(f"STR_DESC_{up}", dict(v.description)) if v.description.get("en") else None
    return _env.get_template("roadvehicle.nml.j2").render(
        v=v,
        cars=cars,
        zooms=[(s, ZOOMS[s]) for s in SCALES],
        liveries=_livery_items(v, strings),
        desc_string=desc_string,
        te_coefficient=_te(v),
        badges=vehicle_badges(v),
        model_life=model_life(v),
        cargo=cargo,
    )


def vehicle_nml(v: Vehicle, strings: Strings) -> str:
    if v.is_road:
        return road_vehicle_nml(v, strings)
    sprite_dir = paths.BUILD_SPRITES / v.id
    specs = v.car_specs
    articulated = all(is_articulated(c.ottd_length) for c in specs)
    if len(specs) > 1 and not articulated:
        raise ValueError(f"{v.id}: multiple-unit cars must be 3/8 or longer")
    kinds = list(KINDS) if articulated else ["normal"]

    def sheet_set(stem: str) -> dict:
        sheets = {
            k: {s: {d: _rel(sheet_for(sprite_dir, stem, k, s, d)) for d in ("8bpp", "32bpp", "mask")} for s in SCALES}
            for k in kinds
        }
        return {"name": stem, "sheets": sheets}

    cars = []
    parts: list[int] = []
    for car, plan in car_plans(v).values():
        light_map = {var: (body, overlay_sheet_name(ovl) if ovl else None) for var, (body, ovl) in plan.mapping.items()}
        single_body = len(plan.bodies) == 1
        has_overlays = any(ovl for _, ovl in plan.mapping.values())  # lamp overlays
        cargo_looks = [{"look": look, "colour": colour} for look, colour in plan.cargo_looks.items()]
        cargo_stages = {st: overlay_sheet_name(name) for st, name in plan.cargo.items()}
        if has_overlays:
            entry = f"sw_{car.key}_mid"
        elif single_body:
            entry = f"sw_{plan.default_body}_shape"
        else:
            entry = f"sw_{car.key}_lights_body"
        cars.append(
            {
                "key": car.key,
                "index": car.index,
                "length": car.ottd_length,
                "kinds": kinds,
                "rects": {k: {s: sprite_layout(s, car.ottd_length, k) for s in SCALES} for k in kinds},
                # every distinct body, plus every distinct lamp overlay (drawn as a second layer)
                "sets": [sheet_set(b) for b in plan.bodies] + [sheet_set(overlay_sheet_name(o)) for o in plan.overlays],
                "light_map": light_map,
                "default_body": plan.default_body,
                "single_body": single_body,
                "has_overlays": has_overlays,
                "shape_proc": _shape_proc(car.ottd_length),
                "mid_pos": len(parts) + 1,
                "entry": entry,
                "cargo_looks": cargo_looks,
                "cargo_stages": cargo_stages,
                "cargo_labels": plan.cargo_labels,
                "default_look": plan.default_look,
            }
        )
        parts += list(parts_for(car.ottd_length))
    n_parts = len(parts)
    # 2 = this unit leads the train, 1 = it is last, 3 = both, 0 = in the middle
    lights_expr = (
        "(position_in_consist == position_in_articulated_veh) * 2 + "
        f"(position_in_consist_from_end + position_in_articulated_veh == {n_parts - 1})"
    )

    up = v.id.upper()
    desc_string = strings.add(f"STR_DESC_{up}", dict(v.description)) if v.description.get("en") else None
    items = _livery_items(v, strings)

    engine_class, running_cost_base, visual_effect = ENGINE[_traction(v)]
    if v.power_kw == 0:
        running_cost_base = "RUNNING_COST_STEAM"  # wagons: OpenTTD's usual base for wagon running costs
    cargo = _cargo(v, [1] * n_parts)
    te = _te(v)
    purchase = None
    if articulated and len(specs) > 1:  # multiple unit: its own buy-menu sprite showing the whole unit
        layout = purchase_layout([c["length"] for c in cars])
        purchase = {
            "name": purchase_sheet_name(v.id),
            "rects": {s: purchase_rect(s, layout) for s in SCALES},
            "sheets": {
                s: {d: _rel(sheet_path(sprite_dir, purchase_sheet_name(v.id), s, d)) for d in ("8bpp", "32bpp", "mask")}
                for s in SCALES
            },
        }
    return _env.get_template("vehicle.nml.j2").render(
        v=v,
        cars=cars,
        articulated=articulated,
        parts=parts,
        lights_expr=lights_expr,
        has_stack=articulated and any(c["has_overlays"] or c["cargo_looks"] for c in cars),
        cargo_looks=cars[0]["cargo_looks"] if len(cars) == 1 else [],
        cargo_label_map=cars[0]["cargo_labels"],
        default_look=cars[0]["default_look"],
        zooms=[(s, ZOOMS[s]) for s in SCALES],
        liveries=items,
        desc_string=desc_string,
        engine_class=engine_class,
        running_cost_base=running_cost_base,
        visual_effect=visual_effect,
        te_coefficient=te,
        track_label=railtypes()[v.railtype].label,
        badges=vehicle_badges(v),
        model_life=model_life(v),
        purchase=purchase,
        cargo=cargo,
    )


def generate(out_dir: Path = paths.BUILD_NML, only: list[str] | None = None) -> Path:
    """Write <out_dir>/puenktlich.nml and <out_dir>/lang/*.lng. Returns the .nml path."""
    strings = Strings()
    static = yaml.safe_load((paths.LANG / "strings.yaml").read_text(encoding="utf-8"))
    version = project_version()
    for key, texts in static.items():
        strings.add(key, {k: t.replace("{VERSION}", version) for k, t in texts.items()})

    vs = [v for v in vehicles().values() if only is None or v.id in only]
    used_ops = sorted({v.operator for v in vs})
    badges = [Badge("operator", "STR_BADGE_CLASS_OPERATOR")]
    for op_id in used_ops:
        op = operators()[op_id]
        badges.append(Badge(op.badge, strings.add(f"STR_BADGE_{op.id.upper()}", {"en": op.name})))
    # gauge/* and traction/*: class badge first, then the values in use (strings: lang/strings.yaml)
    used = sorted({b for v in vs for b in vehicle_badges(v) if not b.startswith("operator/")})
    for cls in sorted({b.split("/")[0] for b in used}):
        badges.append(Badge(cls, f"STR_BADGE_CLASS_{cls.upper()}"))
        badges += [Badge(b, f"STR_BADGE_{b.replace('/', '_').upper()}") for b in used if b.startswith(cls + "/")]
    used_rts = sorted({v.railtype for v in vs if v.railtype})
    cargos = sorted(
        {label for v in vs for label in v.capacity}
        | {label for v in vs for _, plan in car_plans(v).values() for label in plan.cargo_labels}
    )

    major, minor, patch = (int(x) for x in version.split(".")[:3])
    parts = [
        _env.get_template("header.nml.j2").render(
            grfid=GRFID,
            version=major * 10000 + minor * 100 + patch,
            min_compatible_version=0,
            railtypes=[railtypes()[r] for r in used_rts],
            cargos=cargos,
            badges=badges,
        ),
        _env.get_template("procedures.nml.j2").render(
            shape_procs={
                _shape_proc(c.ottd_length)
                for v in vs
                for c in v.car_specs
                if not v.is_road and is_articulated(c.ottd_length)
            }
        ),
    ]
    for v in vs:
        parts.append(vehicle_nml(v, strings))

    out_dir.mkdir(parents=True, exist_ok=True)
    nml = out_dir / f"{paths.GRF_NAME}.nml"
    nml.write_text("".join(parts), encoding="utf-8")
    strings.write(out_dir / "lang")
    return nml


def partial_grf() -> Path:
    """GRF of a `pk build <ids>`: only those vehicles, never installed or released."""
    return paths.BUILD / f"{paths.GRF_NAME}_partial.grf"


def grf_for(vehicle_ids: list[str]) -> Path | None:
    """GRF to test `vehicle_ids` with: the partial build if it is newer than the full one and
    holds all of them, otherwise the full GRF (None: nothing built yet)."""
    full, partial = paths.BUILD / f"{paths.GRF_NAME}.grf", partial_grf()
    ids_file = partial.with_suffix(".json")
    if partial.exists() and ids_file.exists():
        newer = not full.exists() or partial.stat().st_mtime > full.stat().st_mtime
        if newer and set(vehicle_ids) <= set(json.loads(ids_file.read_text())):
            return partial
    return full if full.exists() else None


def _compile_stamp(nml: Path) -> str:
    """Everything nmlc reads: the NML, the language files, every sheet it references (path,
    size, mtime) and the nml version."""
    from importlib.metadata import version

    h = hashlib.sha1(version("nml").encode())
    text = nml.read_text(encoding="utf-8")
    h.update(text.encode())
    for lng in sorted((nml.parent / "lang").glob("*.lng")):
        h.update(lng.read_bytes())
    for sheet in sorted(set(re.findall(r'"([^"\n]+\.png)"', text))):
        st = (paths.ROOT / sheet).stat()
        h.update(f"{sheet}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()


def compile_grf(nml: Path, grf: Path | None = None, vehicle_ids: list[str] | None = None) -> Path:
    """Compile with nmlc. Skipped when the NML, the language files and every referenced sheet
    are unchanged since the GRF was written (nmlc otherwise re-parses the whole NML each time)."""
    grf = grf or paths.BUILD / f"{paths.GRF_NAME}.grf"
    stamp_file = grf.with_suffix(".stamp")
    stamp = _compile_stamp(nml)
    if vehicle_ids is not None:
        grf.with_suffix(".json").write_text(json.dumps(sorted(vehicle_ids)))
    if grf.exists() and stamp_file.exists() and stamp_file.read_text() == stamp:
        return grf
    stamp_file.unlink(missing_ok=True)
    subprocess.run(
        [
            "nmlc",
            "--quiet",
            "-c",
            "--lang-dir",
            str(nml.parent / "lang"),
            "--cache-dir",
            str(paths.BUILD / ".nmlcache"),
            "--grf",
            str(grf),
            str(nml),
        ],
        cwd=paths.ROOT,
        check=True,
    )
    stamp_file.write_text(stamp)
    return grf
