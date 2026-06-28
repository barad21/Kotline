"""SVG section export."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from kesit.config import DrawingConfig
from kesit.models import SectionShape, ShapeKind


def _bounds(shapes: list[SectionShape]) -> tuple[float, float, float, float]:
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
    pad_x = (maxx - minx) * 0.05 or 50
    pad_y = (maxy - miny) * 0.05 or 50
    return minx - pad_x, miny - pad_y, maxx + pad_x, maxy + pad_y


def _flip_y(y: float, z_min: float, z_max: float) -> float:
    return z_min + z_max - y


def _path_from_polygon(poly: Polygon, z_min: float, z_max: float) -> str:
    coords = list(poly.exterior.coords)
    if not coords:
        return ""
    parts = []
    x0, y0 = coords[0]
    parts.append(f"M {_flip_y(y0, z_min, z_max):.3f} {x0:.3f}")
    for x, y in coords[1:]:
        parts.append(f"L {_flip_y(y, z_min, z_max):.3f} {x:.3f}")
    parts.append("Z")
    return " ".join(parts)


def _path_from_line(line: LineString, z_min: float, z_max: float) -> str:
    coords = list(line.coords)
    if len(coords) < 2:
        return ""
    x0, y0 = coords[0]
    parts = [f"M {_flip_y(y0, z_min, z_max):.3f} {x0:.3f}"]
    for x, y in coords[1:]:
        parts.append(f"L {_flip_y(y, z_min, z_max):.3f} {x:.3f}")
    return " ".join(parts)


def _geometry_to_path(geom: BaseGeometry, z_min: float, z_max: float) -> str:
    if geom.geom_type == "Polygon":
        return _path_from_polygon(geom, z_min, z_max)
    if geom.geom_type == "LineString":
        return _path_from_line(geom, z_min, z_max)
    if geom.geom_type == "MultiPolygon":
        return " ".join(_path_from_polygon(g, z_min, z_max) for g in geom.geoms)
    return ""


def _hatch_pattern(spacing: float, z_min: float, z_max: float) -> str:
    s = spacing
    return (
        f'<pattern id="hatch" patternUnits="userSpaceOnUse" width="{s}" height="{s}">'
        f'<path d="M 0 0 L {s} {s}" stroke="#333" stroke-width="0.5"/>'
        f"</pattern>"
    )


def export_svg(
    shapes: list[SectionShape],
    path: str | Path,
    config: DrawingConfig,
    title: str = "Section",
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ctx = config.units
    display_shapes = shapes
    scale = 1.0
    if ctx.output.value != "mm":
        from dataclasses import replace

        from shapely.affinity import scale as shapely_scale

        scaled = []
        mm_to_out = ctx.internal_to_output(1.0)
        for shape in shapes:
            scaled.append(
                replace(
                    shape,
                    geometry=shapely_scale(shape.geometry, mm_to_out, mm_to_out, origin=(0, 0)),
                )
            )
        display_shapes = scaled
        scale = mm_to_out

    s_min, z_min, s_max, z_max = _bounds(display_shapes)
    width = s_max - s_min
    height = z_max - z_min

    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {width:.2f} {height:.2f}",
        width=f"{width:.2f}",
        height=f"{height:.2f}",
    )

    style = ET.SubElement(svg, "style")
    style.text = """
      .cut-line { fill: #cccccc; stroke: #000; stroke-width: 2; }
      .projection-line { fill: none; stroke: #666; stroke-width: 0.5; }
      .opening { fill: none; stroke: #000; stroke-width: 1; stroke-dasharray: 4 2; }
      .baseline { fill: none; stroke: #000; stroke-width: 1.5; }
      .hatch { fill: url(#hatch); stroke: #000; stroke-width: 1.5; }
      .annotation { fill: #333; font-size: 12px; font-family: sans-serif; }
    """

    defs = ET.SubElement(svg, "defs")
    hatch_spacing = config.hatch_spacing_mm * scale if scale != 1.0 else ctx.internal_to_output(config.hatch_spacing_mm)
    defs.append(ET.fromstring(_hatch_pattern(hatch_spacing, z_min, z_max)))

    group = ET.SubElement(svg, "g", transform=f"translate({-s_min:.3f}, 0)")

    for shape in display_shapes:
        d = _geometry_to_path(shape.geometry, z_min, z_max)
        if not d:
            continue
        css = shape.css_class or shape.kind.value
        attrs = {
            "d": d,
            "class": css,
        }
        if shape.hatch and shape.kind == ShapeKind.CUT:
            attrs["class"] = "cut-line hatch"
        ET.SubElement(group, "path", attrs)

    title_el = ET.SubElement(svg, "title")
    title_el.text = title

    tree = ET.ElementTree(svg)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=True)
