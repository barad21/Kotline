from pathlib import Path

from kesit.architecture.layer_mapping import LayerMapping, classify_layer, match_layer
from kesit.architecture.plan_builder import build_elements_from_inventory
from kesit.cad_io.dxf_reader import read_dxf
from kesit.config import load_config
from kesit.generation.section_generator import generate_section
from kesit.geometry.section_line import SectionLine
from kesit.models import ShapeKind
from kesit.fixtures.floorplan_expectations import (
    FLOORPLAN_ENTITY_COUNT,
    FLOORPLAN_LAYER_COUNT,
    MIN_CUT_SHAPES,
    MIN_OPENING_SHAPES,
    REQUIRE_BASELINE,
)

ROOT = Path(__file__).resolve().parents[1]


def test_layer_suffix_wildcard():
    mapping = LayerMapping(walls=["*A-WALL"])
    assert match_layer("xref-Bishop-Overland-08$0$A-WALL", "*A-WALL")
    assert classify_layer("xref-Bishop-Overland-08$0$A-WALL", mapping) == "walls"


def test_floorplan_end_to_end():
    config_path = ROOT / "config" / "floorplan.yaml"
    dxf_path = ROOT / "sample-files" / "dxf" / "dxf-parser" / "floorplan.dxf"

    raw = read_dxf(dxf_path)
    assert raw.total_entities == FLOORPLAN_ENTITY_COUNT
    assert len(raw.layers) == FLOORPLAN_LAYER_COUNT

    config = load_config(config_path, dxf_insunits=raw.insunits)
    inventory = read_dxf(dxf_path, convert_geometry=True, unit_context=config.units)
    elements, mapping_counts, wall_stats, _ = build_elements_from_inventory(inventory, config)

    assert mapping_counts.get("walls", 0) > 0
    assert wall_stats["paired_lines"] + wall_stats["closed_polys"] >= MIN_CUT_SHAPES

    section = SectionLine.from_tuples(
        config.section.p0,
        config.section.p1,
        config.section.view_point,
    )
    result = generate_section(
        elements,
        section,
        config,
        detected_layers=inventory.layers,
        layer_mapping_results=mapping_counts,
        wall_extraction=wall_stats,
    )

    cut_shapes = [s for s in result.shapes if s.kind == ShapeKind.CUT]
    opening_shapes = [s for s in result.shapes if s.kind == ShapeKind.OPENING]
    baseline_shapes = [s for s in result.shapes if s.kind == ShapeKind.BASELINE]

    assert len(cut_shapes) >= MIN_CUT_SHAPES
    assert len(opening_shapes) >= MIN_OPENING_SHAPES
    if REQUIRE_BASELINE:
        assert len(baseline_shapes) >= 1
    assert len(result.diagnostics.detected_layers) == FLOORPLAN_LAYER_COUNT
