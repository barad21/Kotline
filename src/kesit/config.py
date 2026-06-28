"""Configuration loading with unit conversion to internal mm."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from kesit.units import UnitContext


@dataclass
class SectionConfig:
    p0: tuple[float, float]
    p1: tuple[float, float]
    view_point: tuple[float, float]


@dataclass
class DrawingConfig:
    """Drawing parameters; *_mm fields are in internal canonical units."""

    units: UnitContext
    output_scale: str = "1:50"
    wall_height_mm: float = 2800.0
    storey_height_mm: float = 3000.0
    ceiling_height_mm: float = 2600.0
    slab_thickness_mm: float = 200.0
    finished_floor_thickness_mm: float = 50.0
    door_height_mm: float = 2100.0
    door_sill_height_mm: float = 0.0
    door_frame_thickness_mm: float = 50.0
    window_sill_height_mm: float = 900.0
    window_head_height_mm: float = 2400.0
    window_frame_thickness_mm: float = 50.0
    section_depth_mm: float = 5000.0
    snap_tolerance_mm: float = 20.0
    intersection_tolerance_mm: float = 5.0
    angle_tolerance: float = 2.0
    cut_lineweight: float = 0.5
    projection_lineweight: float = 0.18
    hatch_spacing_mm: float = 100.0
    wall_pair_max_offset_mm: float = 300.0
    wall_pair_min_offset_mm: float = 50.0
    dxf_path: str | None = None
    section: SectionConfig | None = None
    layer_mapping: dict[str, list[str]] = field(default_factory=dict)
    skip_entity_types: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def wall_height(self) -> float:
        return self.wall_height_mm

    @property
    def storey_height(self) -> float:
        return self.storey_height_mm

    @property
    def door_height(self) -> float:
        return self.door_height_mm

    @property
    def window_sill_height(self) -> float:
        return self.window_sill_height_mm

    @property
    def window_head_height(self) -> float:
        return self.window_head_height_mm

    @property
    def section_depth(self) -> float:
        return self.section_depth_mm

    @property
    def snap_tolerance(self) -> float:
        return self.snap_tolerance_mm

    @property
    def intersection_tolerance(self) -> float:
        return self.intersection_tolerance_mm


def _load_raw(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml", ".kesit"):
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _float_param(ctx: UnitContext, data: dict[str, Any], key: str, default: float) -> float:
    return ctx.param_to_internal(float(data.get(key, default)))


def _plan_tolerance_mm(ctx: UnitContext, data: dict[str, Any], key: str, default: float) -> float:
    """Tolerances in plan space are expressed in source units."""
    return ctx.plan_to_internal(float(data.get(key, default)))


def load_config(
    path: str | Path,
    dxf_insunits: int | None = None,
    overrides: dict[str, Any] | None = None,
) -> DrawingConfig:
    path = Path(path)
    data = _load_raw(path)
    if overrides:
        data = {**data, **overrides}

    units = UnitContext.from_config(data.get("units"), dxf_insunits)

    section = None
    if "section" in data:
        sec = data["section"]
        p0 = tuple(sec["p0"])
        p1 = tuple(sec["p1"])
        view = tuple(sec["view_point"])
        section = SectionConfig(
            p0=(units.plan_to_internal(p0[0]), units.plan_to_internal(p0[1])),
            p1=(units.plan_to_internal(p1[0]), units.plan_to_internal(p1[1])),
            view_point=(units.plan_to_internal(view[0]), units.plan_to_internal(view[1])),
        )

    return DrawingConfig(
        units=units,
        output_scale=str(data.get("output_scale", "1:50")),
        wall_height_mm=_float_param(units, data, "wall_height", 280),
        storey_height_mm=_float_param(units, data, "storey_height", 300),
        ceiling_height_mm=_float_param(units, data, "ceiling_height", 260),
        slab_thickness_mm=_float_param(units, data, "slab_thickness", 20),
        finished_floor_thickness_mm=_float_param(units, data, "finished_floor_thickness", 5),
        door_height_mm=_float_param(units, data, "door_height", 210),
        door_sill_height_mm=_float_param(units, data, "door_sill_height", 0),
        door_frame_thickness_mm=_float_param(units, data, "door_frame_thickness", 5),
        window_sill_height_mm=_float_param(units, data, "window_sill_height", 90),
        window_head_height_mm=_float_param(units, data, "window_head_height", 240),
        window_frame_thickness_mm=_float_param(units, data, "window_frame_thickness", 5),
        section_depth_mm=_float_param(units, data, "section_depth", 500),
        snap_tolerance_mm=_plan_tolerance_mm(units, data, "snap_tolerance", 2),
        intersection_tolerance_mm=_plan_tolerance_mm(units, data, "intersection_tolerance", 0.5),
        angle_tolerance=float(data.get("angle_tolerance", 2)),
        cut_lineweight=float(data.get("cut_lineweight", 0.5)),
        projection_lineweight=float(data.get("projection_lineweight", 0.18)),
        hatch_spacing_mm=_float_param(units, data, "hatch_spacing", 10),
        wall_pair_max_offset_mm=_plan_tolerance_mm(units, data, "wall_pair_max_offset", 30),
        wall_pair_min_offset_mm=_plan_tolerance_mm(units, data, "wall_pair_min_offset", 5),
        dxf_path=data.get("dxf_path"),
        section=section,
        layer_mapping=dict(data.get("layer_mapping", {})),
        skip_entity_types=list(data.get("skip_entity_types", [])),
        raw=data,
    )


def save_config(data: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in (".yaml", ".yml", ".kesit"):
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
