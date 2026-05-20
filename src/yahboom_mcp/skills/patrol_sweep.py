"""Skill: yahboom-patrol-sweep — autonomous patrol circuit."""


def yahboom_patrol_sweep() -> str:
    """Autonomous patrol pattern: square circuit with obstacle awareness."""
    return """Execute a safe patrol circuit with the Yahboom Raspbot v2.

## Phase 1: Pre-mission
1. yahboom_tool(operation="health_check") — verify ROS bridge and battery > 20%.
2. lidar(operation="read") — check nearest obstacle in each sector.

## Phase 2: Square patrol (4 sides)
For each side of the square:
  a. yahboom_tool(operation="forward", param1=0.3) — drive 3 seconds.
  b. yahboom_tool(operation="stop") — pause.
  c. lidar(operation="read") — re-check obstacles at the corner.
  d. yahboom_tool(operation="turn_left", param1=0.5) — rotate ~90 degrees (adjust param1 for timing).

After all 4 sides:
  e. yahboom_tool(operation="read_battery") — report final charge.
  f. yahboom_tool(operation="stop_all") — ensure full halt.

## Obstacle handling
If lidar reports nearest_m < 0.5m: stop, turn right 45 degrees, re-scan.
If path is still blocked after two attempts: call stop_all and report position.

## Notes
- Use `yahboom_agentic_workflow` for complex multi-step goals if the agentic loop is active.
- The patrol speed defaults to 0.3 m/s (safe for indoor mapping)."""
