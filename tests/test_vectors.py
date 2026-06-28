from kesit.geometry.section_line import SectionLine
from kesit.geometry.vectors import Vec2, dot


def test_view_point_selects_interior_perpendicular():
    section = SectionLine.from_tuples((0, 0), (0, 10), (5, 5))
    v = section.direction_v()
    assert dot(Vec2(5, 5) - Vec2(0, 0), v) > 0


def test_normalize_and_section_length():
    section = SectionLine.from_tuples((0, 0), (3, 4), (0, 5))
    assert abs(section.section_length() - 5.0) < 1e-9


def test_section_line_angle_from_p0():
    from kesit.ui.widgets.plan_canvas import PlanCanvas

    assert abs(PlanCanvas._angle_from_p0_deg((0, 0), (1, 0)) - 0.0) < 1e-9
    assert abs(PlanCanvas._angle_from_p0_deg((0, 0), (0, 1)) - 90.0) < 1e-9
    assert abs(PlanCanvas._angle_from_p0_deg((10, 10), (10, 20)) - 90.0) < 1e-9
