"""Section generation pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from kesit.architecture.section_rules import classify_element, generate_shapes_for_element
from kesit.config import DrawingConfig
from kesit.geometry.section_line import SectionLine
from kesit.models import DiagnosticReport, PlanElement, SectionMode, SectionShape, ShapeKind


@dataclass
class SectionResult:
    shapes: list[SectionShape]
    diagnostics: DiagnosticReport


def _sort_key(shape: SectionShape) -> int:
    order = {
        ShapeKind.BASELINE: 0,
        ShapeKind.PROJECTION: 1,
        ShapeKind.OPENING: 2,
        ShapeKind.CUT: 3,
    }
    return order.get(shape.kind, 5)


def generate_section(
    elements: list[PlanElement],
    section: SectionLine,
    config: DrawingConfig,
    source_dxf: str | None = None,
    detected_layers: list[str] | None = None,
    extra_warnings: list[str] | None = None,
    layer_mapping_results: dict[str, int] | None = None,
    wall_extraction: dict[str, int] | None = None,
    unsupported_layers: list[str] | None = None,
    unsupported_entity_types: dict[str, int] | None = None,
) -> SectionResult:
    shapes: list[SectionShape] = []
    intersections = []
    counts = {
        "walls": 0,
        "columns": 0,
        "doors": 0,
        "windows": 0,
        "openings": 0,
        "cut": 0,
        "projected": 0,
        "ignored_depth": 0,
        "ignored_unclassified": 0,
    }
    warnings = list(extra_warnings or [])

    has_slab = any(e.kind.value == "slab" for e in elements)
    if not has_slab:
        from shapely.geometry import LineString

        from kesit.models import ElementKind, PlanElement

        elements = [
            PlanElement(
                id="floor_baseline",
                kind=ElementKind.SLAB,
                geometry=LineString([(0, 0), (1, 0)]),
            ),
            *elements,
        ]

    for element in elements:
        mode = classify_element(section, element, config)
        if mode == SectionMode.IGNORE:
            counts["ignored_depth"] += 1
            continue
        if mode == SectionMode.CUT:
            counts["cut"] += 1
        elif mode == SectionMode.PROJECT:
            counts["projected"] += 1

        kind_key = element.kind.value
        if kind_key in counts:
            counts[kind_key] += 1
        elif element.kind.value == "opening":
            counts["openings"] += 1

        element_shapes, record = generate_shapes_for_element(section, element, mode, config)
        shapes.extend(element_shapes)
        if record:
            entry = {
                "element_id": record.element_id,
                "s_range": [record.s_min, record.s_max],
                "mode": record.mode.value,
            }
            if record.depth_mm is not None:
                entry["depth_mm"] = record.depth_mm
            intersections.append(entry)

    shapes.sort(key=_sort_key)

    diagnostics = DiagnosticReport(
        section_line=section.to_dict(),
        source_dxf=source_dxf,
        units=config.units.to_diagnostics_dict(),
        detected_layers=detected_layers or [],
        unsupported_layers=unsupported_layers or [],
        layer_mapping_results=layer_mapping_results or {},
        wall_extraction=wall_extraction or {},
        counts=counts,
        intersections=intersections,
        warnings=warnings,
        unsupported_entity_types=unsupported_entity_types or {},
    )
    return SectionResult(shapes=shapes, diagnostics=diagnostics)


def write_diagnostics(diagnostics: DiagnosticReport, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(diagnostics.to_dict(), indent=2), encoding="utf-8")
