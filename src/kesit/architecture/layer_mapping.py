"""Layer name matching with wildcard suffix support."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayerMapping:
    walls: list[str] = field(default_factory=list)
    openings: list[str] = field(default_factory=list)
    doors: list[str] = field(default_factory=list)
    windows: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    slab: list[str] = field(default_factory=list)
    structure: list[str] = field(default_factory=list)
    fixtures: list[str] = field(default_factory=list)
    footprint: list[str] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, list[str]] | None) -> LayerMapping:
        data = data or {}
        return cls(
            walls=list(data.get("walls", [])),
            openings=list(data.get("openings", [])),
            doors=list(data.get("doors", [])),
            windows=list(data.get("windows", [])),
            columns=list(data.get("columns", [])),
            slab=list(data.get("slab", [])),
            structure=list(data.get("structure", [])),
            # "furniture" is accepted as a legacy alias for "fixtures".
            fixtures=list(data.get("fixtures", [])) + list(data.get("furniture", [])),
            footprint=list(data.get("footprint", [])),
            annotations=list(data.get("annotations", [])),
        )

    def all_patterns(self) -> dict[str, list[str]]:
        return {
            "walls": self.walls,
            "openings": self.openings,
            "doors": self.doors,
            "windows": self.windows,
            "columns": self.columns,
            "slab": self.slab,
            "structure": self.structure,
            "fixtures": self.fixtures,
            "footprint": self.footprint,
            "annotations": self.annotations,
        }


def match_layer(layer: str, pattern: str) -> bool:
    if pattern.startswith("*"):
        return layer.endswith(pattern[1:])
    return layer == pattern


def classify_layer(layer: str, mapping: LayerMapping) -> str | None:
    for role, patterns in mapping.all_patterns().items():
        for pattern in patterns:
            if match_layer(layer, pattern):
                return role
    return None


def is_skipped_layer(layer: str, mapping: LayerMapping) -> bool:
    return classify_layer(layer, mapping) == "annotations"
