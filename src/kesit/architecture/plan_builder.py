"""Build PlanElement list from DXF inventory."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from kesit.architecture.layer_mapping import LayerMapping, classify_layer, is_skipped_layer
from kesit.architecture.wall_extraction import extract_walls_from_lines
from kesit.cad_io.dxf_reader import DxfInventory
from kesit.config import DrawingConfig
from kesit.geometry.cleanup import remove_zero_length_lines
from kesit.models import ElementKind, PlanElement

# Entity types we still cannot turn into section geometry.
_UNSUPPORTED_TYPES = ("POINT",)


def _iter_base_geoms(geom: BaseGeometry | None) -> list[BaseGeometry]:
    """Flatten (Multi*/GeometryCollection) geometries into base parts."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type in (
        "GeometryCollection",
        "MultiLineString",
        "MultiPolygon",
        "MultiPoint",
    ):
        out: list[BaseGeometry] = []
        for part in geom.geoms:
            out.extend(_iter_base_geoms(part))
        return out
    return [geom]


def build_elements_from_inventory(
    inventory: DxfInventory,
    config: DrawingConfig,
) -> tuple[list[PlanElement], dict[str, int], dict[str, int], list[str]]:
    mapping = LayerMapping.from_dict(config.layer_mapping)
    skip_types = set(config.skip_entity_types)
    warnings: list[str] = []
    mapping_counts: dict[str, int] = {}
    wall_stats = {"closed_polys": 0, "paired_lines": 0, "orphan_lines": 0}

    wall_lines: list[LineString] = []
    wall_polys: list[Polygon] = []
    opening_items: list[tuple[str, str, BaseGeometry, ElementKind]] = []
    window_geoms: list[tuple[str, BaseGeometry]] = []
    column_items: list[tuple[str, str, BaseGeometry]] = []
    furniture_items: list[tuple[str, str, BaseGeometry]] = []
    slab_added = False
    elements: list[PlanElement] = []
    unclassified = 0

    def bump(role: str) -> None:
        mapping_counts[role] = mapping_counts.get(role, 0) + 1

    for entity in inventory.entities:
        if entity.dxftype in skip_types:
            if classify_layer(entity.layer, mapping) == "annotations":
                mapping_counts["annotations_skipped"] = mapping_counts.get("annotations_skipped", 0) + 1
            continue

        if entity.dxftype in _UNSUPPORTED_TYPES:
            warnings.append(f"Unsupported entity {entity.dxftype} on layer {entity.layer}")
            continue

        if entity.geometry is None:
            continue

        role = classify_layer(entity.layer, mapping)
        if role is None:
            unclassified += 1
            continue
        if is_skipped_layer(entity.layer, mapping):
            mapping_counts["annotations_skipped"] = mapping_counts.get("annotations_skipped", 0) + 1
            continue

        handle = entity.handle or entity.layer
        for geom in _iter_base_geoms(entity.geometry):
            if role == "walls":
                if isinstance(geom, Polygon):
                    wall_polys.append(geom)
                elif isinstance(geom, LineString):
                    wall_lines.append(geom)

            elif role in ("openings", "doors"):
                line = geom.boundary if isinstance(geom, Polygon) else geom
                opening_items.append((role, handle, line, ElementKind.DOOR))

            elif role == "windows":
                window_geoms.append((handle, geom))

            elif role == "columns":
                column_items.append(("columns", handle, geom))

            elif role == "structure":
                # Structural members read as cut poché at storey height (column rule).
                column_items.append(("structure", handle, geom))

            elif role in ("fixtures", "footprint"):
                furniture_items.append((role, handle, geom))

            elif role == "slab" and not slab_added:
                elements.append(
                    PlanElement(id="slab_baseline", kind=ElementKind.SLAB, geometry=geom, layer=entity.layer)
                )
                slab_added = True
                bump("slab")

    cleaned_lines, removed = remove_zero_length_lines(wall_lines, config.snap_tolerance_mm / 10)
    if removed:
        warnings.append(f"{removed} zero-length wall lines removed")

    wall_stats["closed_polys"] = len(wall_polys)
    for i, poly in enumerate(wall_polys):
        elements.append(
            PlanElement(id=f"wall_poly_{i}", kind=ElementKind.WALL, geometry=poly, layer="A-WALL")
        )

    extraction = extract_walls_from_lines(
        cleaned_lines,
        angle_tolerance=config.angle_tolerance,
        min_offset=config.wall_pair_min_offset_mm,
        max_offset=config.wall_pair_max_offset_mm,
    )
    wall_stats["paired_lines"] = extraction.paired_count
    wall_stats["orphan_lines"] = len(extraction.orphan_lines)
    for i, poly in enumerate(extraction.walls):
        elements.append(
            PlanElement(id=f"wall_pair_{i}", kind=ElementKind.WALL, geometry=poly, layer="A-WALL")
        )
    realized_walls = len(wall_polys) + len(extraction.walls)
    if realized_walls:
        mapping_counts["walls"] = realized_walls

    for i, (role, handle, geom, kind) in enumerate(opening_items):
        elements.append(PlanElement(id=f"opening_{handle}_{i}", kind=kind, geometry=geom, layer="A-OPENING"))
        bump(role)

    for i, (handle, geom) in enumerate(window_geoms):
        g = geom.boundary if isinstance(geom, Polygon) else geom
        elements.append(PlanElement(id=f"window_{handle}_{i}", kind=ElementKind.WINDOW, geometry=g, layer="A-HEADER"))
        bump("windows")

    for i, (role, handle, geom) in enumerate(column_items):
        elements.append(PlanElement(id=f"column_{handle}_{i}", kind=ElementKind.COLUMN, geometry=geom, layer="A-COLS"))
        bump(role)

    for i, (role, handle, geom) in enumerate(furniture_items):
        g = geom.boundary if isinstance(geom, Polygon) else geom
        elements.append(PlanElement(id=f"furniture_{handle}_{i}", kind=ElementKind.FURNITURE, geometry=g, layer="A-FURN"))
        bump(role)

    if unclassified:
        mapping_counts["unclassified"] = unclassified

    return elements, mapping_counts, wall_stats, warnings
