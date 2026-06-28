"""Convert DXF entities to Shapely geometry in internal mm."""

from __future__ import annotations

import math

from shapely.geometry import GeometryCollection, LineString, Polygon

from kesit.units import UnitContext

_ARC_SEGMENTS = 32


def _convert_xy(x: float, y: float, ctx: UnitContext) -> tuple[float, float]:
    return ctx.plan_to_internal(x), ctx.plan_to_internal(y)


def convert_line(entity, ctx: UnitContext) -> LineString:
    x0, y0, _ = entity.dxf.start
    x1, y1, _ = entity.dxf.end
    p0 = _convert_xy(x0, y0, ctx)
    p1 = _convert_xy(x1, y1, ctx)
    return LineString([p0, p1])


def convert_lwpolyline(entity, ctx: UnitContext) -> LineString | Polygon:
    points = [_convert_xy(x, y, ctx) for x, y, *_ in entity.get_points("xy")]
    if len(points) < 2:
        raise ValueError("LWPOLYLINE has fewer than 2 points")
    if entity.closed and len(points) >= 3:
        return Polygon(points)
    return LineString(points)


def convert_polyline(entity, ctx: UnitContext) -> LineString | Polygon:
    points = [_convert_xy(p[0], p[1], ctx) for p in entity.points()]
    if len(points) < 2:
        raise ValueError("POLYLINE has fewer than 2 points")
    if entity.is_closed and len(points) >= 3:
        return Polygon(points)
    return LineString(points)


def _arc_points(cx: float, cy: float, r: float, a0: float, a1: float) -> list[tuple[float, float]]:
    if a1 < a0:
        a1 += 360.0
    span = a1 - a0
    steps = max(2, int(_ARC_SEGMENTS * span / 360.0))
    pts = []
    for i in range(steps + 1):
        ang = math.radians(a0 + span * i / steps)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def convert_arc(entity, ctx: UnitContext) -> LineString:
    cx, cy, _ = entity.dxf.center
    r = entity.dxf.radius
    pts = _arc_points(cx, cy, r, entity.dxf.start_angle, entity.dxf.end_angle)
    return LineString([_convert_xy(x, y, ctx) for x, y in pts])


def convert_circle(entity, ctx: UnitContext) -> Polygon:
    cx, cy, _ = entity.dxf.center
    r = entity.dxf.radius
    pts = _arc_points(cx, cy, r, 0.0, 360.0)
    return Polygon([_convert_xy(x, y, ctx) for x, y in pts])


def convert_insert(entity, ctx: UnitContext) -> GeometryCollection:
    """Explode a block reference into its primitive geometries."""
    geoms = []
    for child in entity.virtual_entities():
        try:
            geom = convert_entity(child, ctx)
        except ValueError:
            continue
        if geom is None or geom.is_empty:
            continue
        if isinstance(geom, GeometryCollection):
            geoms.extend(g for g in geom.geoms if not g.is_empty)
        else:
            geoms.append(geom)
    return GeometryCollection(geoms)


def convert_entity(entity, ctx: UnitContext):
    dxftype = entity.dxftype()
    if dxftype == "LINE":
        return convert_line(entity, ctx)
    if dxftype == "LWPOLYLINE":
        return convert_lwpolyline(entity, ctx)
    if dxftype == "POLYLINE":
        return convert_polyline(entity, ctx)
    if dxftype == "ARC":
        return convert_arc(entity, ctx)
    if dxftype == "CIRCLE":
        return convert_circle(entity, ctx)
    if dxftype == "INSERT":
        return convert_insert(entity, ctx)
    raise ValueError(f"Unsupported entity type for conversion: {dxftype}")
