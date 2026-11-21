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

from puenktlich.voxel.model import CENTRE_Y, Model


@dataclass
class CrossSection:
    floor: float = 14  # z of body underside
    roof: float = 50  # z of roof top (centre line)
    half_width: float = 19.5  # 19.5 -> y 1..40, 40 voxels wide
    roof_radius: float = 7  # radius of the roof/side rounding
    tumblehome: float = 1.0  # inward lean of the side below `tumble_from` (voxels)
    tumble_from: float = 24  # z above which the side is vertical

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

    def setback(self, Z: np.ndarray, dy: np.ndarray, cs: CrossSection) -> np.ndarray:
        span = max(1.0, cs.roof - self.rake_from)
        t = np.clip((Z - self.rake_from) / span, 0, 1)
        if self.profile == "ellipse":
            sb = self.rake * (1 - np.sqrt(np.maximum(1 - t * t, 0)))
        else:
            sb = self.rake * t**self.rake_curve
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
