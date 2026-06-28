from shapely.geometry import LineString

from kesit.architecture.wall_extraction import extract_walls_from_lines


def test_pair_parallel_lines_into_wall():
    line_a = LineString([(0, 0), (100, 0)])
    line_b = LineString([(0, 10), (100, 10)])
    result = extract_walls_from_lines(
        [line_a, line_b],
        angle_tolerance=2,
        min_offset=5,
        max_offset=300,
    )
    assert result.paired_count == 1
    assert len(result.walls) == 1
    assert result.walls[0].area > 0


def test_orphan_line_when_no_pair():
    line_a = LineString([(0, 0), (10, 0)])
    result = extract_walls_from_lines([line_a], min_offset=5, max_offset=300)
    assert result.paired_count == 0
    assert len(result.orphan_lines) == 1
