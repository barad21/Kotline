"""Intersections between section line and plan geometry."""

from __future__ import annotations

from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from kesit.geometry.section_line import SectionLine
from kesit.geometry.vectors import Vec2


def intersects(section: SectionLine, geometry: BaseGeometry, tolerance: float = 0.0) -> bool:
    line = section.as_shapely_line()
    if tolerance > 0:
        line = line.buffer(tolerance, cap_style=2, join_style=2)
    return line.intersects(geometry)


def intersection_interval_s(
    section: SectionLine,
    geometry: BaseGeometry,
    tolerance: float = 0.0,
) -> tuple[float, float] | None:
    """Return s-range where geometry meets the section line, or None."""
    line = section.as_shapely_line()
    query = geometry
    if tolerance > 0:
        query = geometry.buffer(tolerance, cap_style=2, join_style=2)
        line = section.as_shapely_line().buffer(tolerance, cap_style=2, join_style=2)

    if not line.intersects(query):
        return None

    intersection = line.intersection(query)
    if intersection.is_empty:
        return None

    geoms = []
    if hasattr(intersection, "geoms"):
        geoms = list(intersection.geoms)
    else:
        geoms = [intersection]

    s_values: list[float] = []
    for geom in geoms:
        if geom.geom_type == "Point":
            s_values.append(section.project_point(Vec2(geom.x, geom.y))[0])
        elif geom.geom_type == "LineString":
            for x, y in geom.coords:
                s_values.append(section.project_point(Vec2(x, y))[0])
        elif geom.geom_type == "MultiPoint":
            for pt in geom.geoms:
                s_values.append(section.project_point(Vec2(pt.x, pt.y))[0])

    if not s_values:
        s_min, s_max, _, _ = _bounds_sd(section, geometry)
        if intersects(section, geometry, tolerance):
            return s_min, s_max
        return None

    return min(s_values), max(s_values)


def _bounds_sd(section: SectionLine, geometry: BaseGeometry) -> tuple[float, float, float, float]:
    from kesit.geometry.projection import project_bounds

    return project_bounds(section, geometry)
