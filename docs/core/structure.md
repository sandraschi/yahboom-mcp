# Project Structure

```
yahboom-mcp/
├── src/yahboom_mcp/
│   ├── server.py              # Main FastMCP server (Unified SSE/STDIO)
│   ├── stack_probe.py         # TTL health.stack: TCP/SSH/Pi/Docker/ros2 graph, lifecycle, docker logs preview
│   ├── core/                  # Bridge logic (ROS2 & Video)
│   ├── operations/            # Portmanteau library (Motion, Sensors, Trajectory)
│   ├── integrations/          # Multi-MCP sync logic
│   └── fastapi_app.py         # Custom API endpoints
├── webapp/                    # SOTA Frontend (Scaffold)
├── ros2/boomy_mission_executor/  # ROS 2: /boomy/mission JSON → /cmd_vel, optional Nav2 + detections
├── docs/                      # Technical guides (e.g. ops/AGENT_MISSION_AND_MCP.md — LLM missions, MCP, Pi)
├── tests/                     # System tests (Pytest)
├── pyproject.toml             # uv / Hatch configuration
└── start.ps1                  # SOTA 2026 Startup Script
```
