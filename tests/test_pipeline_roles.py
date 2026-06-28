"""Tests for role wiring, DXF entity conversion, mapping alias, per-shape depth."""

from __future__ import annotations

import ezdxf
from shapely.geometry import GeometryCollection, LineString, Polygon

from kesit.architecture.layer_mapping import LayerMapping
from kesit.architecture.plan_builder import build_elements_from_inventory
from kesit.architecture.section_rules import classify_element, generate_shapes_for_element
from kesit.cad_io.dxf_reader import DxfEntity, DxfInventory
from kesit.cad_io.entity_converter import convert_entity
from kesit.fixtures.synthetic_plan import synthetic_config, synthetic_section
from kesit.models import ElementKind, SectionMode, ShapeKind
from kesit.units import UnitContext


def _inventory(entities: list[DxfEntity], layers: list[str]) -> DxfInventory:
    return DxfInventory(
        path="memory.dxf",
        dxf_version="AC1027",
        insunits=None,
        insunits_unit=None,
        entity_counts={},
        layer_entity_counts={},
        layers=layers,
        entities=entities,
        block_names=[],
    )


def test_mapping_alias_furniture_to_fixtures():
    mapping = LayerMapping.from_dict({"furniture": ["A-FURN"]})
    assert "A-FURN" in mapping.fixtures

    merged = LayerMapping.from_dict({"fixtures": ["X"], "furniture": ["Y"]})
    assert merged.fixtures == ["X", "Y"]


def test_columns_and_furniture_roles_become_elements():
    config = synthetic_config()
    config.layer_mapping = {
        "columns": ["A-COLS"],
        "fixtures": ["A-FURN"],
        "footprint": ["A-FOOT"],
    }
    s = config.units.plan_to_internal(1.0)

    column = Polygon([(480 * s, 380 * s), (520 * s, 380 * s), (520 * s, 420 * s), (480 * s, 420 * s)])
    furniture = Polygon([(600 * s, 600 * s), (650 * s, 600 * s), (650 * s, 650 * s), (600 * s, 650 * s)])
    footprint = LineString([(0, 0), (100 * s, 0), (100 * s, 100 * s)])

    inv = _inventory(
        [
            DxfEntity("LWPOLYLINE", "A-COLS", column, "1"),
            DxfEntity("LWPOLYLINE", "A-FURN", furniture, "2"),
            DxfEntity("LWPOLYLINE", "A-FOOT", footprint, "3"),
        ],
        ["A-COLS", "A-FURN", "A-FOOT"],
    )
    elements, counts, _stats, _warnings = build_elements_from_inventory(inv, config)
    kinds = [e.kind for e in elements]

    assert ElementKind.COLUMN in kinds
    assert kinds.count(ElementKind.FURNITURE) == 2  # fixtures + footprint
    assert counts.get("columns") == 1
    assert counts.get("fixtures") == 1
    assert counts.get("footprint") == 1


def test_entity_converter_arc_circle_insert():
    ctx = UnitContext.from_config({"source": "mm", "parameters": "mm", "output": "mm"})
    doc = ezdxf.new()
    msp = doc.modelspace()

    arc = msp.add_arc(center=(0, 0, 0), radius=100, start_angle=0, end_angle=90)
    arc_geom = convert_entity(arc, ctx)
    assert isinstance(arc_geom, LineString)
    assert len(arc_geom.coords) >= 3

    circle = msp.add_circle(center=(0, 0, 0), radius=50)
    circle_geom = convert_entity(circle, ctx)
    assert isinstance(circle_geom, Polygon)
    assert circle_geom.area > 0

    block = doc.blocks.new(name="DOORBLK")
    block.add_line((0, 0), (10, 0))
    block.add_lwpolyline([(0, 0), (10, 0), (10, 10)])
    insert = msp.add_blockref("DOORBLK", (5, 5))
    insert_geom = convert_entity(insert, ctx)
    assert isinstance(insert_geom, GeometryCollection)
    assert len(insert_geom.geoms) >= 1


def test_projected_wall_has_per_edge_depth_variation():
    config = synthetic_config()
    section = synthetic_section()
    s = config.units.plan_to_internal(1.0)
    # A slanted wall fully east of the vertical section line, so its two
    # endpoints sit at different perpendicular distances (front vs back).
    from kesit.models import PlanElement

    geom = LineString([(300 * s, 150 * s), (400 * s, 650 * s)])
    element = PlanElement(id="slanted_wall", kind=ElementKind.WALL, geometry=geom)

    mode = classify_element(section, element, config)
    assert mode == SectionMode.PROJECT

    shapes, _record = generate_shapes_for_element(section, element, mode, config)
    proj = [sh for sh in shapes if sh.kind == ShapeKind.PROJECTION]
    assert len(proj) == 2
    depths = sorted(sh.depth_mm for sh in proj)
    assert all(d > 0 for d in depths)
    assert depths[0] != depths[1]
