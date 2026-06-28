"""Render section shapes to tkinter canvas."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from kesit.models import SectionShape, ShapeKind
from kesit.rendering.coords import world_to_screen
from kesit.rendering.depth_colors import depth_to_fill, depth_to_stroke
from kesit.ui import theme


def draw_section_shapes(
    canvas,
    shapes: list[SectionShape],
    scale: float,
    offset_x: float,
    offset_y: float,
    canvas_height: int,
    z_min: float,
    z_max: float,
    depth_gradient: bool = False,
    section_depth_mm: float = 5000.0,
) -> None:
    draw_list = shapes
    if depth_gradient:
        draw_list = sorted(
            shapes,
            key=lambda s: (s.depth_mm if s.depth_mm is not None else 0.0),
            reverse=True,
        )
    for shape in draw_list:
        _draw_shape(
            canvas,
            shape,
            scale,
            offset_x,
            offset_y,
            canvas_height,
            z_min,
            z_max,
            depth_gradient=depth_gradient,
            section_depth_mm=section_depth_mm,
        )


def _flip_z(z: float, z_min: float, z_max: float) -> float:
    return z_max - z


def _draw_shape(
    canvas,
    shape: SectionShape,
    scale: float,
    offset_x: float,
    offset_y: float,
    canvas_height: int,
    z_min: float,
    z_max: float,
    depth_gradient: bool = False,
    section_depth_mm: float = 5000.0,
) -> None:
    geom = shape.geometry
    kind = shape.kind

    if depth_gradient:
        fill_color = depth_to_fill(shape.depth_mm, section_depth_mm, kind)
        stroke_color = depth_to_stroke(shape.depth_mm, section_depth_mm, kind)
        hatch_color = depth_to_stroke(shape.depth_mm, section_depth_mm, kind)
    else:
        fill_color = theme.CUT_FILL
        stroke_color = theme.LINE_CUT if kind in (ShapeKind.CUT, ShapeKind.OPENING, ShapeKind.BASELINE) else theme.LINE_PROJ
        hatch_color = theme.GRID

    if kind == ShapeKind.CUT and isinstance(geom, Polygon):
        coords = list(geom.exterior.coords)
        flat = []
        for s, z in coords:
            zf = _flip_z(z, z_min, z_max)
            sx, sy = world_to_screen(s, zf, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)
            flat.extend([sx, sy])
        if len(flat) >= 6:
            canvas.create_polygon(
                *flat,
                fill=fill_color if depth_gradient else theme.CUT_FILL,
                outline=stroke_color,
                width=2,
                tags="section",
            )
            _draw_hatch(
                canvas,
                geom.bounds,
                scale,
                offset_x,
                offset_y,
                canvas_height,
                z_min,
                z_max,
                hatch_color=hatch_color if depth_gradient else theme.GRID,
            )

    elif kind in (ShapeKind.OPENING, ShapeKind.PROJECTION) and isinstance(geom, Polygon):
        coords = list(geom.exterior.coords)
        flat = []
        dash = () if kind == ShapeKind.PROJECTION else (4, 2)
        for s, z in coords:
            zf = _flip_z(z, z_min, z_max)
            sx, sy = world_to_screen(s, zf, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)
            flat.extend([sx, sy])
        if len(flat) >= 6:
            if depth_gradient:
                # The vivid depth gradient lives in the fill; a slightly lighter
                # outline of the same hue keeps the edge crisp (and enables
                # occlusion via the far->near draw order).
                canvas.create_polygon(
                    *flat, fill=fill_color, outline=stroke_color, width=1, dash=dash, tags="section",
                )
            else:
                color = theme.LINE_PROJ if kind == ShapeKind.PROJECTION else theme.LINE_CUT
                canvas.create_polygon(*flat, outline=color, fill="", width=1, dash=dash, tags="section")

    elif isinstance(geom, LineString):
        if not depth_gradient:
            color = theme.LINE_CUT if kind == ShapeKind.BASELINE else theme.LINE_PROJ
        else:
            # Projection/opening lines carry the full saturated gradient so
            # front/back depth variation reads clearly.
            color = depth_to_fill(shape.depth_mm, section_depth_mm, kind)
        width = 2 if kind == ShapeKind.BASELINE else 1
        flat = []
        for s, z in geom.coords:
            zf = _flip_z(z, z_min, z_max)
            sx, sy = world_to_screen(s, zf, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)
            flat.extend([sx, sy])
        if len(flat) >= 4:
            canvas.create_line(*flat, fill=color, width=width, tags="section")


def _draw_hatch(
    canvas,
    bounds,
    scale,
    offset_x,
    offset_y,
    canvas_height,
    z_min,
    z_max,
    hatch_color: str = theme.GRID,
) -> None:
    s0, z0, s1, z1 = bounds
    spacing = 50
    z0f = _flip_z(z0, z_min, z_max)
    z1f = _flip_z(z1, z_min, z_max)
    z_start = min(z0f, z1f)
    z_end = max(z0f, z1f)
    s_start = min(s0, s1)
    s_end = max(s0, s1)
    step = spacing
    z = z_start
    while z < z_end:
        sx0, sy0 = world_to_screen(s_start, z, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)
        sx1, sy1 = world_to_screen(s_end, z + step, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)
        canvas.create_line(sx0, sy0, sx1, sy1, fill=hatch_color, width=1, tags="section")
        z += step


def _nice_round(value: float) -> float:
    """Round a length down to a 1/2/5 x 10^n step for a tidy scale bar."""
    if value <= 0:
        return 1.0
    import math

    exp = math.floor(math.log10(value))
    base = 10 ** exp
    for mult in (5, 2, 1):
        if mult * base <= value:
            return float(mult * base)
    return float(base)


def draw_section_chrome(
    canvas,
    scale: float,
    offset_x: float,
    offset_y: float,
    canvas_height: int,
    z_min: float,
    z_max: float,
    s_min: float,
    s_max: float,
    levels: list[tuple[str, float]],
    ground_label: str,
) -> None:
    """Draw the ground datum, vertical z-axis with mm labels, and level markers."""
    axis_s = s_min

    def to_screen(s: float, z: float) -> tuple[float, float]:
        zf = _flip_z(z, z_min, z_max)
        return world_to_screen(s, zf, scale, offset_x, offset_y, flip_y=False, canvas_height=canvas_height)

    # Vertical z-axis at the left edge of content.
    ax0 = to_screen(axis_s, z_min)
    ax1 = to_screen(axis_s, z_max)
    canvas.create_line(*ax0, *ax1, fill=theme.LINE_PROJ, width=1, tags="chrome")

    # Ground datum at z = 0 (spanning the section width).
    g0 = to_screen(s_min, 0.0)
    g1 = to_screen(s_max, 0.0)
    canvas.create_line(*g0, *g1, fill=theme.LINE_CUT, width=1, tags="chrome")
    canvas.create_text(
        g1[0] + 6, g1[1], text=ground_label, anchor="w",
        fill=theme.TEXT_MUTED, font=theme.FONT_MONO, tags="chrome",
    )

    seen_z: set[int] = set()
    for label, z in levels:
        if z <= 0:
            continue
        key = int(round(z))
        if key in seen_z:
            continue
        seen_z.add(key)
        p0 = to_screen(s_min, z)
        p1 = to_screen(s_max, z)
        canvas.create_line(*p0, *p1, fill=theme.GRID, width=1, dash=(2, 4), tags="chrome")
        # Tick + mm label on the axis.
        canvas.create_line(p0[0] - 4, p0[1], p0[0], p0[1], fill=theme.LINE_PROJ, width=1, tags="chrome")
        canvas.create_text(
            p0[0] - 6, p0[1], text=f"{key}", anchor="e",
            fill=theme.TEXT_MUTED, font=theme.FONT_MONO, tags="chrome",
        )
        # Level name on the right.
        canvas.create_text(
            p1[0] + 6, p1[1], text=label, anchor="w",
            fill=theme.TEXT_MUTED, font=theme.FONT_MONO, tags="chrome",
        )


def draw_scale_bar(
    canvas,
    scale: float,
    canvas_width: int,
    canvas_height: int,
    scale_label: str,
) -> None:
    """Draw a real-mm scale bar (fixed screen overlay, bottom-left)."""
    if scale <= 0:
        return
    target_px = 90.0
    length_mm = _nice_round(target_px / scale)
    bar_px = length_mm * scale
    x0 = 16
    y0 = canvas_height - 20
    x1 = x0 + bar_px
    canvas.create_line(x0, y0, x1, y0, fill=theme.TEXT_PRIMARY, width=2, tags="chrome")
    for x in (x0, x1):
        canvas.create_line(x, y0 - 4, x, y0 + 4, fill=theme.TEXT_PRIMARY, width=2, tags="chrome")
    canvas.create_text(
        x0, y0 - 8, text=f"{int(length_mm)} mm", anchor="sw",
        fill=theme.TEXT_PRIMARY, font=theme.FONT_MONO, tags="chrome",
    )
    canvas.create_text(
        x1 + 10, y0, text=scale_label, anchor="w",
        fill=theme.TEXT_MUTED, font=theme.FONT_MONO, tags="chrome",
    )


def section_bounds(shapes: list[SectionShape]) -> tuple[float, float, float, float]:
    if not shapes:
        return 0, 0, 1000, 3000
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for shape in shapes:
        gx0, gy0, gx1, gy1 = shape.geometry.bounds
        minx = min(minx, gx0)
        miny = min(miny, gy0)
        maxx = max(maxx, gx1)
        maxy = max(maxy, gy1)
    return minx, miny, maxx, maxy
