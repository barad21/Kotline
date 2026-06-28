"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shapely.geometry.base import BaseGeometry


class ElementKind(str, Enum):
    WALL = "wall"
    COLUMN = "column"
    DOOR = "door"
    WINDOW = "window"
    OPENING = "opening"
    SLAB = "slab"
    FURNITURE = "furniture"


class SectionMode(str, Enum):
    CUT = "cut"
    PROJECT = "project"
    IGNORE = "ignore"


class ShapeKind(str, Enum):
    CUT = "cut"
    PROJECTION = "projection"
    BASELINE = "baseline"
    OPENING = "opening"


@dataclass
class PlanElement:
    id: str
    kind: ElementKind
    geometry: BaseGeometry
    layer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionShape:
    kind: ShapeKind
    geometry: BaseGeometry
    element_id: str = ""
    lineweight: float = 0.25
    hatch: bool = False
    css_class: str = ""
    depth_mm: float | None = None
    section_mode: SectionMode | None = None


@dataclass
class IntersectionRecord:
    element_id: str
    s_min: float
    s_max: float
    mode: SectionMode
    depth_mm: float | None = None


@dataclass
class DiagnosticReport:
    section_line: dict[str, list[float]] | None = None
    source_dxf: str | None = None
    units: dict[str, Any] = field(default_factory=dict)
    detected_layers: list[str] = field(default_factory=list)
    unsupported_layers: list[str] = field(default_factory=list)
    layer_mapping_results: dict[str, int] = field(default_factory=dict)
    wall_extraction: dict[str, int] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    intersections: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_entity_types: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_line": self.section_line,
            "source_dxf": self.source_dxf,
            "units": self.units,
            "detected_layers": self.detected_layers,
            "unsupported_layers": self.unsupported_layers,
            "layer_mapping_results": self.layer_mapping_results,
            "wall_extraction": self.wall_extraction,
            "counts": self.counts,
            "intersections": self.intersections,
            "warnings": self.warnings,
            "unsupported_entity_types": self.unsupported_entity_types,
        }
