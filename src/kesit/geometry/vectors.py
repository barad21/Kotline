"""2D vector utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalize(self) -> Vec2:
        length = self.length()
        if length < 1e-12:
            raise ValueError("Cannot normalize zero-length vector")
        return Vec2(self.x / length, self.y / length)

    def perpendicular_ccw(self) -> Vec2:
        return Vec2(-self.y, self.x)

    def perpendicular_cw(self) -> Vec2:
        return Vec2(self.y, -self.x)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


def dot(a: Vec2, b: Vec2) -> float:
    return a.dot(b)


def normalize(v: Vec2) -> Vec2:
    return v.normalize()


def distance(a: Vec2, b: Vec2) -> float:
    return (a - b).length()


def angle_degrees(v: Vec2) -> float:
    return math.degrees(math.atan2(v.y, v.x))
