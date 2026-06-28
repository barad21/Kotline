"""Section generation pipeline shared by CLI and GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kesit.app.project_state import ProjectState
from kesit.architecture.layer_mapping import LayerMapping, classify_layer
from kesit.architecture.plan_builder import build_elements_from_inventory
from kesit.cad_io.dxf_reader import DxfInventory, read_dxf

# Entity types the converter/pipeline can turn into geometry.
_SUPPORTED_ENTITY_TYPES = frozenset(
    {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "INSERT"}
)
from kesit.config import DrawingConfig
from kesit.geometry.section_line import SectionLine
from kesit.generation.section_generator import SectionResult, generate_section
from kesit.models import PlanElement


@dataclass
class PipelineResult:
    elements: list[PlanElement]
    section_result: SectionResult
    inventory: DxfInventory
    config: DrawingConfig
    section_line: SectionLine
    mapping_counts: dict[str, int]
    wall_stats: dict[str, int]
    warnings: list[str]


def load_inventory(state: ProjectState, convert_geometry: bool = False) -> DxfInventory:
    if not state.dxf_path:
        raise ValueError("No DXF file loaded")
    path = Path(state.dxf_path)
    if convert_geometry:
        config = state.to_drawing_config()
        return read_dxf(path, convert_geometry=True, unit_context=config.units)
    inv = read_dxf(path)
    state.dxf_insunits = inv.insunits
    return inv


def run_pipeline(state: ProjectState) -> PipelineResult:
    if not state.is_ready_to_generate():
        raise ValueError("Project is missing DXF path or section definition")

    raw = read_dxf(state.dxf_path)
    state.dxf_insunits = raw.insunits
    config = state.to_drawing_config()
    inventory = read_dxf(state.dxf_path, convert_geometry=True, unit_context=config.units)

    if config.section is None:
        raise ValueError("Section configuration is incomplete")

    section_line = SectionLine.from_tuples(
        config.section.p0,
        config.section.p1,
        config.section.view_point,
    )

    elements, mapping_counts, wall_stats, warnings = build_elements_from_inventory(
        inventory, config
    )

    mapping = LayerMapping.from_dict(config.layer_mapping)
    unsupported_layers = sorted(
        layer for layer in inventory.layers if classify_layer(layer, mapping) is None
    )
    skip_types = set(config.skip_entity_types)
    unsupported_entity_types = {
        dxftype: count
        for dxftype, count in inventory.entity_counts.items()
        if dxftype not in _SUPPORTED_ENTITY_TYPES and dxftype not in skip_types
    }

    section_result = generate_section(
        elements,
        section_line,
        config,
        source_dxf=str(state.dxf_path),
        detected_layers=inventory.layers,
        extra_warnings=warnings,
        layer_mapping_results=mapping_counts,
        wall_extraction=wall_stats,
        unsupported_layers=unsupported_layers,
        unsupported_entity_types=unsupported_entity_types,
    )

    result = PipelineResult(
        elements=elements,
        section_result=section_result,
        inventory=inventory,
        config=config,
        section_line=section_line,
        mapping_counts=mapping_counts,
        wall_stats=wall_stats,
        warnings=warnings,
    )
    state.last_pipeline_result = result
    return result
