"""Generate section from DXF floor plan."""

from __future__ import annotations

import argparse
from pathlib import Path

from kesit.app.config_io import load_project
from kesit.app.pipeline import run_pipeline
from kesit.app.project_state import ProjectState
from kesit.generation.section_generator import write_diagnostics
from kesit.generation.svg_exporter import export_svg


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate section from DXF")
    parser.add_argument("--config", default="config/floorplan.yaml")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    config_path = root / args.config
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    state = load_project(config_path)
    if state.dxf_path and not Path(state.dxf_path).is_absolute():
        state.dxf_path = str(root / state.dxf_path)

    result = run_pipeline(state)

    svg_path = output_dir / "floorplan-section.svg"
    diag_path = output_dir / "floorplan-diagnostics.json"
    export_svg(result.section_result.shapes, svg_path, result.config, title="Floorplan Section")
    write_diagnostics(result.section_result.diagnostics, diag_path)

    counts = result.section_result.diagnostics.counts
    print("Floorplan section generated.")
    print(f"  elements={len(result.elements)} cut={counts.get('cut', 0)} projected={counts.get('projected', 0)}")
    print(f"  wall_extraction={result.wall_stats}")
    print(f"  SVG: {svg_path}")
    print(f"  Diagnostics: {diag_path}")


if __name__ == "__main__":
    main()
