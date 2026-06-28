"""In-memory project state for GUI and pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kesit.architecture.layer_mapping import LayerMapping, classify_layer
from kesit.config import DrawingConfig, SectionConfig, load_config


DEFAULT_SKIP_TYPES = ["TEXT", "MTEXT", "DIMENSION", "LEADER", "HATCH", "VIEWPORT"]

LAYER_ROLES = [
    "walls",
    "openings",
    "doors",
    "windows",
    "columns",
    "slab",
    "structure",
    "fixtures",
    "footprint",
    "annotations",
    "skip",
]


@dataclass
class SectionState:
    p0: tuple[float, float] | None = None
    p1: tuple[float, float] | None = None
    view_point: tuple[float, float] | None = None


@dataclass
class SavedView:
    """Named section line + view point preset."""

    name: str
    p0: tuple[float, float]
    p1: tuple[float, float]
    view_point: tuple[float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "section": {
                "p0": list(self.p0),
                "p1": list(self.p1),
                "view_point": list(self.view_point),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SavedView:
        sec = data.get("section", data)
        name = str(data.get("name", "View"))
        return cls(
            name=name,
            p0=tuple(sec["p0"]),
            p1=tuple(sec["p1"]),
            view_point=tuple(sec["view_point"]),
        )


@dataclass
class ProjectState:
    dxf_path: str | None = None
    project_path: str | None = None
    units: dict[str, Any] = field(
        default_factory=lambda: {
            "source": "auto",
            "source_override": None,
            "parameters": "cm",
            "output": "cm",
        }
    )
    section: SectionState = field(default_factory=SectionState)
    views: list[SavedView] = field(default_factory=list)
    active_view_name: str | None = None
    layer_roles: dict[str, str] = field(default_factory=dict)
    layer_mapping: dict[str, list[str]] = field(default_factory=dict)
    skip_entity_types: list[str] = field(default_factory=lambda: list(DEFAULT_SKIP_TYPES))
    output_scale: str = "1:50"
    wall_height: float = 280
    storey_height: float = 300
    ceiling_height: float = 260
    slab_thickness: float = 20
    finished_floor_thickness: float = 5
    door_height: float = 210
    door_sill_height: float = 0
    door_frame_thickness: float = 5
    window_sill_height: float = 90
    window_head_height: float = 240
    window_frame_thickness: float = 5
    section_depth: float = 500
    snap_tolerance: float = 2
    intersection_tolerance: float = 0.5
    angle_tolerance: float = 2
    cut_lineweight: float = 0.5
    projection_lineweight: float = 0.18
    hatch_spacing: float = 10
    wall_pair_max_offset: float = 30
    wall_pair_min_offset: float = 5
    dxf_insunits: int | None = None
    detected_layers: list[str] = field(default_factory=list)
    locale: str = "en"
    last_pipeline_result: Any = None

    def is_ready_to_generate(self) -> bool:
        return (
            self.dxf_path is not None
            and self.section.p0 is not None
            and self.section.p1 is not None
            and self.section.view_point is not None
        )

    def is_ready_to_save_view(self) -> bool:
        return (
            self.section.p0 is not None
            and self.section.p1 is not None
            and self.section.view_point is not None
        )

    def save_current_view(self, name: str) -> SavedView | None:
        """Save or update a named view from the current section definition."""
        name = name.strip()
        if not name or not self.is_ready_to_save_view():
            return None
        view = SavedView(
            name=name,
            p0=self.section.p0,  # type: ignore[arg-type]
            p1=self.section.p1,  # type: ignore[arg-type]
            view_point=self.section.view_point,  # type: ignore[arg-type]
        )
        for idx, existing in enumerate(self.views):
            if existing.name == name:
                self.views[idx] = view
                self.active_view_name = name
                return view
        self.views.append(view)
        self.active_view_name = name
        return view

    def apply_saved_view(self, view: SavedView) -> None:
        self.section = SectionState(p0=view.p0, p1=view.p1, view_point=view.view_point)
        self.active_view_name = view.name

    def delete_saved_view(self, name: str) -> bool:
        before = len(self.views)
        self.views = [v for v in self.views if v.name != name]
        if self.active_view_name == name:
            self.active_view_name = self.views[0].name if self.views else None
        return len(self.views) < before

    def find_view(self, name: str) -> SavedView | None:
        for view in self.views:
            if view.name == name:
                return view
        return None

    def apply_defaults_from_inventory(
        self,
        layers: list[str],
        default_mapping: dict[str, list[str]] | None = None,
    ) -> None:
        default_mapping = default_mapping or {}
        mapping = LayerMapping.from_dict({**default_mapping, **self.layer_mapping})
        self.detected_layers = list(layers)
        self.layer_roles = {}
        for layer in layers:
            role = classify_layer(layer, mapping)
            self.layer_roles[layer] = role if role else "skip"

    def rebuild_layer_mapping_from_roles(self) -> None:
        """Convert per-layer role assignments back to pattern-based mapping."""
        patterns: dict[str, set[str]] = {role: set() for role in LAYER_ROLES if role != "skip"}
        for layer, role in self.layer_roles.items():
            if role in ("skip", None):
                continue
            if role in patterns:
                patterns[role].add(layer)
        self.layer_mapping = {k: sorted(v) for k, v in patterns.items() if v}

    def to_config_dict(self) -> dict[str, Any]:
        self.rebuild_layer_mapping_from_roles()
        data: dict[str, Any] = {
            "dxf_path": self.dxf_path,
            "units": self.units,
            "layer_mapping": self.layer_mapping,
            "skip_entity_types": self.skip_entity_types,
            "output_scale": self.output_scale,
            "wall_height": self.wall_height,
            "storey_height": self.storey_height,
            "ceiling_height": self.ceiling_height,
            "slab_thickness": self.slab_thickness,
            "finished_floor_thickness": self.finished_floor_thickness,
            "door_height": self.door_height,
            "door_sill_height": self.door_sill_height,
            "door_frame_thickness": self.door_frame_thickness,
            "window_sill_height": self.window_sill_height,
            "window_head_height": self.window_head_height,
            "window_frame_thickness": self.window_frame_thickness,
            "section_depth": self.section_depth,
            "snap_tolerance": self.snap_tolerance,
            "intersection_tolerance": self.intersection_tolerance,
            "angle_tolerance": self.angle_tolerance,
            "cut_lineweight": self.cut_lineweight,
            "projection_lineweight": self.projection_lineweight,
            "hatch_spacing": self.hatch_spacing,
            "wall_pair_max_offset": self.wall_pair_max_offset,
            "wall_pair_min_offset": self.wall_pair_min_offset,
        }
        if self.section.p0 and self.section.p1 and self.section.view_point:
            data["section"] = {
                "p0": list(self.section.p0),
                "p1": list(self.section.p1),
                "view_point": list(self.section.view_point),
            }
        if self.views:
            data["views"] = [v.to_dict() for v in self.views]
        if self.active_view_name:
            data["active_view"] = self.active_view_name
        if self.locale and self.locale != "en":
            data["locale"] = self.locale
        return data

    def to_drawing_config(self) -> DrawingConfig:
        from kesit.config import _float_param, _plan_tolerance_mm
        from kesit.units import UnitContext

        data = self.to_config_dict()
        units = UnitContext.from_config(data.get("units"), self.dxf_insunits)

        section = None
        if self.section.p0 and self.section.p1 and self.section.view_point:
            section = SectionConfig(
                p0=(
                    units.plan_to_internal(self.section.p0[0]),
                    units.plan_to_internal(self.section.p0[1]),
                ),
                p1=(
                    units.plan_to_internal(self.section.p1[0]),
                    units.plan_to_internal(self.section.p1[1]),
                ),
                view_point=(
                    units.plan_to_internal(self.section.view_point[0]),
                    units.plan_to_internal(self.section.view_point[1]),
                ),
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

    @classmethod
    def from_config_file(cls, path: str | Path, dxf_insunits: int | None = None) -> ProjectState:
        config = load_config(path, dxf_insunits=dxf_insunits)
        raw = config.raw
        state = cls(
            dxf_path=config.dxf_path,
            project_path=str(path),
            units=dict(raw.get("units", {})),
            layer_mapping=dict(config.layer_mapping),
            skip_entity_types=list(config.skip_entity_types),
            output_scale=config.output_scale,
            dxf_insunits=dxf_insunits,
        )
        for key in (
            "wall_height", "storey_height", "ceiling_height", "slab_thickness",
            "finished_floor_thickness", "door_height", "door_sill_height",
            "door_frame_thickness", "window_sill_height", "window_head_height",
            "window_frame_thickness", "section_depth", "snap_tolerance",
            "intersection_tolerance", "angle_tolerance", "cut_lineweight",
            "projection_lineweight", "hatch_spacing", "wall_pair_max_offset",
            "wall_pair_min_offset",
        ):
            if key in raw:
                setattr(state, key, raw[key])

        if "section" in raw:
            sec = raw["section"]
            state.section = SectionState(
                p0=tuple(sec["p0"]),
                p1=tuple(sec["p1"]),
                view_point=tuple(sec["view_point"]),
            )
        if "views" in raw:
            state.views = [SavedView.from_dict(item) for item in raw["views"]]
        state.active_view_name = raw.get("active_view")
        if "layer_roles" in raw and isinstance(raw["layer_roles"], dict):
            state.layer_roles = {str(k): str(v) for k, v in raw["layer_roles"].items()}
        locale = raw.get("locale", "en")
        state.locale = str(locale) if locale in ("en", "tr") else "en"
        return state

    @classmethod
    def load_default_mapping(cls, root: Path) -> dict[str, list[str]]:
        path = root / "config" / "layer_mapping.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}
