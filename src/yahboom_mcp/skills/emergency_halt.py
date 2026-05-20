"""Skill: yahboom-emergency-halt — emergency stop and recovery procedures."""


def yahboom_emergency_halt() -> str:
    """Emergency halt protocol: stop all motion, assess, recover."""
    return """Emergency procedures for the Yahboom Raspbot v2.

## Immediate halt
1. yahboom_tool(operation="stop_all") — kills all motion, lightstrip, and voice.

## Assessment
2. yahboom_tool(operation="health_check") — check if ROS bridge survived.
3. yahboom_tool(operation="read_imu") — orientation (did we flip?).
4. yahboom_tool(operation="read_battery") — power state.
5. lidar(operation="read") — obstacle map around the robot.

## Recovery paths

### Path A: ROS bridge intact, battery ok
   - yahboom_tool(operation="stop") — soft halt.
   - yahboom_tool(operation="forward", param1=0.15) — creep forward slowly to clear obstruction.
   - Re-assess with lidar.

### Path B: ROS bridge lost
   - ros_resync() — attempt topic re-discovery.
   - If ros_resync fails: ros_restart_bringup() — remote restart via SSH.
   - Wait 10 seconds, re-check health.

### Path C: Battery critical (< 15%)
   - Do NOT move the robot.
   - yahboom_tool(operation="led", param1=255, param2=0, param3=0) — red light.
   - Report: "Battery critical. Manual recovery required. Robot at last known position."

## Post-recovery
- Record trajectory if recording was active.
- yahboom_tool(operation="light_effect", param1="patrol") — restore normal light pattern.
- Report summary to operator."""
