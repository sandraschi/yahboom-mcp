"""Skill: yahboom-quick-pilot — rapid manual driving & telemetry check."""


def yahboom_quick_pilot() -> str:
    """Quick-start skill: manual driving and basic telemetry for the Yahboom Raspbot v2."""
    return """You are piloting the Yahboom Raspbot v2 in manual mode.

## Pre-flight
1. yahboom_tool(operation="health_check") — confirm ROS bridge + battery.
2. yahboom_tool(operation="read_battery") — battery percentage.
3. yahboom_tool(operation="read_imu") — heading, pitch, roll.

## Driving
- yahboom_tool(operation="forward", param1=0.3) — forward at 0.3 m/s.
- yahboom_tool(operation="turn_left", param1=0.5) — turn left 0.5 rad/s.
- yahboom_tool(operation="stop") — halt immediately.
- yahboom_tool(operation="strafe_left", param1=0.2) — lateral strafe.

## Sensors
- yahboom_tool(operation="read_all") — full telemetry dump.
- lidar(operation="read") — obstacle distances per 8 sectors.

## Quick run
Execute: health_check → forward (3s) → stop → read_all. Report heading and obstacles."""
