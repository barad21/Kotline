"""Coordinate transforms for canvas rendering."""

from __future__ import annotations


def fit_bounds(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    width: int,
    height: int,
    padding: float = 20,
) -> tuple[float, float, float]:
    """Return scale, offset_x, offset_y to fit world bounds in canvas."""
    world_w = max(maxx - minx, 1e-6)
    world_h = max(maxy - miny, 1e-6)
    scale = min((width - 2 * padding) / world_w, (height - 2 * padding) / world_h)
    offset_x = padding - minx * scale
    offset_y = padding - miny * scale
    return scale, offset_x, offset_y


def world_to_screen(
    x: float,
    y: float,
    scale: float,
    offset_x: float,
    offset_y: float,
    flip_y: bool = False,
    canvas_height: int = 0,
) -> tuple[float, float]:
    sx = x * scale + offset_x
    sy = y * scale + offset_y
    if flip_y:
        sy = canvas_height - sy
    return sx, sy


def screen_to_world(
    sx: float,
    sy: float,
    scale: float,
    offset_x: float,
    offset_y: float,
    flip_y: bool = False,
    canvas_height: int = 0,
) -> tuple[float, float]:
    if flip_y:
        sy = canvas_height - sy
    x = (sx - offset_x) / scale if scale else 0
    y = (sy - offset_y) / scale if scale else 0
    return x, y
