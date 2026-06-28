"""Demo project loading tests."""

from pathlib import Path

from kesit.app.demo import is_demo_available, load_demo_project
from kesit.app.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_demo_available():
    assert is_demo_available(ROOT)


def test_demo_pipeline_produces_cuts():
    project = load_demo_project(ROOT)
    result = run_pipeline(project)
    counts = result.section_result.diagnostics.counts
    assert counts.get("cut", 0) >= 10
    assert project.section.p0 == (-420, -180)
    assert project.section.view_point == (-220, 80)
