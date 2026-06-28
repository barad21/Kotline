from kesit.units import (
    Unit,
    UnitContext,
    convert_length,
    insunits_to_unit,
    resolve_source_unit,
)


def test_cm_to_mm_round_trip():
    assert convert_length(280, Unit.CM, Unit.MM) == 2800
    assert convert_length(2800, Unit.MM, Unit.CM) == 280


def test_insunits_mapping():
    assert insunits_to_unit(4) == Unit.MM
    assert insunits_to_unit(5) == Unit.CM
    assert insunits_to_unit(6) == Unit.M


def test_source_override_ignores_header():
    resolved, detected, applied = resolve_source_unit("auto", "cm", dxf_insunits=4)
    assert resolved == Unit.CM
    assert detected == Unit.MM
    assert applied is True


def test_unit_context_diagnostics():
    ctx = UnitContext.from_config(
        {"source": "auto", "source_override": "cm", "parameters": "cm", "output": "cm"},
        dxf_insunits=4,
    )
    diag = ctx.to_diagnostics_dict()
    assert diag["source_resolved"] == "cm"
    assert diag["source_detected_from_dxf"] == "mm"
    assert diag["source_override_applied"] is True


def test_wall_height_in_meters():
    ctx = UnitContext.from_config({"source": "cm", "parameters": "m", "output": "cm"})
    assert ctx.param_to_internal(2.8) == 2800
