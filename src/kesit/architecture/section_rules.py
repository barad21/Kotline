"""Cut vs projection classification and section shape generation."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon, box

from kesit.config import DrawingConfig
from kesit.geometry.intersections import intersection_interval_s, intersects
from kesit.geometry.projection import project_bounds
from kesit.geometry.section_line import SectionLine
from kesit.geometry.vectors import Vec2
from kesit.models import (
    ElementKind,
    IntersectionRecord,
    PlanElement,
    SectionMode,
    SectionShape,
    ShapeKind,
)


def classify_element(
    section: SectionLine,
    element: PlanElement,
    config: DrawingConfig,
) -> SectionMode:
    tol = config.intersection_tolerance_mm
    if intersects(section, element.geometry, tol):
        return SectionMode.CUT

    _, _, d_min, d_max = project_bounds(section, element.geometry)
    if d_max <= 0:
        return SectionMode.IGNORE
    if d_min > config.section_depth_mm:
        return SectionMode.IGNORE
    return SectionMode.PROJECT


def element_depth_mm(
    section: SectionLine,
    element: PlanElement,
    mode: SectionMode,
) -> float:
    if mode == SectionMode.CUT:
        return 0.0
    _, _, d_min, _ = project_bounds(section, element.geometry)
    return max(d_min, 0.0)


def _projected_sd(section: SectionLine, geometry) -> list[tuple[float, float]]:
    """Project a geometry's vertices into (s, d) section coordinates."""
    if geometry.geom_type == "LineString":
        coords = list(geometry.coords)
    elif hasattr(geometry, "exterior"):
        coords = list(geometry.exterior.coords)
    else:
        minx, miny, maxx, maxy = geometry.bounds
        coords = [(minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy)]
    return [section.project_point(Vec2(x, y)) for x, y in coords]


def _depth_at_extreme_s(
    section: SectionLine,
    geometry,
    *,
    want_max: bool,
) -> float | None:
    """Depth (perpendicular distance) of the vertex with the min/max s value.

    Used so a projected wall's two emitted edges carry their own front/back
    depth rather than sharing one nearest-corner value for the whole element.
    """
    sd = _projected_sd(section, geometry)
    if not sd:
        return None
    chosen = (max if want_max else min)(sd, key=lambda p: p[0])
    return max(chosen[1], 0.0)


def _rect_shape(
    s_min: float,
    s_max: float,
    z_min: float,
    z_max: float,
    kind: ShapeKind,
    element_id: str,
    config: DrawingConfig,
    mode: SectionMode,
    depth_mm: float,
    hatch: bool = False,
) -> SectionShape:
    css = {
        ShapeKind.CUT: "cut-line",
        ShapeKind.PROJECTION: "projection-line",
        ShapeKind.OPENING: "opening",
        ShapeKind.BASELINE: "baseline",
    }[kind]
    lw = config.cut_lineweight if kind == ShapeKind.CUT else config.projection_lineweight
    return SectionShape(
        kind=kind,
        geometry=box(s_min, z_min, s_max, z_max),
        element_id=element_id,
        lineweight=lw,
        hatch=hatch,
        css_class=css,
        depth_mm=depth_mm,
        section_mode=mode,
    )


def generate_shapes_for_element(
    section: SectionLine,
    element: PlanElement,
    mode: SectionMode,
    config: DrawingConfig,
) -> tuple[list[SectionShape], IntersectionRecord | None]:
    tol = config.intersection_tolerance_mm
    interval = intersection_interval_s(section, element.geometry, tol)
    depth_mm = element_depth_mm(section, element, mode)
    record = None
    if interval:
        record = IntersectionRecord(
            element_id=element.id,
            s_min=interval[0],
            s_max=interval[1],
            mode=mode,
            depth_mm=depth_mm,
        )

    if mode == SectionMode.IGNORE:
        return [], record

    if interval is None:
        s_min, s_max, _, _ = project_bounds(section, element.geometry)
    else:
        s_min, s_max = interval

    shapes: list[SectionShape] = []

    if element.kind == ElementKind.WALL:
        z_top = config.wall_height_mm
        if mode == SectionMode.CUT:
            shapes.append(
                _rect_shape(
                    s_min, s_max, 0, z_top, ShapeKind.CUT, element.id, config, mode, depth_mm, hatch=True
                )
            )
        else:
            for s, want_max in ((s_min, False), (s_max, True)):
                edge_depth = _depth_at_extreme_s(section, element.geometry, want_max=want_max)
                shapes.append(
                    SectionShape(
                        kind=ShapeKind.PROJECTION,
                        geometry=LineString([(s, 0), (s, z_top)]),
                        element_id=element.id,
                        lineweight=config.projection_lineweight,
                        css_class="projection-line",
                        depth_mm=edge_depth if edge_depth is not None else depth_mm,
                        section_mode=mode,
                    )
                )

    elif element.kind == ElementKind.COLUMN:
        z_top = config.storey_height_mm
        if mode == SectionMode.CUT:
            shapes.append(
                _rect_shape(
                    s_min, s_max, 0, z_top, ShapeKind.CUT, element.id, config, mode, depth_mm, hatch=True
                )
            )
        else:
            shapes.append(
                _rect_shape(s_min, s_max, 0, z_top, ShapeKind.PROJECTION, element.id, config, mode, depth_mm)
            )

    elif element.kind in (ElementKind.DOOR, ElementKind.OPENING):
        z0 = config.door_sill_height_mm
        z1 = config.door_height_mm
        shapes.append(
            _rect_shape(s_min, s_max, z0, z1, ShapeKind.OPENING, element.id, config, mode, depth_mm)
        )

    elif element.kind == ElementKind.WINDOW:
        z0 = config.window_sill_height_mm
        z1 = config.window_head_height_mm
        kind = ShapeKind.OPENING if mode == SectionMode.CUT else ShapeKind.PROJECTION
        shapes.append(
            _rect_shape(s_min, s_max, z0, z1, kind, element.id, config, mode, depth_mm)
        )

    elif element.kind == ElementKind.FURNITURE:
        # Best-effort projected outline for fixtures/footprint, from floor to a
        # waist-height band so it reads as a low object behind the cut.
        z0 = 0.0
        z1 = config.window_sill_height_mm
        shapes.append(
            _rect_shape(s_min, s_max, z0, z1, ShapeKind.PROJECTION, element.id, config, mode, depth_mm)
        )

    elif element.kind == ElementKind.SLAB:
        shapes.append(
            SectionShape(
                kind=ShapeKind.BASELINE,
                geometry=LineString([(0, 0), (section.section_length(), 0)]),
                element_id=element.id,
                lineweight=config.projection_lineweight,
                css_class="baseline",
                depth_mm=0.0,
                section_mode=SectionMode.CUT,
            )
        )

    return shapes, record
