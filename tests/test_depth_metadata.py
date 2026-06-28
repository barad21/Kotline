from pathlib import Path

from kesit.architecture.section_rules import classify_element, generate_shapes_for_element
from kesit.fixtures.synthetic_plan import synthetic_config, synthetic_elements, synthetic_section
from kesit.models import SectionMode, ShapeKind
from kesit.rendering.depth_colors import depth_factor, depth_to_fill, gradient_at
from kesit.ui import theme

ROOT = Path(__file__).resolve().parents[1]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def test_cut_wall_has_zero_depth():
    section = synthetic_section()
    config = synthetic_config()
    wall = synthetic_elements()[0]
    mode = classify_element(section, wall, config)
    assert mode == SectionMode.CUT
    shapes, record = generate_shapes_for_element(section, wall, mode, config)
    assert len(shapes) == 1
    assert shapes[0].depth_mm == 0.0
    assert shapes[0].section_mode == SectionMode.CUT
    assert record is not None
    assert record.depth_mm == 0.0


def test_projected_element_has_positive_depth():
    section = synthetic_section()
    config = synthetic_config()
    column = synthetic_elements()[2]
    mode = classify_element(section, column, config)
    assert mode == SectionMode.PROJECT
    shapes, record = generate_shapes_for_element(section, column, mode, config)
    assert len(shapes) == 1
    assert shapes[0].depth_mm is not None and shapes[0].depth_mm > 0
    assert shapes[0].depth_mm <= config.section_depth_mm
    assert shapes[0].section_mode == SectionMode.PROJECT


def test_floorplan_depth_metadata():
    from kesit.app.demo import load_demo_project
    from kesit.app.pipeline import run_pipeline

    project = load_demo_project(ROOT)
    result = run_pipeline(project)
    shapes = result.section_result.shapes
    cut_mode_shapes = [s for s in shapes if s.section_mode == SectionMode.CUT]
    project_mode_shapes = [s for s in shapes if s.section_mode == SectionMode.PROJECT]

    assert len(cut_mode_shapes) >= 10
    assert all(s.depth_mm == 0.0 for s in cut_mode_shapes)

    assert len(project_mode_shapes) >= 50
    assert all(s.depth_mm is not None and s.depth_mm >= 0 for s in project_mode_shapes)
    assert sum(1 for s in project_mode_shapes if s.depth_mm > 0) >= 40

    counts = result.section_result.diagnostics.counts
    assert counts["cut"] >= 10
    assert counts["projected"] >= 50


def test_depth_color_mapping():
    near = gradient_at(0.0)
    far = gradient_at(1.0)
    assert near == theme.DEPTH_NEAR
    assert far == theme.DEPTH_FAR

    near_rgb = _hex_to_rgb(near)
    far_rgb = _hex_to_rgb(far)
    assert near_rgb[0] > near_rgb[2]
    assert far_rgb[2] > far_rgb[0]

    mid = gradient_at(0.5)
    assert mid == depth_to_fill(2500.0, 5000.0, ShapeKind.PROJECTION)
    assert depth_factor(2500.0, 5000.0) == 0.5
    assert depth_factor(None, 5000.0) == 0.0


def test_diagnostics_include_depth():
    from kesit.app.demo import load_demo_project
    from kesit.app.pipeline import run_pipeline

    project = load_demo_project(ROOT)
    result = run_pipeline(project)
    intersections = result.section_result.diagnostics.intersections
    assert intersections
    assert any("depth_mm" in item for item in intersections)


def test_view_flip_changes_projection():
    from kesit.app.demo import load_demo_project
    from kesit.app.pipeline import run_pipeline
    from kesit.models import SectionMode

    east = load_demo_project(ROOT)
    east.section.view_point = (-220, 80)
    east_result = run_pipeline(east)

    west = load_demo_project(ROOT)
    west.section.view_point = (-620, 80)
    west_result = run_pipeline(west)

    east_counts = east_result.section_result.diagnostics.counts
    west_counts = west_result.section_result.diagnostics.counts
    assert east_counts["projected"] != west_counts["projected"]

    east_depths = sorted(
        s.depth_mm for s in east_result.section_result.shapes if s.section_mode == SectionMode.PROJECT
    )
    west_depths = sorted(
        s.depth_mm for s in west_result.section_result.shapes if s.section_mode == SectionMode.PROJECT
    )
    assert east_depths != west_depths
