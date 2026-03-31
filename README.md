# Yahboom ROS 2 MCP Server (v2.0.0-alpha.1)

Industrial-grade agentic control interface for the **Yahboom Raspbot v2** (Raspberry Pi 5 / ROS 2 Humble). This project is a core component of the [Robotics Fleet](docs/fleet_overview.md).

## 🤖 Federated Robotics Fleet
Yahboom-MCP operates as a specialized manipulation and navigation node within a wider federated fleet including:
- **Dreame-MCP**: Floor mapping and autonomous sweeping.
- **Virtual-Robotics-MCP**: Physics-based simulation and testing.
- **Central-Hub**: Intelligent orchestration and fleet-wide lifecycle management.

## 🚀 SOTA 2026 Architecture

This server is built on **FastMCP 3.1** and implements high-density agentic workflows using the **Portmanteau Pattern**, **sampling** (SEP-1577), **prompts**, **skills**, and **scripts**.

- **Port**: `10792` (backend), `10893` (Vite dashboard)
- **Protocol**: FastMCP 3.1
- **AI Core**: SEP-1577 sampling via `yahboom_agentic_workflow`; prompts for quick-start, patrol, diagnostics.

## 🛠️ Tools

| Tool | Description |
|------|-------------|
| `yahboom(operation, ...)` | Single operation: health_check, forward, backward, turn_left, turn_right, strafe_*, stop, read_imu, read_battery, trajectory recording, config_show |
| `yahboom_help(category, topic)` | Multi-level help (motion, sensors, connection, api, mcp_tools, startup, troubleshooting) |
| `yahboom_agentic_workflow(goal)` | High-level goal; LLM plans and runs a sequence of health/motion/sensor steps (sampling with sub-tools) |

## 🛰️ Sensory Hub & Expansion (RPi 5 Bridge)

Boomy's sensory substrate is expanded via a dedicated **Peripheral Bridge** running on the Pi 5, mapping local GPIO and I2C sensors to the ROS 2 bus.

- **Ultrasound (Sonar)**: Proximity detection for reactive avoidance (Benny-safe).
- **Line Follower**: Cliff detection (Table Guard) and line navigation.
- **Physical Button**: Top-mounted "KEY" button for silencing alarms (Snooze) and aborting missions.
- **Auto-Discovery**: I2C bus scanning for SSD1306/SH1106 displays and environmental sensors.

> [!TIP]
> Details on topic mapping and GPIO configuration can be found in [SENSORY_HUB.md](docs/SENSORY_HUB.md).

## 🧠 Mission Intelligence

Advanced autonomous behaviors utilizing the expanded sensory substrate for safe navigation.

- **"Cliff Guard" Dominance**: Real-time cliff detection overrides all movement with an immediate `Emergency Halt`.
- **"Benny-Safe" Avoidance**: Reactive state-machine that executes a 45° tangent-pivot maneuver to bypass obstacles detected by sonar.
- **Physical Silence**: The hardware button provides an immediate manual override for "Smart Alarm" and "Emergency Mode" sequences.

> [!IMPORTANT]
> Detailed autonomous logic and avoidance maneuvers are documented in [AVOIDANCE_STRATEGY.md](docs/AVOIDANCE_STRATEGY.md).

## 📋 Prompts

- `yahboom_quick_start(robot_ip)` — Setup and connect instructions
- `yahboom_patrol(duration_seconds)` — Patrol plan (e.g. square)
- `yahboom_diagnostics()` — Diagnostic checklist

## 📂 Skills & Scripts

- **skills/yahboom-operator.md** — Operator skill: tool usage, prompts, workflow rules
- **skills/yahboom-robots-expert.md** — Expert skill: hardware, ROS 2, URDF/frames, mecanum, fleet integration
- **scripts/check_health.py** — REST health/telemetry (no MCP client): `python scripts/check_health.py [--base http://localhost:10792]`
- **scripts/run_patrol_square.ps1** — Check server and print agentic workflow usage

## 📦 Getting Started

**Robot connection:** The server connects to ROSBridge on the robot. Default robot IP is **192.168.0.250** (Ethernet). Override with env: `YAHBOOM_IP=192.168.0.250` (or `YAHBOOM_IP=192.168.1.11` for WiFi hotspot). Rosbridge port: `YAHBOOM_BRIDGE_PORT=9090` (default).

