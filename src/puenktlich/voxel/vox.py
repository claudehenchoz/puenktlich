"""Minimal MagicaVoxel .vox reader/writer.

Coordinate convention (matches GoRender's OpenTTD manifests):
    x = vehicle length (0 = rear, x_max = front)   default 126
    y = vehicle width                              default 40
    z = height (0 = rail level)                    default 48

Voxel values are TTD palette indices (1..255, 0 = empty). GoRender interprets the
index stored in the file directly as a TTD palette index, so we never remap. The
optional RGBA chunk is written purely so MagicaVoxel shows the right colours.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class VoxelGrid:
    data: np.ndarray  # shape (x, y, z), dtype uint8

    @classmethod
    def empty(cls, x: int = 126, y: int = 40, z: int = 48) -> VoxelGrid:
        return cls(np.zeros((x, y, z), dtype=np.uint8))

    @property
    def size(self) -> tuple[int, int, int]:
        return tuple(int(v) for v in self.data.shape)  # type: ignore[return-value]

    def count(self) -> int:
        return int(np.count_nonzero(self.data))

    def bounds(self) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]] | None:
        """Inclusive (min, max) per axis of occupied voxels, or None when empty."""
        idx = np.nonzero(self.data)
        if len(idx[0]) == 0:
            return None
        return tuple((int(a.min()), int(a.max())) for a in idx)  # type: ignore[return-value]


def _chunk(tag: bytes, content: bytes, children: bytes = b"") -> bytes:
    return tag + struct.pack("<ii", len(content), len(children)) + content + children


def write_vox(grid: VoxelGrid, path: Path, rgb_palette: list[tuple[int, int, int]] | None = None) -> None:
    """Write `grid` as a single-model .vox file (version 150)."""
    sx, sy, sz = grid.size
    if max(sx, sy, sz) > 256:
        raise ValueError(f"vox models are limited to 256 per axis, got {grid.size}")
    xs, ys, zs = np.nonzero(grid.data)
    cols = grid.data[xs, ys, zs]
    xyzi = np.stack([xs, ys, zs, cols], axis=1).astype(np.uint8)

    size = _chunk(b"SIZE", struct.pack("<iii", sx, sy, sz))
    voxels = _chunk(b"XYZI", struct.pack("<i", len(xyzi)) + xyzi.tobytes())
    children = size + voxels
    if rgb_palette is not None:
        # MagicaVoxel: RGBA entry k is used by colour index k+1.
        rgba = bytearray()
        for k in range(256):
            r, g, b = rgb_palette[(k + 1) % 256]
            rgba += bytes((r, g, b, 255))
        children += _chunk(b"RGBA", bytes(rgba))
    main = _chunk(b"MAIN", b"", children)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"VOX " + struct.pack("<i", 150) + main)


def read_vox(path: Path) -> VoxelGrid:
    """Read the first model of a .vox file (ignores scene graph / materials)."""
    buf = path.read_bytes()
    if buf[:4] != b"VOX ":
        raise ValueError(f"{path} is not a .vox file")
    pos = 8
    # MAIN header
    if buf[pos : pos + 4] != b"MAIN":
        raise ValueError(f"{path}: missing MAIN chunk")
    pos += 12
    size: tuple[int, int, int] | None = None
    grid: VoxelGrid | None = None
    while pos < len(buf):
        tag = buf[pos : pos + 4]
        n_content, n_children = struct.unpack_from("<ii", buf, pos + 4)
        body = pos + 12
        if tag == b"SIZE" and size is None:
            size = struct.unpack_from("<iii", buf, body)
        elif tag == b"XYZI" and grid is None:
            assert size is not None
            n = struct.unpack_from("<i", buf, body)[0]
            arr = np.frombuffer(buf, dtype=np.uint8, count=n * 4, offset=body + 4).reshape(n, 4)
            grid = VoxelGrid.empty(*size)
            grid.data[arr[:, 0], arr[:, 1], arr[:, 2]] = arr[:, 3]
        pos = body + n_content + n_children
    if grid is None:
        raise ValueError(f"{path}: no voxel data")
    return grid
