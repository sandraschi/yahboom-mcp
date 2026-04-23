# Installation & Setup

This guide covers **developer** setup on Goliath. For **operators** (power, Wi‑Fi AP, Ethernet, Docker/bringup on the Pi, and what the dashboard can do), read **[Startup & bringup](STARTUP_AND_BRINGUP.md)** first.

## Prerequisites

- **Python**: 3.12+ (see `pyproject.toml`).
- **Dependency manager**: `uv` (recommended).
- **Hardware**: Raspberry Pi 5 on the Raspbot; optional ESP32 ROSMASTER tier (USB to Pi).

## Launching the unified gateway

The gateway serves **REST + MCP (SSE)** on one port; the Vite dashboard proxies `/api` to it.

### Standard (fleet ports)

From repo root:

```powershell
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port 10892
```

Or use **`webapp/start.ps1`**, which runs **`uv sync`**, starts the server on **10892**, and **`npm run dev`** on **10893** with the correct working directory.

### Modes

- **`--mode stdio`** — MCP over stdio (e.g. Cursor); no HTTP dashboard.
- **`--mode dual`** / **`http`** — FastAPI + MCP SSE (Unified Gateway); use with the webapp.

### Configuration (env)

- **`YAHBOOM_IP`** — Pi address (default in scripts often `192.168.1.11`).
- **`YAHBOOM_BRIDGE_PORT`** — rosbridge WebSocket port (default **9090**).
- **`YAHBOOM_FALLBACK_IP`** — Optional second address (e.g. Ethernet) when the robot exposes two paths.

Further reading: [ROSBRIDGE.md](../hardware/ROSBRIDGE.md), [ROSBRIDGE_AT_BOOT.md](ROSBRIDGE_AT_BOOT.md).
