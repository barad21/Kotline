from pathlib import Path

import yaml

from kesit.app.config_io import save_project
from kesit.app.project_state import ProjectState, SavedView


def test_save_and_apply_view():
    state = ProjectState()
    state.section.p0 = (-420.0, -180.0)
    state.section.p1 = (-420.0, 300.0)
    state.section.view_point = (-220.0, 80.0)

    view = state.save_current_view("North")
    assert view is not None
    assert len(state.views) == 1
    assert state.active_view_name == "North"

    state.section.p0 = (0.0, 0.0)
    state.section.p1 = (100.0, 0.0)
    state.section.view_point = (50.0, 50.0)

    saved = state.find_view("North")
    assert saved is not None
    state.apply_saved_view(saved)
    assert state.section.p0 == (-420.0, -180.0)
    assert state.section.view_point == (-220.0, 80.0)


def test_update_view_same_name():
    state = ProjectState()
    state.section.p0 = (0.0, 0.0)
    state.section.p1 = (0.0, 10.0)
    state.section.view_point = (5.0, 5.0)
    state.save_current_view("A")

    state.section.p1 = (0.0, 20.0)
    state.save_current_view("A")
    assert len(state.views) == 1
    assert state.views[0].p1 == (0.0, 20.0)


def test_delete_view():
    state = ProjectState()
    state.section.p0 = (0.0, 0.0)
    state.section.p1 = (0.0, 10.0)
    state.section.view_point = (5.0, 5.0)
    state.save_current_view("A")
    state.save_current_view("B")
    assert state.delete_saved_view("A")
    assert len(state.views) == 1
    assert state.active_view_name == "B"


def test_views_persist_in_project_file(tmp_path):
    state = ProjectState()
    state.dxf_path = "sample.dxf"
    state.section.p0 = (1.0, 2.0)
    state.section.p1 = (3.0, 4.0)
    state.section.view_point = (5.0, 6.0)
    state.save_current_view("TestView")

    path = tmp_path / "proj.yaml"
    save_project(path, state)

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "views" in loaded
    assert loaded["views"][0]["name"] == "TestView"
    assert loaded["active_view"] == "TestView"

    restored = ProjectState.from_config_file(path)
    assert len(restored.views) == 1
    assert restored.views[0].name == "TestView"
    assert restored.active_view_name == "TestView"


def test_saved_view_from_dict():
    data = {
        "name": "East",
        "section": {"p0": [1, 2], "p1": [3, 4], "view_point": [5, 6]},
    }
    view = SavedView.from_dict(data)
    assert view.name == "East"
    assert view.p0 == (1, 2)
