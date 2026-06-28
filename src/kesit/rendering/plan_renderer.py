"""Render plan geometry to tkinter canvas."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from kesit.cad_io.dxf_reader import DxfInventory, DxfEntity
from kesit.ui import theme


def collect_plan_bounds(inventory: DxfInventory) -> tuple[float, float, float, float]:
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for entity in inventory.entities:
        if entity.geometry is None:
            continue
        bx0, by0, bx1, by1 = entity.geometry.bounds
        minx = min(minx, bx0)
        miny = min(miny, by0)
        maxx = max(maxx, bx1)
        maxy = max(maxy, by1)
    if minx == float("inf"):
        return 0, 0, 100, 100
    return minx, miny, maxx, maxy


def draw_plan_entity(
    canvas,
    entity: DxfEntity,
    scale: float,
    offset_x: float,
    offset_y: float,
    canvas_height: int,
    tag: str = "plan",
    color: str | None = None,
    width: int = 1,
) -> None:
    from kesit.rendering.coords import world_to_screen

    geom = entity.geometry
    if geom is None:
        return
    if entity.dxftype not in ("LINE", "LWPOLYLINE"):
        return
    line_color = color or theme.LINE_PLAN

    if isinstance(geom, Polygon):
        coords = list(geom.exterior.coords)
        flat = []
        for x, y in coords:
            sx, sy = world_to_screen(x, y, scale, offset_x, offset_y, flip_y=True, canvas_height=canvas_height)
            flat.extend([sx, sy])
        if len(flat) >= 4:
            canvas.create_line(*flat, fill=line_color, width=width, tags=tag)
    elif isinstance(geom, LineString):
        coords = list(geom.coords)
        flat = []
        for x, y in coords:
            sx, sy = world_to_screen(x, y, scale, offset_x, offset_y, flip_y=True, canvas_height=canvas_height)
            flat.extend([sx, sy])
        if len(flat) >= 4:
            canvas.create_line(*flat, fill=line_color, width=width, tags=tag)


def draw_inventory(
    canvas,
    inventory: DxfInventory,
    scale: float,
    offset_x: float,
    offset_y: float,
    canvas_height: int,
    highlight_layer: str | None = None,
) -> None:
    dim_color = theme.GRID if highlight_layer else theme.LINE_PLAN

    for entity in inventory.entities:
        if entity.dxftype not in ("LINE", "LWPOLYLINE"):
            continue
        if highlight_layer and entity.layer == highlight_layer:
            continue
        draw_plan_entity(
            canvas, entity, scale, offset_x, offset_y, canvas_height,
            color=dim_color, width=1,
        )

    if highlight_layer:
        for entity in inventory.entities:
            if entity.layer != highlight_layer:
                continue
            if entity.dxftype not in ("LINE", "LWPOLYLINE"):
                continue
            draw_plan_entity(
                canvas, entity, scale, offset_x, offset_y, canvas_height,
                tag="plan_highlight",
                color=theme.LAYER_HIGHLIGHT,
                width=3,
            )
