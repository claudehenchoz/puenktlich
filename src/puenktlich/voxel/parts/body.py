"""Car bodies: a parametric shell with rounded roof, tumblehome and shaped ends.

The shell is defined implicitly: a voxel is inside when it lies within the
cross-section (half-width, roof curve) *and* behind both end surfaces. End
surfaces are described by `EndShape`, which sets how far the face sits back from
the nominal end at each height and lateral offset. That one description covers a
flat Swiss coach end and a rounded Lok 2000 nose.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from puenktlich.voxel import palette as P
from puenktlich.voxel.model import CENTRE_Y, Model


@dataclass
class CrossSection:
    floor: float = 14  # z of body underside
    roof: float = 50  # z of roof top (centre line)
    half_width: float = 19.5  # 19.5 -> y 1..40, 40 voxels wide
    roof_radius: float = 7  # radius of the roof/side rounding
    tumblehome: float = 1.0  # inward lean of the side below `tumble_from` (voxels)
    tumble_from: float = 24  # z above which the side is vertical
    # chamfered upper body (panorama coaches): from `chamfer_from` the side slopes inwards by
    # `chamfer_inset` voxels at the roof, a straight bevel instead of the round roof corner
    chamfer_from: float | None = None
    chamfer_inset: float = 0

    def mask(
        self,
        Y: np.ndarray,
        Z: np.ndarray,
        cy: float = CENTRE_Y,
        floor: np.ndarray | float | None = None,
        roof: np.ndarray | float | None = None,
    ) -> np.ndarray:
        """floor/roof override the section's (arrays broadcast over x: double-deck cars)."""
        floor = self.floor if floor is None else floor
        roof = self.roof if roof is None else roof
        dy = np.abs(Y - cy)
        hw = np.full(np.broadcast(Y, Z, floor).shape, self.half_width)
        # tumblehome: linearly narrower towards the floor
        below = self.tumble_from > Z
        frac = np.clip((self.tumble_from - Z) / np.maximum(1.0, self.tumble_from - floor), 0, 1)
        hw = np.where(below, hw - self.tumblehome * frac, hw)
        if self.chamfer_from is not None:
            t = np.clip((Z - self.chamfer_from) / np.maximum(1.0, roof - self.chamfer_from), 0, 1)
            hw = hw - self.chamfer_inset * t
        inside = (dy <= hw) & (floor <= Z) & (roof >= Z)
        # roof rounding at the corners
        r = self.roof_radius
        cy, cz = self.half_width - r, roof - r
        corner = (dy > cy) & (cz < Z)
        inside &= ~corner | ((dy - cy) ** 2 + (Z - cz) ** 2 <= r * r)
        return inside


@dataclass
class EndShape:
    """Set-back of the end face from the nominal end, in voxels.

    setback(z, dy) = slope(z) + plan(dy) + bottom(z)
      slope:  windscreen rake — 0 below `rake_from`, rising to `rake` at the roof
              along a power curve (`rake_curve` 1 = straight, 2 = rounded nose).
      plan:   plan-view rounding of the corners, radius `corner_radius`.
      bottom: undercut of the lower edge (skirt/plough), `undercut` over `undercut_height`.
    """

    rake: float = 0
    rake_from: float = 30
    rake_curve: float = 1.6
    corner_radius: float = 3
    undercut: float = 0
    undercut_height: float = 4
    # "power": rake * t**rake_curve; "ellipse": a quarter ellipse (vertical at rake_from,
    # flat at the roof), the bulbous noses of modern multiple units
    profile: str = "power"
    # plan taper of pointed noses (FV-Dosto): setback plan_depth * (dy / half_width)**plan_power,
    # combined with the windscreen rake by max() (the nose recedes either way); 0 = off
    plan_depth: float = 0
    plan_power: float = 5

    def setback(self, Z: np.ndarray, dy: np.ndarray, cs: CrossSection) -> np.ndarray:
        span = max(1.0, cs.roof - self.rake_from)
        t = np.clip((Z - self.rake_from) / span, 0, 1)
        if self.profile == "ellipse":
            sb = self.rake * (1 - np.sqrt(np.maximum(1 - t * t, 0)))
        else:
            sb = self.rake * t**self.rake_curve
        if self.plan_depth > 0:
            sb = np.maximum(sb, self.plan_depth * np.clip(dy / cs.half_width, 0, 1) ** self.plan_power)
        rc = self.corner_radius
        if rc > 0:
            edge = np.clip(dy - (cs.half_width - rc), 0, rc)
            sb = sb + (rc - np.sqrt(np.maximum(rc * rc - edge * edge, 0)))
        if self.undercut > 0:
            u = (
                np.clip((self.rake_from - Z) / self.undercut_height, 0, 1)
                if self.profile == "ellipse"
                else np.clip((cs.floor + self.undercut_height - Z) / self.undercut_height, 0, 1)
            )
            sb = sb + self.undercut * u
        return sb


@dataclass
class Shell:
    x_rear: float
    x_front: float
    section: CrossSection = field(default_factory=CrossSection)
    front: EndShape = field(default_factory=EndShape)
    rear: EndShape | None = None  # None = same as front (symmetric vehicle)
    # optional floor / roof height along x (double-deck cars: low lower deck between the
    # bogies, lower cab roof). Called with the X coordinate array, returns heights.
    floor_at: Callable[[np.ndarray], np.ndarray] | None = None
    roof_at: Callable[[np.ndarray], np.ndarray] | None = None

    def mask(self, model: Model) -> np.ndarray:
        X, Y, Z = model.coords()
        cs = self.section
        floor = self.floor_at(X) if self.floor_at else None
        roof = self.roof_at(X) if self.roof_at else None
        inside = cs.mask(Y, Z, model.cy, floor, roof)
        dy = np.abs(Y - model.cy)
        rear = self.rear or self.front
        inside = inside & (self.x_front - self.front.setback(Z, dy, cs) >= X)
        inside = inside & (self.x_rear + rear.setback(Z, dy, cs) <= X)
        return inside

    @property
    def length(self) -> float:
        return self.x_front - self.x_rear

    @property
    def mid(self) -> float:
        return (self.x_front + self.x_rear) / 2


