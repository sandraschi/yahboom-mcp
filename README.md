# Yahboom ROS 2 MCP Server (v1.2.0)

Industrial-grade agentic control interface for the **Yahboom Raspbot v2** (Raspberry Pi 5 / ROS 2 Humble). This project is a core component of the [Robotics Fleet](docs/fleet_overview.md).

## 🤖 Federated Robotics Fleet
Yahboom-MCP operates as a specialized manipulation and navigation node within a wider federated fleet including:
- **Dreame-MCP**: Floor mapping and autonomous sweeping.
- **Virtual-Robotics-MCP**: Physics-based simulation and testing.
- **Central-Hub**: Intelligent orchestration and fleet-wide lifecycle management.

## 🚀 SOTA 2026 Architecture

This server is built on **FastMCP 3.0** and implements high-density agentic workflows using the **Portmanteau Pattern**.

- **Port**: `10792` (SOTA Webapp Dashboard)
- **Protocol**: FastMCP 3.0 (GA Feb 18, 2026)
- **AI Core**: SEP-1577 Sampling with trajectory reasoning.

## 🛠️ Operations Hub

| Operation | Family | Description |
|-----------|--------|-------------|
| `forward` | Motion | Trajectory-aware motion control |
| `read_imu` | Sensors | 9-axis telemetry feedback |
| `move_to` | Navigation | Autonomous waypoint resolution |
| `health` | Diagnostics | Real-time system integrity |

## 📦 Getting Started

```powershell
# Install dependencies
uv sync

# Start the server (SOTA standard)
uv run yahboom-mcp
```

## 🌐 SOTA Webapp Dashboard

Access the premium monitoring interface at:
[http://localhost:10792](http://localhost:10792)

## ⚖️ Status & Compliance
- [x] FastMCP 3.0 Standard
- [x] SEP-1577 Sampling Verified
- [x] Multi-MCP Integration (Resonite/HumeReady)
- [x] SOTA 2026 Webapp Visuals
- [x] Federated Fleet Integration

## 📚 Documentation
For detailed guides on fleet architecture, integration, and status, see the [docs](docs/) directory:
- [Connectivity Guide](docs/CONNECTIVITY.md) — WiFi setup and robot IP discovery.
- [Architecture](docs/architecture.md) — System design and Portmanteau pattern.
- [Pi-less Setup](docs/PI_LESS_SETUP.md) — High-performance PC-as-Brain configuration.
- [AI & Vision Capabilities](docs/AI_CAPABILITIES.md) — Local LLMs and computer vision on RPi 5.
- [Fleet Overview](docs/fleet_overview.md) — Vision for the federated robotics fleet.
- [Integration Guide](docs/integration_guide.md) — Cross-robot workflows.
- [Project Status](docs/status.md) — Roadmap and completion metrics.
