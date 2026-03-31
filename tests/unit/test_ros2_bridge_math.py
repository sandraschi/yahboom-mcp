"""Unit tests for pure helpers in ros2_bridge (no network, no ROS)."""

from __future__ import annotations

import math

import pytest

from yahboom_mcp.core.ros2_bridge import _quat_to_euler_deg, _scan_to_obstacle_summary


@pytest.mark.unit
def test_quat_identity_heading() -> None:
    q = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    e = _quat_to_euler_deg(q)
    assert abs(e["roll"]) < 0.01
    assert abs(e["pitch"]) < 0.01
    assert abs(e["yaw"]) < 0.01


@pytest.mark.unit
def test_scan_to_obstacle_summary_empty() -> None:
    s = _scan_to_obstacle_summary([], 0.0, 0.1)
    assert all(v is None for v in s.values())


@pytest.mark.unit
def test_scan_to_obstacle_summary_front_sector() -> None:
    # 8 sectors over 2π; index 0 maps to front sector name in implementation
    n = 40
    angle_min = 0.0
    angle_increment = 2 * math.pi / n
    ranges = [float("inf")] * n
    ranges[0] = 1.0
    s = _scan_to_obstacle_summary(ranges, angle_min, angle_increment)
    assert s["front"] == 1.0