def side_band(model: Model, x0: float, x1: float, z0: float, z1: float) -> np.ndarray:
    """Mask covering both body sides between x0..x1 and z0..z1 (for windows, grilles…)."""
    return model.box(x0, x1, 0, model.d.shape[1], z0, z1)


def end_band(
    model: Model, shell: Shell, z0: float, z1: float, half_width: float, front: bool = True, depth: float = 20
) -> np.ndarray:
    """Mask covering the end face region of the shell (windscreens, lamps…)."""
    if front:
        x0, x1 = shell.x_front - depth, shell.x_front + 1
    else:
        x0, x1 = shell.x_rear, shell.x_rear + depth
    return model.centred_box(x0, x1, half_width, z0, z1)


def face_mask(model: Model, front: bool = True, depth: float = 2) -> np.ndarray:
    """The skin seen from one end: for every (y, z) the first `depth` voxels from the front
    (high x) or rear. Paints windscreens and lamps on raked noses without touching the sides."""
    occ = model.d != 0
    sx = occ.shape[0]
    X, _, _ = model.coords()
    has = occ.any(axis=0)[None, :, :]
    if front:
        edge = (sx - 1 - np.argmax(occ[::-1], axis=0))[None, :, :]
        return has & (edge >= X) & (edge - depth < X)
    edge = np.argmax(occ, axis=0)[None, :, :]
    return has & (edge <= X) & (edge + depth > X)


def end_span(shell: Shell, front: bool, a: float, b: float) -> tuple[float, float]:
    """x-range measured inwards from one end: `a`..`b` voxels behind the front (or rear) face.
    Lets recipes place cab windows/doors once and mirror them to the other end."""
    if front:
        return shell.x_front - b, shell.x_front - a
    return shell.x_rear + a, shell.x_rear + b


def side_skin(model: Model) -> np.ndarray:
    """Filled voxels with an empty neighbour outwards in y (the visible body sides)."""
    occ = model.d != 0
    out = np.zeros_like(occ)
    cy = int(model.cy)
    out[:, : cy + 1] = occ[:, : cy + 1] & ~np.pad(occ, ((0, 0), (1, 0), (0, 0)))[:, : cy + 1]
    out[:, cy + 1 :] = occ[:, cy + 1 :] & ~np.pad(occ, ((0, 0), (0, 1), (0, 0)))[:, cy + 2 :]
    return out


def door_outline(
    model: Model, x0: float, x1: float, z0: float, z1: float, colour: int, sill: float = 1, lintel: float = 1
) -> None:
    """Recessed seam around a door leaf x0..x1, z0..z1 on both sides (one voxel wide at the
    jambs; `sill` / `lintel` = seam height at the bottom / top, 0 for none)."""
    model.inset(side_band(model, x0, x1, z0, z1) & ~side_band(model, x0 + 1, x1 - 1, z0 + sill, z1 - lintel), colour)


def louvres(
    model: Model,
    x0: float,
    x1: float,
    z0: float,
    z1: float,
    *,
    horizontal: bool = False,
    pitch: int = 3,
    back: int = P.DARK_GREY,
    slat: int = P.MID_GREY,
) -> None:
    """Recessed ventilation grille on both sides: dark panel with lighter slats every `pitch`
    voxels (vertical slats by default; horizontal=True for slats along the body)."""
    X, _, Z = model.coords()
    panel = side_band(model, x0, x1, z0, z1)
    model.inset(panel, back)
    model.paint(panel & (((Z if horizontal else X).astype(int) % pitch) == 0), slat)


def rounded_window(model: Model, x0: float, x1: float, z0: float, z1: float, frame: int = P.BLACK) -> None:
    """Rounded-rectangle window on both sides: frame with clipped corners, glass inset."""
    X, _, Z = model.coords()
    outer = side_band(model, x0, x1, z0, z1)
    corner = ((x0 + 1 > X) | (x1 - 1 <= X)) & ((z0 + 1 > Z) | (z1 - 1 <= Z))
    model.paint(outer & ~corner, frame)
    model.inset(side_band(model, x0 + 1, x1 - 1, z0 + 1, z1 - 1), P.GLASS)


def gangway(model: Model, x_end: float, front: bool, half_width: float, z0: float, z1: float, colour: int) -> None:
    """Dark gangway bellows standing 3 voxels proud of an end face."""
    xa, xb = (x_end + 1, x_end + 4) if front else (x_end - 3, x_end)
    model.solid(model.centred_box(xa, xb, half_width, z0, z1), colour)


def windows_in_gaps(
    model: Model,
    keep: list[tuple[float, float]],
    width: float,
    pitch: float,
    z0: float,
    z1: float,
    frame: int = P.BLACK,
) -> None:
    """Rounded windows spread evenly over every free stretch between the `keep` x-ranges
    (doors, joints, cab): as many as fit at `pitch`, `width` wide (voxels)."""
    keep = sorted(keep)
    for (_, a), (b, _) in zip(keep, keep[1:], strict=False):
        n = int((b - a + (pitch - width)) // pitch)
        if n <= 0:
            continue
        gap = (b - a - n * width) / (n + 1)
        for i in range(n):
            x0 = a + gap + i * (width + gap)
            rounded_window(model, x0, x0 + width, z0, z1, frame=frame)
