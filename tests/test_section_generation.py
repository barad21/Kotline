from pathlib import Path

from kesit.generation.section_generator import generate_section
from kesit.generation.svg_exporter import export_svg
from kesit.fixtures.synthetic_plan import synthetic_config, synthetic_elements, synthetic_section


def test_synthetic_section_generation(tmp_path):
    config = synthetic_config()
    section = synthetic_section()
    elements = synthetic_elements()

    result = generate_section(elements, section, config)
    counts = result.diagnostics.counts

    assert counts["cut"] >= 2
    assert counts["projected"] >= 1
    assert len(result.shapes) > 0

    out = tmp_path / "section.svg"
    export_svg(result.shapes, out, config)
    assert out.exists()
    assert "<svg" in out.read_text(encoding="utf-8")
