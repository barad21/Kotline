"""Unit conversion and DXF INSUNITS resolution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Unit(str, Enum):
    MM = "mm"
    CM = "cm"
    M = "m"
    IN = "in"
    FT = "ft"
    AUTO = "auto"


CANONICAL = Unit.MM

_TO_MM: dict[Unit, float] = {
    Unit.MM: 1.0,
    Unit.CM: 10.0,
    Unit.M: 1000.0,
    Unit.IN: 25.4,
    Unit.FT: 304.8,
}

# DXF $INSUNITS codes (AutoCAD)
_INSUNITS_MAP: dict[int, Unit] = {
    0: Unit.MM,  # unitless — treat as mm
    1: Unit.IN,
    2: Unit.FT,
    3: Unit.M,  # mile in spec but rarely used
    4: Unit.MM,
    5: Unit.CM,
    6: Unit.M,
    7: Unit.M,  # km — map to meters
}


def parse_unit(value: str | Unit | None, default: Unit = Unit.MM) -> Unit:
    if value is None:
        return default
    if isinstance(value, Unit):
        return value
    normalized = str(value).strip().lower()
    if normalized == "auto":
        return Unit.AUTO
    for unit in Unit:
        if unit.value == normalized:
            return unit
    raise ValueError(f"Unsupported unit: {value!r}")


def insunits_to_unit(code: int | None) -> Unit | None:
    if code is None:
        return None
    return _INSUNITS_MAP.get(int(code))


def convert_length(value: float, from_unit: Unit, to_unit: Unit) -> float:
    if from_unit == to_unit:
        return value
    if from_unit == Unit.AUTO or to_unit == Unit.AUTO:
        raise ValueError("Cannot convert with AUTO unit")
    mm_value = value * _TO_MM[from_unit]
    return mm_value / _TO_MM[to_unit]


def resolve_source_unit(
    source_config: str | Unit,
    source_override: str | Unit | None,
    dxf_insunits: int | None = None,
) -> tuple[Unit, Unit | None, bool]:
    """Return (resolved_source, detected_from_dxf, override_applied)."""
    configured = parse_unit(source_config, Unit.AUTO)
    override = parse_unit(source_override, Unit.MM) if source_override else None
    if override is not None and str(source_override).lower() != "null":
        detected = insunits_to_unit(dxf_insunits) if dxf_insunits is not None else None
        return override, detected, True

    if configured != Unit.AUTO:
        detected = insunits_to_unit(dxf_insunits) if dxf_insunits is not None else None
        return configured, detected, False

    detected = insunits_to_unit(dxf_insunits)
    if detected is not None:
        return detected, detected, False
    return Unit.MM, None, False


@dataclass(frozen=True)
class UnitContext:
    source: Unit
    parameters: Unit
    output: Unit
    source_configured: str
    source_detected_from_dxf: Unit | None = None
    source_override_applied: bool = False

    @classmethod
    def from_config(
        cls,
        units_block: dict[str, Any] | None,
        dxf_insunits: int | None = None,
    ) -> UnitContext:
        block = units_block or {}
        source_cfg = block.get("source", "auto")
        override_raw = block.get("source_override")
        parameters = parse_unit(block.get("parameters", "cm"), Unit.CM)
        output = parse_unit(block.get("output") or block.get("parameters", "cm"), Unit.CM)

        override: str | Unit | None = override_raw
        if override_raw is None or str(override_raw).lower() in ("null", "none", ""):
            override = None

        resolved, detected, override_applied = resolve_source_unit(
            source_cfg, override, dxf_insunits
        )
        return cls(
            source=resolved,
            parameters=parameters,
            output=output,
            source_configured=str(source_cfg),
            source_detected_from_dxf=detected,
            source_override_applied=override_applied,
        )

    def plan_to_internal(self, value: float) -> float:
        return convert_length(value, self.source, CANONICAL)

    def param_to_internal(self, value: float) -> float:
        return convert_length(value, self.parameters, CANONICAL)

    def internal_to_output(self, value: float) -> float:
        return convert_length(value, CANONICAL, self.output)

    def convert_point_plan_to_internal(self, x: float, y: float) -> tuple[float, float]:
        return self.plan_to_internal(x), self.plan_to_internal(y)

    def to_diagnostics_dict(self) -> dict[str, Any]:
        return {
            "source_configured": self.source_configured,
            "source_resolved": self.source.value,
            "source_detected_from_dxf": (
                self.source_detected_from_dxf.value
                if self.source_detected_from_dxf
                else None
            ),
            "source_override_applied": self.source_override_applied,
            "parameters": self.parameters.value,
            "internal": CANONICAL.value,
            "output": self.output.value,
        }
