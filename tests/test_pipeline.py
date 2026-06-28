from pathlib import Path

import pytest

from kesit.app.config_io import load_project, save_project
from kesit.app.pipeline import run_pipeline
from kesit.app.project_state import ProjectState

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_matches_floorplan_config():
    config_path = ROOT / "config" / "floorplan.yaml"
    state = load_project(config_path)
    if state.dxf_path and not Path(state.dxf_path).is_absolute():
        state.dxf_path = str(ROOT / state.dxf_path)

    result = run_pipeline(state)
    counts = result.section_result.diagnostics.counts

    assert len(result.elements) > 0
    assert counts.get("cut", 0) >= 1
    assert result.wall_stats["paired_lines"] + result.wall_stats["closed_polys"] >= 1


def test_project_save_round_trip(tmp_path):
    state = ProjectState(
        dxf_path="sample-files/dxf/dxf-parser/floorplan.dxf",
        wall_height=280,
        section=ProjectState().section,
    )
    state.section.p0 = (-400, -150)
    state.section.p1 = (-400, 250)
    state.section.view_point = (-200, 50)
    state.layer_mapping = {"walls": ["*A-WALL"]}

    out = tmp_path / "project.yaml"
    save_project(out, state)
    assert out.exists()

    loaded = load_project(out)
    assert loaded.wall_height == 280
    assert loaded.section.p0 == (-400, -150)
