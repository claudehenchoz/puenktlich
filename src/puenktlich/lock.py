"""`data/ids.lock`: the NewGRF ids that saved games depend on.

Item id = `grf_id * 8 + livery index`, so a vehicle's `grf_id` and the order of its
liveries must never change once released. The lock file records both; `problems()`
(run by `pk lint` and the tests) compares the data against it, and `pk lock` appends
new vehicles and liveries. Entries are never rewritten or removed by the tool.
"""

from __future__ import annotations

import yaml

from puenktlich import paths
from puenktlich.schema import Vehicle, vehicles

LOCK = paths.DATA / "ids.lock"
HEADER = (
    "# Saved-game ids: vehicle id -> grf_id and liveries in item-id order.\n"
    "# Written by `pk lock` (append-only). Never edit or remove entries: games saved with\n"
    "# an earlier release would get the wrong vehicles.\n"
)

Lock = dict[str, dict]


def entry(v: Vehicle) -> dict:
    return {"grf_id": v.grf_id, "liveries": [livery.id for livery in v.liveries]}


def load() -> Lock:
    if not LOCK.exists():
        return {}
    return yaml.safe_load(LOCK.read_text(encoding="utf-8")) or {}


def problems(vs: dict[str, Vehicle] | None = None, lock: Lock | None = None) -> list[str]:
    """Differences between the data and the lock that would break saved games,
    plus anything not locked yet."""
    vs = vehicles() if vs is None else vs
    lock = load() if lock is None else lock
    out: list[str] = []
    for vid, locked in lock.items():
        v = vs.get(vid)
        if v is None:
            out.append(f"{vid}: in data/ids.lock but no longer in data/vehicles (released vehicles can't be removed)")
            continue
        if v.grf_id != locked["grf_id"]:
            out.append(f"{vid}: grf_id changed {locked['grf_id']} -> {v.grf_id} (permanent, see data/ids.lock)")
        now = [livery.id for livery in v.liveries]
        was = locked["liveries"]
        if now[: len(was)] != was:
            out.append(f"{vid}: liveries are append-only; locked order {was}, now {now}")
        elif len(now) > len(was):
            out.append(f"{vid}: new liveries {now[len(was) :]} not locked yet — run `pk lock`")
    locked_grf = {e["grf_id"]: vid for vid, e in lock.items()}
    for vid, v in vs.items():
        if vid in lock:
            continue
        if v.grf_id in locked_grf:
            out.append(f"{vid}: grf_id {v.grf_id} is locked for {locked_grf[v.grf_id]} and can't be reused")
        else:
            out.append(f"{vid}: not locked yet — run `pk lock`")
    return out


def update() -> list[str]:
    """Append new vehicles and liveries to the lock. Refuses while the data conflicts with it.
    Returns what was added."""
    vs, lock = vehicles(), load()
    conflicts = [p for p in problems(vs, lock) if "not locked yet" not in p]
    if conflicts:
        raise ValueError("\n".join(conflicts))
    added: list[str] = []
    for vid, v in vs.items():
        new = entry(v)
        if vid not in lock:
            added.append(f"{vid}: grf_id {v.grf_id}, liveries {new['liveries']}")
        elif new != lock[vid]:
            added.append(f"{vid}: liveries {new['liveries'][len(lock[vid]['liveries']) :]}")
        lock[vid] = new
    if added or not LOCK.exists():
        ordered = dict(sorted(lock.items(), key=lambda kv: (kv[1]["grf_id"], kv[0])))
        body = yaml.safe_dump(ordered, sort_keys=False, default_flow_style=None, allow_unicode=True)
        LOCK.write_text(HEADER + body, encoding="utf-8")
    return added
