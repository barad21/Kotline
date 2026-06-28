def test_locale_saved_in_project(tmp_path):
    from kesit.app.config_io import load_project, save_project
    from tests.test_project_file import _sample_state

    state = _sample_state()
    state.locale = "tr"
    path = tmp_path / "tr.kesit"
    save_project(path, state)
    loaded = load_project(path, root_dir=tmp_path.parent)
    assert loaded.locale == "tr"
