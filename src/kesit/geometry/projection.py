"""Projection of plan geometry into section (s, d) coordinates."""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry

from kesit.geometry.section_line import SectionLine
from kesit.geometry.vectors import Vec2


def project_point(section: SectionLine, x: float, y: float) -> tuple[float, float]:
    return section.project_point(Vec2(x, y))


def project_coords(section: SectionLine, coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [section.project_point(Vec2(x, y)) for x, y in coords]


def project_bounds(
    section: SectionLine,
    geometry: BaseGeometry,
) -> tuple[float, float, float, float]:
    """Return s_min, s_max, d_min, d_max for geometry bounds corners."""
    minx, miny, maxx, maxy = geometry.bounds
    corners = [(minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy)]
    sd = [section.project_point(Vec2(x, y)) for x, y in corners]
    s_vals = [s for s, _ in sd]
    d_vals = [d for _, d in sd]
    return min(s_vals), max(s_vals), min(d_vals), max(d_vals)
