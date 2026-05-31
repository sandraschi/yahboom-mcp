"""Floor-draw path patterns for Boomy (open-loop odometry, chalk/marker mount)."""

from __future__ import annotations

import math
from typing import Any


def _circle_points(cx: float, cy: float, r: float, n: int = 24) -> list[tuple[float, float]]:
    return [
        (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def _polyline_to_segments(
    points: list[tuple[float, float]],
    *,
    speed: float,
) -> list[dict[str, Any]]:
    if len(points) < 2:
        return []
    segments: list[dict[str, Any]] = []
    heading = 0.0
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 0.005:
            continue
        target = math.atan2(dy, dx)
        dtheta = (target - heading + math.pi) % (2 * math.pi) - math.pi
        if abs(dtheta) > 0.08:
            segments.append({"kind": "turn", "angle_rad": dtheta, "rate": 0.45})
            heading = target
        segments.append({"kind": "drive", "distance_m": dist, "speed": speed})
    return segments


def list_patterns() -> dict[str, Any]:
    return {
        "success": True,
        "patterns": [
            {
                "id": "smiley",
                "colors": 2,
                "description": "Circle face + eyes (color 1), smile arc (color 2)",
            },
            {
                "id": "heart",
                "colors": 2,
                "description": "Heart outline (color 1), inner highlight (color 2)",
            },
            {
                "id": "boomy_b",
                "colors": 1,
                "description": "Stylised letter B for Boomy branding",
            },
        ],
        "hardware_notes": (
            "Mount spring-loaded chalk/marker on chassis (~15° down). "
            "Two-color: dual holder + servo, or manual swap at color_swap pause."
        ),
    }


def pattern_layers(pattern_id: str, *, speed: float = 0.06) -> list[dict[str, Any]]:
    """Return ordered draw layers: each has color index + motion segments."""
    pid = pattern_id.strip().lower()
    if pid == "smiley":
        face = _circle_points(0.0, 0.0, 0.18, n=28)
        left_eye = [(0.06, 0.06), (0.06, 0.06)]
        right_eye = [(-0.06, 0.06), (-0.06, 0.06)]
        smile = _circle_points(0.0, -0.02, 0.10, n=14)[3:11]
        return [
            {
                "color": 1,
                "label": "outline",
                "segments": _polyline_to_segments(face + left_eye + right_eye, speed=speed),
            },
            {
                "color": 2,
                "label": "smile",
                "segments": _polyline_to_segments(smile, speed=speed),
            },
        ]
    if pid == "heart":
        pts: list[tuple[float, float]] = []
        for t in range(65):
            ang = math.pi * t / 32
            x = 0.16 * math.sin(ang) ** 3
            y = 0.13 * math.cos(ang) - 0.05 * math.cos(2 * ang) - 0.02
            pts.append((x, y))
        inner = [(p[0] * 0.55, p[1] * 0.55 - 0.02) for p in pts[10:40:3]]
        return [
            {
                "color": 1,
                "label": "heart_outline",
                "segments": _polyline_to_segments(pts, speed=speed),
            },
            {
                "color": 2,
                "label": "highlight",
                "segments": _polyline_to_segments(inner, speed=speed),
            },
        ]
    if pid == "boomy_b":
        # Stylised B in ~40cm tall box (metres)
        stem = [(0.0, 0.0), (0.0, 0.35)]
        top_loop = _circle_points(0.08, 0.26, 0.09, n=12)[0:7]
        bot_loop = _circle_points(0.08, 0.09, 0.09, n=12)[0:7]
        pts = stem + top_loop + [(0.0, 0.17)] + bot_loop + [(0.0, 0.0)]
        return [
            {
                "color": 1,
                "label": "letter_b",
                "segments": _polyline_to_segments(pts, speed=speed),
            },
        ]
    raise ValueError(f"Unknown pattern: {pattern_id}")
