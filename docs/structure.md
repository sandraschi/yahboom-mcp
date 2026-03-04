# Project Structure

```
yahboom-mcp/
├── src/yahboom_mcp/
│   ├── server.py              # Main FastMCP server (Unified SSE/STDIO)
│   ├── core/                  # Bridge logic (ROS2 & Video)
│   ├── operations/            # Portmanteau library (Motion, Sensors, Trajectory)
│   ├── integrations/          # Multi-MCP sync logic
│   └── fastapi_app.py         # Custom API endpoints
├── webapp/                    # SOTA Frontend (Scaffold)
├── docs/                      # Technical Guides & Fleet Vision
├── tests/                     # System tests (Pytest)
├── pyproject.toml             # uv / Hatch configuration
└── start.ps1                  # SOTA 2026 Startup Script
```
