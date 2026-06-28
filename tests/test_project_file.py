from pathlib import Path

import yaml

from kesit.app.config_io import KESIT_EXTENSION, KESIT_FORMAT, KESIT_VERSION, load_project, save_project
from kesit.app.project_state import ProjectState

ROOT = Path(__file__).resolve().parents[1]


def _sample_state() -> ProjectState:
    from kesit.app.pipeline import load_inventory

    state = ProjectState(
        dxf_path=str(ROOT / "sample-files" / "dxf" / "dxf-parser" / "floorplan.dxf"),
        wall_height=280,
        section_depth=500,
    )
    state.section.p0 = (-420.0, -180.0)
    state.section.p1 = (-420.0, 300.0)
    state.section.view_point = (-220.0, 80.0)
    state.units["source_override"] = "cm"
    inv = load_inventory(state)
    if inv.layers:
        state.layer_roles = {layer: "skip" for layer in inv.layers}
        state.layer_roles[inv.layers[0]] = "walls"
    state.rebuild_layer_mapping_from_roles()
    state.save_current_view("Demo")
    state._test_wall_layer = inv.layers[0] if inv.layers else None
    return state


def test_kesit_project_save_contains_format(tmp_path):
    state = _sample_state()
    path = tmp_path / "my-project.kesit"
    save_project(path, state)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["kesit_format"] == KESIT_FORMAT
    assert raw["kesit_version"] == KESIT_VERSION
    assert "layer_roles" in raw
    assert raw["views"][0]["name"] == "Demo"
    assert path.suffix == KESIT_EXTENSION


def test_kesit_project_round_trip(tmp_path):
    state = _sample_state()
    wall_layer = state._test_wall_layer
    path = tmp_path / "roundtrip.kesit"
    save_project(path, state)

    loaded = load_project(path, root_dir=ROOT)
    assert loaded.wall_height == 280
    assert loaded.section.p0 == (-420.0, -180.0)
    assert loaded.section.view_point == (-220.0, 80.0)
    if wall_layer:
        assert loaded.layer_roles.get(wall_layer) == "walls"
    assert len(loaded.views) == 1
    assert loaded.active_view_name == "Demo"
    assert Path(loaded.dxf_path).exists()


def test_save_without_extension_gets_kesit_suffix(tmp_path):
    state = _sample_state()
    path = tmp_path / "unnamed"
    save_project(path, state)
    assert path.with_suffix(KESIT_EXTENSION).exists()
