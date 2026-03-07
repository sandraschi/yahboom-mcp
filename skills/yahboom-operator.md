# Yahboom G1 Operator Skill

Use this skill when controlling or troubleshooting a Yahboom ROSmaster G1 (or compatible) robot via the Yahboom MCP server.

## Tool Set

- **yahboom(operation, param1, param2, payload)** — Single operation. `operation` one of: `health_check`, `forward`, `backward`, `turn_left`, `turn_right`, `strafe_left`, `strafe_right`, `stop`, `read_imu`, `read_battery`, `read_encoders`, `start_recording`, `stop_recording`, `list_trajectories`, `config_show`. Use `param1` for speed/duration where applicable.
- **yahboom_help(category, topic)** — Drill-down help. Categories: motion, sensors, connection, api, mcp_tools, startup, troubleshooting.
- **yahboom_agentic_workflow(goal)** — High-level goal (SEP-1577). Describe what you want the robot to do in natural language; the LLM plans and runs a sequence of health/motion/sensor steps.

## Prompts

- **yahboom_quick_start(robot_ip)** — Setup instructions for connecting the server to the robot.
- **yahboom_patrol(duration_seconds)** — Get a patrol plan (e.g. square or figure-8).
- **yahboom_diagnostics()** — Diagnostic checklist for connection and sensors.

## Workflow Rules

1. Always run `yahboom(operation='health_check')` before motion to confirm bridge and battery.
2. Use `yahboom_agentic_workflow` for multi-step goals (patrol, inspect, return); use single `yahboom` calls for one-off commands.
3. For low battery (< 20%) avoid long motions; suggest charging.
4. Recording trajectories: `start_recording`, then motion, then `stop_recording` with a name.

## Scripts

- `scripts/check_health.py` — Call REST API health/telemetry (no MCP client).
- `scripts/run_patrol_square.ps1` — Example: start server in dual mode and open dashboard (user runs agentic workflow from Chat or MCP client).
