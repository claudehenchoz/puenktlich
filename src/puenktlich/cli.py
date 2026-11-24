"""`pk` — the Pünktlich command line. Run `uv run pk --help`."""

from __future__ import annotations

import shutil
from typing import Annotated

import typer

from puenktlich import paths

app = typer.Typer(help="Pünktlich asset pipeline: data -> voxels -> sprites -> NML -> GRF.", no_args_is_help=True)

IdsArg = Annotated[list[str] | None, typer.Argument(help="Vehicle ids (default: all)")]


def _select(ids: list[str] | None):
    from puenktlich.schema import vehicles

    vs = vehicles()
    if not ids:
        return list(vs.values())
    unknown = [i for i in ids if i not in vs]
    if unknown:
        raise typer.BadParameter(f"unknown vehicle id(s): {', '.join(unknown)}. Known: {', '.join(vs)}")
    return [vs[i] for i in ids]


@app.command("list")
def list_vehicles() -> None:
    """List vehicles with their key stats."""
    for v in _select(None):
        stats = f"{v.intro_year}  {v.max_speed_kmh:>3} km/h  L{v.ottd_length}"
        typer.echo(f"{v.id:<16} {v.grf_id:>5}  {v.operator:<8} {v.kind:<12} {stats}  {v.name['en']}")


@app.command()
def vox(ids: IdsArg = None) -> None:
    """Build voxel models (every variant) into build/vox/<id>/base/."""
    from puenktlich.models import write_models

    for v in _select(ids):
        _, files = write_models(v)
        for p in files:
            typer.echo(f"{v.id}: {paths.rel(p)}")


JobsOpt = Annotated[
    int | None, typer.Option("--jobs", "-j", help="Vehicles rendered at once (default: half the cores, or PK_JOBS)")
]


@app.command()
def render(
    ids: IdsArg = None,
    force: Annotated[bool, typer.Option(help="Re-render even if up to date")] = False,
    jobs: JobsOpt = None,
    draft: Annotated[
        bool, typer.Option(help="4x only with GoRender's fast sampler, into build/sprites_draft/")
    ] = False,
) -> None:
    """Variants -> hill tilt (Cargopositor) -> GoRender 1x/2x/4x (24 views + hills) -> overrides -> lint."""
    import os
    import time

    from puenktlich.pipeline import render_vehicles

    failed = False
    start = time.perf_counter()
    totals: dict[str, float] = {}
    for r in render_vehicles(_select(ids), force=force, draft=draft, jobs=jobs):
        n = r.sheets_rendered
        typer.echo(f"{r.vehicle_id}: {n} sheet(s) rendered" if n else f"{r.vehicle_id}: up to date")
        for o in r.overrides:
            typer.echo(f"  override: {paths.rel(o)}")
        for pr in r.problems:
            typer.secho(f"  {pr}", fg="red")
        failed |= bool(r.problems)
        for stage, secs in r.timings.items():
            totals[stage] = totals.get(stage, 0.0) + secs
    if os.environ.get("PK_TIMING"):
        stages = ", ".join(f"{k} {v:.1f}" for k, v in totals.items())
        typer.echo(f"timing: {time.perf_counter() - start:.1f} s wall; summed over vehicles: {stages}")
    if failed:
        raise typer.Exit(1)


@app.command()
def preview(
    ids: IdsArg = None,
    render_first: Annotated[bool, typer.Option("--render/--no-render")] = True,
    draft: Annotated[
        bool, typer.Option(help="Quick look while modelling: 4x only, fast sampler, <id>_draft.png (not for release)")
    ] = False,
    jobs: JobsOpt = None,
) -> None:
    """Render and write a review contact sheet to build/previews/<id>.png."""
    from puenktlich.pipeline import DRAFT_SCALES, sprite_dir
    from puenktlich.render import SCALES
    from puenktlich.sprites import contact_sheet

    if render_first:
        render(ids, force=False, jobs=jobs, draft=draft)
    for v in _select(ids):
        name = f"{v.id}_draft.png" if draft else f"{v.id}.png"
        scales = DRAFT_SCALES if draft else SCALES
        out = contact_sheet(v, sprite_dir(v, draft), paths.BUILD_PREVIEWS / name, scales=scales)
        typer.echo(f"{v.id}: {out}")


