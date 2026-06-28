"""DXF reading and inventory reporting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing

from kesit.units import insunits_to_unit


@dataclass
class DxfEntity:
    dxftype: str
    layer: str
    geometry: Any = None
    handle: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DxfInventory:
    path: str
    dxf_version: str
    insunits: int | None
    insunits_unit: str | None
    entity_counts: dict[str, int]
    layer_entity_counts: dict[str, dict[str, int]]
    layers: list[str]
    entities: list[DxfEntity]
    block_names: list[str]
    warnings: list[str] = field(default_factory=list)

    @property
    def total_entities(self) -> int:
        return sum(self.entity_counts.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "dxf_version": self.dxf_version,
            "insunits": self.insunits,
            "insunits_unit": self.insunits_unit,
            "total_entities": self.total_entities,
            "entity_counts": self.entity_counts,
            "layers": self.layers,
            "layer_entity_counts": self.layer_entity_counts,
            "block_names": self.block_names[:30],
            "warnings": self.warnings,
        }


def read_dxf(path: str | Path, convert_geometry: bool = False, unit_context=None) -> DxfInventory:
    path = Path(path)
    warnings: list[str] = []
    doc: Drawing = ezdxf.readfile(path)
    msp = doc.modelspace()

    entity_counts: Counter[str] = Counter()
    layer_entity: Counter[tuple[str, str]] = Counter()
    layers: set[str] = set()
    entities: list[DxfEntity] = []

    converter = None
    if convert_geometry and unit_context is not None:
        from kesit.cad_io.entity_converter import convert_entity as _convert

        converter = _convert

    for entity in msp:
        dxftype = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
        entity_counts[dxftype] += 1
        layer_entity[(layer, dxftype)] += 1
        layers.add(layer)

        geometry = None
        if converter is not None:
            try:
                geometry = converter(entity, unit_context)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Failed to convert {dxftype} on {layer}: {exc}")

        entities.append(
            DxfEntity(
                dxftype=dxftype,
                layer=layer,
                geometry=geometry,
                handle=str(entity.dxf.handle),
                metadata={"block_name": entity.dxf.name} if dxftype == "INSERT" else {},
            )
        )

    insunits = doc.header.get("$INSUNITS")
    unit = insunits_to_unit(insunits)
    block_names = [b.name for b in doc.blocks if not b.name.startswith("*")]

    layer_entity_counts: dict[str, dict[str, int]] = {}
    for (layer, dxftype), count in layer_entity.items():
        layer_entity_counts.setdefault(layer, {})[dxftype] = count

    return DxfInventory(
        path=str(path),
        dxf_version=doc.dxfversion,
        insunits=insunits,
        insunits_unit=unit.value if unit else None,
        entity_counts=dict(entity_counts),
        layer_entity_counts=layer_entity_counts,
        layers=sorted(layers),
        entities=entities,
        block_names=block_names,
        warnings=warnings,
    )
