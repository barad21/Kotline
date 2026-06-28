from pathlib import Path

import pytest

from kesit.cad_io.dxf_reader import read_dxf

ROOT = Path(__file__).resolve().parents[1]
DXF_DIR = ROOT / "sample-files" / "dxf" / "dxf-parser"


@pytest.mark.parametrize(
    ("filename", "expected_total", "expected_type"),
    [
        ("lines.dxf", 11, "LINE"),
        ("lwpolylines.dxf", 2, "LWPOLYLINE"),
        ("blocks1.dxf", 2, "INSERT"),
    ],
)
def test_micro_dxf_counts(filename, expected_total, expected_type):
    inv = read_dxf(DXF_DIR / filename)
    assert inv.total_entities == expected_total
    assert inv.entity_counts.get(expected_type) == expected_total


def test_floorplan_inventory():
    inv = read_dxf(DXF_DIR / "floorplan.dxf")
    assert inv.total_entities == 967
    assert len(inv.layers) == 17
    assert inv.entity_counts.get("LINE") == 624
    assert inv.entity_counts.get("LWPOLYLINE") == 124
    assert inv.insunits == 4
