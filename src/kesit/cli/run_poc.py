"""Run synthetic proof-of-concept."""

from __future__ import annotations

import argparse
from pathlib import Path

from kesit.config import load_config
from kesit.generation.section_generator import generate_section, write_diagnostics
from kesit.generation.svg_exporter import export_svg
from kesit.fixtures.synthetic_plan import synthetic_elements, synthetic_section


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate section from synthetic plan")
    parser.add_argument("--config", default="config/defaults.yaml")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    config_path = root / args.config
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    section = synthetic_section()
    elements = synthetic_elements()

    result = generate_section(elements, section, config)
    export_svg(result.shapes, output_dir / "section.svg", config, title="Synthetic Section")
    write_diagnostics(result.diagnostics, output_dir / "diagnostics.json")

    counts = result.diagnostics.counts
    print("Synthetic section generated.")
    print(f"  cut={counts.get('cut', 0)} projected={counts.get('projected', 0)}")
    print(f"  SVG: {output_dir / 'section.svg'}")
    print(f"  Diagnostics: {output_dir / 'diagnostics.json'}")


if __name__ == "__main__":
    main()