@app.command()
def build(
    ids: IdsArg = None,
    skip_render: Annotated[bool, typer.Option("--skip-render")] = False,
    jobs: JobsOpt = None,
) -> None:
    """Full build: lint data, render changed models, generate NML, compile build/puenktlich.grf.

    With vehicle ids it builds only those into build/puenktlich_partial.grf (for a quick
    `pk ingame <ids>`); build/puenktlich.grf always holds every vehicle."""
    from puenktlich.nml.generate import compile_grf, generate, partial_grf

    lint(sprites=False, models=True)
    if not skip_render:
        render(ids, force=False, jobs=jobs, draft=False)
    from puenktlich.tracks.build import build_tracks

    if ids:
        nml = generate(paths.BUILD / "nml_partial", only=ids)
        grf = compile_grf(nml, partial_grf(), vehicle_ids=ids)
    else:
        from puenktlich.models import prune_caches

        grf = compile_grf(generate())
        freed = prune_caches()
        if freed:
            typer.echo(f"pruned {freed // 2**20} MiB of unused cache entries")
    typer.secho(f"built {paths.rel(grf)} ({grf.stat().st_size // 1024} KiB)", fg="green")
    tracks = build_tracks()
    typer.secho(f"built {paths.rel(tracks)} ({tracks.stat().st_size // 1024} KiB)", fg="green")


@app.command()
def lint(
    sprites: Annotated[bool, typer.Option(help="Also lint rendered sprite sheets")] = True,
    models: Annotated[bool, typer.Option(help="Also check the voxel models (puenktlich/checks.py)")] = True,
) -> None:
    """Validate data files, the voxel models and (optionally) rendered sprites."""
    from puenktlich.schema import validate_all, vehicles
    from puenktlich.sprites import lint_vehicle

    problems = validate_all()
    if models and not problems:
        from puenktlich.checks import check_all

        problems += check_all()
    if sprites:
        for v in vehicles().values():
            problems += lint_vehicle(v)
    for p in problems:
        typer.secho(p, fg="red")
    if problems:
        raise typer.Exit(1)
    typer.secho("lint ok", fg="green")


@app.command()
def lock() -> None:
    """Record new vehicles and liveries in data/ids.lock (the ids saved games depend on)."""
    from puenktlich.lock import LOCK, update

    try:
        added = update()
    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(1) from e
    for a in added:
        typer.echo(f"locked {a}")
    typer.secho(f"{paths.rel(LOCK)}: {len(added)} new entr{'y' if len(added) == 1 else 'ies'}", fg="green")


@app.command()
def new(
    operator: Annotated[str, typer.Argument(help="Operator id from data/operators.yaml, e.g. sbb")],
    vehicle_id: Annotated[str, typer.Argument(help="New vehicle id, e.g. re420 (lower case, permanent)")],
    kind: Annotated[str, typer.Option(help="locomotive | coach | control_car | emu | wagon | bus")] = "locomotive",
    name: Annotated[str | None, typer.Option(help='Display name, e.g. "SBB Re 420"')] = None,
) -> None:
    """Start a new vehicle: YAML with the next free grf_id, a recipe stub that already builds, and
    a REFERENCE.md. Then fill in the TODOs (see .claude/skills/new-vehicle/SKILL.md)."""
    from puenktlich.scaffold import new_vehicle

    try:
        files = new_vehicle(operator, vehicle_id, kind, name or vehicle_id)
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e
    for f in files:
        typer.echo(f"created {paths.rel(f)}")
    typer.echo(f"next: uv run pk elevation {vehicle_id}   (seconds)  ->  uv run pk preview {vehicle_id} --draft")
    typer.echo("when the ids are final: uv run pk lock")


@app.command()
def coverage(write: Annotated[bool, typer.Option(help="Write docs/COMPLETENESS.md")] = True) -> None:
    """Report how much of the official fleet lists is implemented."""
    from puenktlich.completeness import coverage as cov
    from puenktlich.completeness import report_markdown

    for c in cov():
        typer.echo(f"{c.operator:<10} {len(c.done):>4}/{c.total:<4} {c.percent:5.1f}%")
    if write:
        (paths.ROOT / "docs" / "COMPLETENESS.md").write_text(report_markdown(), encoding="utf-8")


@app.command()
def install(
    openttd_dir: Annotated[
        str | None,
        typer.Argument(
            help="OpenTTD data dir (default: ~/.local/share/openttd on Linux, Documents\\OpenTTD on Windows)"
        ),
    ] = None,
) -> None:
    """Copy build/puenktlich.grf and build/puenktlich_tracks.grf into OpenTTD's newgrf folder."""
    from pathlib import Path

    from puenktlich.ingame import personal_dir

    base = Path(openttd_dir).expanduser() if openttd_dir else personal_dir()
    dst_dir = base / "newgrf"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in (paths.BUILD / f"{paths.GRF_NAME}.grf", paths.BUILD / "puenktlich_tracks.grf"):
        if src.exists():
            shutil.copy2(src, dst_dir / src.name)
            typer.echo(f"installed {dst_dir / src.name}")


