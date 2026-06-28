"""Synthetic plan fixture for Phase 1 tests and PoC."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from kesit.config import DrawingConfig
from kesit.geometry.section_line import SectionLine
from kesit.models import ElementKind, PlanElement
from kesit.units import UnitContext


def synthetic_config() -> DrawingConfig:
    ctx = UnitContext.from_config(
        {
            "source": "cm",
            "parameters": "cm",
            "output": "cm",
        }
    )
    return DrawingConfig(
        units=ctx,
        wall_height_mm=ctx.param_to_internal(280),
        storey_height_mm=ctx.param_to_internal(300),
        door_height_mm=ctx.param_to_internal(210),
        window_sill_height_mm=ctx.param_to_internal(90),
        window_head_height_mm=ctx.param_to_internal(240),
        section_depth_mm=ctx.param_to_internal(500),
        snap_tolerance_mm=ctx.plan_to_internal(2),
        intersection_tolerance_mm=ctx.plan_to_internal(0.5),
    )


def synthetic_section() -> SectionLine:
    ctx = synthetic_config().units
    return SectionLine.from_tuples(
        p0=ctx.convert_point_plan_to_internal(200, 100),
        p1=ctx.convert_point_plan_to_internal(200, 700),
        view_point=ctx.convert_point_plan_to_internal(500, 400),
    )


def synthetic_elements() -> list[PlanElement]:
    u = synthetic_config().units
    scale = u.plan_to_internal(1.0)

    wall_a = Polygon(
        [
            (200 * scale, 100 * scale),
            (220 * scale, 100 * scale),
            (220 * scale, 700 * scale),
            (200 * scale, 700 * scale),
        ]
    )
    wall_b = Polygon(
        [
            (900 * scale, 100 * scale),
            (920 * scale, 100 * scale),
            (920 * scale, 700 * scale),
            (900 * scale, 700 * scale),
        ]
    )
    column = Polygon(
        [
            (480 * scale, 380 * scale),
            (520 * scale, 380 * scale),
            (520 * scale, 420 * scale),
            (480 * scale, 420 * scale),
        ]
    )
    door = LineString([(200 * scale, 350 * scale), (200 * scale, 440 * scale)])
    window = LineString([(900 * scale, 300 * scale), (900 * scale, 420 * scale)])

    return [
        PlanElement(id="wall_a", kind=ElementKind.WALL, geometry=wall_a),
        PlanElement(id="wall_b", kind=ElementKind.WALL, geometry=wall_b),
        PlanElement(id="column_1", kind=ElementKind.COLUMN, geometry=column),
        PlanElement(id="door_1", kind=ElementKind.DOOR, geometry=door),
        PlanElement(id="window_1", kind=ElementKind.WINDOW, geometry=window),
    ]
