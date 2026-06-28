"""Geometry cleanup helpers."""

from __future__ import annotations

from shapely.geometry import LineString


def remove_zero_length_lines(lines: list[LineString], tolerance: float = 1e-6) -> tuple[list[LineString], int]:
    kept: list[LineString] = []
    removed = 0
    for line in lines:
        if line.length <= tolerance:
            removed += 1
            continue
        kept.append(line)
    return kept, removed