def _cargo_loco(wagons: list) -> str:
    """First locomotive of the same gauge family as the wagons (standard / metre)."""
    from puenktlich.schema import vehicles

    family = wagons[0].railtype.split("_")[0]
    for v in vehicles().values():
        if v.kind == "locomotive" and v.railtype.split("_")[0] == family:
            return f"{v.name['en']} ({v.liveries[0].name['en']})"
    raise typer.BadParameter(f"no {family}-gauge locomotive to pull {wagons[0].id}")


@app.command("elevation")
def elevation_cmd(ids: IdsArg = None) -> None:
    """Orthographic side/front/rear views of every car (build/previews/<id>_elevation.png),
    for comparing proportions with photos. Seconds, no GoRender."""
    from puenktlich.elevation import elevation

    for v in _select(ids):
        typer.echo(f"{v.id}: {elevation(v)}")


@app.command()
def ingame(
    ids: IdsArg = None,
    zoom: Annotated[list[str] | None, typer.Option(help="Zoom levels: 1x, 2x, 4x or all (repeatable)")] = None,
    parallel: Annotated[bool, typer.Option(help="Run all zoom levels at once (heavy on laptops)")] = False,
    scene: Annotated[
        str,
        typer.Option(
            help="loop | infra (crossing, bridge, tunnel, depots, rack) | cargo (wagons loading) | road (buses)"
        ),
    ] = "loop",
    shots: Annotated[int, typer.Option(help="Screenshots per zoom level (one per game month, ~67 s each)")] = 3,
    all_liveries: Annotated[bool, typer.Option(help="Every livery of each vehicle, not just the first")] = False,
    with_: Annotated[
        list[str] | None,
        typer.Option("--with", help='Append a vehicle by exact in-game name, e.g. "Passenger Carriage" (repeatable)'),
    ] = None,
    baseset: Annotated[
        str | None,
        typer.Option(help="Base graphics set from OpenTTD's content downloads, e.g. abase (default: OpenGFX)"),
    ] = None,
) -> None:
    """Run OpenTTD headless with build/puenktlich.grf and screenshot the vehicles in-game.

    Builds a test loop with a ramp via a Game Script, runs one train of the selected
    vehicles in the given order (first livery each unless --all-liveries), turns it round
    after shot 3 (push-pull check) and writes screenshots to build/ingame/<zoom>/ (several
    zoom levels share one run in build/ingame/all/). Takes ~1 min per shot and zoom level."""
    from puenktlich.ingame import default_baseset, find_baseset, run
    from puenktlich.nml.generate import grf_for

    vs = _select(ids)
    grf = grf_for([v.id for v in vs])
    if grf is None:
        raise typer.BadParameter("build/puenktlich.grf missing — run `pk build` first")
    typer.echo(f"using {paths.rel(grf)}")
    if all_liveries:
        targets = [v.name["en"] for v in vs]
    else:
        targets = [f"{v.name['en']} ({v.liveries[0].name['en']})" for v in vs]
    if scene == "infra":
        zoom, shots = ["2x"], min(shots, 4)  # one run: overview + close-up shots
    if any(v.is_road for v in vs):
        scene = "road"  # buses always run on the road loop
    if scene == "cargo":
        # a fitting locomotive in front of two of each selected wagon
        targets = [_cargo_loco(vs)] + [t for t in targets for _ in range(2)]
        shots = max(shots, 4)
    zooms = zoom or ["4x"]  # 4x shows the most detail; ask for others explicitly
    if "all" in zooms:
        zooms = ["1x", "2x", "4x"]
    results = run(
        grf,
        targets,
        zooms,
        shots=shots,
        parallel=parallel,
        scene=scene,
        extras=with_,
        baseset=find_baseset(baseset) if baseset else default_baseset(),
    )
    failed = False
    for r in results:
        typer.secho(f"== {r.zoom}", bold=True)
        for line in r.script_lines:
            typer.echo(f"  {line}")
        for e in r.errors:
            typer.secho(f"  {e}", fg="red")
        for s in r.screenshots:
            typer.echo(f"  screenshot: {s}")
        failed |= bool(r.errors) or not r.screenshots
    if failed:
        raise typer.Exit(1)


@app.command("tracks-preview")
def tracks_preview_cmd(zoom: Annotated[int, typer.Option(help="1, 2 or 4")] = 4) -> None:
    """Contact sheet of the metre-gauge track GRF -> build/previews/tracks.png."""
    from puenktlich.tracks.preview import tracks_preview

    typer.echo(tracks_preview(paths.BUILD_PREVIEWS / "tracks.png", zoom))


@app.command()
def clean() -> None:
    """Delete build/."""
    shutil.rmtree(paths.BUILD, ignore_errors=True)


if __name__ == "__main__":
    app()