```powershell
git clone https://github.com/sandraschi/yahboom-mcp.git
Set-Location yahboom-mcp
uv sync

# Start server (stdio for Cursor/Claude; dual for dashboard + MCP)
uv run python -m yahboom_mcp.server --mode stdio
# Or with web dashboard (robot on Ethernet 192.168.0.250 by default):
uv run python -m yahboom_mcp.server --mode dual --port 10792
# Or set robot IP explicitly:
$env:YAHBOOM_IP = "192.168.0.250"; uv run python -m yahboom_mcp.server --mode dual --port 10792
```

## 🌐 SOTA Webapp Dashboard

Backend API: [http://localhost:10792](http://localhost:10792) (when running `--mode dual`).  
Dashboard UI: [http://localhost:10893](http://localhost:10893) (Vite dev server; start via `webapp/start.bat` or `start.ps1`).

## 🧰 Hardware Diagnostics & Boomy Insight

This project includes a high-performance diagnostic bridge to resolve the Raspberry Pi 5's I2C timing anomalies.

- **Diagnostic Dashboard**: Access via `/diagnostics` for real-time `dmesg` streaming and I2C health status.
- **Remote Shell**: Integrated SSH-over-FastAPI shell for hardware maintenance and recovery.
- **I2C Stability Patch**: Standardized **100kHz** baudrate cap for consistent expansion board communication.
- **WiFi Transition Guide**: See the [WiFi Transition Guide](docs/WIFI_TRANSITION.md) for Ethernet-to-AP migration.

## ⚖️ Status & Compliance
- [x] FastMCP 3.1 (sampling, prompts)
- [x] SEP-1577 agentic workflow tool
- [x] Multi-MCP Integration (Resonite/HumeReady)
- [x] SOTA 2026 Webapp Visuals
- [x] Federated Fleet Integration
- [x] **Sensory Hub & "Benny-Safe" Avoidance**
- [x] **Physical Button Override**

## 📚 Documentation
For detailed guides on fleet architecture, integration, and status, see the [docs](docs/) directory:
- [Connectivity Guide](docs/CONNECTIVITY.md) — WiFi setup and robot IP discovery.
- [Architecture](docs/architecture.md) — System design and Portmanteau pattern.
- [Pi-less Setup](docs/PI_LESS_SETUP.md) — High-performance PC-as-Brain configuration.
- [Hardware & ROS 2](docs/HARDWARE_AND_ROS2.md) — Pi tiers, ROS 2 interaction, terminal tools, LIDAR integration.
- [Sensory Hub](docs/SENSORY_HUB.md) — Technical details on Ultrasound, Line sensors, and Pi 5 Button mapping.
- [Avoidance Strategy](docs/AVOIDANCE_STRATEGY.md) — "Benny-Safe" reactive navigation and Cliff Guard logic.
- [Raspbot motion troubleshooting](docs/RASPBOT_MOTION_TROUBLESHOOTING.md) — Camera works but no drive; SSH and `/cmd_vel` checks.
- [Webapp 3D Viz](docs/WEBAPP_3D_VIZ.md) — R3F scene, Y-up vs URDF Z-up, wheel/chassis placement.
- [Testing](docs/TESTING.md) — pytest layout, `MockROS2Bridge`, `YAHBOOM_USE_MOCK_BRIDGE`, hardware markers.
- [Embodied AI](docs/EMBODIED_AI.md) — Observe -> LLM -> act loop, snapshot/move API.
- [Neurophilosophy overview](docs/NEUROPHILOSOPHY_OVERVIEW.md) — Damasio, GWT, IIT, enactivism; arxiv papers; link to embodied loop.
- [Boomy Racing Vision](docs/BOOMY_RACING_VISION.md) — Dual-robot competition, "Shazbat!" collision protocol, and FPV racing.
- [AI & Vision Capabilities](docs/AI_CAPABILITIES.md) — Local LLMs and computer vision on RPi 5.
- [Fleet Overview](docs/fleet_overview.md) — Vision for the federated robotics fleet.
- [Integration Guide](docs/integration_guide.md) — Cross-robot workflows.
- [Project Status](docs/status.md) — Roadmap and completion metrics.
- [WiFi Transition Guide](docs/WIFI_TRANSITION.md) — Ethernet-to-AP migration steps.
