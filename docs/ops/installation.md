# Installation & Setup

This guide covers the technical setup and operational commands for the Yahboom Raspbot v2 (Boomy).

## 📊 Prerequisites

*   **Environment**: Python 3.10+
*   **Dependency Manager**: `uv` (recommended) or `pip`
*   **Hardware**: Raspberry Pi 5 core with a ROSMASTER ESP32 expansion board.

## 🚀 Launching the Gateway

The project utilizes a dual-mode FastMCP gateway that bridges human controls (Webapp) and machine controls (AI Agents).

### Standard Execution
To start the unified server on the default port:
```powershell
uv run python -m yahboom_mcp.server --mode dual --port 10792
```

### Modes of Operation
*   `--mode web`: Launch only the React/Vite telemetry dashboard.
*   `--mode mcp`: Launch only the MCP server for AI agent orchestration.
*   `--mode dual`: (Default) Launch both interfaces simultaneously.

---

## 🛠️ Configuration

Operational parameters are managed via `mcp_config.json`. Key fields include:
*   `YAHBOOM_IP`: The static IP address of the Raspbot v2.
*   `ROS_DOMAIN_ID`: Standard ROS 2 domain identifier for network participation.

For detailed hardware setup, refer to [Hardware Technicals](../hardware/).
