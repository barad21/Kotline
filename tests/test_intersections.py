from shapely.geometry import LineString, Polygon

from kesit.geometry.intersections import intersection_interval_s, intersects
from kesit.geometry.section_line import SectionLine


def test_polygon_intersection_interval():
    section = SectionLine.from_tuples((5, 0), (5, 10), (8, 5))
    wall = Polygon([(4, 2), (6, 2), (6, 8), (4, 8)])
    assert intersects(section, wall)
    interval = intersection_interval_s(section, wall)
    assert interval is not None
    s_min, s_max = interval
    assert s_min <= s_max


def test_line_not_intersecting():
    section = SectionLine.from_tuples((0, 0), (10, 0), (5, 5))
    line = LineString([(5, 5), (5, 8)])
    assert not intersects(section, line)
    assert intersection_interval_s(section, line) is None
