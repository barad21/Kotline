"""Depth-based colors for section preview gradient mode."""

from __future__ import annotations

from kesit.models import ShapeKind
from kesit.ui import theme


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return _rgb_to_hex(r, g, bl)


def gradient_at(t: float) -> str:
    return _lerp_color(theme.DEPTH_NEAR, theme.DEPTH_FAR, t)


def depth_factor(depth_mm: float | None, section_depth_mm: float) -> float:
    if depth_mm is None:
        return 0.0
    if section_depth_mm <= 0:
        return 0.0
    return max(0.0, min(1.0, depth_mm / section_depth_mm))


def depth_to_fill(
    depth_mm: float | None,
    section_depth_mm: float,
    kind: ShapeKind,
) -> str:
    if kind in (ShapeKind.CUT, ShapeKind.BASELINE):
        return theme.DEPTH_CUT_FILL
    t = depth_factor(depth_mm, section_depth_mm)
    return _lerp_color(theme.DEPTH_NEAR, theme.DEPTH_FAR, t)


def depth_to_stroke(
    depth_mm: float | None,
    section_depth_mm: float,
    kind: ShapeKind,
) -> str:
    if kind in (ShapeKind.CUT, ShapeKind.BASELINE):
        return theme.DEPTH_CUT_STROKE
    # Outline uses the same near->far endpoints as the legend (gradient_at),
    # only slightly lightened so thin edges stay legible over their own fill.
    t = depth_factor(depth_mm, section_depth_mm)
    base = _lerp_color(theme.DEPTH_NEAR, theme.DEPTH_FAR, t)
    return _lerp_color(base, "#ffffff", 0.12)
