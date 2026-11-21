"""Generate NML + language files from data/, then compile with nmlc.

Item IDs: each vehicle owns the block `grf_id * 8 .. grf_id * 8 + 7`; livery N
(0-based, list order) becomes item `grf_id * 8 + N`. The liveries list is therefore
append-only — reordering breaks saved games.
"""

from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from puenktlich import paths
from puenktlich.models import sprite_name, variants
from puenktlich.render import KINDS, SCALES, is_articulated, parts_for, sprite_layout
from puenktlich.schema import Livery, Vehicle, operators, railtypes, vehicles
from puenktlich.sprites import sheet_for

GRFID = "PK\\43\\48"  # "PKCH" — never change after the first public release
MAX_LIVERIES = 8
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


def _shape_proc(length: int) -> str:
    """Timberwolf: vehicles longer than 4/8 compare with the part in front only."""
    return "pk_shape_medium" if length > 4 else "pk_shape_short"


def vehicle_nml(v: Vehicle, strings: Strings) -> str:
    if len(v.liveries) > MAX_LIVERIES:
        raise ValueError(f"{v.id}: at most {MAX_LIVERIES} liveries")
    sprite_dir = paths.BUILD_SPRITES / v.id
    length = v.ottd_length
    articulated = is_articulated(length)
    kinds = list(KINDS) if articulated else ["normal"]
    rects = {k: {s: sprite_layout(s, length, k) for s in SCALES} for k in kinds}
    var_list = []
    for var in variants(v):
        name = sprite_name(v, var)
        sheets = {
            k: {s: {d: _rel(sheet_for(sprite_dir, name, k, s, d)) for d in ("8bpp", "32bpp", "mask")} for s in SCALES}
            for k in kinds
        }
        var_list.append({"name": name, "sheets": sheets})

    up = v.id.upper()
    desc_string = strings.add(f"STR_DESC_{up}", dict(v.description)) if v.description.get("en") else None
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

    engine_class, running_cost_base, visual_effect = ENGINE[_traction(v)]
    te = None
    if v.tractive_effort_kn:
        te = round(min(1.0, v.tractive_effort_kn / (v.weight_t * 9.81)), 3)
    op = operators()[v.operator]
    return _env.get_template("vehicle.nml.j2").render(
        v=v,
        variants=var_list,
        kinds=kinds,
        rects=rects,
        articulated=articulated,
        parts=parts_for(length),
        shape_proc=_shape_proc(length),
        zooms=[(s, ZOOMS[s]) for s in SCALES],
        liveries=items,
        desc_string=desc_string,
        engine_class=engine_class,
        running_cost_base=running_cost_base,
        visual_effect=visual_effect,
        te_coefficient=te,
        track_label=railtypes()[v.railtype].label,
        badges=[op.badge],
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
    used_rts = sorted({v.railtype for v in vs})

    major, minor, patch = (int(x) for x in version.split(".")[:3])
    parts = [
        _env.get_template("header.nml.j2").render(
            grfid=GRFID,
            version=major * 10000 + minor * 100 + patch,
            min_compatible_version=0,
            railtypes=[railtypes()[r] for r in used_rts],
            badges=badges,
        ),
        _env.get_template("procedures.nml.j2").render(
            shape_procs={_shape_proc(v.ottd_length) for v in vs if is_articulated(v.ottd_length)}
        ),
    ]
    for v in vs:
        parts.append(vehicle_nml(v, strings))

    out_dir.mkdir(parents=True, exist_ok=True)
    nml = out_dir / f"{paths.GRF_NAME}.nml"
    nml.write_text("".join(parts), encoding="utf-8")
    strings.write(out_dir / "lang")
    return nml


def compile_grf(nml: Path, grf: Path | None = None) -> Path:
    grf = grf or paths.BUILD / f"{paths.GRF_NAME}.grf"
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
    return grf
