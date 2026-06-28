"""Extract wall polygons from paired parallel lines."""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from kesit.geometry.vectors import Vec2, angle_degrees


@dataclass
class WallExtractionResult:
    walls: list[Polygon]
    paired_count: int
    orphan_lines: list[LineString]
    closed_polys: int = 0


def _line_angle(line: LineString) -> float:
    x0, y0 = line.coords[0]
    x1, y1 = line.coords[-1]
    return angle_degrees(Vec2(x1 - x0, y1 - y0))


def _line_midpoint(line: LineString) -> tuple[float, float]:
    x0, y0 = line.coords[0]
    x1, y1 = line.coords[-1]
    return (x0 + x1) / 2, (y0 + y1) / 2


def _parallel_offset(line_a: LineString, line_b: LineString) -> float:
    x0, y0 = line_a.coords[0]
    x1, y1 = line_a.coords[-1]
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    mx, my = _line_midpoint(line_b)
    ax, ay = _line_midpoint(line_a)
    return abs((mx - ax) * nx + (my - ay) * ny)


def _angles_compatible(a1: float, a2: float, tolerance: float) -> bool:
    diff = abs((a1 - a2 + 180) % 180)
    return diff <= tolerance or abs(diff - 180) <= tolerance


def _wall_polygon_from_pair(line_a: LineString, line_b: LineString) -> Polygon:
    a0, a1 = line_a.coords[0], line_a.coords[-1]
    b0, b1 = line_b.coords[0], line_b.coords[-1]
    dist_a0_b = math.dist(a0, b0) + math.dist(a1, b1)
    dist_a0_b1 = math.dist(a0, b1) + math.dist(a1, b0)
    if dist_a0_b <= dist_a0_b1:
        ring = [a0, a1, b1, b0, a0]
    else:
        ring = [a0, a1, b0, b1, a0]
    return Polygon(ring)


def extract_walls_from_lines(
    lines: list[LineString],
    angle_tolerance: float = 2.0,
    min_offset: float = 50.0,
    max_offset: float = 300.0,
) -> WallExtractionResult:
    """Pair parallel lines into wall polygons."""
    unused = set(range(len(lines)))
    walls: list[Polygon] = []
    paired = 0

    indexed = [(i, lines[i], _line_angle(lines[i])) for i in unused]

    for i, line_a, ang_a in indexed:
        if i not in unused:
            continue
        best_j = None
        best_score = float("inf")
        for j, line_b, ang_b in indexed:
            if j == i or j not in unused:
                continue
            if not _angles_compatible(ang_a, ang_b, angle_tolerance):
                continue
            offset = _parallel_offset(line_a, line_b)
            if offset < min_offset or offset > max_offset:
                continue
            overlap = min(line_a.length, line_b.length)
            if overlap < min_offset:
                continue
            if offset < best_score:
                best_score = offset
                best_j = j
        if best_j is not None:
            poly = _wall_polygon_from_pair(line_a, lines[best_j])
            if poly.is_valid and not poly.is_empty:
                walls.append(poly)
                paired += 1
                unused.discard(i)
                unused.discard(best_j)

    orphans = [lines[i] for i in sorted(unused)]
    return WallExtractionResult(
        walls=walls,
        paired_count=paired,
        orphan_lines=orphans,
    )
