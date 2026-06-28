from kesit.geometry.section_line import SectionLine
from kesit.geometry.vectors import Vec2


def test_project_point_along_section():
    section = SectionLine.from_tuples((0, 0), (10, 0), (5, 5))
    s, d = section.project_point(Vec2(5, 3))
    assert abs(s - 5) < 1e-9
    assert abs(d - 3) < 1e-9


def test_project_point_on_section_line():
    section = SectionLine.from_tuples((0, 0), (10, 0), (5, 5))
    s, d = section.project_point(Vec2(4, 0))
    assert abs(s - 4) < 1e-9
    assert abs(d) < 1e-9
