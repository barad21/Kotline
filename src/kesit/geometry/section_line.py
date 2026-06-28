"""Section line basis and point projection."""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString

from kesit.geometry.vectors import Vec2, dot, normalize


@dataclass
class SectionLine:
    p0: Vec2
    p1: Vec2
    view_point: Vec2
    min_length: float = 1e-6

    def __post_init__(self) -> None:
        direction = self.p1 - self.p0
        if direction.length() < self.min_length:
            raise ValueError("Section line endpoints must be distinct")

    @classmethod
    def from_tuples(
        cls,
        p0: tuple[float, float],
        p1: tuple[float, float],
        view_point: tuple[float, float],
    ) -> SectionLine:
        return cls(
            p0=Vec2(*p0),
            p1=Vec2(*p1),
            view_point=Vec2(*view_point),
        )

    def direction_u(self) -> Vec2:
        return normalize(self.p1 - self.p0)

    def direction_v(self) -> Vec2:
        u = self.direction_u()
        ccw = u.perpendicular_ccw()
        cw = u.perpendicular_cw()
        mid = Vec2(
            (self.p0.x + self.p1.x) / 2,
            (self.p0.y + self.p1.y) / 2,
        )
        to_view = self.view_point - mid
        if dot(to_view, ccw) >= dot(to_view, cw):
            return normalize(ccw)
        return normalize(cw)

    def section_length(self) -> float:
        return (self.p1 - self.p0).length()

    def project_point(self, p: Vec2 | tuple[float, float]) -> tuple[float, float]:
        if not isinstance(p, Vec2):
            p = Vec2(p[0], p[1])
        rel = p - self.p0
        u = self.direction_u()
        v = self.direction_v()
        s = dot(rel, u)
        d = dot(rel, v)
        return s, d

    def as_shapely_line(self) -> LineString:
        return LineString([self.p0.as_tuple(), self.p1.as_tuple()])

    def to_dict(self) -> dict[str, list[float]]:
        return {
            "p0": list(self.p0.as_tuple()),
            "p1": list(self.p1.as_tuple()),
            "view_point": list(self.view_point.as_tuple()),
        }
